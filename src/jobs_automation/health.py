"""System health check and diagnostic monitoring for Jobs Automation OS."""

from __future__ import annotations

import datetime
import time
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select, text

from jobs_automation.automation.adapters.registry import ATSAdapterRegistry
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.db.models import (
    AuditLogModel,
    InboundMessageModel,
    PolicyRegistryModel,
    TaskModel,
)


class ComponentHealth(BaseModel):
    """Health status and diagnostic metrics for an individual component."""

    name: str
    status: str  # HEALTHY | DEGRADED | UNHEALTHY
    message: str
    latency_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class HealthReport(BaseModel):
    """Consolidated system health report."""

    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    overall_status: str  # HEALTHY | DEGRADED | UNHEALTHY
    components: dict[str, ComponentHealth] = Field(default_factory=dict)


class HealthCheckService:
    """Evaluates readiness, connectivity, security switches, and operational state."""

    def __init__(self, session_factory: Any) -> None:
        self.session_factory = session_factory

    def check_database(self) -> ComponentHealth:
        """Verifies database connectivity, query latency, and pending task load."""
        start = time.perf_counter()
        try:
            with self.session_factory() as session:
                session.execute(text("SELECT 1"))
                from jobs_automation.db.canary_provenance import durable_canary_provenance

                provenance = durable_canary_provenance(session)
                pending_task_rows = session.scalars(
                    select(TaskModel).where(TaskModel.status == "pending")
                ).all()
                pending_tasks = sum(
                    not provenance.task_is_quarantined(task) for task in pending_task_rows
                )
                excluded_pending_tasks = len(pending_task_rows) - pending_tasks
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            status = "HEALTHY" if elapsed_ms < 500 else "DEGRADED"
            return ComponentHealth(
                name="database",
                status=status,
                message=f"Connected in {elapsed_ms}ms, {pending_tasks} pending tasks in queue.",
                latency_ms=elapsed_ms,
                details={
                    "pending_tasks": pending_tasks,
                    "reconciliation_only_pending_tasks_excluded": excluded_pending_tasks,
                },
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(
                name="database",
                status="UNHEALTHY",
                message=f"Database connection failed: {exc}",
                latency_ms=elapsed_ms,
                details={"error": str(exc)},
            )

    def check_kill_switches(self) -> ComponentHealth:
        """Inspects global and per-platform safety kill switches."""
        ks = KillSwitchManager()
        global_killed, global_reason = ks.is_global_active()
        greenhouse_killed, _ = ks.is_platform_active("greenhouse")
        lever_killed, _ = ks.is_platform_active("lever")
        details = {
            "global_kill_switch_active": global_killed,
            "greenhouse_killed": greenhouse_killed,
            "lever_killed": lever_killed,
        }
        if global_killed:
            return ComponentHealth(
                name="kill_switches",
                status="DEGRADED",
                message=f"Global automation kill switch is ACTIVE: {global_reason}",
                details=details,
            )
        return ComponentHealth(
            name="kill_switches",
            status="HEALTHY",
            message="Kill switches nominal. Submissions permitted according to policy.",
            details=details,
        )

    def check_policy_registry(self) -> ComponentHealth:
        """Inspects policy registry for expired policy reviews."""
        try:
            with self.session_factory() as session:
                policies = session.scalars(select(PolicyRegistryModel)).all()
                now = datetime.datetime.now(datetime.UTC)
                expired: list[str] = []
                for p in policies:
                    if p.review_due_at and p.review_due_at < now:
                        expired.append(f"{p.platform} ({p.domain_pattern})")

                if expired:
                    return ComponentHealth(
                        name="policy_registry",
                        status="DEGRADED",
                        message=f"{len(expired)} platform policy reviews are expired.",
                        details={"expired_platforms": expired},
                    )

                return ComponentHealth(
                    name="policy_registry",
                    status="HEALTHY",
                    message=f"{len(policies)} platform policies verified and up to date.",
                    details={"total_policies": len(policies)},
                )
        except Exception as exc:
            return ComponentHealth(
                name="policy_registry",
                status="UNHEALTHY",
                message=f"Failed to query policy registry: {exc}",
                details={"error": str(exc)},
            )

    def check_adapters(self) -> ComponentHealth:
        """Inspects availability of registered automated ATS adapters, distinguishing live-capable vs mock-only."""
        registry = ATSAdapterRegistry()
        adapters = registry.registered_platforms
        if not adapters:
            return ComponentHealth(
                name="adapters",
                status="DEGRADED",
                message="No ATS adapters registered in registry.",
                details={"registered_platforms": [], "live_capable_platforms": []},
            )

        # In current release, greenhouse and lever return NOT_IMPLEMENTED for live external submission unless mock_mode is active.
        live_capable: list[str] = []
        for name in adapters:
            adp = registry.find_adapter(f"boards.{name}.io") or registry.find_adapter(
                f"jobs.{name}.co"
            )
            if hasattr(adp, "is_live_capable") and getattr(adp, "is_live_capable"):
                live_capable.append(name)

        status = "HEALTHY" if live_capable else "DEGRADED"
        msg = f"{len(adapters)} ATS adapters registered ({', '.join(adapters)}), {len(live_capable)} live-capable."
        if not live_capable:
            msg += " (Live automation NOT_IMPLEMENTED; simulation/mock mode only)."

        return ComponentHealth(
            name="adapters",
            status=status,
            message=msg,
            details={
                "registered_platforms": adapters,
                "live_capable_platforms": live_capable,
                "simulation_only_platforms": [p for p in adapters if p not in live_capable],
            },
        )

    # Threshold for marking a RUNNING record as stale/interrupted (seconds)
    WORKER_STALE_RUN_THRESHOLD_SECONDS: int = 7200  # 2 hours

    def check_worker(self) -> ComponentHealth:
        """Inspects crash-durable worker run history and reports execution state.

        Follows B-R20-05:
        - Reads worker_run (begin) and worker_run_finished (finalize) AuditLog records.
        - Identifies newest attempt by comparing begin and finish records.
        - True latest-attempt worker health reflects unfinished RUNNING attempts.
        - Detects stale RUNNING records (begin with no matching finish after threshold).
        - Exposes: last_attempt_at, last_attempt_status, last_success_at, last_error_at,
          last_error_category, last_reconciliation_at, stale_running_run, stale_run_id.
        """
        try:
            with self.session_factory() as session:
                now = datetime.datetime.now(datetime.UTC)

                # 1. Find the most recent begin record
                last_begin = session.scalar(
                    select(AuditLogModel)
                    .where(AuditLogModel.action_type == "worker_run")
                    .order_by(AuditLogModel.occurred_at.desc())
                )

                # 2. Find the most recent finalize record
                last_finish = session.scalar(
                    select(AuditLogModel)
                    .where(AuditLogModel.action_type == "worker_run_finished")
                    .order_by(AuditLogModel.occurred_at.desc())
                )

                # 3. Detect unfinished or stale RUNNING attempt
                stale_running = False
                stale_run_id: str | None = None
                is_currently_running = False

                if last_begin and last_begin.result == "RUNNING":
                    run_id = last_begin.external_reference
                    has_finish = session.scalar(
                        select(AuditLogModel)
                        .where(AuditLogModel.action_type == "worker_run_finished")
                        .where(AuditLogModel.external_reference == run_id)
                    )
                    if not has_finish:
                        age_seconds = (now - last_begin.occurred_at).total_seconds()
                        if age_seconds > self.WORKER_STALE_RUN_THRESHOLD_SECONDS:
                            stale_running = True
                            stale_run_id = run_id
                        else:
                            is_currently_running = True

                # 4. Scan recent finishes for last success, last error, last reconciliation
                last_success_at: str | None = None
                last_error_at: str | None = None
                last_error_category: str | None = None
                last_reconciliation_at: str | None = None

                recent_finishes = session.scalars(
                    select(AuditLogModel)
                    .where(AuditLogModel.action_type == "worker_run_finished")
                    .order_by(AuditLogModel.occurred_at.desc())
                    .limit(50)
                ).all()

                for f in recent_finishes:
                    f_meta = f.metadata_json or {}
                    if f.result == "SUCCESS" and last_success_at is None:
                        last_success_at = f.occurred_at.isoformat()
                    if f.result in ("FAILED", "PARTIAL") and last_error_at is None:
                        last_error_at = f.occurred_at.isoformat()
                        cats = f_meta.get("error_categories", [])
                        if cats:
                            last_error_category = cats[0]
                        elif f_meta.get("sample_errors"):
                            last_error_category = f_meta["sample_errors"][0]
                    if f_meta.get("reconciliation_performed") and last_reconciliation_at is None:
                        last_reconciliation_at = f.occurred_at.isoformat()

                # Determine true latest attempt
                if last_begin and (
                    not last_finish or last_begin.occurred_at > last_finish.occurred_at
                ):
                    # True newest attempt is the begin record (RUNNING or interrupted)
                    last_attempt_at = last_begin.occurred_at.isoformat()
                    last_attempt_status = "RUNNING"
                    attempt_age_seconds = (now - last_begin.occurred_at).total_seconds()
                elif last_finish:
                    last_attempt_at = last_finish.occurred_at.isoformat()
                    last_attempt_status = last_finish.result
                    attempt_age_seconds = (now - last_finish.occurred_at).total_seconds()
                else:
                    # Fall back to legacy worker_sweep if present
                    last_sweep = session.scalar(
                        select(AuditLogModel)
                        .where(AuditLogModel.action_type == "worker_sweep")
                        .order_by(AuditLogModel.occurred_at.desc())
                    )
                    if last_sweep:
                        age_seconds = (now - last_sweep.occurred_at).total_seconds()
                        has_errors = bool(last_sweep.metadata_json.get("errors"))
                        status = "DEGRADED" if (has_errors or age_seconds > 28800) else "HEALTHY"
                        return ComponentHealth(
                            name="worker",
                            status=status,
                            message=(
                                f"Last worker sweep {round(age_seconds / 60, 1)}m ago "
                                f"({last_sweep.result}). [legacy record]"
                            ),
                            details={
                                "last_attempt_at": last_sweep.occurred_at.isoformat(),
                                "last_attempt_status": last_sweep.result,
                                "last_success_at": None,
                                "last_error_at": None,
                                "last_error_category": None,
                                "last_reconciliation_at": None,
                                "age_seconds": round(age_seconds, 1),
                                "stale_running_run": False,
                                "stale_run_id": None,
                                "metrics": last_sweep.metadata_json,
                            },
                        )
                    return ComponentHealth(
                        name="worker",
                        status="DEGRADED",
                        message="No worker runs have been recorded yet.",
                        details={
                            "last_attempt_at": None,
                            "last_attempt_status": None,
                            "last_success_at": None,
                            "last_error_at": None,
                            "last_error_category": None,
                            "last_reconciliation_at": None,
                            "age_seconds": None,
                            "stale_running_run": False,
                            "stale_run_id": None,
                            "metrics": {},
                        },
                    )

                fin_meta = (last_finish.metadata_json or {}) if last_finish else {}
                has_errors = bool(fin_meta.get("error_count", 0)) or last_attempt_status == "FAILED"
                is_stale = attempt_age_seconds > 28800  # 8 hours without a run

                if stale_running or last_attempt_status == "FAILED" or is_stale:
                    status = "DEGRADED"
                elif has_errors:
                    status = "DEGRADED"
                else:
                    status = "HEALTHY"

                stale_note = (
                    f" STALE_RUNNING run_id={stale_run_id} detected." if stale_running else ""
                )
                running_note = " [RUNNING in progress]" if is_currently_running else ""

                return ComponentHealth(
                    name="worker",
                    status=status,
                    message=(
                        f"Last worker run {round(attempt_age_seconds / 60, 1)}m ago "
                        f"({last_attempt_status}).{stale_note}{running_note}"
                    ),
                    details={
                        "last_attempt_at": last_attempt_at,
                        "last_attempt_status": last_attempt_status,
                        "last_success_at": last_success_at,
                        "last_error_at": last_error_at,
                        "last_error_category": last_error_category,
                        "last_reconciliation_at": last_reconciliation_at,
                        "age_seconds": round(attempt_age_seconds, 1),
                        "stale_running_run": stale_running,
                        "stale_run_id": stale_run_id,
                        "metrics": fin_meta,
                    },
                )
        except Exception as exc:
            return ComponentHealth(
                name="worker",
                status="UNHEALTHY",
                message=f"Failed to inspect worker status: {exc}",
                details={"error": str(exc)},
            )

    def check_gmail(self, readiness_result: dict[str, Any] | None = None) -> ComponentHealth:
        """Inspects Gmail adapter readiness without heuristic credential assumptions.

        Follows B-R20-04:
        - Fails safely as DEGRADED / NOT_INTEGRATED unless an explicit typed readiness
          result is provided (supplied by Lane C's J20G-03 service).
        - Avoids any environment variable heuristic (e.g. GMAIL_CREDENTIALS_JSON) that
          could falsely claim live readiness.
        """
        try:
            with self.session_factory() as session:
                from jobs_automation.db.canary_provenance import durable_canary_provenance

                provenance = durable_canary_provenance(session)
                messages = session.scalars(
                    select(InboundMessageModel).order_by(InboundMessageModel.received_at.desc())
                ).all()
                visible_messages = [
                    message
                    for message in messages
                    if str(message.id) not in provenance.message_references
                ]
                last_msg = visible_messages[0] if visible_messages else None
                last_received_at = last_msg.received_at.isoformat() if last_msg else None
                excluded_messages = len(messages) - len(visible_messages)

            if readiness_result is not None:
                # Typed readiness result supplied (e.g. from Lane C's diagnostic service)
                status = readiness_result.get("status", "DEGRADED")
                message = readiness_result.get("message", f"Gmail readiness verified: {status}")
                details = dict(readiness_result)
                details["last_message_received_at"] = last_received_at
                details["durable_canary_messages_excluded"] = excluded_messages
                return ComponentHealth(
                    name="gmail",
                    status=status,
                    message=message,
                    details=details,
                )

            # Secret-free, non-interactive readiness assessment (V17-M03). It never
            # launches OAuth or touches the mailbox; PROVEN requires a recorded real run.
            from jobs_automation.ingestion.readiness import assess_gmail_readiness

            with self.session_factory() as session:
                readiness = assess_gmail_readiness(session=session)
            details = readiness.to_health_result()
            details["last_message_received_at"] = last_received_at
            details["durable_canary_messages_excluded"] = excluded_messages
            return ComponentHealth(
                name="gmail",
                status=str(details["status"]),
                message=str(details["message"]),
                details=details,
            )
        except Exception as exc:
            return ComponentHealth(
                name="gmail",
                status="UNHEALTHY",
                message=f"Failed to check Gmail health: {exc}",
                details={"error": str(exc)},
            )

    def run_full_check(self) -> HealthReport:
        """Executes all diagnostics and returns consolidated health report."""
        components = {
            "database": self.check_database(),
            "kill_switches": self.check_kill_switches(),
            "policy_registry": self.check_policy_registry(),
            "adapters": self.check_adapters(),
            "worker": self.check_worker(),
            "gmail": self.check_gmail(),
        }

        # Calculate overall status
        statuses = [c.status for c in components.values()]
        if "UNHEALTHY" in statuses:
            overall = "UNHEALTHY"
        elif "DEGRADED" in statuses:
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return HealthReport(overall_status=overall, components=components)

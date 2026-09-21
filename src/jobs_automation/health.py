"""System health check and diagnostic monitoring for Jobs Automation OS."""

from __future__ import annotations

import datetime
import os
import time
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import func, select, text

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
                pending_tasks = (
                    session.scalar(
                        select(func.count(TaskModel.id)).where(
                            TaskModel.status == "pending"
                        )
                    )
                    or 0
                )
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            status = "HEALTHY" if elapsed_ms < 500 else "DEGRADED"
            return ComponentHealth(
                name="database",
                status=status,
                message=f"Connected in {elapsed_ms}ms, {pending_tasks} pending tasks in queue.",
                latency_ms=elapsed_ms,
                details={"pending_tasks": pending_tasks},
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
            adp = registry.find_adapter(f"boards.{name}.io") or registry.find_adapter(f"jobs.{name}.co")
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

    def check_worker(self) -> ComponentHealth:
        """Inspects durable worker run history and reports last execution status."""
        try:
            with self.session_factory() as session:
                last_sweep = session.scalar(
                    select(AuditLogModel)
                    .where(AuditLogModel.action_type == "worker_sweep")
                    .order_by(AuditLogModel.occurred_at.desc())
                )
                if not last_sweep:
                    return ComponentHealth(
                        name="worker",
                        status="DEGRADED",
                        message="No worker sweeps have been recorded yet.",
                        details={"last_run": None},
                    )

                now = datetime.datetime.now(datetime.UTC)
                age_seconds = (now - last_sweep.occurred_at).total_seconds()
                has_errors = bool(last_sweep.metadata_json.get("errors"))
                status = "DEGRADED" if (has_errors or age_seconds > 28800) else "HEALTHY"

                return ComponentHealth(
                    name="worker",
                    status=status,
                    message=f"Last worker sweep {round(age_seconds / 60, 1)}m ago ({last_sweep.result}).",
                    details={
                        "last_run_at": last_sweep.occurred_at.isoformat(),
                        "result": last_sweep.result,
                        "age_seconds": round(age_seconds, 1),
                        "metrics": last_sweep.metadata_json,
                    },
                )
        except Exception as exc:
            return ComponentHealth(
                name="worker",
                status="UNHEALTHY",
                message=f"Failed to inspect worker status: {exc}",
                details={"error": str(exc)},
            )

    def check_gmail(self) -> ComponentHealth:
        """Inspects Gmail adapter configuration and last ingestion timestamp."""
        try:
            with self.session_factory() as session:
                last_msg = session.scalar(
                    select(InboundMessageModel)
                    .order_by(InboundMessageModel.received_at.desc())
                )
                creds_configured = bool(
                    os.getenv("GMAIL_CREDENTIALS_JSON") or os.path.exists("credentials.json")
                )
                details: dict[str, Any] = {
                    "credentials_configured": creds_configured,
                    "last_message_received_at": last_msg.received_at.isoformat() if last_msg else None,
                }
                if not creds_configured:
                    return ComponentHealth(
                        name="gmail",
                        status="DEGRADED",
                        message="Gmail live credentials not configured. Ingestion operates with mock adapter.",
                        details=details,
                    )
                return ComponentHealth(
                    name="gmail",
                    status="HEALTHY",
                    message="Gmail configured.",
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

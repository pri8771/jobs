"""Background worker daemon for periodic ingestion, evaluation, and lifecycle automation."""

from __future__ import annotations

import datetime
import logging
import re
import signal
import time
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.core.config import ConfigLoader
from jobs_automation.db.models import AuditLogModel, InboundMessageModel
from jobs_automation.ingestion.engine import (
    EmailIngestionEngine,
    reclassify_persisted_canary_messages,
)
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.engine import LifecycleEngine

logger = logging.getLogger(__name__)

# Regex patterns for sensitive tokens, credentials, and bodies
_SECRET_PATTERNS = [
    re.compile(r"ya29\.[a-zA-Z0-9_\-]+"),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]+"),
    re.compile(r"client_secret=[^\s&]+", re.IGNORECASE),
    re.compile(r"password=[^\s&]+", re.IGNORECASE),
    re.compile(r"access_token=[^\s&]+", re.IGNORECASE),
    re.compile(r"refresh_token=[^\s&]+", re.IGNORECASE),
]


def sanitize_error_message(err: Any, max_length: int = 256) -> str:
    """Sanitizes an error string to scrub OAuth tokens, passwords, bearer credentials, and secrets."""
    clean = str(err)
    for pattern in _SECRET_PATTERNS:
        clean = pattern.sub("[REDACTED_SECRET]", clean)
    clean = clean.strip().replace("\n", " ")
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    return clean


def categorize_error(err: Any) -> str:
    """Categorizes error strings into safe bounded category codes."""
    err_lower = str(err).lower()
    if (
        "gmail adapter unavailable" in err_lower
        or "credentials" in err_lower
        or "oauth" in err_lower
        or "token" in err_lower
        or "auth" in err_lower
    ):
        return "GMAIL_AUTH_ERROR"
    if "gmail" in err_lower or "http" in err_lower or "timeout" in err_lower or "connection" in err_lower:
        return "GMAIL_API_ERROR"
    if "kill_switch" in err_lower:
        return "KILL_SWITCH_ACTIVE"
    if "database" in err_lower or "sql" in err_lower or "session" in err_lower or "integrity" in err_lower:
        return "DB_ERROR"
    if "config" in err_lower or "profile" in err_lower:
        return "CONFIG_ERROR"
    if "pipeline" in err_lower or "lifecycle" in err_lower or "ingestion" in err_lower:
        return "PIPELINE_ERROR"
    return "UNKNOWN_ERROR"


class WorkerDaemon:
    """Manages scheduled background sweeps across ingestion, evaluation, and lifecycle."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        poll_interval_seconds: int = 14400,  # 4 hours default
        config_dir: str = "config",
        email_adapter: EmailAdapter | None = None,
        candidate_emails: list[str] | None = None,
        canary_identities: list[str] | None = None,
        reconciliation_interval_seconds: int = 86400,  # 24 hours default
    ) -> None:
        self.session_factory = session_factory
        self.poll_interval_seconds = poll_interval_seconds
        self.config_dir = config_dir
        self.email_adapter = email_adapter
        self.candidate_emails = candidate_emails
        # Explicit identities supplement, rather than replace, the durable policy in
        # platforms.yaml.  A scheduler cannot accidentally disable configured aliases
        # by omitting a command-line flag.
        self.canary_identities = list(canary_identities or [])
        self.reconciliation_interval_seconds = reconciliation_interval_seconds
        self.last_reconciliation_at: datetime.datetime | None = None
        self._running = False

    def handle_signal(self, signum: int, frame: Any) -> None:
        """Gracefully handle termination signals."""
        logger.info("Termination signal %s received. Shutting down worker daemon...", signum)
        self._running = False

    def _resolve_email_adapter(self) -> EmailAdapter | None:
        """Resolve the email adapter. Fails closed without mocking if credentials are missing."""
        if self.email_adapter is not None:
            return self.email_adapter
        try:
            from jobs_automation.adapters.gmail import GmailAdapter

            return GmailAdapter()
        except Exception as exc:
            logger.warning(
                "Live Gmail API adapter unavailable (%s). "
                "Skipping automated mailbox ingestion — will NOT fabricate mock data.",
                exc,
            )
            return None

    def _resolve_candidate_emails(self) -> list[str]:
        """Resolve candidate emails from explicit parameter or loaded profile."""
        if self.candidate_emails is not None:
            return self.candidate_emails
        try:
            loader = ConfigLoader(self.config_dir)
            profile, _ = loader.load_candidate_profile()
            if profile.identity.email:
                return [profile.identity.email]
        except Exception as exc:
            logger.debug("Could not load candidate email from config: %s", exc)
        return []

    def _resolve_canary_identities(self) -> list[str]:
        """Load configured aliases and add explicit worker-only aliases.

        The generic worker is an ingestion entrypoint, so it must share the durable
        canary policy used by bounded ingestion instead of relying on an ephemeral
        command invocation.
        """
        configured: list[str] = []
        try:
            loader = ConfigLoader(self.config_dir)
            platforms, _ = loader.load_platforms()
            configured = list(platforms.email.canary_identities)
        except FileNotFoundError:
            # A bootstrap install may not have platforms.yaml yet. There is no hidden
            # policy to silently discard; explicit identities still apply.
            configured = []
        except Exception as exc:
            # A present-but-invalid policy is unsafe to ignore: do not ingest a fresh
            # mailbox batch without knowing whether owner-controlled aliases exist.
            raise RuntimeError("canary policy configuration unavailable") from exc
        return list(dict.fromkeys([*configured, *self.canary_identities]))

    # Threshold beyond which a RUNNING record is considered stale/interrupted (seconds)
    STALE_RUN_THRESHOLD_SECONDS: int = 7200  # 2 hours

    def run_sweep(self, reconcile: bool | None = None) -> dict[str, Any]:
        """Executes a single cycle of ingestion, lifecycle checks, and pipeline maintenance.

        Call order is strictly:
        1. Durable RUNNING begin record committed in a short-lived separate session.
        2. Kill-switch check (KILLED if blocked).
        3. Email ingestion sweep (Gmail or configured adapter).
        4. Lifecycle alerts (unanswered recruiters, stale applications).
        5. Lifecycle transitions for incoming messages.
        6. Durable SUCCESS/PARTIAL/FAILED finalize record committed in a separate session.

        The begin and finalize records use separate DB sessions so that a pipeline
        rollback (step 3-5) cannot erase operational evidence.
        """
        logger.info("Executing scheduled maintenance and lifecycle sweep...")
        now = datetime.datetime.now(datetime.UTC)
        run_id = str(uuid.uuid4())

        # Determine if reconciliation should run
        if reconcile is not None:
            should_reconcile = reconcile
        else:
            if (
                self.last_reconciliation_at is None
                or (now - self.last_reconciliation_at).total_seconds()
                >= self.reconciliation_interval_seconds
            ):
                should_reconcile = True
            else:
                should_reconcile = False

        results: dict[str, Any] = {
            "run_id": run_id,
            "messages_polled": 0,
            "messages_ingested": 0,
            "jobs_discovered": 0,
            "lifecycle_transitions": 0,
            "unanswered_alerts": 0,
            "stale_alerts": 0,
            "canary_messages_reclassified": 0,
            "reconciliation_performed": False,
            "errors": [],
            "warnings": [],
        }

        # --- Begin record (separate session, committed before pipeline work) ---
        try:
            with self.session_factory() as begin_session:
                begin_audit = AuditLogModel(
                    action_type="worker_run",
                    entity_type="worker",
                    actor="worker_daemon",
                    result="RUNNING",
                    external_reference=run_id,
                    metadata_json={
                        "run_id": run_id,
                        "run_kind": "scheduled_sweep",
                        "started_at": now.isoformat(),
                        "reconcile_requested": should_reconcile,
                    },
                )
                begin_session.add(begin_audit)
                begin_session.commit()
        except Exception as begin_exc:
            logger.error(
                "Failed to write worker-run begin record for run %s: %s",
                run_id,
                begin_exc,
                exc_info=True,
            )
            # FAIL CLOSED: do NOT proceed with pipeline sweep if operational begin cannot be persisted
            results["errors"].append("begin_record_failed: operational evidence store unavailable")
            return results

        # Check safety kill switch — must record KILLED if blocked
        ks = KillSwitchManager()
        is_killed, kill_reason = ks.is_global_active()
        if is_killed:
            logger.warning(
                "Global kill switch is ACTIVE: %s. Scheduled worker sweep halted.", kill_reason
            )
            self._finalize_run(
                run_id=run_id,
                final_status="KILLED",
                results=results,
                error_note=f"kill_switch: {kill_reason}",
            )
            return results

        # --- Main pipeline (separate session from begin/finalize) ---
        pipeline_exception: Exception | None = None
        try:
            with self.session_factory() as session:
                # Reconcile the configured policy before any worker consumer sees
                # durable mailbox state. This must happen even when Gmail is unavailable:
                # old rows can otherwise reach alerts or lifecycle processing untagged.
                canary_identities = self._resolve_canary_identities()
                reclassified_canaries = reclassify_persisted_canary_messages(
                    session, canary_identities
                )
                if reclassified_canaries:
                    session.commit()
                results["canary_messages_reclassified"] = reclassified_canaries

                # 1. Email Ingestion (Performed FIRST)
                adapter = self._resolve_email_adapter()
                if adapter is not None:
                    candidate_emails = self._resolve_candidate_emails()
                    try:
                        ingestion_engine = EmailIngestionEngine(
                            session=session,
                            adapter=adapter,
                            candidate_emails=candidate_emails,
                            canary_identities=canary_identities,
                        )
                        summary = ingestion_engine.run_sweep(reconcile=should_reconcile)
                        results["messages_polled"] = summary.messages_polled
                        results["messages_ingested"] = summary.messages_ingested
                        results["jobs_discovered"] = summary.jobs_discovered_new
                        if summary.errors:
                            results["errors"].extend(summary.errors)
                        else:
                            if should_reconcile:
                                self.last_reconciliation_at = now
                                results["reconciliation_performed"] = True
                    except Exception as exc:
                        logger.error(
                            "Error during scheduled email ingestion sweep: %s",
                            exc,
                            exc_info=True,
                        )
                        results["errors"].append(str(exc))
                else:
                    results["errors"].append(
                        "Gmail adapter unavailable (missing or unconfigured credentials)"
                    )

                # 2. Lifecycle transitions & follow-up alerts (Performed AFTER ingestion)
                alert_service = LifecycleAlertService(session)
                unanswered = alert_service.check_unanswered_recruiters()
                stale = alert_service.check_stale_applications()
                results["unanswered_alerts"] = len(unanswered)
                results["stale_alerts"] = len(stale)

                # 3. Check unprocessed non-alert messages
                lifecycle_engine = LifecycleEngine(session)
                unprocessed_messages = session.scalars(
                    select(InboundMessageModel)
                    .where(InboundMessageModel.classification != "JOB_ALERT")
                    .order_by(InboundMessageModel.received_at.asc())
                ).all()

                for msg in unprocessed_messages:
                    res = lifecycle_engine.process_message(msg)
                    if res:
                        results["lifecycle_transitions"] += 1

                session.commit()
        except Exception as exc:
            logger.error(
                "Unhandled exception during worker sweep %s: %s", run_id, exc, exc_info=True
            )
            results["errors"].append(f"pipeline_exception: {exc}")
            pipeline_exception = exc

        # --- Finalize record (separate session, independent of pipeline commit) ---
        if pipeline_exception is not None:
            final_status = "FAILED"
        elif results["errors"]:
            final_status = "PARTIAL"
        else:
            final_status = "SUCCESS"

        self._finalize_run(run_id=run_id, final_status=final_status, results=results)

        logger.info(
            "Sweep %s completed [%s]: %d messages ingested, %d jobs discovered, "
            "%d transitions, %d unanswered alerts, %d stale alerts.",
            run_id,
            final_status,
            results["messages_ingested"],
            results["jobs_discovered"],
            results["lifecycle_transitions"],
            results["unanswered_alerts"],
            results["stale_alerts"],
        )
        return results

    def _finalize_run(
        self,
        run_id: str,
        final_status: str,
        results: dict[str, Any],
        error_note: str | None = None,
    ) -> None:
        """Writes the finalize AuditLog record for a worker run in a dedicated session.

        This is intentionally isolated from the pipeline session so that a pipeline
        rollback cannot erase the run evidence. No secrets, tokens, or email bodies
        are stored in the metadata.
        """
        finished_at = datetime.datetime.now(datetime.UTC)
        raw_errors = results.get("errors", [])
        safe_errors = [sanitize_error_message(e) for e in raw_errors][:10]
        error_categories = sorted(list({categorize_error(e) for e in raw_errors}))
        metadata: dict[str, Any] = {
            "run_id": run_id,
            "final_status": final_status,
            "finished_at": finished_at.isoformat(),
            "messages_polled": results.get("messages_polled", 0),
            "messages_ingested": results.get("messages_ingested", 0),
            "jobs_discovered": results.get("jobs_discovered", 0),
            "lifecycle_transitions": results.get("lifecycle_transitions", 0),
            "unanswered_alerts": results.get("unanswered_alerts", 0),
            "stale_alerts": results.get("stale_alerts", 0),
            "reconciliation_performed": results.get("reconciliation_performed", False),
            "error_count": len(raw_errors),
            "error_categories": error_categories,
            "sample_errors": safe_errors,
        }
        if error_note:
            metadata["error_note"] = sanitize_error_message(error_note)

        try:
            with self.session_factory() as fin_session:
                fin_audit = AuditLogModel(
                    action_type="worker_run_finished",
                    entity_type="worker",
                    actor="worker_daemon",
                    result=final_status,
                    external_reference=run_id,
                    metadata_json=metadata,
                )
                fin_session.add(fin_audit)
                fin_session.commit()
        except Exception as fin_exc:
            logger.error(
                "Failed to write worker-run finalize record for run %s: %s",
                run_id,
                fin_exc,
                exc_info=True,
            )

    def start(self) -> None:
        """Starts the continuous worker daemon loop."""
        self._running = True
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        logger.info(
            "Worker daemon started. Scheduled polling interval: %d seconds.",
            self.poll_interval_seconds,
        )

        while self._running:
            try:
                self.run_sweep()
            except Exception as exc:
                logger.error("Error during scheduled worker sweep: %s", exc, exc_info=True)

            # Polite sleep in 1-second chunks so signal interrupts cleanly
            for _ in range(self.poll_interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

        logger.info("Worker daemon stopped cleanly.")

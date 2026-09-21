"""Background worker daemon for periodic ingestion, evaluation, and lifecycle automation."""

from __future__ import annotations

import datetime
import logging
import signal
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.core.config import ConfigLoader
from jobs_automation.db.models import AuditLogModel, InboundMessageModel
from jobs_automation.ingestion.engine import EmailIngestionEngine
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.engine import LifecycleEngine

logger = logging.getLogger(__name__)


class WorkerDaemon:
    """Manages scheduled background sweeps across ingestion, evaluation, and lifecycle."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        poll_interval_seconds: int = 14400,  # 4 hours default
        config_dir: str = "config",
        email_adapter: EmailAdapter | None = None,
        candidate_emails: list[str] | None = None,
        reconciliation_interval_seconds: int = 86400,  # 24 hours default
    ) -> None:
        self.session_factory = session_factory
        self.poll_interval_seconds = poll_interval_seconds
        self.config_dir = config_dir
        self.email_adapter = email_adapter
        self.candidate_emails = candidate_emails
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

    def run_sweep(self, reconcile: bool | None = None) -> dict[str, Any]:
        """Executes a single cycle of ingestion, lifecycle checks, and pipeline maintenance.

        Call order is strictly:
        1. Email ingestion sweep (Gmail or configured adapter)
        2. Lifecycle alerts (unanswered recruiters, stale applications)
        3. Lifecycle transitions for incoming messages
        """
        logger.info("Executing scheduled maintenance and lifecycle sweep...")
        now = datetime.datetime.now(datetime.UTC)

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
            "messages_polled": 0,
            "messages_ingested": 0,
            "jobs_discovered": 0,
            "lifecycle_transitions": 0,
            "unanswered_alerts": 0,
            "stale_alerts": 0,
            "reconciliation_performed": False,
            "errors": [],
            "warnings": [],
        }

        # Check safety kill switch
        ks = KillSwitchManager()
        is_killed, kill_reason = ks.is_global_active()
        if is_killed:
            logger.warning("Global kill switch is ACTIVE: %s. Scheduled worker sweep halted.", kill_reason)
            return results

        with self.session_factory() as session:
            # 1. Email Ingestion (Performed FIRST)
            adapter = self._resolve_email_adapter()
            if adapter is not None:
                candidate_emails = self._resolve_candidate_emails()
                try:
                    ingestion_engine = EmailIngestionEngine(
                        session=session,
                        adapter=adapter,
                        candidate_emails=candidate_emails,
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
                results["errors"].append("Gmail adapter unavailable (missing or unconfigured credentials)")

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

            # Record durable worker run history
            sweep_audit = AuditLogModel(
                action_type="worker_sweep",
                entity_type="worker",
                actor="worker_daemon",
                result="success" if not results["errors"] else "error",
                external_reference=now.isoformat(),
                metadata_json=dict(results),
            )
            session.add(sweep_audit)
            session.commit()

        logger.info(
            "Sweep completed: %d messages ingested, %d jobs discovered, %d transitions, %d unanswered alerts, %d stale alerts.",
            results["messages_ingested"],
            results["jobs_discovered"],
            results["lifecycle_transitions"],
            results["unanswered_alerts"],
            results["stale_alerts"],
        )
        return results

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

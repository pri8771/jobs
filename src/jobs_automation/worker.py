"""Background worker daemon for periodic ingestion, evaluation, and lifecycle automation."""

from __future__ import annotations

import logging
import signal
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.engine import LifecycleEngine

logger = logging.getLogger(__name__)


class WorkerDaemon:
    """Manages scheduled background sweeps across ingestion, evaluation, and lifecycle."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        poll_interval_seconds: int = 14400,  # 4 hours default
    ) -> None:
        self.session_factory = session_factory
        self.poll_interval_seconds = poll_interval_seconds
        self._running = False

    def handle_signal(self, signum: int, frame: Any) -> None:
        """Gracefully handle termination signals."""
        logger.info("Termination signal %s received. Shutting down worker daemon...", signum)
        self._running = False

    def run_sweep(self) -> dict[str, int]:
        """Executes a single cycle of lifecycle checks, follow-up alerts, and pipeline maintenance."""
        logger.info("Executing scheduled maintenance and lifecycle sweep...")
        results = {
            "unanswered_alerts": 0,
            "stale_alerts": 0,
            "lifecycle_transitions": 0,
        }

        # Check safety kill switch
        ks = KillSwitchManager()
        is_killed, kill_reason = ks.is_global_active()
        if is_killed:
            logger.warning("Global kill switch is ACTIVE: %s. Scheduled worker sweep halted.", kill_reason)
            return results

        with self.session_factory() as session:
            # 1. Lifecycle transitions & follow-up alerts
            alert_service = LifecycleAlertService(session)
            unanswered = alert_service.check_unanswered_recruiters()
            stale = alert_service.check_stale_applications()
            results["unanswered_alerts"] = len(unanswered)
            results["stale_alerts"] = len(stale)

            # 2. Check unprocessed messages
            lifecycle_engine = LifecycleEngine(session)
            from sqlalchemy import select

            from jobs_automation.db.models import InboundMessageModel

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

        logger.info(
            "Sweep completed successfully: %d transitions, %d unanswered alerts, %d stale alerts.",
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

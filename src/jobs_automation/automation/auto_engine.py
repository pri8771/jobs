"""Controlled automatic application engine with rate limiting, kill switch, and allowlist validation."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.automation.adapters.registry import ATSAdapterRegistry
from jobs_automation.automation.base import SubmissionResult
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.automation.rate_limiter import DomainRateLimiter
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.policy_registry import PolicyDecision
from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    AuditLogModel,
    JobModel,
    TaskModel,
)
from jobs_automation.policy.evaluator import PolicyEvaluator

logger = logging.getLogger(__name__)


class ControlledAutoApplicationResult(BaseModel):
    """Result of an automated submission attempt."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    application_id: str | None = None
    status: str  # SUBMITTED, BLOCKED, KILL_SWITCH_ACTIVE, RATE_LIMITED, STOPPED_UNKNOWN_QUESTION, NO_ADAPTER, ALREADY_SUBMITTED, FAILED
    destination_domain: str
    platform: str | None = None
    receipt_id: str | None = None
    confirmation_url: str | None = None
    retries_performed: int = 0
    message: str


class ControlledAutoApplicationEngine:
    """Orchestrates compliant, idempotent, rate-limited automatic applications."""

    def __init__(
        self,
        session: Session,
        policy_evaluator: PolicyEvaluator,
        candidate_profile: CandidateProfileConfig,
        adapter_registry: ATSAdapterRegistry | None = None,
        rate_limiter: DomainRateLimiter | None = None,
        kill_switch: KillSwitchManager | None = None,
        max_retries: int = 3,
        backoff_base_seconds: float = 1.0,
    ) -> None:
        self.session = session
        self.policy_evaluator = policy_evaluator
        self.candidate = candidate_profile
        self.registry = adapter_registry or ATSAdapterRegistry()
        self.rate_limiter = rate_limiter or DomainRateLimiter()
        self.kill_switch = kill_switch or KillSwitchManager()
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def _extract_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def execute_auto_apply(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
        mock_mode: bool = False,
    ) -> ControlledAutoApplicationResult:
        """Executes automatic application pipeline adhering to all policy and safety gates."""
        job = self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if not job:
            raise ValueError(f"Job {job_id} not found")

        apply_url = job.apply_url
        if not apply_url:
            raise ValueError(f"Job {job.normalized_title} has no apply URL")

        domain = self._extract_domain(apply_url)

        # 1. Idempotency Guard
        existing_app = self.session.scalar(
            select(ApplicationModel).where(ApplicationModel.job_id == job_id)
        )
        if existing_app and existing_app.status == "SUBMITTED":
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                application_id=str(existing_app.id),
                status="ALREADY_SUBMITTED",
                destination_domain=domain,
                message=f"Application for {job.normalized_title} already submitted on {existing_app.applied_at}",
            )

        # 2. Policy Gate Evaluation
        policy_res = self.policy_evaluator.evaluate(domain, capability="submit_application")
        if policy_res.decision != PolicyDecision.AUTO_ALLOWED:
            self._log_audit(
                action_type="auto_apply_policy_rejected",
                entity_type="job",
                entity_id=job.id,
                result="rejected",
                metadata={
                    "policy": policy_res.decision.value,
                    "reason": policy_res.reason,
                    "domain": domain,
                },
            )
            self.session.commit()
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                destination_domain=domain,
                message=f"Auto-submission not permitted for {domain}: policy is {policy_res.decision.value.upper()} ({policy_res.reason})",
            )

        # 3. Kill Switch Check (Global and Platform)
        platform_name = policy_res.platform or "unknown"
        is_killed, kill_reason = self.kill_switch.is_platform_active(platform_name)
        if is_killed:
            self._log_audit(
                action_type="auto_apply_kill_switch_triggered",
                entity_type="job",
                entity_id=job.id,
                result="blocked",
                metadata={"kill_reason": kill_reason, "platform": platform_name},
            )
            self.session.commit()
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="KILL_SWITCH_ACTIVE",
                destination_domain=domain,
                platform=platform_name,
                message=f"Submission aborted: {kill_reason}",
            )

        # 4. Domain Rate Limiting Check
        rate_ok, rate_msg, retry_after = self.rate_limiter.check_rate_limit(domain)
        if not rate_ok:
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="RATE_LIMITED",
                destination_domain=domain,
                platform=platform_name,
                message=f"Rate limit exceeded: {rate_msg}",
            )

        # 5. ATS Adapter Resolution
        adapter = self.registry.find_adapter(domain)
        if not adapter:
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="NO_ADAPTER",
                destination_domain=domain,
                message=f"No automated submission adapter found for domain {domain}",
            )

        # 6. Retrieve Application Packet
        packet: ApplicationPacketModel | None = None
        if packet_id:
            packet = self.session.scalar(
                select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet_id)
            )
        else:
            packet = self.session.scalar(
                select(ApplicationPacketModel)
                .where(ApplicationPacketModel.job_id == job_id)
                .order_by(ApplicationPacketModel.created_at.desc())
            )

        if not packet:
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="FAILED",
                destination_domain=domain,
                message="No prepared application packet found for job.",
            )

        # 7. Adapter Packet Validation & Unknown-Question Stop Condition
        validation = adapter.validate_packet(packet, self.candidate)
        if not validation.is_valid:
            if validation.unknown_question_stop:
                # Route to human review queue
                self._enqueue_review_task(
                    job_id=job_id,
                    reason=f"Unknown screening questions stopped auto-apply: {', '.join(validation.unresolved_questions)}",
                )
                self.session.commit()
                return ControlledAutoApplicationResult(
                    job_id=str(job_id),
                    status="STOPPED_UNKNOWN_QUESTION",
                    destination_domain=domain,
                    platform=adapter.platform_name,
                    message=f"Auto-submission paused: unknown screening questions required: {', '.join(validation.unresolved_questions)}",
                )
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status="FAILED",
                destination_domain=domain,
                platform=adapter.platform_name,
                message=f"Packet validation failed: {validation.message}",
            )

        # 8. Execution with Exponential Backoff Retry Policy
        sub_res: SubmissionResult | None = None
        attempts = 0
        last_error_msg = ""

        for attempt in range(self.max_retries):
            attempts += 1
            try:
                sub_res = adapter.submit_application(
                    packet=packet,
                    target_url=apply_url,
                    candidate_profile=self.candidate,
                    mock_mode=mock_mode,
                )
                if sub_res.success:
                    break
                elif sub_res.status == "RETRYABLE_ERROR":
                    sleep_time = self.backoff_base_seconds * (2**attempt)
                    time.sleep(sleep_time)
                else:
                    # Non-retryable error
                    break
            except Exception as e:
                last_error_msg = str(e)
                logger.warning(f"Submission attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_base_seconds * (2**attempt)
                    time.sleep(sleep_time)

        # Record domain rate limiter timestamp
        self.rate_limiter.record_submission(domain)

        if not sub_res or not sub_res.success:
            err_msg = sub_res.message if sub_res else last_error_msg
            status_val = sub_res.status if sub_res else "FAILED"
            self._log_audit(
                action_type="auto_apply_failed",
                entity_type="job",
                entity_id=job_id,
                input_hash=packet.packet_hash,
                result="failed" if status_val != "NOT_IMPLEMENTED" else "not_implemented",
                metadata={"error": err_msg, "attempts": attempts, "domain": domain, "status": status_val},
            )
            self.session.commit()
            return ControlledAutoApplicationResult(
                job_id=str(job_id),
                status=status_val,
                destination_domain=domain,
                platform=adapter.platform_name,
                retries_performed=attempts - 1,
                message=f"Submission not executed: {err_msg}" if status_val == "NOT_IMPLEMENTED" else f"Submission failed after {attempts} attempt(s): {err_msg}",
            )

        # 9. Atomic Submission State & Receipt Recording
        now = utc_now()
        is_simulation = (sub_res.status == "SIMULATED")
        app_status = "SIMULATED" if is_simulation else "SUBMITTED"
        event_type = "APPLICATION_SIMULATED" if is_simulation else "APPLICATION_SUBMITTED"
        app_mode = "auto_simulated" if is_simulation else "auto"

        app = existing_app or ApplicationModel(
            job_id=job_id,
            destination_domain=domain,
            policy_decision="auto_allowed",
            application_mode=app_mode,
            packet_id=packet.id,
        )
        app.status = app_status
        app.applied_at = now
        app.last_activity_at = now
        if not existing_app:
            self.session.add(app)
        self.session.flush()

        event = ApplicationEventModel(
            application_id=app.id,
            event_type=event_type,
            source="ats_adapter",
            actor="system",
            payload_json={
                "receipt_id": sub_res.receipt_id,
                "confirmation_url": sub_res.confirmation_url,
                "domain": domain,
                "platform": adapter.platform_name,
                "response": sub_res.response_payload,
                "simulated": is_simulation,
            },
        )
        self.session.add(event)

        audit_action = "auto_application_simulated" if is_simulation else "auto_application_submitted"
        self._log_audit(
            action_type=audit_action,
            entity_type="application",
            entity_id=app.id,
            input_hash=packet.packet_hash,
            result="simulated" if is_simulation else "success",
            external_reference=sub_res.receipt_id,
            metadata={
                "domain": domain,
                "platform": adapter.platform_name,
                "receipt_id": sub_res.receipt_id,
                "attempts": attempts,
                "simulated": is_simulation,
            },
        )

        # Complete pending review tasks
        self._complete_tasks_for_job(job_id=job.id, app_id=app.id)
        self.session.commit()

        msg = (
            f"Application simulated in mock mode for {adapter.platform_name}. Simulation ID: {sub_res.receipt_id}"
            if is_simulation
            else f"Application automatically submitted to {adapter.platform_name}. Receipt: {sub_res.receipt_id}"
        )

        return ControlledAutoApplicationResult(
            job_id=str(job_id),
            application_id=str(app.id),
            status=app_status,
            destination_domain=domain,
            platform=adapter.platform_name,
            receipt_id=sub_res.receipt_id,
            confirmation_url=sub_res.confirmation_url,
            retries_performed=attempts - 1,
            message=msg,
        )

    def _enqueue_review_task(self, job_id: uuid.UUID, reason: str) -> None:
        task = TaskModel(
            job_id=job_id,
            task_type="NEEDS_REVIEW",
            status="pending",
            payload_json={"reason": reason, "channel": "auto_apply_unknown_question"},
        )
        self.session.add(task)

    def _complete_tasks_for_job(self, job_id: uuid.UUID, app_id: uuid.UUID) -> None:
        tasks = self.session.scalars(
            select(TaskModel).where(TaskModel.job_id == job_id, TaskModel.status == "pending")
        ).all()
        for t in tasks:
            t.status = "completed"
            t.application_id = app_id

    def _log_audit(
        self,
        action_type: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        result: str,
        input_hash: str | None = None,
        external_reference: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLogModel(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor="auto_engine",
            input_hash=input_hash,
            result=result,
            external_reference=external_reference,
            metadata_json=metadata or {},
        )
        self.session.add(audit)

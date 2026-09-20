"""Assisted application execution engine with policy enforcement and human-in-the-loop review."""

from __future__ import annotations

import logging
import uuid
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.browser.base import BrowserRunner
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.policy_registry import PolicyDecision
from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    AuditLogModel,
    JobModel,
    TaskModel,
)
from jobs_automation.policy.evaluator import PolicyEvaluationResult, PolicyEvaluator

logger = logging.getLogger(__name__)


class AssistedApplicationPlan(BaseModel):
    """Execution plan for an assisted application."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    packet_id: str | None = None
    company_name: str
    job_title: str
    apply_url: str
    destination_domain: str
    policy: PolicyEvaluationResult
    prefill_data: dict[str, str] = Field(default_factory=dict)
    file_uploads: dict[str, str] = Field(default_factory=dict)
    unresolved_questions: list[str] = Field(default_factory=list)
    can_prefill: bool = False
    instructions: str = ""


class AssistedApplicationResult(BaseModel):
    """Outcome of assisted application execution."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    application_id: str | None = None
    status: str  # SUBMITTED, MANUAL_RECORDED, BLOCKED, REVIEW_REQUIRED, ALREADY_SUBMITTED
    policy_decision: str
    destination_domain: str
    prefilled_count: int = 0
    receipt_text: str | None = None
    confirmation_url: str | None = None
    message: str


class AssistedApplicationEngine:
    """Coordinates policy checks, safe field prefilling, and human review gates."""

    def __init__(
        self,
        session: Session,
        policy_evaluator: PolicyEvaluator,
        browser_runner: BrowserRunner,
        candidate_profile: CandidateProfileConfig,
    ) -> None:
        self.session = session
        self.policy_evaluator = policy_evaluator
        self.browser_runner = browser_runner
        self.candidate = candidate_profile

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def build_plan(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
    ) -> AssistedApplicationPlan:
        """Inspects job and application packet to construct a prefill and policy execution plan."""
        job = self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        apply_url = job.apply_url
        if not apply_url:
            raise ValueError(f"Job {job.title} at {job.company_name} has no apply URL")

        domain = self._extract_domain(apply_url)
        policy_res = self.policy_evaluator.evaluate(domain, capability="submit_application")

        packet: ApplicationPacketModel | None = None
        if packet_id:
            packet = self.session.scalar(
                select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet_id)
            )
        else:
            # Pick latest prepared packet for this job
            packet = self.session.scalar(
                select(ApplicationPacketModel)
                .where(ApplicationPacketModel.job_id == job_id)
                .order_by(ApplicationPacketModel.created_at.desc())
            )

        prefill_data: dict[str, str] = {}
        file_uploads: dict[str, str] = {}
        unresolved: list[str] = []

        if packet:
            unresolved = list(packet.unresolved_questions_json)
            # Find resume artifact file storage path
            if packet.resume_artifact_id:
                resume_art = self.session.scalar(
                    select(ArtifactModel).where(ArtifactModel.id == packet.resume_artifact_id)
                )
                if resume_art:
                    file_uploads["resume"] = resume_art.storage_uri

            # Map pre-computed screening answers
            for q_key, answer_val in packet.answers_json.items():
                prefill_data[q_key] = str(answer_val)

        # Standard candidate profile fields
        parts = self.candidate.identity.full_name.split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""

        prefill_data.setdefault("first_name", first_name)
        prefill_data.setdefault("last_name", last_name)
        prefill_data.setdefault("full_name", self.candidate.identity.full_name)
        if self.candidate.identity.email:
            prefill_data.setdefault("email", self.candidate.identity.email)
        if self.candidate.identity.phone:
            prefill_data.setdefault("phone", self.candidate.identity.phone)
        prefill_data.setdefault(
            "location", f"{self.candidate.identity.city}, {self.candidate.identity.state}"
        )

        if self.candidate.links.linkedin:
            prefill_data.setdefault("linkedin", self.candidate.links.linkedin)
        if self.candidate.links.github:
            prefill_data.setdefault("github", self.candidate.links.github)
        if self.candidate.links.portfolio:
            prefill_data.setdefault("portfolio", self.candidate.links.portfolio)
        if self.candidate.links.personal_site:
            prefill_data.setdefault("personal_site", self.candidate.links.personal_site)

        can_prefill = policy_res.decision in (PolicyDecision.ASSISTED, PolicyDecision.AUTO_ALLOWED)

        if policy_res.decision == PolicyDecision.BLOCKED:
            instructions = f"Automation BLOCKED for {domain}: {policy_res.reason}. Do not submit automated requests."
        elif policy_res.decision == PolicyDecision.MANUAL_ONLY:
            instructions = (
                f"Platform {domain} requires manual native submission per policy. "
                "Open url in candidate's standard browser and use candidate worksheet to submit manually."
            )
        else:
            instructions = (
                f"Assisted mode permitted for {domain}. Form will be prefilled and reviewed "
                "prior to final human confirmation."
            )

        return AssistedApplicationPlan(
            job_id=str(job.id),
            packet_id=str(packet.id) if packet else None,
            company_name=job.company_name,
            job_title=job.title,
            apply_url=apply_url,
            destination_domain=domain,
            policy=policy_res,
            prefill_data=prefill_data,
            file_uploads=file_uploads,
            unresolved_questions=unresolved,
            can_prefill=can_prefill,
            instructions=instructions,
        )

    def execute(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
        auto_confirm: bool = False,
        receipt_text: str | None = None,
    ) -> AssistedApplicationResult:
        """Executes the assisted application flow with strict policy checks and human review gate."""
        plan = self.build_plan(job_id=job_id, packet_id=packet_id)

        # Idempotency check: see if application already exists and is submitted
        existing_app = self.session.scalar(
            select(ApplicationModel).where(ApplicationModel.job_id == job_id)
        )
        if existing_app and existing_app.status == "SUBMITTED":
            return AssistedApplicationResult(
                job_id=str(job_id),
                application_id=str(existing_app.id),
                status="ALREADY_SUBMITTED",
                policy_decision=existing_app.policy_decision,
                destination_domain=plan.destination_domain,
                message=f"Application for {plan.job_title} at {plan.company_name} was already submitted on {existing_app.applied_at}.",
            )

        # Policy Gate: Blocked destinations halt immediately
        if plan.policy.decision == PolicyDecision.BLOCKED:
            self._log_audit(
                action_type="policy_blocked_application_attempt",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={"reason": plan.policy.reason, "domain": plan.destination_domain},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Application blocked by platform policy: {plan.policy.reason}",
            )

        # Policy Gate: MANUAL_ONLY destinations (e.g., LinkedIn, Indeed)
        if plan.policy.decision == PolicyDecision.MANUAL_ONLY:
            app = existing_app or ApplicationModel(
                job_id=job_id,
                destination_domain=plan.destination_domain,
                policy_decision=plan.policy.decision.value,
                application_mode="manual",
                status="MANUAL_IN_PROGRESS",
                packet_id=uuid.UUID(plan.packet_id) if plan.packet_id else None,
            )
            if not existing_app:
                self.session.add(app)
                self.session.flush()

            if auto_confirm:
                # User completed manual submission in native UI
                now = utc_now()
                app.status = "SUBMITTED"
                app.applied_at = now
                app.last_activity_at = now

                self._record_submission_event(
                    application_id=app.id,
                    source="manual_native",
                    receipt=receipt_text or "Confirmed manual submission via native portal",
                    domain=plan.destination_domain,
                    packet_id=plan.packet_id,
                )
                self._complete_review_task(job_id=job_id, app_id=app.id)
                self.session.commit()

                return AssistedApplicationResult(
                    job_id=str(job_id),
                    application_id=str(app.id),
                    status="MANUAL_RECORDED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    receipt_text=receipt_text or "Manual native submission confirmed",
                    message="Manual native application recorded as submitted.",
                )
            else:
                self.session.commit()
                return AssistedApplicationResult(
                    job_id=str(job_id),
                    application_id=str(app.id),
                    status="REVIEW_REQUIRED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    message=(
                        f"Manual submission required for {plan.destination_domain}. "
                        f"Apply URL: {plan.apply_url}. Confirm after submitting in portal."
                    ),
                )

        # Assisted execution for permitted domains (Greenhouse, Lever, ATS)
        # Step 1: Prefill form via runner
        prefill_res = self.browser_runner.prefill_form(
            url=plan.apply_url,
            field_values=plan.prefill_data,
            file_uploads=plan.file_uploads,
        )

        # Step 2: Interactive review session (halts before submission)
        session_res = self.browser_runner.open_interactive_session(
            url=plan.apply_url,
            prefilled_fields=prefill_res.prefilled_fields,
            file_uploads=plan.file_uploads,
        )

        app = existing_app or ApplicationModel(
            job_id=job_id,
            destination_domain=plan.destination_domain,
            policy_decision=plan.policy.decision.value,
            application_mode="assisted",
            status="ASSISTED_PREFILLED",
            packet_id=uuid.UUID(plan.packet_id) if plan.packet_id else None,
        )
        if not existing_app:
            self.session.add(app)
            self.session.flush()

        # Step 3: Human review checkpoint
        # If user explicitly confirms or runner reports successful candidate submission:
        is_confirmed = auto_confirm or session_res.submitted
        if is_confirmed:
            now = utc_now()
            app.status = "SUBMITTED"
            app.applied_at = now
            app.last_activity_at = now

            final_receipt = (
                receipt_text
                or session_res.receipt_text
                or "Application submitted via assisted browser"
            )
            self._record_submission_event(
                application_id=app.id,
                source="assisted_browser",
                receipt=final_receipt,
                domain=plan.destination_domain,
                packet_id=plan.packet_id,
            )
            self._complete_review_task(job_id=job_id, app_id=app.id)
            self.session.commit()

            return AssistedApplicationResult(
                job_id=str(job_id),
                application_id=str(app.id),
                status="SUBMITTED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                prefilled_count=len(prefill_res.prefilled_fields),
                receipt_text=final_receipt,
                confirmation_url=session_res.confirmation_url,
                message=f"Application for {plan.job_title} at {plan.company_name} successfully submitted and recorded.",
            )
        else:
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                application_id=str(app.id),
                status="REVIEW_REQUIRED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                prefilled_count=len(prefill_res.prefilled_fields),
                message="Form prefilled. Awaiting human review and submission confirmation.",
            )

    def _record_submission_event(
        self,
        application_id: uuid.UUID,
        source: str,
        receipt: str,
        domain: str,
        packet_id: str | None,
    ) -> None:
        event = ApplicationEventModel(
            application_id=application_id,
            event_type="APPLICATION_SUBMITTED",
            source=source,
            actor="candidate",
            payload_json={
                "receipt": receipt,
                "domain": domain,
                "packet_id": packet_id,
            },
        )
        self.session.add(event)

        packet_hash: str | None = None
        if packet_id:
            packet = self.session.scalar(
                select(ApplicationPacketModel).where(
                    ApplicationPacketModel.id == uuid.UUID(packet_id)
                )
            )
            if packet:
                packet_hash = packet.packet_hash

        self._log_audit(
            action_type="assisted_application_submitted",
            entity_type="application",
            entity_id=application_id,
            input_hash=packet_hash,
            result="success",
            metadata={"domain": domain, "source": source, "receipt": receipt},
        )

    def _complete_review_task(self, job_id: uuid.UUID, app_id: uuid.UUID) -> None:
        tasks = self.session.scalars(
            select(TaskModel).where(
                TaskModel.job_id == job_id,
                TaskModel.status == "pending",
            )
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
        metadata: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLogModel(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor="assisted_engine",
            input_hash=input_hash,
            result=result,
            metadata_json=metadata or {},
        )
        self.session.add(audit)

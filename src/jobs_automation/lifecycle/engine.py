"""Lifecycle engine coordinating state transitions, interviews, CRM, and audits."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    ContactModel,
    InboundMessageModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.interview import InterviewExtractor

logger = logging.getLogger(__name__)


class LifecycleTransitionResult(BaseModel):
    """Result of processing a recruiting message for lifecycle transition."""

    model_config = ConfigDict(extra="forbid")

    application_id: str
    previous_status: str
    new_status: str
    event_type: str
    contact_name: str | None = None
    interview_scheduled: bool = False
    regression_prevented: bool = False
    message: str


class LifecycleEngine:
    """Manages application state transitions driven by verified communication evidence."""

    TRANSITION_MAP: dict[str, tuple[str, str]] = {
        "APPLICATION_CONFIRMATION": ("CONFIRMED", "APPLICATION_CONFIRMED"),
        "RECRUITER_OUTREACH": ("SCREENING", "RECRUITER_CONTACTED"),
        "RECRUITER_FOLLOW_UP": ("SCREENING", "RECRUITER_FOLLOWED_UP"),
        "SCREENING_REQUEST": ("SCREENING", "SCREENING_REQUESTED"),
        "ASSESSMENT_REQUEST": ("ASSESSMENT", "ASSESSMENT_REQUESTED"),
        "INTERVIEW_REQUEST": ("INTERVIEWING", "INTERVIEW_REQUESTED"),
        "INTERVIEW_CONFIRMATION": ("INTERVIEWING", "INTERVIEW_CONFIRMED"),
        "INTERVIEW_RESCHEDULE": ("INTERVIEWING", "INTERVIEW_RESCHEDULED"),
        "INTERVIEW_CANCELLED": ("INTERVIEWING", "INTERVIEW_CANCELLED"),
        "OFFER": ("OFFER_RECEIVED", "OFFER_EXTENDED"),
        # BACKGROUND_CHECK is intentionally excluded from TRANSITION_MAP.
        # A background check is evidence of process, not proof of a formal offer.
        # It is handled via EVIDENCE_ONLY_MAP below as a stage-preserving evidence event.
        "ONBOARDING": ("ONBOARDING", "ONBOARDING_INITIATED"),
        "REJECTION": ("REJECTED", "APPLICATION_REJECTED"),
        "WITHDRAWAL": ("WITHDRAWN", "APPLICATION_WITHDRAWN"),
    }

    # Classifications that record an evidence event without changing the application stage.
    # The event is written using the associated event_type; the application status is unchanged.
    EVIDENCE_ONLY_MAP: dict[str, str] = {
        "BACKGROUND_CHECK": "BACKGROUND_CHECK_INITIATED",
    }

    STAGE_RANKS: dict[str, int] = {
        "DISCOVERED": 0,
        "DRAFT": 0,
        "PREPARED": 0,
        "SUBMITTED": 1,
        "CONFIRMED": 2,
        "SCREENING": 3,
        "ASSESSMENT": 4,
        "INTERVIEWING": 5,
        "OFFER_RECEIVED": 6,
        "OFFER_ACCEPTED": 7,
        "ONBOARDING": 8,
    }

    TERMINAL_STATUSES: set[str] = {"REJECTED", "WITHDRAWN", "OFFER_DECLINED"}

    def __init__(self, session: Session) -> None:
        self.session = session
        self.crm = RecruiterCRMService(session)
        self.interview_extractor = InterviewExtractor(session)
        self.alert_service = LifecycleAlertService(session)

    def process_message(
        self,
        message: InboundMessageModel,
        confidence_threshold: float = 0.8,
    ) -> LifecycleTransitionResult | None:
        """Evaluates an inbound message and triggers verified, idempotent lifecycle transitions."""
        # Find associated application via links
        links = self.session.scalars(
            select(MessageLinkModel).where(
                MessageLinkModel.inbound_message_id == message.id,
                MessageLinkModel.application_id.is_not(None),
            )
        ).all()

        if not links:
            return None

        # Check for ambiguity: multiple applications linked with high confidence
        if len(links) > 1:
            self._route_ambiguity_to_review(
                message, [str(link_item.application_id) for link_item in links]
            )
            return None

        link = links[0]
        if link.confidence < confidence_threshold:
            # Low confidence must not silently transition state
            self._route_ambiguity_to_review(
                message,
                [str(link.application_id)],
                reason=f"Low link confidence: {link.confidence}",
            )
            return None

        app = self.session.scalar(
            select(ApplicationModel).where(ApplicationModel.id == link.application_id)
        )
        if not app:
            return None

        # Idempotency check: has this message already been processed for this application?
        existing_event = self.session.scalar(
            select(ApplicationEventModel).where(
                ApplicationEventModel.application_id == app.id,
                ApplicationEventModel.source_reference == message.provider_message_id,
            )
        )
        if existing_event:
            logger.info(
                "Message %s already processed for application %s; skipping duplicate sweep.",
                message.provider_message_id,
                app.id,
            )
            return None

        # Check for thread-role divergence (e.g. recruiter reuses thread for a different requisition)
        if self._detect_thread_role_divergence(message, app, link):
            self._route_ambiguity_to_review(
                message,
                [str(app.id)],
                reason="Message in existing thread references a different role or requisition",
            )
            return None

        # Record or update Recruiter Contact in CRM
        contact: ContactModel | None = None
        if message.direction == "inbound":
            company_id = app.job.company_id if app.job else None
            contact = self.crm.get_or_create_contact(
                sender_header=message.sender,
                company_id=company_id,
            )
            self.crm.record_touchpoint(contact, message)
            
            # V23-OG-05: Record explicit FK for evidence projection
            if link.contact_id is None and contact is not None:
                link.contact_id = contact.id

        classification = message.classification

        # Evidence-only classifications: record the event but do NOT advance the application stage.
        # A background check is process evidence, not proof of a formal offer.
        if classification in self.EVIDENCE_ONLY_MAP:
            evidence_event_type = self.EVIDENCE_ONLY_MAP[classification]
            previous_status = app.status
            app.last_activity_at = message.received_at
            self._record_event_and_audit(
                app=app,
                message=message,
                event_type=evidence_event_type,
                previous_status=previous_status,
                new_status=previous_status,
                contact=contact,
                regression_prevented=False,
            )
            logger.info(
                "BACKGROUND_CHECK evidence recorded for application %s; stage preserved at %s.",
                app.id,
                previous_status,
            )
            return LifecycleTransitionResult(
                application_id=str(app.id),
                previous_status=previous_status,
                new_status=previous_status,
                event_type=evidence_event_type,
                contact_name=contact.name if contact else None,
                interview_scheduled=False,
                regression_prevented=False,
                message=(
                    f"Application {app.id} background check evidence recorded; "
                    f"stage preserved at {previous_status}"
                ),
            )

        if classification not in self.TRANSITION_MAP:
            # General message, record touchpoint and update activity without state transition
            app.last_activity_at = message.received_at
            return None

        target_status, event_type = self.TRANSITION_MAP[classification]
        previous_status = app.status

        # Terminal state protection
        if previous_status in self.TERMINAL_STATUSES:
            logger.info(
                "Skipping status transition from terminal state %s to %s for app %s",
                previous_status,
                target_status,
                app.id,
            )
            # Record historical event for audit trail without altering status
            self._record_event_and_audit(
                app=app,
                message=message,
                event_type=event_type,
                previous_status=previous_status,
                new_status=previous_status,
                contact=contact,
                regression_prevented=True,
            )
            return None

        # Stage progression & regression policy
        regression_prevented = False
        if target_status == "REJECTED":
            if previous_status in ("OFFER_ACCEPTED", "ONBOARDING"):
                logger.warning(
                    "Contradictory rejection message received for application %s in %s state. "
                    "Routing to human review and preserving current state.",
                    app.id,
                    previous_status,
                )
                self._route_contradiction_to_review(
                    message=message,
                    application_id=str(app.id),
                    previous_status=previous_status,
                )
                new_status = previous_status
                regression_prevented = True
            else:
                new_status = "REJECTED"
                app.status = new_status
                app.closed_at = message.received_at
        elif target_status == "WITHDRAWN":
            new_status = "WITHDRAWN"
            app.status = new_status
            app.closed_at = message.received_at
        elif classification == "INTERVIEW_CANCELLED":
            # Cancellation updates interview record without regressing application stage
            new_status = previous_status
        elif self.STAGE_RANKS.get(previous_status, 0) > self.STAGE_RANKS.get(target_status, 0):
            # Out-of-order lower-stage email arriving late; prevent regression
            logger.info(
                "Preventing status regression from %s to %s for app %s",
                previous_status,
                target_status,
                app.id,
            )
            new_status = previous_status
            regression_prevented = True
        else:
            new_status = target_status
            app.status = new_status

        app.last_activity_at = message.received_at

        # Check and extract interview details if applicable
        interview_scheduled = False
        if classification in (
            "INTERVIEW_REQUEST",
            "INTERVIEW_CONFIRMATION",
            "INTERVIEW_RESCHEDULE",
            "INTERVIEW_CANCELLED",
            "SCREENING_REQUEST",
        ):
            details = self.interview_extractor.extract_from_message(message)
            if details:
                interview = self.interview_extractor.record_interview(
                    application_id=app.id,
                    details=details,
                    source_message_id=message.provider_message_id,
                )
                if interview and interview.status == "scheduled":
                    interview_scheduled = True

        # Record ApplicationEvent and AuditLog
        self._record_event_and_audit(
            app=app,
            message=message,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            contact=contact,
            regression_prevented=regression_prevented,
        )

        return LifecycleTransitionResult(
            application_id=str(app.id),
            previous_status=previous_status,
            new_status=new_status,
            event_type=event_type,
            contact_name=contact.name if contact else None,
            interview_scheduled=interview_scheduled,
            regression_prevented=regression_prevented,
            message=f"Application {app.id} transitioned from {previous_status} to {new_status}"
            if not regression_prevented
            else f"Application {app.id} status preserved at {previous_status} (regression prevented)",
        )

    def _record_event_and_audit(
        self,
        app: ApplicationModel,
        message: InboundMessageModel,
        event_type: str,
        previous_status: str,
        new_status: str,
        contact: ContactModel | None,
        regression_prevented: bool = False,
    ) -> None:
        payload: dict[str, Any] = {
            "message_id": str(message.id),
            "classification": message.classification,
            "subject": message.subject,
            "sender": message.sender,
            "contact_id": str(contact.id) if contact else None,
            "regression_prevented": regression_prevented,
        }

        event = ApplicationEventModel(
            application_id=app.id,
            event_type=event_type,
            source="email_lifecycle",
            source_reference=message.provider_message_id,
            actor="recruiter" if message.direction == "inbound" else "candidate",
            payload_json=payload,
        )
        self.session.add(event)

        audit = AuditLogModel(
            action_type="lifecycle_state_transition",
            entity_type="application",
            entity_id=app.id,
            actor="lifecycle_engine",
            result=new_status,
            external_reference=message.provider_message_id,
            metadata_json={
                "previous_status": previous_status,
                "new_status": new_status,
                "event_type": event_type,
                "message_id": str(message.id),
                "regression_prevented": regression_prevented,
            },
        )
        self.session.add(audit)

    def _detect_thread_role_divergence(
        self,
        message: InboundMessageModel,
        app: ApplicationModel,
        link: MessageLinkModel,
    ) -> bool:
        """Detects if a message in an existing thread is discussing a completely different role."""
        if not app.job or not app.job.normalized_title:
            return False

        current_title = app.job.normalized_title.lower()
        combined = f"{message.subject} {message.body_text}".lower()

        # Phrases indicating a distinct new opportunity in the same thread
        divergence_indicators = [
            "different role",
            "another position",
            "new opportunity",
            "different opportunity",
            "separate position",
            "new requisition",
            "other open role",
        ]
        if any(indicator in combined for indicator in divergence_indicators):
            return True

        # Check if subject mentions an explicit role that contradicts current job
        match = re.search(r"\b(?:role|position|job)\s*:\s*([A-Za-z0-9\s]+)", message.subject)
        if match:
            mentioned_title = match.group(1).strip().lower()
            if mentioned_title and mentioned_title not in current_title and current_title not in mentioned_title:
                return True

        return False

    def _route_ambiguity_to_review(
        self,
        message: InboundMessageModel,
        app_ids: list[str],
        reason: str = "Ambiguous message matches multiple applications",
    ) -> None:
        task = TaskModel(
            task_type="NEEDS_REVIEW",
            status="pending",
            payload_json={
                "reason": reason,
                "message_id": str(message.id),
                "provider_message_id": message.provider_message_id,
                "subject": message.subject,
                "matched_application_ids": app_ids,
            },
        )
        self.session.add(task)

    def _route_contradiction_to_review(
        self,
        message: InboundMessageModel,
        application_id: str,
        previous_status: str,
    ) -> None:
        task = TaskModel(
            task_type="NEEDS_REVIEW",
            application_id=uuid.UUID(application_id),
            status="pending",
            payload_json={
                "reason": f"Contradictory rejection message received while application is in {previous_status} state",
                "message_id": str(message.id),
                "provider_message_id": message.provider_message_id,
                "subject": message.subject,
                "application_id": application_id,
                "current_status": previous_status,
                "proposed_status": "REJECTED",
                "action_required": "Operator must verify if offer was rescinded or if rejection is an automated system glitch.",
            },
        )
        self.session.add(task)

"""Lifecycle engine coordinating state transitions, interviews, CRM, and audits."""

from __future__ import annotations

import logging

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
    message: str


class LifecycleEngine:
    """Manages application state transitions driven by verified communication evidence."""

    TRANSITION_MAP: dict[str, tuple[str, str]] = {
        "APPLICATION_CONFIRMATION": ("CONFIRMED", "APPLICATION_CONFIRMED"),
        "RECRUITER_OUTREACH": ("SCREENING", "RECRUITER_CONTACTED"),
        "SCREENING_REQUEST": ("SCREENING", "SCREENING_SCHEDULED"),
        "INTERVIEW_REQUEST": ("INTERVIEWING", "INTERVIEW_REQUESTED"),
        "INTERVIEW_CONFIRMATION": ("INTERVIEWING", "INTERVIEW_CONFIRMED"),
        "INTERVIEW_RESCHEDULE": ("INTERVIEWING", "INTERVIEW_RESCHEDULED"),
        "OFFER": ("OFFER_RECEIVED", "OFFER_EXTENDED"),
        "REJECTION": ("REJECTED", "APPLICATION_REJECTED"),
    }

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
        """Evaluates an inbound message and triggers verified lifecycle transitions."""
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

        # Record or update Recruiter Contact in CRM
        contact: ContactModel | None = None
        if message.direction == "inbound":
            company_id = app.job.company_id if app.job else None
            contact = self.crm.get_or_create_contact(
                sender_header=message.sender,
                company_id=company_id,
            )
            self.crm.record_touchpoint(contact, message)

        classification = message.classification
        if classification not in self.TRANSITION_MAP:
            # General message, record touchpoint only
            app.last_activity_at = message.received_at
            return None

        new_status, event_type = self.TRANSITION_MAP[classification]
        previous_status = app.status

        # If already rejected or in an equal/later stage, update activity without regressing
        if previous_status == "REJECTED" and new_status != "REJECTED":
            # Rejection is terminal unless offer/screening is explicitly proven
            logger.info(
                f"Skipping status regression from REJECTED to {new_status} for app {app.id}"
            )
            return None

        # Perform transition
        app.status = new_status
        app.last_activity_at = message.received_at
        if new_status == "REJECTED":
            app.closed_at = message.received_at

        # Check and extract interview details if applicable
        interview_scheduled = False
        if classification in (
            "INTERVIEW_REQUEST",
            "INTERVIEW_CONFIRMATION",
            "INTERVIEW_RESCHEDULE",
            "SCREENING_REQUEST",
        ):
            details = self.interview_extractor.extract_from_message(message)
            if details:
                self.interview_extractor.record_interview(application_id=app.id, details=details)
                interview_scheduled = True

        # Record ApplicationEventModel
        event = ApplicationEventModel(
            application_id=app.id,
            event_type=event_type,
            source="email_lifecycle",
            source_reference=message.provider_message_id,
            actor="recruiter" if message.direction == "inbound" else "candidate",
            payload_json={
                "message_id": str(message.id),
                "classification": classification,
                "subject": message.subject,
                "sender": message.sender,
                "contact_id": str(contact.id) if contact else None,
            },
        )
        self.session.add(event)

        # Audit log entry
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
            },
        )
        self.session.add(audit)

        return LifecycleTransitionResult(
            application_id=str(app.id),
            previous_status=previous_status,
            new_status=new_status,
            event_type=event_type,
            contact_name=contact.name if contact else None,
            interview_scheduled=interview_scheduled,
            message=f"Application {app.id} transitioned from {previous_status} to {new_status}",
        )

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
                "subject": message.subject,
                "matched_application_ids": app_ids,
            },
        )
        self.session.add(task)

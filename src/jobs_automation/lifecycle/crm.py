"""Recruiter and hiring manager CRM service."""

from __future__ import annotations

import email.utils
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ContactModel,
    InboundMessageModel,
    MessageLinkModel,
)

logger = logging.getLogger(__name__)


class RecruiterCRMService:
    """Extracts, maintains, and retrieves recruiter contacts and interaction timelines."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def parse_sender(self, sender_header: str) -> tuple[str, str | None]:
        """Extracts display name and clean email from a RFC 2822 sender string."""
        name, addr = email.utils.parseaddr(sender_header)
        clean_addr = addr.strip().lower() if addr else None
        clean_name = name.strip() if name else (clean_addr or "Unknown Contact")
        return clean_name, clean_addr

    def get_or_create_contact(
        self,
        sender_header: str,
        company_id: uuid.UUID | None = None,
        role: str | None = "Recruiter",
    ) -> ContactModel:
        """Finds or creates a ContactModel from an email message sender."""
        name, clean_email = self.parse_sender(sender_header)

        contact: ContactModel | None = None
        if clean_email:
            contact = self.session.scalar(
                select(ContactModel).where(ContactModel.email == clean_email)
            )

        if not contact:
            contact = ContactModel(
                company_id=company_id,
                name=name,
                email=clean_email,
                role=role,
                source="email",
            )
            self.session.add(contact)
            self.session.flush()
        elif company_id and not contact.company_id:
            contact.company_id = company_id

        return contact

    def record_touchpoint(
        self,
        contact: ContactModel,
        message: InboundMessageModel,
    ) -> None:
        """Updates contact timestamp activity."""
        ts = message.received_at
        if contact.first_contact_at is None or ts < contact.first_contact_at:
            contact.first_contact_at = ts
        if contact.last_contact_at is None or ts > contact.last_contact_at:
            contact.last_contact_at = ts

    def get_timeline_for_application(
        self,
        application_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Returns chronological communication timeline linked to an application."""
        stmt = (
            select(InboundMessageModel)
            .join(MessageLinkModel, MessageLinkModel.inbound_message_id == InboundMessageModel.id)
            .where(MessageLinkModel.application_id == application_id)
            .order_by(InboundMessageModel.received_at.asc())
        )
        messages = self.session.scalars(stmt).all()

        timeline: list[dict[str, Any]] = []
        for msg in messages:
            timeline.append(
                {
                    "message_id": str(msg.id),
                    "provider_message_id": msg.provider_message_id,
                    "provider_thread_id": msg.provider_thread_id,
                    "direction": msg.direction,
                    "sender": msg.sender,
                    "subject": msg.subject,
                    "received_at": msg.received_at.isoformat(),
                    "classification": msg.classification,
                    "body_snippet": msg.body_text[:200].replace("\n", " "),
                }
            )
        return timeline

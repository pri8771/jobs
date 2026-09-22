"""Recruiter and hiring manager CRM service supporting multi-role relationships, timelines, and manual correction."""

from __future__ import annotations

import email.utils
import logging
import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    ContactModel,
    InboundMessageModel,
    MessageLinkModel,
)

logger = logging.getLogger(__name__)


class RecruiterCRMService:
    """Extracts, maintains, retrieves, and corrects recruiter contacts and multi-role interaction timelines."""

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
        """Updates contact timestamp activity idempotently."""
        ts = message.received_at
        if contact.first_contact_at is None or ts < contact.first_contact_at:
            contact.first_contact_at = ts
        if contact.last_contact_at is None or ts > contact.last_contact_at:
            contact.last_contact_at = ts

    def prior_thread_contact(
        self, application_id: uuid.UUID, message: InboundMessageModel
    ) -> ContactModel | None:
        """Reuse only one contact proven by prior lifecycle evidence in this thread."""
        rows = self.session.execute(
            select(ApplicationEventModel, InboundMessageModel)
            .join(
                InboundMessageModel,
                InboundMessageModel.provider_message_id == ApplicationEventModel.source_reference,
            )
            .join(MessageLinkModel, MessageLinkModel.inbound_message_id == InboundMessageModel.id)
            .where(
                ApplicationEventModel.application_id == application_id,
                ApplicationEventModel.source == "email_lifecycle",
                MessageLinkModel.application_id == application_id,
                MessageLinkModel.confidence >= 0.8,
                InboundMessageModel.provider_thread_id == message.provider_thread_id,
                InboundMessageModel.received_at < message.received_at,
            )
        ).all()
        contact_ids: set[uuid.UUID] = set()
        for event, prior in rows:
            if (prior.headers_json or {}).get("_provider", {}).get("canary"):
                continue
            raw_id = (event.payload_json or {}).get("contact_id")
            if raw_id is not None:
                try:
                    contact_ids.add(uuid.UUID(str(raw_id)))
                except ValueError:
                    return None
        if len(contact_ids) != 1:
            return None
        return self.session.get(ContactModel, next(iter(contact_ids)))

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

    def _contact_emails(self, contact: ContactModel) -> set[str]:
        """Retain merged sender aliases in the existing correction audit trail."""
        emails = {contact.email.lower()} if contact.email else set()
        audits = self.session.scalars(
            select(AuditLogModel).where(
                AuditLogModel.action_type == "merge_contacts",
                AuditLogModel.result == "success",
                AuditLogModel.entity_type == "contact",
                AuditLogModel.entity_id == contact.id,
            )
        )
        for audit in audits:
            metadata = audit.metadata_json or {}
            inherited = metadata.get("secondary_emails", [])
            aliases = [metadata.get("secondary_email")]
            if isinstance(inherited, list):
                aliases.extend(inherited)
            emails.update(value.lower() for value in aliases if isinstance(value, str) and value)
        return emails

    def _contact_message_ids(self, contact: ContactModel) -> list[uuid.UUID]:
        emails = self._contact_emails(contact)
        references = set(
            self.session.scalars(
                select(ApplicationEventModel.source_reference).where(
                    ApplicationEventModel.source == "email_lifecycle",
                    ApplicationEventModel.payload_json["contact_id"].as_string() == str(contact.id),
                )
            )
        )
        predicates = [
            InboundMessageModel.sender.icontains(address, autoescape=True) for address in emails
        ]
        if references:
            predicates.append(InboundMessageModel.provider_message_id.in_(references))
        if not predicates:
            return []
        messages = self.session.scalars(select(InboundMessageModel).where(or_(*predicates)))
        # A substring match alone must not conflate two distinct mailboxes.
        return [
            message.id
            for message in messages
            if message.provider_message_id in references
            or self.parse_sender(message.sender)[1] in emails
        ]

    def get_applications_for_contact(
        self,
        contact_id: uuid.UUID,
    ) -> list[ApplicationModel]:
        """Finds all applications associated with this recruiter contact across multiple roles."""
        contact = self.session.get(ContactModel, contact_id)
        if not contact:
            return []

        msg_ids = self._contact_message_ids(contact)
        if not msg_ids:
            return []

        app_stmt = (
            select(ApplicationModel)
            .join(MessageLinkModel, MessageLinkModel.application_id == ApplicationModel.id)
            .where(MessageLinkModel.inbound_message_id.in_(msg_ids))
            .distinct()
        )
        return list(self.session.scalars(app_stmt).all())

    def get_timeline_for_contact(
        self,
        contact_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Returns chronological communication timeline across all roles/applications for a contact."""
        contact = self.session.get(ContactModel, contact_id)
        if not contact:
            return []

        stmt = (
            select(InboundMessageModel, MessageLinkModel.application_id)
            .outerjoin(
                MessageLinkModel, MessageLinkModel.inbound_message_id == InboundMessageModel.id
            )
            .where(InboundMessageModel.id.in_(self._contact_message_ids(contact)))
            .distinct()
            .order_by(InboundMessageModel.received_at.asc())
        )
        results = self.session.execute(stmt).all()

        timeline: list[dict[str, Any]] = []
        for msg, app_id in results:
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
                    "application_id": str(app_id) if app_id else None,
                    "body_snippet": msg.body_text[:200].replace("\n", " "),
                }
            )
        return timeline

    def get_contact_summary(
        self,
        contact_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """Returns a consolidated summary of a recruiter contact and their linked applications."""
        contact = self.session.get(ContactModel, contact_id)
        if not contact:
            return None

        apps = self.get_applications_for_contact(contact_id)
        app_summaries = [
            {
                "application_id": str(a.id),
                "job_title": a.job.normalized_title if a.job else "Unknown Role",
                "status": a.status,
                "destination_domain": a.destination_domain,
            }
            for a in apps
        ]

        return {
            "contact_id": str(contact.id),
            "name": contact.name,
            "email": contact.email,
            "role": contact.role,
            "company_name": contact.company.normalized_name if contact.company else None,
            "first_contact_at": (
                contact.first_contact_at.isoformat() if contact.first_contact_at else None
            ),
            "last_contact_at": (
                contact.last_contact_at.isoformat() if contact.last_contact_at else None
            ),
            "applications_count": len(apps),
            "applications": app_summaries,
        }

    def relink_message(
        self,
        inbound_message_id: uuid.UUID,
        new_application_id: uuid.UUID,
        corrected_by: str = "operator",
        notes: str | None = None,
    ) -> MessageLinkModel:
        """Manually corrects a message link to point to the intended application, recording an audit event."""
        msg = self.session.get(InboundMessageModel, inbound_message_id)
        app = self.session.get(ApplicationModel, new_application_id)
        if msg is None:
            raise ValueError(f"Inbound message {inbound_message_id} not found")
        if app is None:
            raise ValueError(f"Application {new_application_id} not found")

        links = list(
            self.session.scalars(
                select(MessageLinkModel)
                .where(
                    MessageLinkModel.inbound_message_id == inbound_message_id,
                    MessageLinkModel.application_id.is_not(None),
                )
                .order_by(MessageLinkModel.id)
            )
        )
        old_app_ids = sorted({str(item.application_id) for item in links})
        link = next(
            (item for item in links if item.application_id == new_application_id),
            links[0] if links else None,
        )
        if link is None:
            link = MessageLinkModel(inbound_message_id=inbound_message_id)
            self.session.add(link)
        for redundant in links:
            if redundant is not link:
                self.session.delete(redundant)
        link.application_id = new_application_id
        link.job_id = app.job_id
        link.company_id = app.job.company_id if app.job else None
        link.method = "manual_correction"
        link.confidence = 1.0
        if app.last_activity_at is None or msg.received_at > app.last_activity_at:
            app.last_activity_at = msg.received_at
        self.session.flush()

        audit = AuditLogModel(
            action_type="manual_message_relink",
            entity_type="message_link",
            entity_id=link.id,
            actor=corrected_by,
            result="success",
            metadata_json={
                "inbound_message_id": str(inbound_message_id),
                "previous_application_id": old_app_ids[0] if len(old_app_ids) == 1 else None,
                "previous_application_ids": old_app_ids,
                "new_application_id": str(new_application_id),
                "notes": notes,
            },
        )
        self.session.add(audit)
        self.session.flush()
        return link

    def unlink_message(
        self,
        inbound_message_id: uuid.UUID,
        application_id: uuid.UUID,
        unlinked_by: str = "operator",
        reason: str = "manual_unlink",
    ) -> bool:
        """Removes a bad message link and logs audit."""
        link = self.session.scalar(
            select(MessageLinkModel).where(
                MessageLinkModel.inbound_message_id == inbound_message_id,
                MessageLinkModel.application_id == application_id,
            )
        )
        if not link:
            return False

        link_id = link.id
        self.session.delete(link)

        audit = AuditLogModel(
            action_type="manual_message_unlink",
            entity_type="message_link",
            entity_id=link_id,
            actor=unlinked_by,
            result="success",
            metadata_json={
                "inbound_message_id": str(inbound_message_id),
                "application_id": str(application_id),
                "reason": reason,
            },
        )
        self.session.add(audit)
        self.session.flush()
        return True

    def merge_contacts(
        self,
        primary_contact_id: uuid.UUID,
        secondary_contact_id: uuid.UUID,
        merged_by: str = "operator",
    ) -> ContactModel:
        """Merges two duplicate contacts, preserves earliest/latest timestamps, and logs an audit record."""
        if primary_contact_id == secondary_contact_id:
            raise ValueError("Cannot merge a contact into itself")
        primary = self.session.get(ContactModel, primary_contact_id)
        secondary = self.session.get(ContactModel, secondary_contact_id)

        if not primary or not secondary:
            raise ValueError("Both primary and secondary contacts must exist to perform merge")

        # Combine timestamps
        all_first = [
            ts for ts in (primary.first_contact_at, secondary.first_contact_at) if ts is not None
        ]
        if all_first:
            primary.first_contact_at = min(all_first)

        all_last = [
            ts for ts in (primary.last_contact_at, secondary.last_contact_at) if ts is not None
        ]
        if all_last:
            primary.last_contact_at = max(all_last)

        if not primary.company_id and secondary.company_id:
            primary.company_id = secondary.company_id

        # Update any events referencing secondary contact
        events = self.session.scalars(
            select(ApplicationEventModel).where(
                ApplicationEventModel.payload_json["contact_id"].as_string()
                == str(secondary_contact_id)
            )
        ).all()
        for ev in events:
            updated_payload = dict(ev.payload_json)
            updated_payload["contact_id"] = str(primary_contact_id)
            ev.payload_json = updated_payload

        secondary_email = secondary.email
        secondary_emails = sorted(self._contact_emails(secondary))
        self.session.delete(secondary)

        audit = AuditLogModel(
            action_type="merge_contacts",
            entity_type="contact",
            entity_id=primary.id,
            actor=merged_by,
            result="success",
            metadata_json={
                "primary_contact_id": str(primary_contact_id),
                "merged_secondary_contact_id": str(secondary_contact_id),
                "secondary_email": secondary_email,
                "secondary_emails": secondary_emails,
            },
        )
        self.session.add(audit)
        self.session.flush()
        return primary

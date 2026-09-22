"""Read-only quarantine checks for durable owner-controlled canary evidence.

Historical mail may be linked to a job or application before a later ingestion
policy reclassifies it as owner-controlled test traffic. This module
deliberately does not repair or delete those historical rows. It builds a
read-only provenance snapshot so operational and dashboard callers can keep
the affected records out of ordinary product flows until an operator has
reconciled them.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.ingestion.engine import canonical_email_addresses, is_durable_canary

CANARY_PROVENANCE_RECONCILIATION_REQUIRED = "CANARY_PROVENANCE_RECONCILIATION_REQUIRED"

# These are the persisted message identifiers used by lifecycle, alerts, and
# timeline records. Looking only at explicit provenance fields avoids treating
# ordinary free text that happens to resemble a provider identifier as evidence.
_MESSAGE_REFERENCE_KEYS: frozenset[str] = frozenset(
    {
        "provider_message_id",
        "source_message_id",
        "message_id",
        "latest_message_id",
        "resolved_by_reply_id",
        "inbound_message_id",
    }
)
_ENTITY_REFERENCE_KEYS: frozenset[str] = frozenset(
    {
        "application_id",
        "matched_application_ids",
        "job_id",
        "interview_id",
        "contact_id",
    }
)
_PROVENANCE_REFERENCE_KEYS = _MESSAGE_REFERENCE_KEYS | _ENTITY_REFERENCE_KEYS


class CanaryProvenanceReconciliationRequiredError(ValueError):
    """Raised before a canary-derived job can enter an operational path."""


def _normalised_reference(value: object) -> str | None:
    if isinstance(value, (str, uuid.UUID)):
        reference = str(value).strip()
        return reference or None
    return None


def _payload_references(
    payload: object,
    references: Collection[str],
    *,
    keys: Collection[str] = _PROVENANCE_REFERENCE_KEYS,
) -> bool:
    """Return whether a structured payload carries a known provenance reference."""
    if not references:
        return False
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key) in keys and _value_references(value, references):
                return True
            if isinstance(value, (Mapping, list, tuple, set)) and _payload_references(
                value, references, keys=keys
            ):
                return True
    elif isinstance(payload, (list, tuple, set)):
        return any(_payload_references(item, references, keys=keys) for item in payload)
    return False


def _value_references(value: object, references: Collection[str]) -> bool:
    if isinstance(value, Mapping):
        return _payload_references(value, references)
    if isinstance(value, (list, tuple, set)):
        return any(_value_references(item, references) for item in value)
    reference = _normalised_reference(value)
    return reference in references if reference is not None else False


def _message_participant_addresses(message: InboundMessageModel) -> set[str]:
    provider_facts = (message.headers_json or {}).get("_provider")
    sender_address = (
        provider_facts.get("sender_address") if isinstance(provider_facts, dict) else None
    )
    return canonical_email_addresses(
        [message.sender, *(message.recipients_json or []), sender_address]
    )


def _uuid_references(values: Iterable[uuid.UUID]) -> set[str]:
    return {str(value) for value in values}


@dataclass(frozen=True)
class DurableCanaryProvenance:
    """Immutable, read-only closure of rows derived from durable canary mail."""

    message_references: frozenset[str]
    job_ids: frozenset[uuid.UUID]
    application_ids: frozenset[uuid.UUID]
    task_ids: frozenset[uuid.UUID]
    interview_ids: frozenset[uuid.UUID]
    contact_ids: frozenset[uuid.UUID]

    def task_is_quarantined(self, task: TaskModel) -> bool:
        """Check both the snapshot and a task's direct durable references."""
        return (
            task.id in self.task_ids
            or task.job_id in self.job_ids
            or task.application_id in self.application_ids
            or _payload_references(
                task.payload_json,
                self.message_references
                | _uuid_references(self.job_ids)
                | _uuid_references(self.application_ids)
                | _uuid_references(self.interview_ids)
                | _uuid_references(self.contact_ids),
            )
        )

    def audit_is_quarantined(self, audit: AuditLogModel) -> bool:
        """Keep logs that point to canary-derived records out of dashboard audit data."""
        related_ids = (
            self.job_ids
            | self.application_ids
            | self.task_ids
            | self.interview_ids
            | self.contact_ids
        )
        if audit.entity_id in related_ids:
            return True
        if audit.entity_id is not None and str(audit.entity_id) in self.message_references:
            return True
        external_reference = _normalised_reference(audit.external_reference)
        if external_reference in self.message_references:
            return True
        return _payload_references(
            audit.metadata_json,
            self.message_references | _uuid_references(related_ids),
        )


def durable_canary_provenance(session: Session) -> DurableCanaryProvenance:
    """Build the durable-canary provenance closure without mutating historical data.

    The persisted canary tag is the only authority here. Current policy aliases
    are intentionally not inferred by dashboard reads; the ingestion preflight is
    responsible for reclassification before a live lifecycle path runs.
    """
    canary_messages = [
        message
        for message in session.scalars(select(InboundMessageModel)).all()
        if is_durable_canary(message)
    ]
    message_ids = {message.id for message in canary_messages}
    message_references = {
        reference
        for message in canary_messages
        for reference in (str(message.id), message.provider_message_id.strip())
        if reference
    }
    canary_addresses = {
        address
        for message in canary_messages
        for address in _message_participant_addresses(message)
    }

    direct_application_ids: set[uuid.UUID] = set()
    job_ids: set[uuid.UUID] = set()
    if message_ids:
        links = session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.inbound_message_id.in_(message_ids))
        ).all()
        direct_application_ids = {
            link.application_id for link in links if link.application_id is not None
        }
        job_ids = {link.job_id for link in links if link.job_id is not None}

    # A legacy lifecycle event can contain the durable provider reference even
    # when its MessageLink was manually removed. Preserve the row, but keep its
    # application (and therefore its job) in reconciliation-only state.
    for event in session.scalars(select(ApplicationEventModel)).all():
        source_reference = _normalised_reference(event.source_reference)
        if source_reference in message_references or _payload_references(
            event.payload_json, message_references, keys=_MESSAGE_REFERENCE_KEYS
        ):
            direct_application_ids.add(event.application_id)

    if direct_application_ids:
        direct_apps = session.scalars(
            select(ApplicationModel).where(ApplicationModel.id.in_(direct_application_ids))
        ).all()
        job_ids.update(app.job_id for app in direct_apps)

    application_ids: set[uuid.UUID] = set(direct_application_ids)
    if job_ids:
        application_ids.update(
            app.id
            for app in session.scalars(
                select(ApplicationModel).where(ApplicationModel.job_id.in_(job_ids))
            ).all()
        )

    all_entity_references = (
        message_references
        | _uuid_references(job_ids)
        | _uuid_references(application_ids)
    )
    task_ids = {
        task.id
        for task in session.scalars(select(TaskModel)).all()
        if task.job_id in job_ids
        or task.application_id in application_ids
        or _payload_references(task.payload_json, all_entity_references)
    }
    interview_ids = {
        interview.id
        for interview in session.scalars(select(InterviewModel)).all()
        if interview.application_id in application_ids
    }

    contact_ids: set[uuid.UUID] = set()
    if canary_addresses:
        for contact in session.scalars(select(ContactModel)).all():
            if canonical_email_addresses([contact.email]) & canary_addresses:
                contact_ids.add(contact.id)
    if application_ids:
        for event in session.scalars(
            select(ApplicationEventModel).where(ApplicationEventModel.application_id.in_(application_ids))
        ).all():
            payload = event.payload_json or {}
            contact_reference = _normalised_reference(payload.get("contact_id"))
            if contact_reference is None:
                continue
            try:
                contact_ids.add(uuid.UUID(contact_reference))
            except ValueError:
                continue

    return DurableCanaryProvenance(
        message_references=frozenset(message_references),
        job_ids=frozenset(job_ids),
        application_ids=frozenset(application_ids),
        task_ids=frozenset(task_ids),
        interview_ids=frozenset(interview_ids),
        contact_ids=frozenset(contact_ids),
    )


def job_ids_with_durable_canary_provenance(
    session: Session,
    job_ids: Collection[uuid.UUID] | None = None,
) -> set[uuid.UUID]:
    """Return jobs historically linked to messages now durably tagged canary."""
    quarantined = set(durable_canary_provenance(session).job_ids)
    return quarantined if job_ids is None else quarantined & set(job_ids)


def job_has_durable_canary_provenance(session: Session, job_id: uuid.UUID) -> bool:
    """Return whether a job must remain reconciliation-only because of canary evidence."""
    return bool(job_ids_with_durable_canary_provenance(session, {job_id}))


def require_job_without_durable_canary_provenance(session: Session, job_id: uuid.UUID) -> None:
    """Fail closed before evaluation, packet generation, or application execution."""
    if job_has_durable_canary_provenance(session, job_id):
        raise CanaryProvenanceReconciliationRequiredError(
            f"{CANARY_PROVENANCE_RECONCILIATION_REQUIRED}: "
            "job is linked to owner-controlled canary evidence and requires reconciliation"
        )

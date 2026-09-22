"""Redacted, runtime-generated recruiting timeline export for one application (V17-R04).

The export binds source message identities (provider ids, provider timestamps), entity
links, lifecycle events, interviews, tasks, contacts, uncertainty, canary exclusion, the
latest application-bound bounded-run replay evidence and the code identity, without
carrying private content: subjects, sender addresses and task reasons are digested,
bodies are never included. ``scripts/export_v17_timeline.py`` writes it;
``scripts/verify_v17_timeline.py`` re-derives it from the trusted runtime database and
compares.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from typing import Any

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
from jobs_automation.ingestion.bounded import (
    BOUNDED_RUN_ACTION,
    code_identity,
    compute_logical_state_digests,
)

TIMELINE_SCHEMA_VERSION = 1
LOW_CONFIDENCE_THRESHOLD = 0.8
# Must match the bounded-run writer's versioned audit metadata contract.
BOUNDED_AUDIT_SCHEMA_VERSION = 2


def _sha(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _domain(address: str | None) -> str | None:
    if not address or "@" not in address:
        return None
    return address.rsplit("@", 1)[1].strip(" >").lower() or None


def _iso(value: datetime.datetime | None) -> str | None:
    return value.isoformat() if value else None


def _application_sha256(application_id: uuid.UUID) -> str:
    """Return the secret-safe application association stored on bounded audits."""
    return hashlib.sha256(str(application_id).encode("utf-8")).hexdigest()


def _metadata_binds_application(metadata: dict[str, Any], application_sha256: str) -> bool:
    """Require an exact application hash in the schema-versioned audit association list."""
    associations = metadata.get("application_id_sha256")
    if isinstance(associations, str):
        return associations == application_sha256
    if not isinstance(associations, list):
        return False
    return any(
        isinstance(association, str) and association == application_sha256
        for association in associations
    )


def _successful_complete_bounded_audit(
    row: AuditLogModel, metadata: dict[str, Any]
) -> bool:
    """A timeline must not surface failed, incomplete, or legacy bounded-run evidence."""
    return (
        row.result == "SUCCESS"
        and metadata.get("schema_version") == BOUNDED_AUDIT_SCHEMA_VERSION
        and metadata.get("status") == "SUCCESS"
        and metadata.get("complete") is True
    )


def _replay_has_bound_original(
    session: Session, metadata: dict[str, Any], application_sha256: str
) -> bool:
    """Verify replay flags and the original audit's application binding before export."""
    replay_of_run_id = metadata.get("replay_of_run_id")
    if replay_of_run_id is None:
        return True
    if (
        not isinstance(replay_of_run_id, str)
        or not replay_of_run_id
        or metadata.get("replay_identical") is not True
        or metadata.get("replay_matches_original") is not True
    ):
        return False
    original = session.scalar(
        select(AuditLogModel).where(
            AuditLogModel.action_type == BOUNDED_RUN_ACTION,
            AuditLogModel.external_reference == replay_of_run_id,
        )
    )
    if original is None:
        return False
    original_metadata = (
        original.metadata_json if isinstance(original.metadata_json, dict) else {}
    )
    return _successful_complete_bounded_audit(
        original, original_metadata
    ) and _metadata_binds_application(original_metadata, application_sha256)


def _latest_application_bounded_audit(
    session: Session, application_sha256: str
) -> tuple[AuditLogModel, dict[str, Any]] | None:
    """Find the latest bounded audit explicitly associated with this application only."""
    rows = session.scalars(
        select(AuditLogModel)
        .where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
        .order_by(AuditLogModel.occurred_at.desc())
    ).all()
    for row in rows:
        metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
        if _metadata_binds_application(metadata, application_sha256):
            return row, metadata
    return None


def timeline_digest(export: dict[str, Any]) -> str:
    """Digest of the export content excluding volatile generation fields."""
    payload = {k: v for k, v in export.items() if k not in {"generated_at_utc", "export_sha256"}}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def build_timeline_export(
    session: Session,
    application_id: uuid.UUID,
    *,
    identity: dict[str, Any] | None = None,
    now: datetime.datetime | None = None,
) -> dict[str, Any]:
    application = session.get(ApplicationModel, application_id)
    if application is None:
        raise ValueError(f"application {application_id} not found")
    job = application.job

    link_rows = session.scalars(
        select(MessageLinkModel).where(MessageLinkModel.application_id == application_id)
    ).all()
    links_by_message = {link.inbound_message_id: link for link in link_rows}
    linked_messages = (
        session.scalars(
            select(InboundMessageModel).where(InboundMessageModel.id.in_(list(links_by_message)))
        ).all()
        if links_by_message
        else []
    )
    # Same-thread messages that are not linked themselves (typically the candidate's own
    # replies, which the alert service already treats as evidence) belong on the timeline.
    thread_ids = sorted({m.provider_thread_id for m in linked_messages if m.provider_thread_id})
    thread_siblings = (
        session.scalars(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_thread_id.in_(thread_ids),
                InboundMessageModel.id.not_in(list(links_by_message)),
            )
        ).all()
        if thread_ids
        else []
    )
    messages = sorted(
        [*linked_messages, *thread_siblings],
        key=lambda m: (m.received_at, m.provider_message_id),
    )

    sources: list[dict[str, Any]] = []
    canary_excluded = 0
    for message in messages:
        provider = dict((message.headers_json or {}).get("_provider") or {})
        link = links_by_message.get(message.id)
        is_canary = bool(provider.get("canary"))
        if is_canary:
            canary_excluded += 1
        sources.append(
            {
                "provider_message_id": message.provider_message_id,
                "provider_thread_id": message.provider_thread_id,
                "provider_received_at": _iso(message.received_at),
                "claimed_date_utc": provider.get("claimed_date_utc"),
                "direction": message.direction,
                "direction_basis": provider.get("direction_basis"),
                "classification": message.classification,
                "confidence": message.confidence,
                "subject_sha256": _sha(message.subject),
                "sender_domain": _domain(provider.get("sender_address") or message.sender),
                "canary": is_canary,
                "link_method": link.method if link is not None else "thread_sibling",
                "link_confidence": link.confidence if link is not None else None,
            }
        )

    events = [
        {
            "event_type": event.event_type,
            "occurred_at": _iso(event.occurred_at),
            "source": event.source,
            "source_reference": event.source_reference,
            "actor": event.actor,
            "regression_prevented": bool((event.payload_json or {}).get("regression_prevented")),
        }
        for event in session.scalars(
            select(ApplicationEventModel)
            .where(ApplicationEventModel.application_id == application_id)
            .order_by(ApplicationEventModel.occurred_at.asc(), ApplicationEventModel.event_type)
        ).all()
    ]
    interviews = [
        {
            "round_type": interview.round_type,
            "scheduled_start": _iso(interview.scheduled_start),
            "scheduled_end": _iso(interview.scheduled_end),
            "timezone": interview.timezone,
            "status": interview.status,
            "meeting_link_present": bool(interview.location_or_link),
        }
        for interview in session.scalars(
            select(InterviewModel)
            .where(InterviewModel.application_id == application_id)
            .order_by(InterviewModel.scheduled_start.asc())
        ).all()
    ]
    tasks = [
        {
            "task_type": task.task_type,
            "status": task.status,
            "due_at": _iso(task.due_at),
            "reason_sha256": _sha(str((task.payload_json or {}).get("reason") or "")),
            "provider_message_id": (task.payload_json or {}).get("provider_message_id"),
        }
        for task in session.scalars(
            select(TaskModel)
            .where(TaskModel.application_id == application_id)
            .order_by(TaskModel.task_type, TaskModel.status)
        ).all()
    ]

    contact_ids: set[str] = set()
    for event in session.scalars(
        select(ApplicationEventModel).where(ApplicationEventModel.application_id == application_id)
    ).all():
        contact_id = (event.payload_json or {}).get("contact_id")
        if contact_id:
            contact_ids.add(str(contact_id))
    contacts: list[dict[str, Any]] = []
    for contact_id in sorted(contact_ids):
        contact = session.get(ContactModel, uuid.UUID(contact_id))
        if contact is None:
            continue
        contacts.append(
            {
                "email_sha256": _sha((contact.email or "").lower()),
                "email_domain": _domain(contact.email),
                "role": contact.role,
                "first_contact_at": _iso(contact.first_contact_at),
                "last_contact_at": _iso(contact.last_contact_at),
            }
        )

    low_confidence = sorted(
        message.provider_message_id
        for message in messages
        if (link := links_by_message.get(message.id)) is not None
        and link.confidence < LOW_CONFIDENCE_THRESHOLD
    )
    pending_review = [
        t for t in tasks if t["task_type"] == "NEEDS_REVIEW" and t["status"] == "pending"
    ]

    replay: dict[str, Any] | None = None
    application_sha256 = _application_sha256(application_id)
    latest_application_run = _latest_application_bounded_audit(session, application_sha256)
    if latest_application_run is not None:
        latest_run, metadata = latest_application_run
        if _successful_complete_bounded_audit(
            latest_run, metadata
        ) and _replay_has_bound_original(session, metadata, application_sha256):
            replay = {
                "run_id": metadata.get("run_id") or latest_run.external_reference,
                "status": metadata.get("status"),
                "adapter": metadata.get("adapter"),
                "synthetic": bool(metadata.get("synthetic")),
                "complete": bool(metadata.get("complete")),
                "replay_of_run_id": metadata.get("replay_of_run_id"),
                "replay_identical": metadata.get("replay_identical"),
                "replay_matches_original": metadata.get("replay_matches_original"),
                "recorded_at": _iso(latest_run.occurred_at),
            }

    genuine_sources = [s for s in sources if not s["canary"]]
    export: dict[str, Any] = {
        "schema_version": TIMELINE_SCHEMA_VERSION,
        "generated_at_utc": (now or datetime.datetime.now(datetime.UTC)).isoformat(),
        "code_identity": dict(identity or code_identity()),
        "application": {
            "id": str(application.id),
            "status": application.status,
            "application_mode": application.application_mode,
            "destination_domain": application.destination_domain,
            "applied_at": _iso(application.applied_at),
            "last_activity_at": _iso(application.last_activity_at),
            "job_id": str(application.job_id),
            "job_title": job.normalized_title if job else None,
            "company": job.company.normalized_name if job and job.company else None,
        },
        "sources": sources,
        "events": events,
        "interviews": interviews,
        "tasks": tasks,
        "contacts": contacts,
        "uncertainty": {
            "pending_review_tasks": len(pending_review),
            "low_confidence_link_message_ids": low_confidence,
            "regression_prevented_events": sum(1 for e in events if e["regression_prevented"]),
        },
        "genuine_evidence": {
            "source_count": len(genuine_sources),
            "canary_excluded_count": canary_excluded,
            "inbound_count": sum(1 for s in genuine_sources if s["direction"] == "inbound"),
            "outbound_count": sum(1 for s in genuine_sources if s["direction"] == "outbound"),
        },
        "replay": replay,
        "logical_state_digests": json.loads(
            compute_logical_state_digests(session).model_dump_json()
        ),
    }
    export["export_sha256"] = timeline_digest(export)
    return export

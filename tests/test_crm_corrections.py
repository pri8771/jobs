"""Standalone synthetic regressions for Jobs V1.7 CRM repairs.

All tests use synthetic records and local SQLite only.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
)
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.engine import LifecycleEngine


def make_session(url: str = "sqlite:///:memory:") -> Session:
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_application(session: Session, company: CompanyModel, title: str) -> ApplicationModel:
    job = JobModel(company_id=company.id, normalized_title=title, status="active")
    session.add(job)
    session.flush()
    application = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="manual",
        destination_domain="example.test",
    )
    session.add(application)
    session.flush()
    return application


def seed_message(
    session: Session,
    provider_id: str,
    sender: str,
    thread: str,
    *,
    classification: str = "REJECTION",
) -> InboundMessageModel:
    row = InboundMessageModel(
        provider_message_id=provider_id,
        provider_thread_id=thread,
        received_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        sender=sender,
        recipients_json=["candidate@example.test"],
        direction="inbound",
        subject="Application status update",
        headers_json={},
        body_text="Unfortunately, we have decided not to move forward.",
        classification=classification,
        confidence=0.99,
    )
    session.add(row)
    session.flush()
    return row


def test_multilink_relink_becomes_one_consistent_link_and_can_process() -> None:
    session = make_session()
    company = CompanyModel(normalized_name="Synthetic Employer")
    session.add(company)
    session.flush()
    old_a = seed_application(session, company, "Old Role A")
    old_b = seed_application(session, company, "Old Role B")
    target = seed_application(session, company, "Correct Role")
    message = seed_message(session, "ambiguous-message", "recruiter@example.test", "thread-1")
    session.add_all(
        [
            MessageLinkModel(
                inbound_message_id=message.id,
                application_id=old_a.id,
                job_id=old_a.job_id,
                company_id=company.id,
                confidence=0.85,
                method="ambiguous",
            ),
            MessageLinkModel(
                inbound_message_id=message.id,
                application_id=old_b.id,
                job_id=old_b.job_id,
                company_id=company.id,
                confidence=0.85,
                method="ambiguous",
            ),
        ]
    )
    session.commit()

    corrected = RecruiterCRMService(session).relink_message(
        message.id,
        target.id,
        corrected_by="synthetic-review",
        notes="resolve ambiguous link",
    )
    session.commit()
    links = session.scalars(
        select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == message.id)
    ).all()

    assert len(links) == 1
    assert corrected.id == links[0].id
    assert links[0].application_id == target.id
    assert links[0].job_id == target.job_id
    assert links[0].company_id == company.id
    assert links[0].method == "manual_correction"
    assert links[0].confidence == 1.0

    transition = LifecycleEngine(session).process_message(message)
    session.commit()
    session.refresh(target)
    session.refresh(old_a)
    session.refresh(old_b)
    assert transition is not None
    assert transition.application_id == str(target.id)
    assert target.status == "REJECTED"
    assert old_a.status == "SUBMITTED"
    assert old_b.status == "SUBMITTED"
    session.close()


def test_relink_to_missing_application_is_atomic_and_leaves_links_untouched() -> None:
    session = make_session()
    company = CompanyModel(normalized_name="Synthetic Employer")
    session.add(company)
    session.flush()
    first = seed_application(session, company, "Role A")
    second = seed_application(session, company, "Role B")
    message = seed_message(session, "invalid-target-message", "recruiter@example.test", "thread-2")
    session.add_all(
        [
            MessageLinkModel(
                inbound_message_id=message.id,
                application_id=first.id,
                job_id=first.job_id,
                company_id=company.id,
                confidence=0.8,
                method="ambiguous",
            ),
            MessageLinkModel(
                inbound_message_id=message.id,
                application_id=second.id,
                job_id=second.job_id,
                company_id=company.id,
                confidence=0.8,
                method="ambiguous",
            ),
        ]
    )
    session.commit()
    before = sorted(
        (str(row.id), str(row.application_id), str(row.job_id), str(row.company_id), row.method)
        for row in session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == message.id)
        ).all()
    )

    import uuid

    with pytest.raises(ValueError, match="application|target|not found"):
        RecruiterCRMService(session).relink_message(message.id, uuid.uuid4())
    session.rollback()
    after = sorted(
        (str(row.id), str(row.application_id), str(row.job_id), str(row.company_id), row.method)
        for row in session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == message.id)
        ).all()
    )
    assert after == before
    session.close()


def test_merged_contact_apps_and_timeline_survive_reopen_without_sender_rewrite(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "crm-merge.sqlite3"
    session = make_session(f"sqlite:///{database_path}")
    company = CompanyModel(normalized_name="Synthetic Employer")
    session.add(company)
    session.flush()
    app_a = seed_application(session, company, "Role A")
    app_b = seed_application(session, company, "Role B")
    primary = ContactModel(
        company_id=company.id,
        name="Primary Recruiter",
        email="primary@example.test",
        role="Recruiter",
        source="email",
    )
    secondary = ContactModel(
        company_id=company.id,
        name="Duplicate Recruiter",
        email="secondary@example.test",
        role="Recruiter",
        source="email",
    )
    session.add_all([primary, secondary])
    session.flush()
    primary_id, secondary_id = primary.id, secondary.id
    app_a_id, app_b_id = app_a.id, app_b.id
    assert primary.email is not None and secondary.email is not None
    msg_a = seed_message(session, "primary-provider-id", primary.email, "primary-thread")
    msg_b = seed_message(session, "secondary-provider-id", secondary.email, "secondary-thread")
    msg_b.received_at = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
    session.add_all(
        [
            MessageLinkModel(
                inbound_message_id=msg_a.id,
                application_id=app_a.id,
                job_id=app_a.job_id,
                company_id=company.id,
                confidence=0.99,
                method="company_match",
            ),
            MessageLinkModel(
                inbound_message_id=msg_b.id,
                application_id=app_b.id,
                job_id=app_b.job_id,
                company_id=company.id,
                confidence=0.99,
                method="company_match",
            ),
            ApplicationEventModel(
                application_id=app_a.id,
                event_type="RECRUITER_OUTREACH",
                source="email_lifecycle",
                source_reference=msg_a.provider_message_id,
                payload_json={"contact_id": str(primary.id)},
            ),
            ApplicationEventModel(
                application_id=app_b.id,
                event_type="RECRUITER_OUTREACH",
                source="email_lifecycle",
                source_reference=msg_b.provider_message_id,
                payload_json={"contact_id": str(secondary.id)},
            ),
        ]
    )
    session.commit()

    RecruiterCRMService(session).merge_contacts(
        primary_id, secondary_id, merged_by="synthetic-review"
    )
    session.commit()
    session.close()

    reopened = make_session(f"sqlite:///{database_path}")
    crm = RecruiterCRMService(reopened)
    applications = crm.get_applications_for_contact(primary_id)
    timeline = crm.get_timeline_for_contact(primary_id)
    senders = {
        row.provider_message_id: row.sender
        for row in reopened.scalars(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id.in_(
                    ("primary-provider-id", "secondary-provider-id")
                )
            )
        ).all()
    }

    assert {row.id for row in applications} == {app_a_id, app_b_id}
    assert [row["provider_message_id"] for row in timeline] == [
        "primary-provider-id",
        "secondary-provider-id",
    ]
    assert len({row["message_id"] for row in timeline}) == 2
    assert senders == {
        "primary-provider-id": "primary@example.test",
        "secondary-provider-id": "secondary@example.test",
    }
    assert reopened.get(ContactModel, secondary_id) is None
    reopened.close()


def test_chained_merge_without_events_ignores_failed_audit_aliases() -> None:
    session = make_session()
    contacts = [
        ContactModel(name=name, email=f"{name}@example.test")
        for name in ("primary", "secondary", "third")
    ]
    session.add_all(contacts)
    session.flush()
    company = CompanyModel(normalized_name="Synthetic")
    session.add(company)
    session.flush()
    app = seed_application(session, company, "Role")
    message = seed_message(session, "third-message", "third@example.test", "thread")
    unrelated = seed_message(session, "failed-merge", "failed@example.test", "other")
    session.add(
        MessageLinkModel(
            inbound_message_id=message.id, application_id=app.id, confidence=1.0, method="test"
        )
    )
    crm = RecruiterCRMService(session)
    crm.merge_contacts(contacts[1].id, contacts[2].id)
    crm.merge_contacts(contacts[0].id, contacts[1].id)
    session.add(
        AuditLogModel(
            action_type="merge_contacts",
            entity_type="contact",
            entity_id=contacts[0].id,
            result="failure",
            actor="test",
            metadata_json={"secondary_email": unrelated.sender},
        )
    )
    session.commit()
    assert [a.id for a in crm.get_applications_for_contact(contacts[0].id)] == [app.id]
    assert [r["message_id"] for r in crm.get_timeline_for_contact(contacts[0].id)] == [
        str(message.id)
    ]
    with pytest.raises(ValueError, match="itself"):
        crm.merge_contacts(contacts[0].id, contacts[0].id)
    assert session.get(ContactModel, contacts[0].id) is not None
    session.close()

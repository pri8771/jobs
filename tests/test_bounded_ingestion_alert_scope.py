"""Synthetic regression coverage for bounded lifecycle and alert scope."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import (
    ApplicationEventModel,
    InboundMessageModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.bounded import BoundedIngestionRequest, BoundedIngestionRunner
from jobs_automation.ingestion.fixtures import get_sample_email_fixtures
from jobs_automation.ingestion.models import RawEmailMessage
from tests.test_bounded_ingestion_scope import (
    MAILBOX,
    WINDOW_END,
    WINDOW_START,
    seed_application,
    seed_old_linked_rejection,
)

CANARY = "synthetic.canary@example.test"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def bounded_request(query: str) -> BoundedIngestionRequest:
    return BoundedIngestionRequest(
        mailbox=MAILBOX,
        query=query,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        cap=50,
    )


def bounded_runner(
    session: Session,
    messages: list[RawEmailMessage],
    *,
    canary_identities: list[str] | None = None,
) -> BoundedIngestionRunner:
    return BoundedIngestionRunner(
        session,
        MockEmailAdapter(messages),
        candidate_emails=[MAILBOX],
        canary_identities=canary_identities or [],
        adapter_kind="mock_fixtures",
        synthetic=True,
        identity={"git_sha": "repair-extra-candidate", "package_version": "0.1.0"},
    )


def test_nonempty_batch_ignores_unrelated_lifecycle_and_alert_records(
    db_session: Session,
) -> None:
    seed_application(db_session)  # Viatris application intentionally exercised by fixtures.
    unrelated_app = seed_application(
        db_session,
        company_name="Unrelated Employer",
        title="Unrelated Role",
        last_activity_at=datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC),
    )
    old_rejection = seed_old_linked_rejection(db_session, unrelated_app)
    unrelated_recruiter = InboundMessageModel(
        provider_message_id="unrelated-old-recruiter",
        provider_thread_id="unrelated-old-thread",
        received_at=datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC),
        sender="unrelated.recruiter@example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Unrelated old recruiter message",
        headers_json={},
        body_text="Synthetic unrelated recruiter evidence.",
        classification="RECRUITER_OUTREACH",
        confidence=0.99,
    )
    db_session.add(unrelated_recruiter)
    db_session.flush()
    preexisting_alert = TaskModel(
        application_id=unrelated_app.id,
        job_id=unrelated_app.job_id,
        task_type="UNANSWERED_RECRUITER",
        status="pending",
        payload_json={
            "thread_id": unrelated_recruiter.provider_thread_id,
            "message_id": str(unrelated_recruiter.id),
        },
    )
    db_session.add(preexisting_alert)
    db_session.commit()

    result = bounded_runner(db_session, get_sample_email_fixtures()).run(
        bounded_request("label:recruiting")
    )

    assert result.status == "SUCCESS"
    assert result.messages_polled > 0
    db_session.refresh(unrelated_app)
    db_session.refresh(preexisting_alert)
    assert unrelated_app.status == "SUBMITTED"
    assert preexisting_alert.status == "pending"
    assert db_session.scalars(
        select(ApplicationEventModel).where(
            ApplicationEventModel.source_reference == old_rejection.provider_message_id
        )
    ).all() == []
    unrelated_new_alerts = db_session.scalars(
        select(TaskModel).where(
            TaskModel.application_id == unrelated_app.id,
            TaskModel.id != preexisting_alert.id,
            TaskModel.task_type.in_(
                ("STALE_APPLICATION_FOLLOW_UP", "STALE_SCREENING_FOLLOW_UP")
            ),
        )
    ).all()
    assert unrelated_new_alerts == []


def test_polled_duplicate_remains_in_batch_for_idempotent_lifecycle_processing(
    db_session: Session,
) -> None:
    app = seed_application(db_session, company_name="Synthetic Employer")
    received_at = datetime.datetime(2026, 1, 15, tzinfo=datetime.UTC)
    raw = RawEmailMessage(
        provider_message_id="duplicate-rejection-in-admitted-batch",
        provider_thread_id="duplicate-rejection-thread",
        received_at=received_at,
        sender="synthetic.recruiter@example.test",
        recipients=[MAILBOX],
        direction="inbound",
        subject="Application status update",
        body_text="Unfortunately, we have decided not to move forward.",
        headers={},
        provider_metadata={},
    )
    persisted = InboundMessageModel(
        provider_message_id=raw.provider_message_id,
        provider_thread_id=raw.provider_thread_id or raw.provider_message_id,
        received_at=raw.received_at,
        sender=raw.sender,
        recipients_json=raw.recipients,
        direction="inbound",
        subject=raw.subject,
        headers_json={},
        body_text=raw.body_text,
        classification="REJECTION",
        confidence=0.99,
    )
    db_session.add(persisted)
    db_session.flush()
    db_session.add(
        MessageLinkModel(
            inbound_message_id=persisted.id,
            application_id=app.id,
            job_id=app.job_id,
            confidence=0.99,
            method="synthetic_preexisting_link",
        )
    )
    db_session.commit()

    result = bounded_runner(db_session, [raw]).run(
        bounded_request("from:synthetic.recruiter@example.test")
    )

    db_session.refresh(app)
    assert result.status == "SUCCESS"
    assert result.messages_polled == 1
    assert result.messages_ingested == 0
    assert result.messages_skipped_duplicate == 1
    assert result.lifecycle_transitions == 1
    assert app.status == "REJECTED"


def test_scoped_reply_closes_only_admitted_thread_and_canary_reply_is_ignored(
    db_session: Session,
) -> None:
    old_time = datetime.datetime(2026, 1, 10, tzinfo=datetime.UTC)

    def seed_thread(thread_id: str, message_id: str) -> TaskModel:
        inbound = InboundMessageModel(
            provider_message_id=message_id,
            provider_thread_id=thread_id,
            received_at=old_time,
            sender=f"{thread_id}@example.test",
            recipients_json=[MAILBOX],
            direction="inbound",
            subject="Synthetic recruiter outreach",
            headers_json={},
            body_text="Would you like to discuss this role?",
            classification="RECRUITER_OUTREACH",
            confidence=0.99,
        )
        db_session.add(inbound)
        db_session.flush()
        task = TaskModel(
            task_type="UNANSWERED_RECRUITER",
            status="pending",
            payload_json={"thread_id": thread_id, "message_id": str(inbound.id)},
        )
        db_session.add(task)
        db_session.flush()
        return task

    admitted_task = seed_thread("admitted-thread", "admitted-old-inbound")
    unrelated_task = seed_thread("unrelated-thread", "unrelated-old-inbound")
    canary_task = seed_thread("canary-thread", "canary-old-inbound")
    db_session.commit()

    reply_time = datetime.datetime(2026, 1, 20, tzinfo=datetime.UTC)
    admitted_reply = RawEmailMessage(
        provider_message_id="admitted-new-reply",
        provider_thread_id="admitted-thread",
        received_at=reply_time,
        sender=MAILBOX,
        recipients=["admitted-thread@example.test"],
        direction="outbound",
        subject="Re: Synthetic recruiter outreach",
        body_text="Thanks for reaching out.",
        headers={},
        provider_metadata={},
    )
    canary_reply = RawEmailMessage(
        provider_message_id="canary-new-reply",
        provider_thread_id="canary-thread",
        received_at=reply_time,
        sender=CANARY,
        recipients=["canary-thread@example.test"],
        direction="outbound",
        subject="Re: Synthetic recruiter outreach",
        body_text="Synthetic canary reply.",
        headers={},
        provider_metadata={},
    )

    result = bounded_runner(
        db_session,
        [admitted_reply, canary_reply],
        canary_identities=[CANARY],
    ).run(bounded_request("subject:recruiter"))

    for task in (admitted_task, unrelated_task, canary_task):
        db_session.refresh(task)
    assert result.status == "SUCCESS"
    assert result.messages_polled == 2
    assert result.canary_messages == 1
    assert admitted_task.status == "completed"
    assert admitted_task.payload_json.get("resolved_by_reply_id")
    assert unrelated_task.status == "pending"
    assert canary_task.status == "pending"

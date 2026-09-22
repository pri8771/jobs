"""Offline regressions for bounded ingestion scope and replay proof."""

from __future__ import annotations

import datetime
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.bounded import (
    BoundedIngestionRequest,
    BoundedIngestionRunner,
)
from jobs_automation.ingestion.fixtures import get_sample_email_fixtures

MAILBOX = "priyansh.chordia@gmail.com"  # identity used by the existing synthetic fixtures
WINDOW_START = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
WINDOW_END = datetime.datetime(2040, 1, 1, tzinfo=datetime.UTC)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def seed_application(
    session: Session,
    *,
    company_name: str = "Viatris",
    title: str = "Solutions Architect",
    last_activity_at: datetime.datetime | None = None,
) -> ApplicationModel:
    company = CompanyModel(normalized_name=company_name)
    session.add(company)
    session.flush()
    job = JobModel(company_id=company.id, normalized_title=title, status="active")
    session.add(job)
    session.flush()
    app = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="assisted",
        destination_domain="example.test",
        applied_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        last_activity_at=last_activity_at
        or datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC),
    )
    session.add(app)
    session.commit()
    return app


def request(*, query: str = "label:recruiting") -> BoundedIngestionRequest:
    return BoundedIngestionRequest(
        mailbox=MAILBOX,
        query=query,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        cap=50,
    )


def runner(
    session: Session,
    messages: list | None = None,
) -> BoundedIngestionRunner:
    return BoundedIngestionRunner(
        session,
        MockEmailAdapter(messages or []),
        candidate_emails=[MAILBOX],
        adapter_kind="mock_fixtures",
        synthetic=True,
        identity={"git_sha": "repair-candidate", "package_version": "0.1.0"},
    )


def seed_old_linked_rejection(session: Session, app: ApplicationModel) -> InboundMessageModel:
    message = InboundMessageModel(
        provider_message_id="old-outside-bounded-batch",
        provider_thread_id="old-outside-thread",
        received_at=datetime.datetime(2019, 1, 1, tzinfo=datetime.UTC),
        sender="synthetic.recruiter@example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Synthetic old rejection",
        headers_json={},
        body_text="Synthetic old evidence outside the bounded batch.",
        classification="REJECTION",
        confidence=0.99,
    )
    session.add(message)
    session.flush()
    session.add(
        MessageLinkModel(
            inbound_message_id=message.id,
            application_id=app.id,
            job_id=app.job_id,
            confidence=0.99,
            method="synthetic_old_evidence",
        )
    )
    session.commit()
    return message


def test_empty_bounded_batch_does_not_process_old_persisted_message(
    db_session: Session,
) -> None:
    app = seed_application(db_session)
    old_message = seed_old_linked_rejection(db_session, app)

    result = runner(db_session).run(request(query="label:no-results"))

    db_session.refresh(app)
    old_events = db_session.scalars(
        select(ApplicationEventModel).where(
            ApplicationEventModel.source_reference == old_message.provider_message_id
        )
    ).all()
    assert result.status == "SUCCESS"
    assert result.messages_polled == 0
    assert result.lifecycle_transitions == 0
    assert app.status == "SUBMITTED"
    assert old_events == []


def test_replay_digest_mismatch_is_not_success(db_session: Session) -> None:
    seed_application(db_session)
    replay_runner = runner(db_session, get_sample_email_fixtures())
    original = replay_runner.run(request())
    assert original.status == "SUCCESS"

    db_session.add(
        TaskModel(
            task_type="synthetic_external_drift",
            status="pending",
            payload_json={"reason": "synthetic logical-state change"},
        )
    )
    db_session.commit()

    replay = replay_runner.replay(original.run_id, MAILBOX)
    assert replay.replay_matches_original is False
    assert replay.status != "SUCCESS"
    assert replay.errors  # mismatch must be machine-readable, not display-only


def test_empty_bounded_batch_does_not_create_unrelated_global_alerts(
    db_session: Session,
) -> None:
    old_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC)
    app = seed_application(db_session, company_name="Unrelated Employer", last_activity_at=old_time)
    old_recruiter = InboundMessageModel(
        provider_message_id="old-unanswered-outside-batch",
        provider_thread_id="old-unanswered-thread",
        received_at=old_time,
        sender="old.recruiter@example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Old unrelated outreach",
        headers_json={},
        body_text="Synthetic old outreach outside the bounded batch.",
        classification="RECRUITER_OUTREACH",
        confidence=0.99,
    )
    db_session.add(old_recruiter)
    db_session.commit()

    result = runner(db_session).run(request(query="label:no-results"))

    unrelated_alerts = db_session.scalars(
        select(TaskModel).where(
            TaskModel.task_type.in_(
                (
                    "UNANSWERED_RECRUITER",
                    "STALE_APPLICATION_FOLLOW_UP",
                    "STALE_SCREENING_FOLLOW_UP",
                )
            )
        )
    ).all()
    assert result.status == "SUCCESS"
    assert result.messages_polled == 0
    assert result.unanswered_alerts == 0
    assert result.stale_alerts == 0
    assert unrelated_alerts == []
    db_session.refresh(app)
    assert app.status == "SUBMITTED"


def test_restart_replay_of_same_bounded_batch_remains_positive(tmp_path: Path) -> None:
    database_path = tmp_path / "bounded-restart.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)

    first_session = session_factory()
    seed_application(first_session)
    first_runner = runner(first_session, get_sample_email_fixtures())
    original = first_runner.run(request())
    assert original.status == "SUCCESS"
    original_run_id = original.run_id
    first_session.close()
    engine.dispose()

    restarted_engine = create_engine(f"sqlite:///{database_path}")
    restarted_session = sessionmaker(bind=restarted_engine)()
    restarted_runner = runner(restarted_session, get_sample_email_fixtures())
    replay = restarted_runner.replay(original_run_id, MAILBOX)

    assert replay.status == "SUCCESS"
    assert replay.messages_ingested == 0
    assert replay.replay_identical is True
    assert replay.replay_matches_original is True
    assert replay.errors == []
    restarted_session.close()
    restarted_engine.dispose()


def test_missing_original_is_failed_not_success(db_session: Session) -> None:
    missing = request().model_copy(update={"replay_of_run_id": "missing-synthetic-run"})
    result = runner(db_session).run(missing)
    assert result.status == "FAILED"
    assert "REPLAY_ORIGINAL_NOT_FOUND" in result.errors


def test_replay_that_changes_logical_state_is_failed(db_session: Session) -> None:
    seed_application(db_session)
    original = runner(db_session).run(request())
    replay = runner(db_session, get_sample_email_fixtures()).replay(original.run_id, MAILBOX)
    assert replay.messages_ingested > 0
    assert replay.replay_identical is False
    assert replay.replay_matches_original is False
    assert replay.status == "FAILED"
    assert "REPLAY_LOGICAL_STATE_MISMATCH" in replay.errors

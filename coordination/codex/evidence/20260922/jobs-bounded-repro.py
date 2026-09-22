"""Synthetic SQLite reproducers for Jobs bounded-ingestion review findings.

Run against the exact reviewed checkout:
    cd <isolated-review-root>/jobs-source
    uv run python <isolated-review-root>/jobs-bounded-repro.py

This script uses only in-memory SQLite and synthetic messages. It does not access Gmail,
OAuth, private candidate data, remote models, network services, or shared databases.
"""

from __future__ import annotations

import datetime

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

MAILBOX = "synthetic.candidate@example.test"


def new_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    return sessionmaker(bind=engine)()


def seed_application(session: Session) -> ApplicationModel:
    company = CompanyModel(normalized_name="Synthetic Employer")
    session.add(company)
    session.flush()
    job = JobModel(
        company_id=company.id,
        normalized_title="Synthetic Role",
        status="active",
    )
    session.add(job)
    session.flush()
    application = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="assisted",
        destination_domain="example.test",
        applied_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        last_activity_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
    )
    session.add(application)
    session.commit()
    return application


def request() -> BoundedIngestionRequest:
    return BoundedIngestionRequest(
        mailbox=MAILBOX,
        query="label:synthetic-bounded-evidence",
        window_start=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        window_end=datetime.datetime(2026, 2, 1, tzinfo=datetime.UTC),
        cap=50,
    )


def runner(session: Session, messages: list | None = None) -> BoundedIngestionRunner:
    return BoundedIngestionRunner(
        session,
        MockEmailAdapter(messages or []),
        candidate_emails=[MAILBOX],
        adapter_kind="mock_fixtures",
        synthetic=True,
        identity={"git_sha": "dd2e0de", "package_version": "0.1.0"},
    )


def reproduce_unbounded_lifecycle_mutation() -> dict[str, object]:
    session = new_session()
    application = seed_application(session)
    old_message = InboundMessageModel(
        provider_message_id="synthetic-old-outside-window",
        provider_thread_id="synthetic-old-thread",
        received_at=datetime.datetime(2019, 1, 1, tzinfo=datetime.UTC),
        sender="synthetic.recruiter@example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Synthetic old rejection",
        headers_json={},
        body_text="Synthetic rejection evidence outside the requested window.",
        classification="REJECTION",
        confidence=0.99,
    )
    session.add(old_message)
    session.flush()
    session.add(
        MessageLinkModel(
            inbound_message_id=old_message.id,
            application_id=application.id,
            job_id=application.job_id,
            confidence=0.99,
            method="synthetic_seeded_old_evidence",
        )
    )
    session.commit()

    result = runner(session).run(request())
    session.refresh(application)
    old_events = session.scalars(
        select(ApplicationEventModel).where(
            ApplicationEventModel.source_reference == old_message.provider_message_id
        )
    ).all()
    observed = {
        "bounded_messages_polled": result.messages_polled,
        "run_status": result.status,
        "lifecycle_transitions": result.lifecycle_transitions,
        "unrelated_app_status_after": application.status,
        "old_event_count": len(old_events),
    }
    assert observed == {
        "bounded_messages_polled": 0,
        "run_status": "SUCCESS",
        "lifecycle_transitions": 1,
        "unrelated_app_status_after": "REJECTED",
        "old_event_count": 1,
    }
    session.close()
    return observed


def reproduce_replay_mismatch_success() -> dict[str, object]:
    session = new_session()
    seed_application(session)
    replay_runner = runner(session, get_sample_email_fixtures())
    original = replay_runner.run(request())
    session.add(
        TaskModel(
            task_type="synthetic_external_drift",
            status="pending",
            payload_json={"reason": "synthetic logical-state change"},
        )
    )
    session.commit()
    replay = replay_runner.replay(original.run_id, MAILBOX)
    observed = {
        "status": replay.status,
        "replay_identical": replay.replay_identical,
        "replay_matches_original": replay.replay_matches_original,
    }
    assert observed == {
        "status": "SUCCESS",
        "replay_identical": True,
        "replay_matches_original": False,
    }
    session.close()
    return observed


if __name__ == "__main__":
    print("bounded_scope_defect", reproduce_unbounded_lifecycle_mutation())
    print("replay_success_defect", reproduce_replay_mismatch_success())

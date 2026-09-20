"""Tests for database models, constraints, and sessions."""

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
)
from jobs_automation.db.session import check_db_connection, init_db


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_db_connection_check() -> None:
    engine = create_engine("sqlite:///:memory:")
    success, msg, latency = check_db_connection(engine)
    assert success is True
    assert "Connected" in msg
    assert latency >= 0


def test_inbound_message_unique_constraint(db_session: Session) -> None:
    now = datetime.datetime.now(datetime.UTC)
    msg1 = InboundMessageModel(
        provider_message_id="gmail_msg_001",
        provider_thread_id="thread_123",
        received_at=now,
        sender="recruiter@techcorp.com",
        recipients_json=["candidate@gmail.com"],
        direction="inbound",
        subject="Interview Invitation",
        headers_json={"Message-ID": "gmail_msg_001"},
        body_text="Hi Priyansh, we would love to schedule a call.",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg1)
    db_session.commit()

    # Attempting to insert duplicate provider_message_id must fail
    msg2 = InboundMessageModel(
        provider_message_id="gmail_msg_001",
        provider_thread_id="thread_123",
        received_at=now,
        sender="recruiter@techcorp.com",
        recipients_json=["candidate@gmail.com"],
        direction="inbound",
        subject="Duplicate Message",
        headers_json={},
        body_text="Duplicate",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_inbound_and_outbound_thread_tracking(db_session: Session) -> None:
    now = datetime.datetime.now(datetime.UTC)
    t1 = now - datetime.timedelta(hours=2)
    t2 = now - datetime.timedelta(hours=1)

    inbound = InboundMessageModel(
        provider_message_id="msg_in_01",
        provider_thread_id="thread_abc",
        received_at=t1,
        sender="recruiter@viatrix.com",
        recipients_json=["candidate@gmail.com"],
        direction="inbound",
        subject="Solutions Architect Role",
        headers_json={},
        body_text="Are you available for a chat?",
        classification="RECRUITER_OUTREACH",
    )
    outbound = InboundMessageModel(
        provider_message_id="msg_out_01",
        provider_thread_id="thread_abc",
        received_at=t2,
        sender="candidate@gmail.com",
        recipients_json=["recruiter@viatrix.com"],
        direction="outbound",
        subject="Re: Solutions Architect Role",
        headers_json={},
        body_text="Yes, I would be glad to connect.",
        classification="CANDIDATE_REPLY",
    )
    db_session.add_all([inbound, outbound])
    db_session.commit()

    # Query chronological thread
    thread_msgs = (
        db_session.execute(
            select(InboundMessageModel)
            .where(InboundMessageModel.provider_thread_id == "thread_abc")
            .order_by(InboundMessageModel.received_at.asc())
        )
        .scalars()
        .all()
    )

    assert len(thread_msgs) == 2
    assert thread_msgs[0].direction == "inbound"
    assert thread_msgs[0].classification == "RECRUITER_OUTREACH"
    assert thread_msgs[1].direction == "outbound"
    assert thread_msgs[1].classification == "CANDIDATE_REPLY"


def test_application_lifecycle_and_audit(db_session: Session) -> None:
    company = CompanyModel(
        normalized_name="Acme Corp",
        domain="acme.com",
        aliases_json=["Acme"],
    )
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Enterprise Solutions Architect",
        location_text="Pittsburgh, PA",
        remote_type="hybrid",
        compensation_min=160000,
        compensation_max=190000,
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(
        job_id=job.id,
        status="READY_TO_APPLY",
        application_mode="assisted",
        destination_domain="acme.com",
        policy_decision="assisted",
    )
    db_session.add(app)
    db_session.flush()

    # Append lifecycle event
    now = datetime.datetime.now(datetime.UTC)
    event = ApplicationEventModel(
        application_id=app.id,
        event_type="APPLICATION_SHORTLISTED",
        occurred_at=now,
        source="scoring_engine",
        actor="system",
        payload_json={"score": 85},
    )
    db_session.add(event)

    # Append audit log
    audit = AuditLogModel(
        action_type="create_application_draft",
        entity_type="application",
        entity_id=app.id,
        actor="cli",
        result="success",
        occurred_at=now,
        metadata_json={"mode": "assisted"},
    )
    db_session.add(audit)
    db_session.commit()

    assert app.job.company is not None
    assert app.job.company.normalized_name == "Acme Corp"
    assert len(app.events) == 1
    assert app.events[0].event_type == "APPLICATION_SHORTLISTED"

"""Tests for V0.6 communication and lifecycle automation."""

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.engine import LifecycleEngine
from jobs_automation.lifecycle.interview import InterviewExtractor


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_recruiter_crm_service(db_session: Session) -> None:
    crm = RecruiterCRMService(db_session)

    # Parse headers
    name, email = crm.parse_sender("Sarah Connor <sarah.connor@cyberdyne.com>")
    assert name == "Sarah Connor"
    assert email == "sarah.connor@cyberdyne.com"

    company = CompanyModel(normalized_name="cyberdyne")
    db_session.add(company)
    db_session.flush()

    # Create contact
    contact = crm.get_or_create_contact(
        "Sarah Connor <sarah.connor@cyberdyne.com>", company_id=company.id
    )
    assert contact.name == "Sarah Connor"
    assert contact.email == "sarah.connor@cyberdyne.com"
    assert contact.company_id == company.id

    now = datetime.datetime.now(datetime.UTC)
    msg = InboundMessageModel(
        provider_message_id="msg-101",
        provider_thread_id="th-101",
        received_at=now,
        sender="sarah.connor@cyberdyne.com",
        subject="Interview chat",
        body_text="Hi Priyansh, let's chat!",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg)
    db_session.flush()

    crm.record_touchpoint(contact, msg)
    assert contact.first_contact_at == now
    assert contact.last_contact_at == now


def test_interview_extractor(db_session: Session) -> None:
    extractor = InterviewExtractor(db_session)

    # Test link extraction
    zoom_text = "Join our Zoom meeting at https://zoom.us/j/123456789?pwd=abc on Tuesday."
    assert extractor.extract_meeting_link(zoom_text) == "https://zoom.us/j/123456789?pwd=abc"

    meet_text = "Google meet link: https://meet.google.com/abc-defg-hij please be on time."
    assert extractor.extract_meeting_link(meet_text) == "https://meet.google.com/abc-defg-hij"

    # Test round type detection
    assert (
        extractor.detect_round_type("Invitation: System Design Interview with Lead Architect")
        == "system_design"
    )
    assert extractor.detect_round_type("Phone screen with recruiter") == "recruiter_screen"
    assert extractor.detect_round_type("Technical coding interview") == "technical_screen"

    now = datetime.datetime.now(datetime.UTC)
    msg = InboundMessageModel(
        provider_message_id="msg-201",
        provider_thread_id="th-201",
        received_at=now,
        sender="talent@netflix.com",
        subject="Netflix System Design Interview Invitation",
        body_text="Hi Priyansh, please join via https://meet.google.com/xyz-uvwx-rst",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg)
    db_session.flush()

    details = extractor.extract_from_message(msg)
    assert details is not None
    assert details.round_type == "system_design"
    assert details.meeting_link == "https://meet.google.com/xyz-uvwx-rst"


def test_lifecycle_engine_state_transitions(db_session: Session) -> None:
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="apple")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Senior iOS Lead", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        destination_domain="jobs.apple.com",
        applied_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(app)
    db_session.flush()

    # Step 1: Confirmation email
    msg_confirm = InboundMessageModel(
        provider_message_id="msg-app-conf",
        provider_thread_id="th-apple-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="jobs-noreply@apple.com",
        subject="Thanks for applying to Apple",
        body_text="We have received your application for Senior iOS Lead.",
        classification="APPLICATION_CONFIRMATION",
    )
    db_session.add(msg_confirm)
    db_session.flush()

    link_confirm = MessageLinkModel(
        inbound_message_id=msg_confirm.id,
        application_id=app.id,
        confidence=0.95,
        method="title_and_company_match",
    )
    db_session.add(link_confirm)
    db_session.commit()

    res_confirm = engine.process_message(msg_confirm)
    assert res_confirm is not None
    assert res_confirm.new_status == "CONFIRMED"
    assert app.status == "CONFIRMED"

    # Step 2: Recruiter interview request
    msg_interview = InboundMessageModel(
        provider_message_id="msg-app-int",
        provider_thread_id="th-apple-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="Jane Doe <jdoe@apple.com>",
        subject="Apple iOS Lead — Technical Screen",
        body_text="Hi Priyansh, let's schedule your technical screen: https://zoom.us/j/987654321",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg_interview)
    db_session.flush()

    link_int = MessageLinkModel(
        inbound_message_id=msg_interview.id,
        application_id=app.id,
        confidence=0.95,
        method="thread_continuation",
    )
    db_session.add(link_int)
    db_session.commit()

    res_int = engine.process_message(msg_interview)
    assert res_int is not None
    assert res_int.new_status == "INTERVIEWING"
    assert res_int.interview_scheduled is True
    assert app.status == "INTERVIEWING"

    # Verify interview record was created
    interview = (
        db_session.query(InterviewModel).filter(InterviewModel.application_id == app.id).first()
    )
    assert interview is not None
    assert interview.round_type == "technical_screen"
    assert "https://zoom.us/j/987654321" in str(interview.location_or_link)

    # Step 3: Offer received
    msg_offer = InboundMessageModel(
        provider_message_id="msg-app-offer",
        provider_thread_id="th-apple-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="Jane Doe <jdoe@apple.com>",
        subject="Offer of Employment - Apple",
        body_text="Congratulations Priyansh, we are thrilled to offer you the Senior iOS Lead position!",
        classification="OFFER",
    )
    db_session.add(msg_offer)
    db_session.flush()

    link_offer = MessageLinkModel(
        inbound_message_id=msg_offer.id,
        application_id=app.id,
        confidence=0.99,
        method="thread_continuation",
    )
    db_session.add(link_offer)
    db_session.commit()

    res_offer = engine.process_message(msg_offer)
    assert res_offer is not None
    assert res_offer.new_status == "OFFER_RECEIVED"
    assert app.status == "OFFER_RECEIVED"


def test_lifecycle_ambiguity_routes_to_review(db_session: Session) -> None:
    engine = LifecycleEngine(db_session)

    job1 = JobModel(normalized_title="Role 1")
    job2 = JobModel(normalized_title="Role 2")
    db_session.add_all([job1, job2])
    db_session.flush()

    app1 = ApplicationModel(job_id=job1.id, status="SUBMITTED")
    app2 = ApplicationModel(job_id=job2.id, status="SUBMITTED")
    db_session.add_all([app1, app2])
    db_session.flush()

    msg = InboundMessageModel(
        provider_message_id="msg-ambig",
        provider_thread_id="th-ambig",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="recruiter@multirole.com",
        subject="Update on your application",
        body_text="We have reviewed your application.",
        classification="REJECTION",
    )
    db_session.add(msg)
    db_session.flush()

    # Link message to both applications
    link1 = MessageLinkModel(
        inbound_message_id=msg.id, application_id=app1.id, confidence=0.85, method="ambiguous"
    )
    link2 = MessageLinkModel(
        inbound_message_id=msg.id, application_id=app2.id, confidence=0.85, method="ambiguous"
    )
    db_session.add_all([link1, link2])
    db_session.commit()

    res = engine.process_message(msg)
    assert res is None  # Ambiguity must NOT transition state

    # Neither application status changed
    assert app1.status == "SUBMITTED"
    assert app2.status == "SUBMITTED"

    # Needs review task was enqueued
    task = db_session.query(TaskModel).filter(TaskModel.task_type == "NEEDS_REVIEW").first()
    assert task is not None
    assert "Ambiguous message" in task.payload_json["reason"]


def test_lifecycle_alerts_unanswered_and_stale(db_session: Session) -> None:
    alert_service = LifecycleAlertService(db_session)
    now = datetime.datetime.now(datetime.UTC)
    three_days_ago = now - datetime.timedelta(days=3)

    # 1. Recruiter email with NO candidate reply
    msg_unanswered = InboundMessageModel(
        provider_message_id="msg-unanswered",
        provider_thread_id="th-unanswered",
        direction="inbound",
        received_at=three_days_ago,
        sender="alice@meta.com",
        subject="Exciting role at Meta",
        body_text="Hi Priyansh, are you free this week to chat?",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg_unanswered)

    # 2. Recruiter email WITH candidate reply
    msg_answered_in = InboundMessageModel(
        provider_message_id="msg-answered-in",
        provider_thread_id="th-answered",
        direction="inbound",
        received_at=three_days_ago,
        sender="bob@google.com",
        subject="Google role",
        body_text="Hi Priyansh, interested in Google?",
        classification="RECRUITER_OUTREACH",
    )
    msg_answered_out = InboundMessageModel(
        provider_message_id="msg-answered-out",
        provider_thread_id="th-answered",
        direction="outbound",
        received_at=three_days_ago + datetime.timedelta(hours=2),
        sender="priyansh.chordia@gmail.com",
        subject="Re: Google role",
        body_text="Hi Bob, yes, I am interested!",
        classification="CANDIDATE_REPLY",
    )
    db_session.add_all([msg_answered_in, msg_answered_out])
    db_session.commit()

    tasks = alert_service.check_unanswered_recruiters(window_hours=48, now=now)
    assert len(tasks) == 1
    assert tasks[0].payload_json["sender"] == "alice@meta.com"

    # 3. Stale application test
    company = CompanyModel(normalized_name="stale co")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Developer")
    db_session.add(job)
    db_session.flush()

    twenty_days_ago = now - datetime.timedelta(days=20)
    stale_app = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        applied_at=twenty_days_ago,
        last_activity_at=twenty_days_ago,
    )
    db_session.add(stale_app)
    db_session.commit()

    stale_tasks = alert_service.check_stale_applications(stale_days=14, now=now)
    assert len(stale_tasks) == 1
    assert stale_tasks[0].application_id == stale_app.id
    assert "no response in 14 days" in stale_tasks[0].payload_json["reason"]

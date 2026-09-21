"""Tests for V0.6 communication and lifecycle automation."""

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    ContactModel,
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
        body_text="Hi Priyansh, your technical screen is scheduled for 2026-10-15 14:00 UTC: https://zoom.us/j/987654321",
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


def test_process_message_idempotency_repeated_sweep(db_session: Session) -> None:
    """Acceptance test 1: Processing same lifecycle message twice produces one event/audit/interview."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="linear")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Staff Frontend Engineer")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, status="SUBMITTED")
    db_session.add(app)
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)
    msg = InboundMessageModel(
        provider_message_id="msg-linear-conf",
        provider_thread_id="th-linear-1",
        received_at=now,
        sender="jobs@linear.app",
        subject="Application received for Staff Frontend Engineer",
        body_text="We have received your application.",
        classification="APPLICATION_CONFIRMATION",
    )
    db_session.add(msg)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=msg.id,
        application_id=app.id,
        confidence=0.95,
        method="title_and_company_match",
    )
    db_session.add(link)
    db_session.commit()

    # First sweep
    res1 = engine.process_message(msg)
    assert res1 is not None
    assert res1.new_status == "CONFIRMED"
    assert app.status == "CONFIRMED"

    events = (
        db_session.query(ApplicationEventModel)
        .filter(ApplicationEventModel.application_id == app.id)
        .all()
    )
    audits = (
        db_session.query(AuditLogModel)
        .filter(AuditLogModel.entity_id == app.id)
        .all()
    )
    assert len(events) == 1
    assert len(audits) == 1

    # Second sweep with identical message -> must be an idempotent no-op
    res2 = engine.process_message(msg)
    assert res2 is None  # No repeated transition

    events_sweep2 = (
        db_session.query(ApplicationEventModel)
        .filter(ApplicationEventModel.application_id == app.id)
        .all()
    )
    audits_sweep2 = (
        db_session.query(AuditLogModel)
        .filter(AuditLogModel.entity_id == app.id)
        .all()
    )
    assert len(events_sweep2) == 1  # No duplicate event
    assert len(audits_sweep2) == 1  # No duplicate audit


def test_interview_no_fabricated_date(db_session: Session) -> None:
    """Acceptance test 2: Interview request with no explicit date must not fabricate a scheduled datetime."""
    engine = LifecycleEngine(db_session)
    extractor = InterviewExtractor(db_session)

    msg = InboundMessageModel(
        provider_message_id="msg-int-no-date",
        provider_thread_id="th-no-date",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="recruiter@figma.com",
        subject="Chat about Figma Engineering role",
        body_text="Hi Priyansh, we'd love to set up an introductory screen. Please let me know your availability for next week.",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg)
    db_session.flush()

    details = extractor.extract_from_message(msg)
    assert details is not None
    assert details.has_explicit_schedule is False
    assert details.scheduled_start is None
    assert details.scheduled_end is None

    # When processed through engine, it must NOT create a fabricated InterviewModel
    company = CompanyModel(normalized_name="figma")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Senior Systems Engineer")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, status="CONFIRMED")
    db_session.add(app)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=msg.id,
        application_id=app.id,
        confidence=0.9,
        method="company_match",
    )
    db_session.add(link)
    db_session.commit()

    res = engine.process_message(msg)
    assert res is not None
    assert res.interview_scheduled is False

    # Zero InterviewModel records with fake date
    interviews = (
        db_session.query(InterviewModel)
        .filter(InterviewModel.application_id == app.id)
        .all()
    )
    assert len(interviews) == 0

    # Routed to NEEDS_REVIEW task with reason
    task = (
        db_session.query(TaskModel)
        .filter(
            TaskModel.application_id == app.id,
            TaskModel.task_type == "NEEDS_REVIEW",
        )
        .first()
    )
    assert task is not None
    assert "no explicit schedule confirmed" in task.payload_json["reason"]


def test_interview_explicit_schedule_and_timezone_parsing(db_session: Session) -> None:
    """Acceptance test 3: Explicit schedule parses correctly across timezones."""
    extractor = InterviewExtractor(db_session)

    # 1. Written date with EDT
    text_edt = (
        "Your technical screen is scheduled for October 15, 2026 at 2:00 PM EDT. "
        "Duration: 45 minutes. Join via https://zoom.us/j/12345"
    )
    start_edt, end_edt, tz_edt = extractor.parse_explicit_datetime(text_edt)
    assert start_edt is not None
    assert end_edt is not None
    assert tz_edt == "EDT"
    # EDT is UTC-4: 14:00 EDT == 18:00 UTC
    assert start_edt == datetime.datetime(2026, 10, 15, 18, 0, tzinfo=datetime.UTC)
    assert end_edt == datetime.datetime(2026, 10, 15, 18, 45, tzinfo=datetime.UTC)

    # 2. ISO timestamp
    text_iso = "Interview confirmed: 2026-11-20T10:00:00Z on Google Meet."
    start_iso, end_iso, tz_iso = extractor.parse_explicit_datetime(text_iso)
    assert start_iso is not None
    assert tz_iso == "Z"
    assert start_iso == datetime.datetime(2026, 11, 20, 10, 0, tzinfo=datetime.UTC)

    # 3. Written date with PST
    text_pst = "Panel interview on November 5, 2026 at 10:00 AM PST."
    start_pst, _, tz_pst = extractor.parse_explicit_datetime(text_pst)
    assert start_pst is not None
    assert tz_pst == "PST"
    # PST is UTC-8: 10:00 PST == 18:00 UTC
    assert start_pst == datetime.datetime(2026, 11, 5, 18, 0, tzinfo=datetime.UTC)


def test_interview_reschedule_reconciliation(db_session: Session) -> None:
    """Acceptance test 4: Reschedule updates/reconciles existing interview rather than inserting duplicate."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="stripe")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Staff Solutions Architect")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, status="INTERVIEWING")
    db_session.add(app)
    db_session.flush()

    # Step 1: Initial scheduled interview
    initial_start = datetime.datetime(2026, 10, 15, 14, 0, tzinfo=datetime.UTC)
    initial_interview = InterviewModel(
        application_id=app.id,
        round_type="technical_screen",
        scheduled_start=initial_start,
        scheduled_end=initial_start + datetime.timedelta(minutes=45),
        timezone="UTC",
        location_or_link="https://meet.google.com/abc-defg-hij",
        status="scheduled",
    )
    db_session.add(initial_interview)
    db_session.commit()

    # Step 2: Reschedule message arrives with new time
    resched_msg = InboundMessageModel(
        provider_message_id="msg-stripe-resched",
        provider_thread_id="th-stripe-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="recruiter@stripe.com",
        subject="Rescheduled: Technical Screen with Stripe",
        body_text="Hi Priyansh, we need to reschedule our interview to 2026-10-18 16:00 UTC. Same link: https://meet.google.com/abc-defg-hij",
        classification="INTERVIEW_RESCHEDULE",
    )
    db_session.add(resched_msg)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=resched_msg.id,
        application_id=app.id,
        confidence=0.95,
        method="thread_continuation",
    )
    db_session.add(link)
    db_session.commit()

    res = engine.process_message(resched_msg)
    assert res is not None
    assert res.interview_scheduled is True

    # Reconciled in place: still exactly 1 interview, NOT 2!
    all_interviews = (
        db_session.query(InterviewModel)
        .filter(InterviewModel.application_id == app.id)
        .all()
    )
    assert len(all_interviews) == 1

    updated_interview = all_interviews[0]
    expected_new_start = datetime.datetime(2026, 10, 18, 16, 0, tzinfo=datetime.UTC)
    assert updated_interview.scheduled_start == expected_new_start
    assert updated_interview.status == "scheduled"
    assert "Rescheduled from" in (updated_interview.notes or "")


def test_interview_cancellation(db_session: Session) -> None:
    """Acceptance test 5: Cancellation changes interview status and keeps historical evidence."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="meta")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Production Engineer")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, status="INTERVIEWING")
    db_session.add(app)
    db_session.flush()

    interview = InterviewModel(
        application_id=app.id,
        round_type="system_design",
        scheduled_start=datetime.datetime(2026, 10, 20, 15, 0, tzinfo=datetime.UTC),
        scheduled_end=datetime.datetime(2026, 10, 20, 15, 45, tzinfo=datetime.UTC),
        timezone="UTC",
        status="scheduled",
    )
    db_session.add(interview)
    db_session.commit()

    cancel_msg = InboundMessageModel(
        provider_message_id="msg-meta-cancel",
        provider_thread_id="th-meta-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="talent@meta.com",
        subject="Cancelled: Meta System Design Interview",
        body_text="Hi Priyansh, our interview is cancelled due to an internal conflict.",
        classification="INTERVIEW_CANCELLED",
    )
    db_session.add(cancel_msg)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=cancel_msg.id,
        application_id=app.id,
        confidence=0.95,
        method="thread_continuation",
    )
    db_session.add(link)
    db_session.commit()

    res = engine.process_message(cancel_msg)
    assert res is not None

    # Interview status must be cancelled, not deleted
    db_session.refresh(interview)
    assert interview.status == "cancelled"
    assert "Cancelled via message msg-meta-cancel" in (interview.notes or "")

    # Application status preserved at INTERVIEWING without crash
    assert app.status == "INTERVIEWING"

    # Event logged
    ev = (
        db_session.query(ApplicationEventModel)
        .filter(
            ApplicationEventModel.application_id == app.id,
            ApplicationEventModel.event_type == "INTERVIEW_CANCELLED",
        )
        .first()
    )
    assert ev is not None


def test_stage_regression_prevention(db_session: Session) -> None:
    """Acceptance test 6: Out-of-order lower-stage email does not regress offer/interview state."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="databricks")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Staff Software Engineer")
    db_session.add(job)
    db_session.flush()

    # Application already reached OFFER_RECEIVED
    app = ApplicationModel(job_id=job.id, status="OFFER_RECEIVED")
    db_session.add(app)
    db_session.flush()

    # Late application confirmation arrives out of order
    msg_late = InboundMessageModel(
        provider_message_id="msg-late-conf",
        provider_thread_id="th-dbx-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="careers@databricks.com",
        subject="Application received",
        body_text="Thanks for applying to Databricks.",
        classification="APPLICATION_CONFIRMATION",
    )
    db_session.add(msg_late)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=msg_late.id,
        application_id=app.id,
        confidence=0.9,
        method="company_match",
    )
    db_session.add(link)
    db_session.commit()

    res = engine.process_message(msg_late)
    assert res is not None

    # Application must NOT regress to CONFIRMED
    assert app.status == "OFFER_RECEIVED"

    # Audit log records regression prevention
    audit = (
        db_session.query(AuditLogModel)
        .filter(AuditLogModel.external_reference == "msg-late-conf")
        .first()
    )
    assert audit is not None
    assert audit.metadata_json["regression_prevented"] is True


def test_recruiter_multi_role_and_cross_application_timeline(db_session: Session) -> None:
    """Acceptance test 7: One recruiter/contact across two applications."""
    crm = RecruiterCRMService(db_session)

    company = CompanyModel(normalized_name="snowflake")
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(company_id=company.id, normalized_title="Senior Backend Engineer")
    job2 = JobModel(company_id=company.id, normalized_title="Principal Architect")
    db_session.add_all([job1, job2])
    db_session.flush()

    app1 = ApplicationModel(job_id=job1.id, status="INTERVIEWING")
    app2 = ApplicationModel(job_id=job2.id, status="SCREENING")
    db_session.add_all([app1, app2])
    db_session.flush()

    recruiter_header = "Rachel Green <rachel.green@snowflake.com>"
    contact = crm.get_or_create_contact(recruiter_header, company_id=company.id)

    # Message 1 for Role 1
    t1 = datetime.datetime(2026, 8, 1, 10, 0, tzinfo=datetime.UTC)
    msg1 = InboundMessageModel(
        provider_message_id="msg-snow-role1",
        provider_thread_id="th-snow-1",
        received_at=t1,
        sender="Rachel Green <rachel.green@snowflake.com>",
        subject="Senior Backend Engineer interview",
        body_text="Hi Priyansh, let's discuss the Senior Backend Engineer role.",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg1)
    db_session.flush()
    crm.record_touchpoint(contact, msg1)

    link1 = MessageLinkModel(
        inbound_message_id=msg1.id, application_id=app1.id, confidence=0.95, method="match"
    )
    db_session.add(link1)

    # Message 2 for Role 2
    t2 = datetime.datetime(2026, 8, 15, 14, 0, tzinfo=datetime.UTC)
    msg2 = InboundMessageModel(
        provider_message_id="msg-snow-role2",
        provider_thread_id="th-snow-2",
        received_at=t2,
        sender="Rachel Green <rachel.green@snowflake.com>",
        subject="Principal Architect position at Snowflake",
        body_text="Hi Priyansh, we also have an open Principal Architect position.",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg2)
    db_session.flush()
    crm.record_touchpoint(contact, msg2)

    link2 = MessageLinkModel(
        inbound_message_id=msg2.id, application_id=app2.id, confidence=0.95, method="match"
    )
    db_session.add(link2)
    db_session.commit()

    # Verify contact spans both applications
    apps_for_contact = crm.get_applications_for_contact(contact.id)
    app_ids = {a.id for a in apps_for_contact}
    assert app1.id in app_ids
    assert app2.id in app_ids

    # Verify contact timeline spans all roles chronologically
    contact_timeline = crm.get_timeline_for_contact(contact.id)
    assert len(contact_timeline) == 2
    assert contact_timeline[0]["provider_message_id"] == "msg-snow-role1"
    assert contact_timeline[1]["provider_message_id"] == "msg-snow-role2"

    # Verify contact summary
    summary = crm.get_contact_summary(contact.id)
    assert summary is not None
    assert summary["applications_count"] == 2
    assert summary["first_contact_at"] == t1.isoformat()
    assert summary["last_contact_at"] == t2.isoformat()


def test_thread_role_divergence_routes_to_review(db_session: Session) -> None:
    """Acceptance test 8: Existing thread + new role ambiguity routes to review."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="uber")
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(company_id=company.id, normalized_title="Senior Android Engineer")
    db_session.add(job1)
    db_session.flush()

    app1 = ApplicationModel(job_id=job1.id, status="CONFIRMED")
    db_session.add(app1)
    db_session.flush()

    # Recruiter reuses same thread for a completely different opportunity
    msg_divergent = InboundMessageModel(
        provider_message_id="msg-uber-divergent",
        provider_thread_id="th-uber-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="recruiter@uber.com",
        subject="Re: Senior Android Engineer - another position available",
        body_text="Hi, we filled the Android role, but we have a different role: Staff Infrastructure Engineer.",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg_divergent)
    db_session.flush()

    link = MessageLinkModel(
        inbound_message_id=msg_divergent.id,
        application_id=app1.id,
        confidence=0.9,
        method="thread_continuation",
    )
    db_session.add(link)
    db_session.commit()

    res = engine.process_message(msg_divergent)
    assert res is None  # Divergence must NOT update old app

    # Old app remains unmutated
    assert app1.status == "CONFIRMED"

    # Needs review task was generated
    review_task = (
        db_session.query(TaskModel)
        .filter(
            TaskModel.task_type == "NEEDS_REVIEW",
            TaskModel.status == "pending",
        )
        .first()
    )
    assert review_task is not None
    assert "different role" in review_task.payload_json["reason"]


def test_alerts_unanswered_recruiter_auto_resolve_on_reply(db_session: Session) -> None:
    """Acceptance test 9: Later candidate reply resolves/suppresses unanswered-recruiter task."""
    alert_service = LifecycleAlertService(db_session)
    now = datetime.datetime.now(datetime.UTC)
    four_days_ago = now - datetime.timedelta(days=4)

    # 1. Inbound recruiter email with no reply initially
    msg_in = InboundMessageModel(
        provider_message_id="msg-meta-outreach",
        provider_thread_id="th-meta-outreach",
        direction="inbound",
        received_at=four_days_ago,
        sender="sarah@meta.com",
        subject="Quick chat about Meta",
        body_text="Hi Priyansh, are you open to chatting?",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg_in)
    db_session.commit()

    # Alert sweep generates pending alert task
    tasks1 = alert_service.check_unanswered_recruiters(window_hours=48, now=now)
    assert len(tasks1) == 1
    task = tasks1[0]
    assert task.status == "pending"

    # 2. Candidate replies later
    msg_reply = InboundMessageModel(
        provider_message_id="msg-meta-reply",
        provider_thread_id="th-meta-outreach",
        direction="outbound",
        received_at=now - datetime.timedelta(hours=1),
        sender="priyansh@example.com",
        subject="Re: Quick chat about Meta",
        body_text="Hi Sarah, yes I would love to chat!",
        classification="CANDIDATE_REPLY",
    )
    db_session.add(msg_reply)
    db_session.commit()

    # Next alert sweep should automatically detect reply and resolve pending task
    tasks2 = alert_service.check_unanswered_recruiters(window_hours=48, now=now)
    assert len(tasks2) == 0  # No new pending tasks

    db_session.refresh(task)
    assert task.status == "completed"
    assert task.payload_json["resolved_by_reply_id"] == str(msg_reply.id)


def test_alerts_duplicate_sweeps_do_not_duplicate_tasks(db_session: Session) -> None:
    """Acceptance test 10: Duplicate sweeps do not duplicate follow-up tasks."""
    alert_service = LifecycleAlertService(db_session)
    now = datetime.datetime.now(datetime.UTC)
    three_days_ago = now - datetime.timedelta(days=3)

    msg_unanswered = InboundMessageModel(
        provider_message_id="msg-dedupe-in",
        provider_thread_id="th-dedupe",
        direction="inbound",
        received_at=three_days_ago,
        sender="recruiter@datadog.com",
        subject="Datadog Engineering",
        body_text="Interested in Datadog?",
        classification="RECRUITER_OUTREACH",
    )
    db_session.add(msg_unanswered)
    db_session.commit()

    # Sweep 1
    tasks1 = alert_service.check_unanswered_recruiters(window_hours=48, now=now)
    assert len(tasks1) == 1

    # Sweep 2 without candidate reply -> should not create a second task
    tasks2 = alert_service.check_unanswered_recruiters(window_hours=48, now=now)
    assert len(tasks2) == 0

    all_tasks = (
        db_session.query(TaskModel)
        .filter(TaskModel.task_type == "UNANSWERED_RECRUITER")
        .all()
    )
    assert len(all_tasks) == 1


def test_manual_correction_relink_and_unlink(db_session: Session) -> None:
    """Test manual correction service for message links (J17-03)."""
    crm = RecruiterCRMService(db_session)

    job1 = JobModel(normalized_title="Role 1")
    job2 = JobModel(normalized_title="Role 2")
    db_session.add_all([job1, job2])
    db_session.flush()

    app1 = ApplicationModel(job_id=job1.id, status="SUBMITTED")
    app2 = ApplicationModel(job_id=job2.id, status="SUBMITTED")
    db_session.add_all([app1, app2])
    db_session.flush()

    msg = InboundMessageModel(
        provider_message_id="msg-manual-link",
        provider_thread_id="th-manual",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="lead@company.com",
        subject="Interview Invitation",
        body_text="Invitation for Role 2",
        classification="INTERVIEW_REQUEST",
    )
    db_session.add(msg)
    db_session.flush()

    # Initially mislinked to app1
    link = MessageLinkModel(
        inbound_message_id=msg.id,
        application_id=app1.id,
        confidence=0.5,
        method="bad_match",
    )
    db_session.add(link)
    db_session.commit()

    # Relink to app2
    updated_link = crm.relink_message(
        inbound_message_id=msg.id,
        new_application_id=app2.id,
        corrected_by="test_operator",
        notes="Corrected erroneous auto-link",
    )
    assert updated_link.application_id == app2.id
    assert updated_link.method == "manual_correction"
    assert updated_link.confidence == 1.0

    # Verify audit log
    audit = (
        db_session.query(AuditLogModel)
        .filter(AuditLogModel.action_type == "manual_message_relink")
        .first()
    )
    assert audit is not None
    assert audit.actor == "test_operator"
    assert audit.metadata_json["new_application_id"] == str(app2.id)

    # Unlink message
    unlinked = crm.unlink_message(
        inbound_message_id=msg.id,
        application_id=app2.id,
        unlinked_by="test_operator",
    )
    assert unlinked is True
    assert db_session.get(MessageLinkModel, updated_link.id) is None


def test_manual_contact_merge(db_session: Session) -> None:
    """Test merging duplicate recruiter contacts (J17-03)."""
    crm = RecruiterCRMService(db_session)

    t1 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    t2 = datetime.datetime(2026, 2, 1, tzinfo=datetime.UTC)
    t3 = datetime.datetime(2026, 3, 1, tzinfo=datetime.UTC)

    primary = ContactModel(
        name="Alex Smith",
        email="alex.smith@corp.com",
        role="Senior Recruiter",
        first_contact_at=t2,
        last_contact_at=t2,
    )
    secondary = ContactModel(
        name="Alex S",
        email="asmith@corp.com",
        role="Recruiter",
        first_contact_at=t1,
        last_contact_at=t3,
    )
    db_session.add_all([primary, secondary])
    db_session.flush()

    merged = crm.merge_contacts(
        primary_contact_id=primary.id,
        secondary_contact_id=secondary.id,
        merged_by="test_admin",
    )

    assert merged.id == primary.id
    # Earliest first contact preserved
    assert merged.first_contact_at == t1
    # Latest last contact preserved
    assert merged.last_contact_at == t3

    # Secondary contact deleted
    assert db_session.get(ContactModel, secondary.id) is None

    # Audit recorded
    audit = (
        db_session.query(AuditLogModel)
        .filter(AuditLogModel.action_type == "merge_contacts")
        .first()
    )
    assert audit is not None
    assert audit.actor == "test_admin"


def test_extended_lifecycle_transitions(db_session: Session) -> None:
    """Test expanded lifecycle classes: ASSESSMENT_REQUEST, BACKGROUND_CHECK, ONBOARDING, WITHDRAWAL (J17-08)."""
    engine = LifecycleEngine(db_session)

    company = CompanyModel(normalized_name="anthropic")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Research Engineer")
    db_session.add(job)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, status="CONFIRMED")
    db_session.add(app)
    db_session.flush()

    # 1. ASSESSMENT_REQUEST transitions to ASSESSMENT
    msg_assess = InboundMessageModel(
        provider_message_id="msg-assess-1",
        provider_thread_id="th-anthropic-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="talent@anthropic.com",
        subject="Technical Assessment Invitation",
        body_text="Please complete the technical coding assessment.",
        classification="ASSESSMENT_REQUEST",
    )
    db_session.add(msg_assess)
    db_session.flush()

    link1 = MessageLinkModel(
        inbound_message_id=msg_assess.id,
        application_id=app.id,
        confidence=0.9,
        method="match",
    )
    db_session.add(link1)
    db_session.commit()

    res_assess = engine.process_message(msg_assess)
    assert res_assess is not None
    assert res_assess.new_status == "ASSESSMENT"
    assert app.status == "ASSESSMENT"

    # 2. OFFER received
    msg_offer = InboundMessageModel(
        provider_message_id="msg-offer-1",
        provider_thread_id="th-anthropic-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="talent@anthropic.com",
        subject="Formal Offer Letter",
        body_text="Congratulations, we are offering you the role.",
        classification="OFFER",
    )
    db_session.add(msg_offer)
    db_session.flush()

    link2 = MessageLinkModel(
        inbound_message_id=msg_offer.id,
        application_id=app.id,
        confidence=0.95,
        method="match",
    )
    db_session.add(link2)
    db_session.commit()

    res_offer = engine.process_message(msg_offer)
    assert res_offer is not None
    assert res_offer.new_status == "OFFER_RECEIVED"
    assert app.status == "OFFER_RECEIVED"

    # 3. BACKGROUND_CHECK retains/advances offer stage with event
    msg_bg = InboundMessageModel(
        provider_message_id="msg-bg-1",
        provider_thread_id="th-anthropic-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="talent@anthropic.com",
        subject="Background check initiation",
        body_text="Please complete your background verification form.",
        classification="BACKGROUND_CHECK",
    )
    db_session.add(msg_bg)
    db_session.flush()

    link3 = MessageLinkModel(
        inbound_message_id=msg_bg.id,
        application_id=app.id,
        confidence=0.95,
        method="match",
    )
    db_session.add(link3)
    db_session.commit()

    res_bg = engine.process_message(msg_bg)
    assert res_bg is not None
    assert res_bg.event_type == "BACKGROUND_CHECK_INITIATED"
    assert app.status == "OFFER_RECEIVED"

    # 4. ONBOARDING transitions to ONBOARDING
    msg_onboard = InboundMessageModel(
        provider_message_id="msg-onboard-1",
        provider_thread_id="th-anthropic-1",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="people@anthropic.com",
        subject="Welcome to Anthropic — Onboarding details",
        body_text="Here is your first day schedule and laptop setup guide.",
        classification="ONBOARDING",
    )
    db_session.add(msg_onboard)
    db_session.flush()

    link4 = MessageLinkModel(
        inbound_message_id=msg_onboard.id,
        application_id=app.id,
        confidence=0.95,
        method="match",
    )
    db_session.add(link4)
    db_session.commit()

    res_onboard = engine.process_message(msg_onboard)
    assert res_onboard is not None
    assert res_onboard.new_status == "ONBOARDING"
    assert app.status == "ONBOARDING"


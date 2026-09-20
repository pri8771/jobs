"""Tests for email ingestion engine, classifier, and job deduplication."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.classifier import EmailClassifier
from jobs_automation.ingestion.deduplication import JobDeduplicationService
from jobs_automation.ingestion.engine import EmailIngestionEngine
from jobs_automation.ingestion.models import (
    EmailClassification,
    ExtractedJobPosting,
    RawEmailMessage,
)
from tests.fixtures.emails.sample_generator import get_sample_email_fixtures


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# EmailClassifier Tests
# ---------------------------------------------------------------------------


def test_classifier_identifies_job_alerts() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])
    msg = RawEmailMessage(
        provider_message_id="msg_alert_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="jobalerts-noreply@linkedin.com",
        recipients=["candidate@gmail.com"],
        subject="3 new jobs for 'Founding Engineer'",
        body_text="Here are new jobs for your search: Founding Engineer at Acme Inc",
    )
    res = classifier.classify(msg)
    assert res.classification == EmailClassification.JOB_ALERT
    assert res.direction == "inbound"
    assert res.needs_review is False


def test_classifier_identifies_application_confirmation() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])
    msg = RawEmailMessage(
        provider_message_id="msg_conf_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="careers@stripe.com",
        recipients=["candidate@gmail.com"],
        subject="Thank you for applying to Stripe",
        body_text="We have received your application for Staff Systems Architect. We will review it shortly.",
    )
    res = classifier.classify(msg)
    assert res.classification == EmailClassification.APPLICATION_CONFIRMATION
    assert res.direction == "inbound"
    assert res.company_hint == "Stripe"


def test_classifier_identifies_recruiter_outreach() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])
    msg = RawEmailMessage(
        provider_message_id="msg_outreach_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="sarah.recruiter@openai.com",
        recipients=["candidate@gmail.com"],
        subject="Exciting role at OpenAI - Staff Infrastructure Engineer",
        body_text="Hi Priyansh, came across your profile and was impressed by your distributed systems work. Would you have 15 minutes to chat?",
    )
    res = classifier.classify(msg)
    assert res.classification == EmailClassification.RECRUITER_OUTREACH
    assert res.direction == "inbound"


def test_classifier_identifies_outbound_candidate_reply() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])
    msg = RawEmailMessage(
        provider_message_id="msg_reply_01",
        provider_thread_id="thread_openai",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="candidate@gmail.com",
        recipients=["sarah.recruiter@openai.com"],
        subject="Re: Exciting role at OpenAI - Staff Infrastructure Engineer",
        body_text="Hi Sarah, thanks for reaching out. Yes, I would be delighted to speak. Here is my availability.",
    )
    res = classifier.classify(msg)
    assert res.classification == EmailClassification.CANDIDATE_REPLY
    assert res.direction == "outbound"
    assert res.needs_review is False


def test_classifier_identifies_interview_and_rejection() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])

    # Interview
    msg_interview = RawEmailMessage(
        provider_message_id="msg_inv_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="recruiting@anthropic.com",
        recipients=["candidate@gmail.com"],
        subject="Invitation to Interview - Technical Discussion",
        body_text="We would like to invite you to a 45-minute technical screen next week.",
    )
    res_inv = classifier.classify(msg_interview)
    assert res_inv.classification == EmailClassification.INTERVIEW_REQUEST

    # Rejection
    msg_rejection = RawEmailMessage(
        provider_message_id="msg_rej_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="talent@databricks.com",
        recipients=["candidate@gmail.com"],
        subject="Update on your application with Databricks",
        body_text="Thank you for your time. Unfortunately, after careful consideration, we have decided to move forward with other candidates at this time.",
    )
    res_rej = classifier.classify(msg_rejection)
    assert res_rej.classification == EmailClassification.REJECTION


def test_classifier_flags_ambiguous_for_review() -> None:
    classifier = EmailClassifier(candidate_emails=["candidate@gmail.com"])
    msg = RawEmailMessage(
        provider_message_id="msg_ambig_01",
        received_at=datetime.datetime.now(datetime.UTC),
        sender="newsletter@weeklydigest.io",
        recipients=["candidate@gmail.com"],
        subject="Your weekly technology digest: New compiler releases",
        body_text="Check out the top engineering blog posts this week.",
    )
    res = classifier.classify(msg)
    assert res.classification == EmailClassification.UNKNOWN_REVIEW_REQUIRED
    assert res.needs_review is True
    assert res.review_reason is not None


# ---------------------------------------------------------------------------
# JobDeduplicationService Tests
# ---------------------------------------------------------------------------


def test_dedup_creates_new_job_and_source(db_session: Session) -> None:
    service = JobDeduplicationService(db_session)
    now = datetime.datetime.now(datetime.UTC)

    posting = ExtractedJobPosting(
        title="Founding Engineer",
        company="Acme AI",
        location="San Francisco, CA",
        remote_type="hybrid",
        compensation_min=180000,
        compensation_max=240000,
        compensation_currency="USD",
        job_url="https://acme.ai/jobs/founding-eng",
        source_provider="linkedin",
        source_job_id="li_12345",
        requisition_id="REQ-001",
        description_snippet="Join our core founding engineering team building generative AI tools.",
    )

    job, is_new = service.ingest_posting(posting, now)
    assert is_new is True
    assert job.normalized_title == "Founding Engineer"
    assert job.company is not None
    assert job.company.normalized_name == "Acme AI"
    assert len(job.sources) == 1
    assert job.sources[0].requisition_id == "REQ-001"
    assert job.sources[0].source_job_id == "li_12345"


def test_dedup_matches_by_requisition_id(db_session: Session) -> None:
    service = JobDeduplicationService(db_session)
    now = datetime.datetime.now(datetime.UTC)

    p1 = ExtractedJobPosting(
        title="Founding Engineer",
        company="Acme AI",
        job_url="https://acme.ai/jobs/req-001",
        source_provider="linkedin",
        source_job_id="li_111",
        requisition_id="REQ-999",
    )
    job1, is_new1 = service.ingest_posting(p1, now)
    assert is_new1 is True

    # Same requisition ID observed on Indeed with different URL and title casing
    later = now + datetime.timedelta(hours=4)
    p2 = ExtractedJobPosting(
        title="Founding Engineer (Core Team)",
        company="Acme AI",
        job_url="https://indeed.com/viewjob?jk=ind_222",
        source_provider="indeed",
        source_job_id="ind_222",
        requisition_id="REQ-999",
    )
    job2, is_new2 = service.ingest_posting(p2, later)
    assert is_new2 is False
    assert job2.id == job1.id
    assert job2.last_seen_at == later
    # Job should now have 2 sources attached
    assert len(job2.sources) == 2


def test_dedup_matches_by_canonical_url(db_session: Session) -> None:
    service = JobDeduplicationService(db_session)
    now = datetime.datetime.now(datetime.UTC)

    canonical_url = "https://jobs.lever.co/datavibe/1234-abcd"
    p1 = ExtractedJobPosting(
        title="Staff Infrastructure Engineer",
        company="DataVibe",
        job_url=canonical_url,
        source_provider="ziprecruiter",
        source_job_id="zr_101",
    )
    job1, is_new1 = service.ingest_posting(p1, now)
    assert is_new1 is True

    # Same canonical URL seen via Dice
    p2 = ExtractedJobPosting(
        title="Staff Infra Engineer",
        company="DataVibe",
        job_url=canonical_url,
        source_provider="dice",
        source_job_id="dice_555",
    )
    job2, is_new2 = service.ingest_posting(p2, now)
    assert is_new2 is False
    assert job2.id == job1.id


def test_dedup_matches_by_normalized_title_and_company(db_session: Session) -> None:
    service = JobDeduplicationService(db_session)
    now = datetime.datetime.now(datetime.UTC)

    p1 = ExtractedJobPosting(
        title="Senior Python Backend Engineer",
        company="CloudScale Systems",
        job_url="https://cloudscale.com/careers/1",
        source_provider="linkedin",
    )
    job1, is_new1 = service.ingest_posting(p1, now)
    assert is_new1 is True

    # Seen again without canonical URL or requisition ID, but same company and title
    p2 = ExtractedJobPosting(
        title="senior python backend engineer",
        company="CloudScale Systems",
        job_url=None,
        source_provider="generic",
    )
    job2, is_new2 = service.ingest_posting(p2, now)
    assert is_new2 is False
    assert job2.id == job1.id


# ---------------------------------------------------------------------------
# EmailIngestionEngine Tests
# ---------------------------------------------------------------------------


def test_engine_sweep_with_sample_fixtures(db_session: Session) -> None:
    fixtures = get_sample_email_fixtures()
    adapter = MockEmailAdapter(fixtures)
    engine = EmailIngestionEngine(
        session=db_session,
        adapter=adapter,
        candidate_emails=["priyansh.chordia@gmail.com"],
    )

    # First sweep: ingest all fixtures
    summary = engine.run_sweep()
    assert summary.messages_polled == len(fixtures)
    assert summary.messages_ingested == len(fixtures)
    assert summary.messages_skipped_duplicate == 0
    assert summary.jobs_discovered_new > 0
    assert summary.checkpoint_advanced_to is not None
    assert len(summary.errors) == 0

    # Verify inbound and outbound messages stored
    stmt_msgs = select(InboundMessageModel)
    all_msgs = db_session.execute(stmt_msgs).scalars().all()
    assert len(all_msgs) == len(fixtures)

    inbound_count = sum(1 for m in all_msgs if m.direction == "inbound")
    outbound_count = sum(1 for m in all_msgs if m.direction == "outbound")
    assert inbound_count > 0
    assert outbound_count > 0

    # Verify thread ID preservation
    threads = {m.provider_thread_id for m in all_msgs if m.provider_thread_id}
    assert "thread_recruiting_viatrix" in threads

    # Verify discovered jobs in DB
    jobs = db_session.execute(select(JobModel)).scalars().all()
    assert len(jobs) == summary.jobs_discovered_new

    # Second sweep with same adapter (incremental): only polls messages in overlap window, skips duplicates
    summary2 = engine.run_sweep()
    assert summary2.messages_ingested == 0
    assert summary2.messages_skipped_duplicate == summary2.messages_polled
    assert summary2.jobs_discovered_new == 0

    # Reconciliation sweep (looks back 48h): polls all fixtures, skips all as duplicates
    summary_recon = engine.run_sweep(reconcile=True)
    assert summary_recon.messages_polled == len(fixtures)
    assert summary_recon.messages_ingested == 0
    assert summary_recon.messages_skipped_duplicate == len(fixtures)
    assert summary_recon.jobs_discovered_new == 0


def test_engine_recruiting_message_linking_and_ambiguity(db_session: Session) -> None:
    now = datetime.datetime.now(datetime.UTC)

    # Setup: Create company and 1 active application
    company = CompanyModel(normalized_name="Stripe", domain="stripe.com", aliases_json=["Stripe"])
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(
        company_id=company.id,
        normalized_title="Staff Systems Architect",
        status="active",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(job1)
    db_session.flush()

    app1 = ApplicationModel(
        job_id=job1.id,
        status="SUBMITTED",
        application_mode="manual",
        policy_decision="manual_only",
        applied_at=now,
        last_activity_at=now,
    )
    db_session.add(app1)
    db_session.commit()

    # Ingest confirmation email for Stripe
    confirmation_msg = RawEmailMessage(
        provider_message_id="msg_conf_stripe",
        received_at=now + datetime.timedelta(minutes=10),
        sender="careers@stripe.com",
        recipients=["priyansh.chordia@gmail.com"],
        subject="Thank you for applying to Stripe",
        body_text="We have received your application for Staff Systems Architect.",
    )

    adapter = MockEmailAdapter([confirmation_msg])
    engine = EmailIngestionEngine(
        session=db_session,
        adapter=adapter,
        candidate_emails=["priyansh.chordia@gmail.com"],
    )
    summary = engine.run_sweep()
    assert summary.messages_ingested == 1

    # Verify MessageLink created
    inbound_msg = db_session.execute(
        select(InboundMessageModel).where(
            InboundMessageModel.provider_message_id == "msg_conf_stripe"
        )
    ).scalar_one()

    link_stmt = select(MessageLinkModel).where(
        MessageLinkModel.inbound_message_id == inbound_msg.id,
        MessageLinkModel.application_id == app1.id,
    )
    link = db_session.execute(link_stmt).scalars().first()
    assert link is not None
    assert link.company_id == company.id

    # Now add a SECOND application for the same company to test ambiguity handling
    job2 = JobModel(
        company_id=company.id,
        normalized_title="Lead Platform Engineer",
        status="active",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(job2)
    db_session.flush()

    app2 = ApplicationModel(
        job_id=job2.id,
        status="SUBMITTED",
        application_mode="manual",
        policy_decision="manual_only",
        applied_at=now,
        last_activity_at=now,
    )
    db_session.add(app2)
    db_session.commit()

    # Send a new message regarding Stripe - should detect ambiguity and create NEEDS_REVIEW task
    ambiguous_msg = RawEmailMessage(
        provider_message_id="msg_interview_stripe_ambig",
        received_at=now + datetime.timedelta(hours=1),
        sender="careers@stripe.com",
        recipients=["priyansh.chordia@gmail.com"],
        subject="Interview Invitation - Stripe",
        body_text="We would like to invite you for an interview at Stripe.",
    )

    adapter2 = MockEmailAdapter([ambiguous_msg])
    engine2 = EmailIngestionEngine(
        session=db_session,
        adapter=adapter2,
        candidate_emails=["priyansh.chordia@gmail.com"],
    )
    summary2 = engine2.run_sweep()
    assert summary2.messages_ingested == 1
    assert summary2.review_tasks_created >= 1

    # Verify task created
    task_stmt = select(TaskModel).where(TaskModel.task_type == "NEEDS_REVIEW")
    task = db_session.execute(task_stmt).scalars().first()
    assert task is not None
    assert "Ambiguous application link" in task.payload_json["reason"]

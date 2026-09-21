"""Tests for V0.4 assisted application engine, policy checks, and review gates."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.browser.assisted_engine import (
    AssistedApplicationEngine,
)
from jobs_automation.browser.base import FormField
from jobs_automation.browser.mock_runner import MockBrowserRunner
from jobs_automation.core import CandidateProfileConfig, ConfigLoader
from jobs_automation.core.policy_registry import (
    DefaultPolicyConfig,
    PolicyDecision,
    PolicyEntryConfig,
    PolicyRegistryConfig,
)
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    AuditLogModel,
    CompanyModel,
    JobModel,
    JobSourceModel,
    TaskModel,
)
from jobs_automation.policy.evaluator import PolicyEvaluator


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def candidate_profile() -> CandidateProfileConfig:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile()
    profile.identity.email = "priyansh.chordia@gmail.com"
    profile.identity.phone = "+1-412-555-0199"
    profile.links.linkedin = "https://linkedin.com/in/priyansh-chordia"
    profile.links.github = "https://github.com/pri8771"
    return profile


@pytest.fixture
def policy_config() -> PolicyRegistryConfig:
    return PolicyRegistryConfig(
        version=1,
        default=DefaultPolicyConfig(
            decision=PolicyDecision.BLOCKED,
            reason="deny_by_default_unverified_destination",
        ),
        entries=[
            PolicyEntryConfig(
                platform="greenhouse",
                domain_pattern="*.greenhouse.io",
                capability="submit_application",
                decision=PolicyDecision.ASSISTED,
                reviewed_at="2026-09-20",
                evidence=["Greenhouse candidate application portal"],
            ),
            PolicyEntryConfig(
                platform="linkedin",
                domain_pattern="*.linkedin.com",
                capability="submit_application",
                decision=PolicyDecision.MANUAL_ONLY,
                reviewed_at="2026-09-20",
                evidence=["LinkedIn User Agreement section 8.2 prohibits bots"],
            ),
            PolicyEntryConfig(
                platform="blocked_scam_board",
                domain_pattern="*.sketchy-board.com",
                capability="submit_application",
                decision=PolicyDecision.BLOCKED,
                reviewed_at="2026-09-20",
                evidence=["Known bot farm / spam destination"],
            ),
        ],
    )


def test_assisted_application_policy_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="sketchy corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Software Engineer",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="sketchy_board",
        canonical_apply_url="https://jobs.sketchy-board.com/apply/123",
    )
    db_session.add(source)
    db_session.commit()

    res = engine.execute(job_id=job.id)
    assert res.status == "BLOCKED"
    assert res.policy_decision == "blocked"

    # Verify audit log was recorded
    audit = db_session.query(AuditLogModel).filter(AuditLogModel.entity_id == job.id).first()
    assert audit is not None
    assert audit.result == "blocked"
    assert audit.action_type == "policy_blocked_application_attempt"


def test_assisted_application_manual_only(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="linkedin co")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Staff Engineer",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="linkedin",
        canonical_apply_url="https://www.linkedin.com/jobs/view/999888",
    )
    db_session.add(source)
    db_session.commit()

    # Step 1: Without confirmation, creates in-progress manual task
    res_review = engine.execute(job_id=job.id, auto_confirm=False)
    assert res_review.status == "REVIEW_REQUIRED"
    assert res_review.policy_decision == "manual_only"

    # Verify browser runner was NOT called to prefill form
    assert len(runner.prefilled_calls) == 0

    # Step 2: With user confirmation that native submission succeeded
    res_confirmed = engine.execute(
        job_id=job.id,
        auto_confirm=True,
        receipt_text="LinkedIn confirmation email received",
    )
    assert res_confirmed.status == "MANUAL_RECORDED"

    app = db_session.query(ApplicationModel).filter(ApplicationModel.job_id == job.id).first()
    assert app is not None
    assert app.status == "SUBMITTED"
    assert app.application_mode == "manual"
    assert app.applied_at is not None

    event = (
        db_session.query(ApplicationEventModel)
        .filter(ApplicationEventModel.application_id == app.id)
        .first()
    )
    assert event is not None
    assert event.event_type == "APPLICATION_SUBMITTED"
    assert event.source == "manual_native"


def test_assisted_application_prefill_and_confirm(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner(
        interactive_submitted=True,
        custom_fields=[
            FormField(name="first_name", selector="#first_name", required=True, label="First Name"),
            FormField(name="last_name", selector="#last_name", required=True, label="Last Name"),
            FormField(name="email", selector="#email", field_type="email", required=True, label="Email"),
            FormField(name="phone", selector="#phone", field_type="tel", required=True, label="Phone"),
            FormField(name="linkedin", selector="#linkedin", required=False, label="LinkedIn Profile"),
            FormField(name="github", selector="#github", required=False, label="GitHub Profile"),
            FormField(name="resume", selector="#resume", field_type="file", required=True, label="Resume/CV"),
            FormField(name="years_of_experience", selector="#years_of_experience", required=False, label="Years of Experience"),
        ],
    )
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="acme corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Solutions Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/acme/jobs/54321",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_markdown",
        storage_uri="/artifacts/resumes/acme_resume.md",
        sha256="abc123resumehash",
        metadata_json={"track": "Enterprise Automation"},
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        answers_json={"years_of_experience": "12", "sponsorship_required": "No"},
        unresolved_questions_json=[],
        packet_hash="packet_hash_xyz_789",
    )
    db_session.add(packet)

    review_task = TaskModel(
        job_id=job.id,
        task_type="NEEDS_REVIEW",
        status="pending",
        payload_json={"reason": "Verify packet before submission"},
    )
    db_session.add(review_task)
    db_session.commit()

    # Execute assisted apply
    res = engine.execute(
        job_id=job.id,
        packet_id=packet.id,
        auto_confirm=True,
        allow_simulation=True,
    )

    assert res.status == "SUBMITTED"
    assert res.policy_decision == "assisted"
    assert res.prefilled_count > 0

    # Verify form was prefilled with candidate facts and answers
    assert len(runner.prefilled_calls) == 1
    call_url, prefilled_dict = runner.prefilled_calls[0]
    assert call_url == job.apply_url
    assert prefilled_dict["first_name"] == "Priyansh"
    assert prefilled_dict["last_name"] == "Chordia"
    assert prefilled_dict["email"] == "priyansh.chordia@gmail.com"
    assert prefilled_dict["years_of_experience"] == "12"

    # Verify application recorded in database
    app = db_session.query(ApplicationModel).filter(ApplicationModel.job_id == job.id).first()
    assert app is not None
    assert app.status == "SUBMITTED"
    assert app.application_mode == "assisted"
    assert app.destination_domain == "boards.greenhouse.io"
    assert app.applied_at is not None

    # Verify event and audit log
    event = (
        db_session.query(ApplicationEventModel)
        .filter(ApplicationEventModel.application_id == app.id)
        .first()
    )
    assert event is not None
    assert event.event_type == "APPLICATION_SUBMITTED"
    assert event.source == "assisted_browser"

    audit = db_session.query(AuditLogModel).filter(AuditLogModel.entity_id == app.id).first()
    assert audit is not None
    assert audit.result == "success"
    assert audit.input_hash == "packet_hash_xyz_789"

    # Verify review task was completed
    db_session.refresh(review_task)
    assert review_task.status == "completed"
    assert review_task.application_id == app.id


def test_assisted_application_idempotency(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=True,
    )

    company = CompanyModel(normalized_name="tech inc")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Lead Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/techinc/1001",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_markdown",
        storage_uri="/artifacts/resumes/techinc_resume.md",
        sha256="techinc_resume_hash",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        answers_json={},
        unresolved_questions_json=[],
        packet_hash="packet_hash_idempotency_123",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    # First submission
    res1 = engine.execute(
        job_id=job.id,
        packet_id=packet.id,
        auto_confirm=True,
        allow_simulation=True,
    )
    assert res1.status == "SUBMITTED"

    # Second attempt must be rejected by idempotency check
    res2 = engine.execute(
        job_id=job.id,
        packet_id=packet.id,
        auto_confirm=True,
        allow_simulation=True,
    )
    assert res2.status == "ALREADY_SUBMITTED"
    assert "was already submitted" in res2.message

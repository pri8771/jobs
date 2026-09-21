"""Tests for V0.5 controlled automatic application, ATS adapters, and safety gates."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.automation.adapters.greenhouse import GreenhouseATSAdapter
from jobs_automation.automation.adapters.lever import LeverATSAdapter
from jobs_automation.automation.auto_engine import ControlledAutoApplicationEngine
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.automation.rate_limiter import DomainRateLimiter
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
            reason="deny_by_default",
        ),
        entries=[
            PolicyEntryConfig(
                platform="greenhouse",
                domain_pattern="*.greenhouse.io",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2026-09-20",
                review_due_at="2027-01-01",
                evidence=["Approved employer Greenhouse ATS endpoint"],
            ),
            PolicyEntryConfig(
                platform="lever",
                domain_pattern="*.lever.co",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2026-09-20",
                review_due_at="2027-01-01",
                evidence=["Approved employer Lever ATS endpoint"],
            ),
            PolicyEntryConfig(
                platform="expired_ats",
                domain_pattern="*.expired-ats.com",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2025-01-01",
                review_due_at="2025-06-01",  # Expired
                evidence=["Old policy review"],
            ),
            PolicyEntryConfig(
                platform="linkedin",
                domain_pattern="*.linkedin.com",
                capability="submit_application",
                decision=PolicyDecision.MANUAL_ONLY,
                reviewed_at="2026-09-20",
                evidence=["LinkedIn User Agreement"],
            ),
        ],
    )


def test_greenhouse_and_lever_adapter_validation(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
) -> None:
    gh_adapter = GreenhouseATSAdapter()
    lever_adapter = LeverATSAdapter()

    assert gh_adapter.can_handle("boards.greenhouse.io")
    assert not gh_adapter.can_handle("jobs.lever.co")
    assert lever_adapter.can_handle("jobs.lever.co")
    assert not lever_adapter.can_handle("boards.greenhouse.io")

    # Valid packet
    import uuid

    sample_artifact_id = uuid.uuid4()
    valid_packet = ApplicationPacketModel(
        candidate_profile_version=1,
        resume_artifact_id=sample_artifact_id,
        answers_json={"years_exp": "10"},
        unresolved_questions_json=[],
        packet_hash="hash123",
    )
    val_gh = gh_adapter.validate_packet(valid_packet, candidate_profile)
    assert val_gh.is_valid is True

    # Packet with unresolved question must trigger unknown_question_stop
    unresolved_packet = ApplicationPacketModel(
        candidate_profile_version=1,
        resume_artifact_id=sample_artifact_id,
        answers_json={},
        unresolved_questions_json=["Do you have an active security clearance?"],
        packet_hash="hash456",
    )
    val_stop = gh_adapter.validate_packet(unresolved_packet, candidate_profile)
    assert val_stop.is_valid is False
    assert val_stop.unknown_question_stop is True


def test_controlled_auto_apply_success(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="stripe")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Staff Solutions Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/stripe/jobs/12345",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_markdown",
        storage_uri="/artifacts/resumes/stripe.md",
        sha256="stripehash123",
        metadata_json={},
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        answers_json={"remote_experience": "yes"},
        unresolved_questions_json=[],
        packet_hash="packet_hash_stripe",
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute_auto_apply(job_id=job.id, mock_mode=True)

    assert res.status == "SIMULATED"
    assert res.platform == "greenhouse"
    assert res.receipt_id is not None
    assert "SIM-GH-" in res.receipt_id
    assert res.confirmation_url is None

    # Verify DB state
    app = db_session.query(ApplicationModel).filter(ApplicationModel.job_id == job.id).first()
    assert app is not None
    assert app.status == "SIMULATED"
    assert app.application_mode == "auto_simulated"

    event = (
        db_session.query(ApplicationEventModel)
        .filter(ApplicationEventModel.application_id == app.id)
        .first()
    )
    assert event is not None
    assert event.event_type == "APPLICATION_SIMULATED"

    audit = db_session.query(AuditLogModel).filter(AuditLogModel.entity_id == app.id).first()
    assert audit is not None
    assert audit.result == "simulated"
    assert audit.external_reference == res.receipt_id


def test_controlled_auto_apply_live_not_implemented(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="airbnb")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Staff Solutions Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/airbnb/jobs/99999",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_markdown",
        storage_uri="/artifacts/resumes/airbnb.md",
        sha256="airbnbhash123",
        metadata_json={},
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        answers_json={"remote_experience": "yes"},
        unresolved_questions_json=[],
        packet_hash="packet_hash_airbnb",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    # Live mode execution must fail closed with NOT_IMPLEMENTED and never fabricate a submission
    res = engine.execute_auto_apply(job_id=job.id, mock_mode=False)

    assert res.status == "NOT_IMPLEMENTED"
    assert "not yet implemented" in res.message

    # Ensure no application was marked submitted
    app = db_session.query(ApplicationModel).filter(ApplicationModel.job_id == job.id).first()
    assert app is None


def test_controlled_auto_apply_unknown_question_stop(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="figma")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Principal Automation Lead",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="lever",
        canonical_apply_url="https://jobs.lever.co/figma/67890",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_markdown",
        storage_uri="/artifacts/resumes/figma.md",
        sha256="figmahash123",
        metadata_json={},
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        answers_json={},
        unresolved_questions_json=["What is your expected notice period at your current employer?"],
        packet_hash="packet_hash_figma",
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute_auto_apply(job_id=job.id, mock_mode=True)

    assert res.status == "STOPPED_UNKNOWN_QUESTION"
    assert "unknown screening questions" in res.message

    # Ensure application was NOT marked submitted
    app = db_session.query(ApplicationModel).filter(ApplicationModel.job_id == job.id).first()
    assert app is None

    # Ensure review task was enqueued
    task = (
        db_session.query(TaskModel)
        .filter(TaskModel.job_id == job.id, TaskModel.status == "pending")
        .first()
    )
    assert task is not None
    assert task.task_type == "NEEDS_REVIEW"


def test_controlled_auto_apply_kill_switch_active(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    ks_manager = KillSwitchManager(global_override=True)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
        kill_switch=ks_manager,
    )

    company = CompanyModel(normalized_name="uber")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Systems Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/uber/1111",
    )
    db_session.add(source)
    db_session.commit()

    res = engine.execute_auto_apply(job_id=job.id, mock_mode=True)
    assert res.status == "KILL_SWITCH_ACTIVE"
    assert "Global kill switch enabled" in res.message


def test_controlled_auto_apply_policy_expiration_triggers_kill_switch(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    ks_manager = KillSwitchManager(policy_config=policy_config)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
        kill_switch=ks_manager,
    )

    company = CompanyModel(normalized_name="old corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        company_id=company.id,
        normalized_title="Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="expired_ats",
        canonical_apply_url="https://jobs.expired-ats.com/oldcorp/123",
    )
    db_session.add(source)
    db_session.commit()

    res = engine.execute_auto_apply(job_id=job.id, mock_mode=True)
    # The policy review expired in 2025, so policy evaluation marks it BLOCKED
    assert res.status == "BLOCKED"
    assert "policy_review_expired" in res.message


def test_controlled_auto_apply_rate_limiting(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    evaluator = PolicyEvaluator(policy_config)
    rate_limiter = DomainRateLimiter(min_interval_seconds=10.0, max_per_hour=5)
    engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=candidate_profile,
        rate_limiter=rate_limiter,
    )

    company = CompanyModel(normalized_name="datadog")
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(company_id=company.id, normalized_title="Lead 1", status="shortlisted")
    job2 = JobModel(company_id=company.id, normalized_title="Lead 2", status="shortlisted")
    db_session.add_all([job1, job2])
    db_session.flush()

    source1 = JobSourceModel(
        job_id=job1.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/datadog/1",
    )
    source2 = JobSourceModel(
        job_id=job2.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/datadog/2",
    )
    db_session.add_all([source1, source2])

    resume_art = ArtifactModel(type="resume", storage_uri="/art/r.md", sha256="h1")
    db_session.add(resume_art)
    db_session.flush()

    pkt1 = ApplicationPacketModel(
        job_id=job1.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="ph1",
    )
    pkt2 = ApplicationPacketModel(
        job_id=job2.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="ph2",
    )
    db_session.add_all([pkt1, pkt2])
    db_session.commit()

    # First apply succeeds (simulated)
    res1 = engine.execute_auto_apply(job_id=job1.id, mock_mode=True)
    assert res1.status == "SIMULATED"

    # Immediate second apply to same domain must be rate limited!
    res2 = engine.execute_auto_apply(job_id=job2.id, mock_mode=True)
    assert res2.status == "RATE_LIMITED"
    assert "Pacing limit" in res2.message

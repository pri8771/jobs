"""Adversarial and safety tests for V1.5 assisted browser application runtime.

Covers all required acceptance scenarios from docs/V1_5_BROWSER_SAFETY_CONTRACT.md:
- no explicit packet ID -> blocked
- unaccepted/wrong-job packet -> blocked
- missing or hash-mismatched resume -> blocked
- inspect_form() not successful -> no prefill
- EEO field discovered -> manual/unfilled
- unknown required field -> review/block
- unresolved packet question -> review/block
- mock runner cannot create real SUBMITTED
- auto_confirm=True without external evidence cannot create real SUBMITTED
- generic receipt text cannot satisfy confirmation
- pre-submit review manifest generated and persisted
- upload hash verified immediately before upload
"""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.browser.assisted_engine import (
    AssistedApplicationEngine,
    classify_field,
    compute_form_fingerprint,
    is_valid_external_confirmation,
)
from jobs_automation.browser.base import (
    BrowserSessionResult,
    FieldClassification,
    FormField,
    FormInspectionResult,
)
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
    profile.identity.full_name = "Priyansh Chordia"
    profile.identity.email = "priyansh.chordia@gmail.com"
    profile.identity.phone = "+1-412-555-0199"
    profile.identity.city = "San Francisco"
    profile.identity.state = "CA"
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
                platform="blocked_board",
                domain_pattern="*.blocked-site.com",
                capability="submit_application",
                decision=PolicyDecision.BLOCKED,
                reviewed_at="2026-09-20",
                evidence=["Blocked policy"],
            ),
        ],
    )


def test_adversarial_no_explicit_packet_id_is_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-00: Assisted application execution without explicit packet_id is blocked."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
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
        normalized_title="Staff AI Engineer",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/acme/jobs/101",
    )
    db_session.add(source)
    db_session.commit()

    # Attempt execute without packet_id
    res = engine.execute(job_id=job.id, packet_id=None)
    assert res.status == "BLOCKED"
    assert "Explicit accepted packet_id is required" in res.message

    # Audit log recorded
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == "assisted_prefill_rejected")
    )
    assert audit is not None
    assert audit.result == "blocked"
    assert audit.metadata_json["reason"] == "missing_explicit_packet_id"


def test_adversarial_wrong_job_packet_is_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-00: Passing a packet that belongs to a different job is blocked."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="target corp")
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(company_id=company.id, normalized_title="Job 1", status="shortlisted")
    job2 = JobModel(company_id=company.id, normalized_title="Job 2", status="shortlisted")
    db_session.add_all([job1, job2])
    db_session.flush()

    source = JobSourceModel(
        job_id=job1.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/target/jobs/1",
    )
    db_session.add(source)

    # Packet for job2
    packet_for_job2 = ApplicationPacketModel(
        job_id=job2.id,
        candidate_profile_version=1,
        packet_hash="hash_pkt_2",
        is_live_ready=True,
    )
    db_session.add(packet_for_job2)
    db_session.commit()

    # Attempt to execute job1 with job2's packet
    res = engine.execute(job_id=job1.id, packet_id=packet_for_job2.id)
    assert res.status == "BLOCKED"
    assert "belongs to job" in res.message


def test_adversarial_non_live_ready_packet_is_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-00: A packet that is not marked live-ready is blocked in live mode."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=False,
        require_live_ready=True,
    )

    company = CompanyModel(normalized_name="beta inc")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="SWE", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/beta/jobs/10",
    )
    db_session.add(source)

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        packet_hash="hash_unready",
        is_live_ready=False,  # NOT live ready
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "BLOCKED"
    assert "not marked live-ready" in res.message


def test_adversarial_unresolved_packet_questions_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-08: Unresolved screening questions in the packet halt prefill."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
    )

    company = CompanyModel(normalized_name="gamma corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Tech Lead", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/gamma/jobs/20",
    )
    db_session.add(source)

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        packet_hash="hash_unresolved",
        is_live_ready=True,
        unresolved_questions_json=["Do you require H1B transfer?"],
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "BLOCKED"
    assert "unresolved consequential questions" in res.message


def test_adversarial_resume_hash_mismatch_blocked(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
    tmp_path: Path,
) -> None:
    """Verify J15-04: Resume artifact disk hash mismatch fails closed."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=False,
    )

    # Write file to disk
    resume_file = tmp_path / "resume.pdf"
    resume_file.write_bytes(b"actual resume bytes on disk")
    actual_sha = hashlib.sha256(b"actual resume bytes on disk").hexdigest()

    company = CompanyModel(normalized_name="delta corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Director", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/delta/jobs/30",
    )
    db_session.add(source)
    db_session.flush()

    # Artifact recorded with different/tampered hash
    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri=str(resume_file),
        sha256="expected_different_tampered_hash_12345",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="packet_hash_delta",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "BLOCKED"
    assert actual_sha != resume_art.sha256
    assert "integrity verification failed" in res.message


def test_adversarial_inspect_form_failure_prevents_prefill(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
    tmp_path: Path,
) -> None:
    """Verify J15-01: If form inspection finds no form, prefill is halted."""
    evaluator = PolicyEvaluator(policy_config)
    # Runner inspection reports no form
    failing_inspection = FormInspectionResult(
        url="https://boards.greenhouse.io/broken/jobs/40",
        title="Error 404 Not Found",
        fields=[],
        form_found=False,
    )
    runner = MockBrowserRunner(custom_inspection=failing_inspection)
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=True,
    )

    company = CompanyModel(normalized_name="broken corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Dev", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/broken/jobs/40",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri="/mock/resume.pdf",
        sha256="mock_sha",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="pkt_broken",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "BLOCKED"
    assert "Form inspection failed: no form found" in res.message
    # prefill was never called
    assert len(runner.prefilled_calls) == 0


def test_adversarial_eeo_demographics_left_unfilled(
    candidate_profile: CandidateProfileConfig,
) -> None:
    """Verify J15-01 & J15-02: Demographic and self-ID fields are classified as EEO_MANUAL."""
    eeo_fields = [
        FormField(name="race_ethnicity", selector="#race", label="Please specify your race/ethnicity"),
        FormField(name="gender", selector="#gender", label="What is your gender?"),
        FormField(name="veteran_status", selector="#vet", label="Voluntary self-identification of veteran status"),
        FormField(name="disability", selector="#disability", label="Voluntary self-identification of disability"),
        FormField(name="pronouns", selector="#pronouns", label="Preferred pronouns"),
    ]

    for f in eeo_fields:
        classification, canonical_key, mapped_val, source_ref = classify_field(
            field=f,
            candidate=candidate_profile,
        )
        assert classification == FieldClassification.EEO_MANUAL
        assert mapped_val is None  # NEVER auto-filled


def test_adversarial_unknown_required_field_halts_prefill(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-08: Unknown required field triggers hard stop before prefill."""
    evaluator = PolicyEvaluator(policy_config)
    custom_fields = [
        FormField(name="first_name", selector="#first_name", required=True, label="First Name"),
        FormField(name="email", selector="#email", field_type="email", required=True, label="Email"),
        FormField(
            name="strange_unmapped_required_code",
            selector="#custom_code",
            required=True,  # Required but completely unknown!
            label="Internal requisition tracking pin",
        ),
    ]
    runner = MockBrowserRunner(custom_fields=custom_fields)
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=True,
    )

    company = CompanyModel(normalized_name="strict corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Engineer", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/strict/jobs/50",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri="/mock/resume.pdf",
        sha256="mock_sha",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="pkt_strict",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "REVIEW_REQUIRED"
    assert "manual barriers requiring candidate action" in res.message
    assert any("unknown_required_field" in b for b in res.barriers)

    # Prefill was halted before write
    assert len(runner.prefilled_calls) == 0

    # Manual barrier review task created
    task = db_session.scalar(
        select(TaskModel).where(
            TaskModel.job_id == job.id, TaskModel.task_type == "MANUAL_BARRIER_REVIEW"
        )
    )
    assert task is not None
    assert task.status == "pending"


def test_adversarial_auth_barrier_halts_prefill(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-02 & J15-08: Captcha or login field halts prefill."""
    evaluator = PolicyEvaluator(policy_config)
    custom_fields = [
        FormField(name="first_name", selector="#first_name", required=True, label="First Name"),
        FormField(name="g-recaptcha-response", selector="#captcha", required=True, label="reCAPTCHA"),
    ]
    runner = MockBrowserRunner(custom_fields=custom_fields)
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=True,
    )

    company = CompanyModel(normalized_name="captcha corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Engineer", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/captcha/jobs/60",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri="/mock/resume.pdf",
        sha256="mock_sha",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="pkt_captcha",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id)
    assert res.status == "REVIEW_REQUIRED"
    assert any("auth_barrier" in b for b in res.barriers)
    assert len(runner.prefilled_calls) == 0


def test_adversarial_mock_runner_cannot_create_real_submitted(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
    tmp_path: Path,
) -> None:
    """Verify J15-10: In live mode (allow_simulation=False), mock runner cannot satisfy SUBMITTED."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner(interactive_submitted=True)
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=False,  # Live execution mode
    )

    resume_file = tmp_path / "resume.pdf"
    resume_file.write_bytes(b"live resume bytes")
    resume_sha = hashlib.sha256(b"live resume bytes").hexdigest()

    company = CompanyModel(normalized_name="live corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Senior SWE", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/live/jobs/70",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri=str(resume_file),
        sha256=resume_sha,
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="pkt_live",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id, auto_confirm=True)
    # MUST NOT be SUBMITTED
    assert res.status == "SUBMISSION_UNCONFIRMED"
    assert "external confirmation evidence was missing" in res.message

    app = db_session.scalar(select(ApplicationModel).where(ApplicationModel.job_id == job.id))
    assert app is not None
    assert app.status == "SUBMISSION_UNCONFIRMED"


def test_adversarial_generic_receipt_text_cannot_satisfy_confirmation() -> None:
    """Verify J15-09: Generic local strings do not qualify as external confirmation."""
    session_res = BrowserSessionResult(
        url="https://boards.greenhouse.io/jobs/1",
        submitted=True,
        is_mock=False,
    )
    generic_strings = [
        "Application submitted via assisted browser",
        "Confirmed manual submission via native portal",
        "Manual native submission confirmed",
        "Application prefilled",
    ]
    for gen in generic_strings:
        valid, msg, ev = is_valid_external_confirmation(
            session_res=session_res,
            auto_confirm=True,
            receipt_text=gen,
            allow_simulation=False,
        )
        assert valid is False
        assert "No verifiable external receipt" in msg


def test_adversarial_pre_submit_review_manifest_generated(
    db_session: Session,
    candidate_profile: CandidateProfileConfig,
    policy_config: PolicyRegistryConfig,
) -> None:
    """Verify J15-03: Pre-submit review manifest is generated, accurate, and persisted as artifact."""
    evaluator = PolicyEvaluator(policy_config)
    runner = MockBrowserRunner()
    engine = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        browser_runner=runner,
        candidate_profile=candidate_profile,
        allow_simulation=True,
    )

    company = CompanyModel(normalized_name="manifest corp")
    db_session.add(company)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="Architect", status="shortlisted")
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/manifest/jobs/80",
    )
    db_session.add(source)
    db_session.flush()

    resume_art = ArtifactModel(
        type="resume_pdf",
        storage_uri="/mock/resume.pdf",
        sha256="manifest_resume_sha",
    )
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id,
        candidate_profile_version=1,
        resume_artifact_id=resume_art.id,
        packet_hash="manifest_packet_hash_123",
        is_live_ready=True,
    )
    db_session.add(packet)
    db_session.commit()

    res = engine.execute(job_id=job.id, packet_id=packet.id, auto_confirm=False)
    assert res.review_manifest is not None
    manifest = res.review_manifest
    assert manifest.job_id == str(job.id)
    assert manifest.packet_id == str(packet.id)
    assert manifest.packet_hash == "manifest_packet_hash_123"
    assert manifest.resume_artifact_sha256 == "manifest_resume_sha"
    assert len(manifest.discovered_fields) > 0
    assert len(manifest.provenance_records) > 0
    assert manifest.form_fingerprint != ""

    # Manifest is saved to ArtifactModel
    manifest_art = db_session.scalar(
        select(ArtifactModel).where(ArtifactModel.type == "assisted_review_manifest")
    )
    assert manifest_art is not None
    assert manifest_art.metadata_json["job_id"] == str(job.id)


def test_adversarial_form_fingerprint_deterministic() -> None:
    """Verify J15-01: Form fingerprint is deterministic and detects field structure changes."""
    fields1 = [
        FormField(name="email", selector="#email", field_type="email", required=True),
        FormField(name="first_name", selector="#fname", required=True),
    ]
    fields2 = [
        FormField(name="first_name", selector="#fname", required=True),
        FormField(name="email", selector="#email", field_type="email", required=True),
    ]
    # Order independence in input
    fp1 = compute_form_fingerprint(fields1, "https://example.com/apply")
    fp2 = compute_form_fingerprint(fields2, "https://example.com/apply")
    assert fp1 == fp2

    # Modified field requirement changes fingerprint
    fields3 = [
        FormField(name="first_name", selector="#fname", required=False),
        FormField(name="email", selector="#email", field_type="email", required=True),
    ]
    fp3 = compute_form_fingerprint(fields3, "https://example.com/apply")
    assert fp1 != fp3

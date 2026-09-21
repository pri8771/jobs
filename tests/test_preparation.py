"""Tests for application preparation: resume variant selection, cover letters, and packet building."""

from __future__ import annotations

import datetime
import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.models import MockModelGateway
from jobs_automation.core import CandidateProfileConfig, ConfigLoader
from jobs_automation.db.models import (
    ApplicationPacketModel,
    ArtifactModel,
    CompanyModel,
    JobModel,
    ResumeVariantModel,
    TaskModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder
from jobs_automation.preparation.tailoring import (
    CoverLetterDrafter,
    ResumeVariantSelector,
    ScreeningQuestionAnsweringService,
)
from jobs_automation.storage.artifact_store import ArtifactStore


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def candidate_profile(tmp_path: Path) -> CandidateProfileConfig:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile("config/candidate_profile.example.yaml")

    # Set up valid test resume sources for all variant keys
    resume_file = tmp_path / "test_resume.md"
    resume_file.write_text("# Test Resume\nSkills: Python, Enterprise Systems\n", encoding="utf-8")
    profile.resume.base_resume_paths = [str(resume_file)]
    profile.resume.resume_sources = {
        "resume_enterprise_automation": str(resume_file),
        "resume_ai_software_engineer": str(resume_file),
        "resume_sap_btp": str(resume_file),
        "resume_mobile_ios": str(resume_file),
        "resume_technical_product": str(resume_file),
        "enterprise_automation_solutions_architect": str(resume_file),
    }
    return profile


def test_resume_variant_selection() -> None:
    job_sap = JobModel(normalized_title="SAP BTP Integration Architect")
    assert ResumeVariantSelector.select_variant(job_sap) == "resume_sap_btp"

    job_ios = JobModel(normalized_title="Senior iOS Mobile Lead")
    assert ResumeVariantSelector.select_variant(job_ios) == "resume_mobile_ios"

    job_swe = JobModel(normalized_title="Senior Python / AI Automation Engineer")
    assert ResumeVariantSelector.select_variant(job_swe) == "resume_ai_software_engineer"

    job_auto = JobModel(normalized_title="Enterprise Solutions Architect")
    assert ResumeVariantSelector.select_variant(job_auto) == "resume_enterprise_automation"


def test_cover_letter_drafting(candidate_profile: CandidateProfileConfig) -> None:
    gateway = MockModelGateway()
    drafter = CoverLetterDrafter(gateway)
    co = CompanyModel(normalized_name="Accenture")
    job = JobModel(normalized_title="Solutions Architect", company=co)

    letter = drafter.draft(job, candidate_profile)
    assert candidate_profile.identity.full_name in letter


def test_screening_question_resolution_and_unresolved_flags(
    candidate_profile: CandidateProfileConfig,
) -> None:
    gateway = MockModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = [
        "What is your race and ethnic background?",  # Demographic -> MUST NOT GUESS
        "Are you willing to relocate to Seattle?",  # Unconfirmed relocation preference -> MUST NOT GUESS
        "What is your required salary?",  # Profile target compensation
    ]

    answers, provenance, unresolved = service.resolve_questions(questions, candidate_profile)

    # Salary resolved from profile min target
    assert "What is your required salary?" in answers
    assert "$150,000 USD" in answers["What is your required salary?"]
    assert "target.target_compensation_usd_min" in provenance["What is your required salary?"]["sources"]

    # Demographic & Relocation MUST be unresolved
    assert len(unresolved) == 2
    assert any("Demographic/EEO" in u for u in unresolved)
    assert any("Relocation question" in u for u in unresolved)


def test_demographic_eeo_questions_always_unresolved(
    candidate_profile: CandidateProfileConfig,
) -> None:
    """Verify J14-09: demographic/EEO questions are always unresolved even if profile has values."""
    candidate_profile.demographic_answers.values = {
        "gender": "Male",
        "race_ethnicity": "Asian",
        "veteran_status": "No",
        "disability_status": "No",
    }
    gateway = MockModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    eeo_questions = [
        "What is your gender?",
        "Please select your race or ethnicity:",
        "Are you Hispanic or Latino?",
        "What is your veteran status?",
        "Do you have a disability?",
    ]

    answers, provenance, unresolved = service.resolve_questions(eeo_questions, candidate_profile)
    assert len(answers) == 0
    assert len(unresolved) == len(eeo_questions)
    for u in unresolved:
        assert "Demographic/EEO" in u


def test_application_packet_builder_creates_reproducible_packet(
    db_session: Session, candidate_profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    now = datetime.datetime.now(datetime.UTC)
    co = CompanyModel(normalized_name="Cresta AI", domain="cresta.ai")
    db_session.add(co)
    db_session.flush()

    job = JobModel(
        company_id=co.id,
        normalized_title="AI Automation Engineer",
        status="shortlisted",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(job)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, candidate_profile, gateway, artifact_store=store)

    questions = ["What is your required salary?"]
    packet, result = builder.build_packet(job, questions=questions)

    assert result.has_unresolved_questions is False
    assert result.resume_variant == "resume_ai_software_engineer"
    assert len(result.packet_hash) == 64
    assert job.status == "packet_prepared"

    # Verify database persistence
    db_packet = db_session.execute(
        select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet.id)
    ).scalar_one()
    assert db_packet.candidate_profile_version == candidate_profile.version
    assert db_packet.resume_artifact_id is not None
    assert db_packet.cover_letter_artifact_id is not None
    assert db_packet.resume_variant_id is not None
    assert "What is your required salary?" in db_packet.answer_provenance_json

    # Verify ResumeVariantModel persistence and linkage (J14-03, J14-04, R14-02)
    db_variant = db_session.execute(
        select(ResumeVariantModel).where(ResumeVariantModel.id == db_packet.resume_variant_id)
    ).scalar_one()
    assert db_variant.name == "resume_ai_software_engineer"
    assert db_variant.resume_family == "Senior Software Engineer / AI Automation Engineer"
    assert len(db_variant.content_hash) == 64

    # Verify artifacts actually exist on disk and hash-match (J14-05)
    resume_artifact = db_session.execute(
        select(ArtifactModel).where(ArtifactModel.id == db_packet.resume_artifact_id)
    ).scalar_one()
    assert store.verify(resume_artifact.storage_uri, resume_artifact.sha256) is True

    cl_artifact = db_session.execute(
        select(ArtifactModel).where(ArtifactModel.id == db_packet.cover_letter_artifact_id)
    ).scalar_one()
    assert store.verify(cl_artifact.storage_uri, cl_artifact.sha256) is True

    # Verify machine-readable manifest (J14-10, R14-02, R14-03)
    manifest_bytes = store.read(result.manifest_artifact_uri)
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    assert manifest["packet_id"] == str(packet.id)
    assert manifest["resume_variant_name"] == "resume_ai_software_engineer"
    assert manifest["resume_family"] == "Senior Software Engineer / AI Automation Engineer"
    assert manifest["resume_artifact_sha256"] == resume_artifact.sha256
    assert manifest["generation_origin"] == "mock"
    assert manifest["is_live_ready"] is False


def test_packet_builder_fails_closed_when_resume_source_missing(
    db_session: Session, candidate_profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    """Verify J14-01: building a packet fails closed if resume source cannot be resolved."""
    candidate_profile.resume.base_resume_paths = []
    candidate_profile.resume.resume_sources = {}

    co = CompanyModel(normalized_name="Acme Corp")
    db_session.add(co)
    db_session.flush()

    job = JobModel(
        company_id=co.id,
        normalized_title="Lead Architect",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, candidate_profile, gateway, artifact_store=store)

    with pytest.raises(FileNotFoundError, match="Selected resume variant .* cannot be resolved"):
        builder.build_packet(job)


def test_packet_builder_flags_unresolved_to_review_queue(
    db_session: Session, candidate_profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    now = datetime.datetime.now(datetime.UTC)
    co = CompanyModel(normalized_name="DefenseCorp")
    db_session.add(co)
    db_session.flush()

    job = JobModel(
        company_id=co.id,
        normalized_title="Systems Architect",
        status="shortlisted",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(job)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, candidate_profile, gateway, artifact_store=store)

    questions = ["What is your gender?", "Are you willing to relocate?"]
    packet, result = builder.build_packet(job, questions=questions)

    assert result.has_unresolved_questions is True
    assert len(result.unresolved_questions) == 2
    assert job.status == "packet_prepared_review_needed"

    # Verify review task created in task table
    tasks = (
        db_session.execute(select(TaskModel).where(TaskModel.task_type == "NEEDS_REVIEW"))
        .scalars()
        .all()
    )
    assert len(tasks) == 1
    assert "unresolved question" in tasks[0].payload_json["reason"]

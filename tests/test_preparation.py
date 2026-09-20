"""Tests for application preparation: resume variant selection, cover letters, and packet building."""

from __future__ import annotations

import datetime
from collections.abc import Generator

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
    TaskModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder
from jobs_automation.preparation.tailoring import (
    CoverLetterDrafter,
    ResumeVariantSelector,
    ScreeningQuestionAnsweringService,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def candidate_profile() -> CandidateProfileConfig:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile()
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
    assert "Priyansh Chordia" in letter
    assert "Viatris" in letter
    assert "Carnegie Mellon" in letter


def test_screening_question_resolution_and_unresolved_flags(
    candidate_profile: CandidateProfileConfig,
) -> None:
    gateway = MockModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = [
        "Do you have experience with Python?",
        "What is your race and ethnic background?",  # Demographic -> MUST NOT GUESS
        "Are you willing to relocate to Seattle?",  # Unconfirmed relocation preference -> MUST NOT GUESS
        "What is your required salary?",  # Profile target compensation
    ]

    answers, unresolved = service.resolve_questions(questions, candidate_profile)

    # Python experience resolved
    assert "Do you have experience with Python?" in answers

    # Salary resolved from profile min target
    assert "What is your required salary?" in answers
    assert "$150,000 USD" in answers["What is your required salary?"]

    # Demographic & Relocation MUST be unresolved
    assert len(unresolved) == 2
    assert any("Demographic question" in u for u in unresolved)
    assert any("Relocation question" in u for u in unresolved)


def test_application_packet_builder_creates_reproducible_packet(
    db_session: Session, candidate_profile: CandidateProfileConfig
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

    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, candidate_profile, gateway)

    questions = ["Do you have experience with Python?"]
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

    # Verify artifacts
    artifacts = db_session.execute(select(ArtifactModel)).scalars().all()
    assert len(artifacts) == 2


def test_packet_builder_flags_unresolved_to_review_queue(
    db_session: Session, candidate_profile: CandidateProfileConfig
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

    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, candidate_profile, gateway)

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

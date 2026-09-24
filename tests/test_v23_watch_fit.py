"""Tests for V23-TW-05: Watch fit evaluation and suppression."""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    CompanyModel,
    JobModel,
    TargetCompanyModel,
    TargetCompanyObservationModel,
    TaskModel,
)
from jobs_automation.db.base import Base
from jobs_automation.intelligence.watch_fit import WatchFitEvaluator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)



def test_fit_evaluator_suppresses_existing_application(db_session: Session) -> None:
    company = CompanyModel(normalized_name="AppliedCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="AppliedCo",
        target_role_families=["ai_software_engineer"],
        watch_status="ACTIVE",
    )
    db_session.add(target)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="AI Engineer", status="active")
    db_session.add(job)
    db_session.flush()

    resume_art = ArtifactModel(type="resume", storage_uri="/r.md", sha256="h1")
    db_session.add(resume_art)
    db_session.flush()

    packet = ApplicationPacketModel(
        job_id=job.id, candidate_profile_version=1,
        resume_artifact_id=resume_art.id, packet_hash="ph1"
    )
    db_session.add(packet)
    db_session.flush()

    app = ApplicationModel(job_id=job.id, packet_id=packet.id, status="SUBMITTED")
    db_session.add(app)
    db_session.commit()

    obs = TargetCompanyObservationModel(
        target_company_id=target.id,
        observation_type="NEW_ROLE",
        source_type="public_api",
        source_reference="https://url",
        observed_at=target.created_at,
        confidence=1.0,
        normalized_payload={"title": "AI Engineer"},
        dedupe_key="key1",
        job_id=job.id,
    )
    db_session.add(obs)
    db_session.commit()

    evaluator = WatchFitEvaluator(db_session)
    fit = evaluator.evaluate_new_role(obs, target, job)

    assert fit["decision"] == "SUPPRESSED"
    assert obs.status == "SUPPRESSED"


def test_fit_evaluator_creates_task_for_shortlisted_role(db_session: Session) -> None:
    company = CompanyModel(normalized_name="ShortlistCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="ShortlistCo",
        target_role_families=["ai_software_engineer"],
        watch_status="ACTIVE",
    )
    db_session.add(target)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="AI Software Engineer", status="discovered")
    db_session.add(job)
    db_session.flush()

    obs = TargetCompanyObservationModel(
        target_company_id=target.id,
        observation_type="NEW_ROLE",
        source_type="public_api",
        source_reference="https://url",
        observed_at=target.created_at,
        confidence=1.0,
        normalized_payload={"title": "AI Software Engineer"},
        dedupe_key="key2",
        job_id=job.id,
    )
    db_session.add(obs)
    db_session.commit()

    evaluator = WatchFitEvaluator(db_session)
    fit = evaluator.evaluate_new_role(obs, target, job)

    assert fit["decision"] == "SHORTLIST"

    # Task should be created
    task = db_session.scalars(
        select(TaskModel).where(
            TaskModel.job_id == job.id,
            TaskModel.task_type == "TARGET_COMPANY_NEW_ROLE",
        )
    ).first()
    assert task is not None
    assert task.status == "pending"


def test_fit_evaluator_no_task_if_paused(db_session: Session) -> None:
    company = CompanyModel(normalized_name="PausedTargetCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="PausedTargetCo",
        target_role_families=["ai_software_engineer"],
        watch_status="PAUSED",
    )
    db_session.add(target)
    db_session.flush()

    job = JobModel(company_id=company.id, normalized_title="AI Software Engineer", status="discovered")
    db_session.add(job)
    db_session.flush()

    obs = TargetCompanyObservationModel(
        target_company_id=target.id,
        observation_type="NEW_ROLE",
        source_type="public_api",
        source_reference="https://url",
        observed_at=target.created_at,
        confidence=1.0,
        normalized_payload={"title": "AI Software Engineer"},
        dedupe_key="key3",
        job_id=job.id,
    )
    db_session.add(obs)
    db_session.commit()

    evaluator = WatchFitEvaluator(db_session)
    fit = evaluator.evaluate_new_role(obs, target, job)

    # Shortlisted decision, but NO task created because target is PAUSED
    task = db_session.scalars(
        select(TaskModel).where(
            TaskModel.job_id == job.id,
            TaskModel.task_type == "TARGET_COMPANY_NEW_ROLE",
        )
    ).first()
    assert task is None

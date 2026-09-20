"""Tests for job evaluation: hard filtering, semantic scoring, and evaluation engine."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.core import CandidateProfileConfig, ConfigLoader, JobSearchConfig
from jobs_automation.db.models import CompanyModel, JobEvaluationModel, JobModel
from jobs_automation.db.session import init_db
from jobs_automation.evaluation.engine import JobEvaluationEngine
from jobs_automation.evaluation.filters import FilterDecisionStatus, HardFilterService
from jobs_automation.evaluation.scorer import SemanticScorer


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def sample_configs() -> tuple[CandidateProfileConfig, JobSearchConfig]:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile("config/candidate_profile.example.yaml")
    search, _ = loader.load_job_search("config/job_search.example.yaml")
    return profile, search


def test_hard_filter_passes_valid_job(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    service = HardFilterService(profile, search)

    job = JobModel(
        normalized_title="Enterprise Automation Architect",
        location_text="Pittsburgh, PA",
        remote_type="hybrid",
        compensation_min=160000,
        compensation_max=190000,
        description_text="Lead enterprise automation and integrations across systems.",
    )
    res = service.evaluate(job)
    assert res.passed is True
    assert res.status == FilterDecisionStatus.PASS


def test_hard_filter_rejects_insufficient_compensation(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    service = HardFilterService(profile, search)

    job = JobModel(
        normalized_title="Systems Engineer",
        location_text="Remote",
        remote_type="remote",
        compensation_min=90000,
        compensation_max=120000,  # Below $150k min
        description_text="Maintenance and support.",
    )
    res = service.evaluate(job)
    assert res.passed is False
    assert res.status == FilterDecisionStatus.REJECT
    assert any("insufficient_compensation" in r for r in res.reason_codes)


def test_hard_filter_rejects_clearance(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    service = HardFilterService(profile, search)

    job = JobModel(
        normalized_title="Solutions Architect - Defense",
        location_text="Remote",
        remote_type="remote",
        compensation_min=170000,
        compensation_max=210000,
        description_text="Candidate must possess active Top Secret / TS/SCI security clearance.",
    )
    res = service.evaluate(job)
    assert res.passed is False
    assert res.status == FilterDecisionStatus.REJECT
    assert any("requires_security_clearance" in r for r in res.reason_codes)


def test_hard_filter_flags_unverified_citizenship_req(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    # Profile has authorized_to_work_in_us = None
    service = HardFilterService(profile, search)

    job = JobModel(
        normalized_title="Cloud Infrastructure Architect",
        location_text="Remote",
        remote_type="remote",
        compensation_min=160000,
        compensation_max=195000,
        description_text="U.S. Citizenship Required due to government contracts.",
    )
    res = service.evaluate(job)
    assert res.passed is False
    assert res.status == FilterDecisionStatus.MUST_REVIEW


def test_semantic_scorer_shortlists_high_fit(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    scorer = SemanticScorer(profile, search)

    job = JobModel(
        normalized_title="SAP BTP Solutions Architect",
        location_text="Pittsburgh, PA",
        remote_type="hybrid",
        compensation_min=170000,
        compensation_max=205000,
        description_text="Architect SAP BTP integrations, ERP workflows, Python automation, and enterprise systems.",
    )
    score_res = scorer.score(job)
    assert score_res.composite_score >= 70.0
    assert score_res.decision == "SHORTLIST"
    assert score_res.matched_role_family is not None
    assert any("strong_title_match" in r for r in score_res.reason_codes)


def test_semantic_scorer_rejects_unrelated_role(
    sample_configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = sample_configs
    scorer = SemanticScorer(profile, search)

    job = JobModel(
        normalized_title="Junior Front Desk Receptionist",
        location_text="New York, NY",
        remote_type="on_site",
        compensation_min=45000,
        compensation_max=55000,
        description_text="Answer phone calls and manage office greeting.",
    )
    score_res = scorer.score(job)
    assert score_res.composite_score < 50.0
    assert score_res.decision == "REJECT"


def test_evaluation_engine_batch_processing(
    db_session: Session, sample_configs: tuple[CandidateProfileConfig, JobSearchConfig]
) -> None:
    profile, search = sample_configs
    now = datetime.datetime.now(datetime.UTC)

    co = CompanyModel(
        normalized_name="Viatris Global", domain="viatris.com", aliases_json=["Viatris"]
    )
    db_session.add(co)
    db_session.flush()

    job_good = JobModel(
        company_id=co.id,
        normalized_title="Enterprise Automation Architect",
        location_text="Pittsburgh, PA",
        remote_type="hybrid",
        compensation_min=165000,
        compensation_max=195000,
        description_text="SAP BTP integrations, Python automation, enterprise systems.",
        status="discovered",
        first_seen_at=now,
        last_seen_at=now,
    )
    job_bad = JobModel(
        company_id=co.id,
        normalized_title="Junior Support Technician",
        location_text="Miami, FL",
        remote_type="on_site",
        compensation_min=40000,
        compensation_max=50000,
        description_text="Password resets and desk support.",
        status="discovered",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add_all([job_good, job_bad])
    db_session.commit()

    engine = JobEvaluationEngine(db_session, profile, search)
    summary = engine.run_evaluation_batch()

    assert summary.total_evaluated == 2
    assert summary.shortlisted == 1
    assert summary.rejected == 1

    # Verify Job statuses updated
    db_session.refresh(job_good)
    db_session.refresh(job_bad)
    assert job_good.status == "shortlisted"
    assert job_bad.status == "rejected"

    # Verify JobEvaluationModel records
    evals = db_session.execute(select(JobEvaluationModel)).scalars().all()
    assert len(evals) == 2

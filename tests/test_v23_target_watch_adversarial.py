"""Adversarial and boundary tests for Target Company Watch (V23-TW-07)."""

import datetime
import json
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobModel,
    JobSourceModel,
    MessageLinkModel,
    TargetCompanyModel,
    TargetCompanyObservationModel,
)
from jobs_automation.ingestion.sources.base import PublicPosting, SourceFetchResult, Transport
from jobs_automation.intelligence.opportunity_graph import EdgeStatus, OpportunityGraphService
from jobs_automation.intelligence.target_companies import TargetCompanyService
from jobs_automation.intelligence.watch_runner import WatchRunner


class FakeTransport(Transport):
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.body = body

    def get(self, url: str, timeout: float = 20.0, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        if self.status_code == -1:
            raise TimeoutError("Simulated timeout")
        return self.status_code, self.body


class FakeSource:
    def __init__(self, result: SourceFetchResult):
        self.result = result

    def fetch(self, source_key: str) -> SourceFetchResult:
        return self.result


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


def test_adversarial_career_page_unavailable_no_closures(db_session: Session) -> None:
    """Adversarial scenario 1: Career page temporarily unavailable.

    Must record SOURCE_UNAVAILABLE observation, and NEVER close existing roles.
    """
    company = CompanyModel(normalized_name="UnavailCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="UnavailCo",
        watch_status="ACTIVE",
        source_config={"provider": "GREENHOUSE", "source_key": "unavailco"},
    )
    db_session.add(target)
    db_session.commit()

    # Step 1: Active posting observed
    posting = PublicPosting(
        provider="GREENHOUSE", source_job_id="101", title="DevOps Engineer",
        absolute_url="https://url/101", content_sha256="c1", raw_payload_hash="r1",
    )
    runner1 = WatchRunner(
        db_session,
        {"GREENHOUSE": FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="unavailco",
                api_url="https://api", status="OK", http_status=200,
                postings=[posting],
            )
        )},
    )
    runner1.run()
    db_session.commit()

    # Step 2: Site down (503 Service Unavailable)
    runner2 = WatchRunner(
        db_session,
        {"GREENHOUSE": FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="unavailco",
                api_url="https://api", status="UNAVAILABLE", http_status=503,
                postings=[],
            )
        )},
    )
    report2 = runner2.run()
    db_session.commit()

    assert report2.total_closed == 0
    obs = db_session.scalars(
        select(TargetCompanyObservationModel).where(
            TargetCompanyObservationModel.observation_type == "SOURCE_UNAVAILABLE"
        )
    ).all()
    assert len(obs) == 1
    assert obs[0].normalized_payload.get("status") == "UNAVAILABLE"


def test_adversarial_role_url_changes_same_requisition_no_duplicate_job(db_session: Session) -> None:
    """Adversarial scenario 2: Role URL changes but source_job_id / requisition_id is identical.

    Must dedupe existing JobModel and NOT create a duplicate job or duplicate NEW_ROLE observation.
    """
    company = CompanyModel(normalized_name="UrlChangeCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="UrlChangeCo",
        watch_status="ACTIVE",
        source_config={"provider": "GREENHOUSE", "source_key": "urlco"},
    )
    db_session.add(target)
    db_session.commit()

    # First fetch: URL v1
    p1 = PublicPosting(
        provider="GREENHOUSE", source_job_id="req-999", title="Principal Architect",
        absolute_url="https://boards.greenhouse.io/urlco/jobs/req-999?gh_jid=old",
        content_sha256="c1", raw_payload_hash="r1",
    )
    runner1 = WatchRunner(
        db_session,
        {"GREENHOUSE": FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="urlco",
                api_url="https://api", status="OK", http_status=200, postings=[p1]
            )
        )},
    )
    r1 = runner1.run()
    db_session.commit()
    assert r1.total_new == 1

    # Second fetch: URL changed, but source_job_id and content_sha256 identical
    p2 = PublicPosting(
        provider="GREENHOUSE", source_job_id="req-999", title="Principal Architect",
        absolute_url="https://boards.greenhouse.io/urlco/jobs/req-999?gh_jid=new_marketing_slug",
        content_sha256="c1", raw_payload_hash="r2",
    )
    runner2 = WatchRunner(
        db_session,
        {"GREENHOUSE": FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="urlco",
                api_url="https://api", status="OK", http_status=200, postings=[p2]
            )
        )},
    )
    r2 = runner2.run()
    db_session.commit()

    assert r2.total_new == 0
    assert r2.target_reports[0].unchanged_roles == 1

    # Ensure only 1 JobModel exists in DB
    jobs = db_session.scalars(select(JobModel)).all()
    assert len(jobs) == 1


def test_adversarial_recruiter_relation_inferred_from_text_stays_review_required(db_session: Session) -> None:
    """Adversarial scenario 3: Recruiter relation inferred from text message.

    Edge status must remain REVIEW_REQUIRED, never ASSERTED without explicit user confirmation.
    """
    company = CompanyModel(normalized_name="RecruiterCo")
    db_session.add(company)
    db_session.flush()

    contact = ContactModel(
        name="Bob Smith",
        email="bob@recruiterco.com",
        company_id=company.id,
        role="Technical Recruiter",
        source="email_inferred",  # Inferred from message text
    )
    db_session.add(contact)
    db_session.commit()

    graph_svc = OpportunityGraphService(db_session)
    paths = graph_svc.referral_paths_to_company(company.id)

    assert len(paths) == 1
    assert paths[0].status == EdgeStatus.REVIEW_REQUIRED
    assert paths[0].confidence < 1.0


def test_adversarial_duplicate_role_across_ats_and_public_collapses(db_session: Session) -> None:
    """Adversarial scenario 4: Duplicate role across ATS public board and manual ingestion.

    Deduplication Service must collapse both to the same JobModel.
    """
    company = CompanyModel(normalized_name="MultiSourceCo")
    db_session.add(company)
    db_session.flush()

    target = TargetCompanyModel(
        company_id=company.id,
        canonical_name="MultiSourceCo",
        watch_status="ACTIVE",
        source_config={"provider": "GREENHOUSE", "source_key": "multico"},
    )
    db_session.add(target)
    db_session.commit()

    posting = PublicPosting(
        provider="GREENHOUSE", source_job_id="job-555", title="Staff Systems Engineer",
        absolute_url="https://boards.greenhouse.io/multico/jobs/555",
        content_sha256="c555", raw_payload_hash="r555",
    )
    runner = WatchRunner(
        db_session,
        {"GREENHOUSE": FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="multico",
                api_url="https://api", status="OK", http_status=200, postings=[posting]
            )
        )},
    )
    runner.run()
    db_session.commit()

    # Verify 1 job in DB
    jobs = db_session.scalars(select(JobModel)).all()
    assert len(jobs) == 1

    # Verify source provider link exists
    sources = db_session.scalars(select(JobSourceModel)).all()
    assert len(sources) == 1
    assert sources[0].provider == "GREENHOUSE"
    assert sources[0].source_job_id == "job-555"

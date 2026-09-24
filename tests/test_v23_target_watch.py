"""Tests for V23-TW-03 (TargetCompanyService) and V23-TW-04 (WatchRunner)."""

from __future__ import annotations

import datetime
import json
import uuid

import pytest
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    CompanyModel,
    ContactModel,
    JobModel,
    JobSourceModel,
    MessageLinkModel,
    InboundMessageModel,
    TargetCompanyModel,
    TargetCompanyObservationModel,
    TaskModel,
)
from jobs_automation.db.base import Base
from jobs_automation.ingestion.sources.base import (
    PublicPosting,
    SourceFetchResult,
    Transport,
)
from jobs_automation.ingestion.sources.greenhouse_board import GreenhouseBoardSource
from jobs_automation.intelligence.watch_runner import WatchRunner, WatchRunReport
from sqlalchemy import create_engine, select
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



# ──────────────────────────────── Fake Transport ────────────────────────────────

class FakeTransport(Transport):
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.body = body
        self.call_count = 0

    def get(self, url: str, timeout: float = 20.0, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        self.call_count += 1
        if self.status_code == -1:
            raise TimeoutError("Fake timeout")
        return self.status_code, self.body


class FakeSource:
    """A fake PublicJobSource that returns controlled results."""

    def __init__(self, result: SourceFetchResult):
        self.result = result
        self.fetch_count = 0

    def fetch(self, source_key: str) -> SourceFetchResult:
        self.fetch_count += 1
        return self.result


def make_greenhouse_payload(jobs: list[dict]) -> bytes:
    return json.dumps({"jobs": jobs}).encode("utf-8")


def make_job_dict(
    job_id: str = "123",
    title: str = "Engineer",
    url: str = "https://boards.greenhouse.io/test/jobs/123",
    content: str = "some description",
    location: str = "Remote",
) -> dict:
    return {
        "id": job_id,
        "title": title,
        "absolute_url": url,
        "content": content,
        "location": {"name": location},
    }


# ──────────────────────────────── TW-03 Tests ────────────────────────────────


class TestTargetCompanyService:
    def test_add_creates_paused_target(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)
        target = svc.add(
            canonical_name="Google",
            domain="google.com",
            priority=1,
            reason="FAANG target",
            role_families=["ai_software_engineer"],
            compensation_floor=150000,
            location_constraints={"remote": True},
            source_config={"provider": "GREENHOUSE", "source_key": "google"},
        )
        db_session.commit()

        assert target.watch_status == "PAUSED"
        assert target.canonical_name == "Google"
        assert target.company_id is not None

        # Company should have been created
        company = db_session.get(CompanyModel, target.company_id)
        assert company is not None

    def test_set_status_activates_target(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)
        target = svc.add(
            canonical_name="Meta",
            domain="meta.com",
            priority=2,
            reason="target",
            role_families=[],
            compensation_floor=None,
            location_constraints={},
            source_config={},
        )
        db_session.commit()

        updated = svc.set_status(target.id, "ACTIVE")
        assert updated.watch_status == "ACTIVE"

    def test_list_filters_by_status(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)
        svc.add("Alpha", None, 1, "r", [], None, {}, {})
        t2 = svc.add("Beta", None, 2, "r", [], None, {}, {})
        db_session.commit()
        svc.set_status(t2.id, "ACTIVE")
        db_session.commit()

        all_targets = svc.list()
        assert len(all_targets) == 2

        active_only = svc.list(status="ACTIVE")
        assert len(active_only) == 1
        assert active_only[0].canonical_name == "Beta"

    def test_duplicate_observation_collapses(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)
        target = svc.add("Dupes Inc", None, 1, "r", [], None, {}, {})
        db_session.commit()

        now = datetime.datetime.now(datetime.UTC)
        obs1, created1 = svc.add_observation(
            target_id=target.id,
            type="NEW_ROLE",
            source_type="public_api",
            source_reference="https://example.com/job/1",
            observed_at=now,
            confidence=1.0,
            payload={"title": "Engineer"},
            dedupe_key="GREENHOUSE:123:NEW_ROLE",
        )
        assert created1 is True

        obs2, created2 = svc.add_observation(
            target_id=target.id,
            type="NEW_ROLE",
            source_type="public_api",
            source_reference="https://example.com/job/1",
            observed_at=now,
            confidence=1.0,
            payload={"title": "Engineer"},
            dedupe_key="GREENHOUSE:123:NEW_ROLE",
        )
        assert created2 is False
        assert obs2.id == obs1.id

    def test_observations_filters(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)
        target = svc.add("FilterCo", None, 1, "r", [], None, {}, {})
        db_session.commit()

        now = datetime.datetime.now(datetime.UTC)
        yesterday = now - datetime.timedelta(days=1)

        svc.add_observation(target.id, "NEW_ROLE", "api", "ref1", yesterday, 1.0, {}, "k1")
        svc.add_observation(target.id, "NEW_ROLE", "api", "ref2", now, 1.0, {}, "k2")
        db_session.commit()

        all_obs = svc.observations(target.id)
        assert len(all_obs) == 2

        recent = svc.observations(target.id, since=now - datetime.timedelta(hours=1))
        assert len(recent) == 1

    def test_company_linking_dedupes_by_name(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)

        # Pre-create a company
        existing = CompanyModel(normalized_name="Existing Corp", domain="existing.com")
        db_session.add(existing)
        db_session.commit()

        target = svc.add("Existing Corp", "existing.com", 1, "r", [], None, {}, {})
        db_session.commit()

        # Should link to the existing company
        assert target.company_id == existing.id

    def test_relationship_signal_cites_refs(self, db_session: Session) -> None:
        from jobs_automation.intelligence.target_companies import TargetCompanyService

        svc = TargetCompanyService(db_session)

        # Create company with a contact and an application
        company = CompanyModel(normalized_name="SignalCo", domain="signal.co")
        db_session.add(company)
        db_session.flush()

        contact = ContactModel(
            name="Jane Doe",
            email="jane@signal.co",
            company_id=company.id,
            role="Recruiter",
            source="email_inferred",
        )
        db_session.add(contact)
        db_session.flush()

        job = JobModel(company_id=company.id, normalized_title="Engineer", status="active")
        db_session.add(job)
        db_session.flush()

        source = JobSourceModel(job_id=job.id, provider="greenhouse", canonical_apply_url="https://url")
        db_session.add(source)
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

        target = svc.add("SignalCo", "signal.co", 1, "r", [], None, {}, {})
        db_session.commit()

        signal = svc.relationship_signal(target.id)
        assert len(signal.known_contacts) >= 1
        assert len(signal.prior_applications) >= 1
        assert signal.artifact_type == "relationship_signal"


# ──────────────────────────────── TW-04 Tests ────────────────────────────────


class TestWatchRunner:
    def _create_active_target(
        self,
        session: Session,
        name: str = "WatchCo",
        provider: str = "GREENHOUSE",
        source_key: str = "watchco",
    ) -> TargetCompanyModel:
        company = CompanyModel(normalized_name=name)
        session.add(company)
        session.flush()

        target = TargetCompanyModel(
            company_id=company.id,
            canonical_name=name,
            priority=1,
            watch_status="ACTIVE",
            source_config={"provider": provider, "source_key": source_key},
            target_role_families=["engineer"],
        )
        session.add(target)
        session.flush()
        return target

    def test_new_role_creates_observation(self, db_session: Session) -> None:
        target = self._create_active_target(db_session)
        db_session.commit()

        posting = PublicPosting(
            provider="GREENHOUSE",
            source_job_id="j1",
            title="ML Engineer",
            absolute_url="https://boards.greenhouse.io/watchco/jobs/j1",
            content_sha256="abc123",
            raw_payload_hash="raw1",
        )
        fake_source = FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE",
                source_key="watchco",
                api_url="https://api.greenhouse.io/test",
                status="OK",
                http_status=200,
                postings=[posting],
            )
        )

        runner = WatchRunner(db_session, {"GREENHOUSE": fake_source})
        report = runner.run()

        assert report.total_new == 1
        assert report.total_closed == 0

        obs = db_session.scalars(
            select(TargetCompanyObservationModel).where(
                TargetCompanyObservationModel.target_company_id == target.id
            )
        ).all()
        assert len(obs) == 1
        assert obs[0].observation_type == "NEW_ROLE"

    def test_second_run_identical_creates_no_observations(self, db_session: Session) -> None:
        target = self._create_active_target(db_session)
        db_session.commit()

        posting = PublicPosting(
            provider="GREENHOUSE",
            source_job_id="j2",
            title="Engineer",
            absolute_url="https://url/j2",
            content_sha256="sha1",
            raw_payload_hash="raw1",
        )
        fake_result = SourceFetchResult(
            provider="GREENHOUSE", source_key="watchco",
            api_url="https://api", status="OK", http_status=200,
            postings=[posting],
        )

        runner = WatchRunner(db_session, {"GREENHOUSE": FakeSource(fake_result)})
        r1 = runner.run()
        db_session.commit()
        assert r1.total_new == 1

        # Second run with identical postings
        r2 = runner.run()
        assert r2.total_new == 0
        assert r2.target_reports[0].unchanged_roles == 1

    def test_posting_removed_triggers_role_closed(self, db_session: Session) -> None:
        target = self._create_active_target(db_session)
        db_session.commit()

        posting = PublicPosting(
            provider="GREENHOUSE",
            source_job_id="j3",
            title="Removed Role",
            absolute_url="https://url/j3",
            content_sha256="sha3",
            raw_payload_hash="raw3",
        )

        # First run: job appears
        runner = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="OK", http_status=200,
                    postings=[posting],
                )
            )},
        )
        runner.run()
        db_session.commit()

        # Second run: job gone
        runner2 = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="OK", http_status=200,
                    postings=[],  # Empty!
                )
            )},
        )
        r2 = runner2.run()
        assert r2.total_closed == 1

    def test_fetch_failure_no_closures(self, db_session: Session) -> None:
        target = self._create_active_target(db_session)
        db_session.commit()

        # First: add a known role
        posting = PublicPosting(
            provider="GREENHOUSE", source_job_id="j4", title="Stable",
            absolute_url="https://url/j4", content_sha256="sha4", raw_payload_hash="raw4",
        )
        runner = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="OK", http_status=200,
                    postings=[posting],
                )
            )},
        )
        runner.run()
        db_session.commit()

        # Second run: fetch fails
        runner2 = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="UNAVAILABLE", http_status=500,
                    postings=[],
                )
            )},
        )
        r2 = runner2.run()

        # Must NOT close the role — only record SOURCE_UNAVAILABLE
        assert r2.total_closed == 0
        unavail_obs = db_session.scalars(
            select(TargetCompanyObservationModel).where(
                TargetCompanyObservationModel.observation_type == "SOURCE_UNAVAILABLE"
            )
        ).all()
        assert len(unavail_obs) == 1

    def test_content_changed_triggers_role_changed(self, db_session: Session) -> None:
        target = self._create_active_target(db_session)
        db_session.commit()

        posting_v1 = PublicPosting(
            provider="GREENHOUSE", source_job_id="j5", title="Evolving Role",
            absolute_url="https://url/j5", content_sha256="sha_v1", raw_payload_hash="raw5v1",
        )

        runner = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="OK", http_status=200,
                    postings=[posting_v1],
                )
            )},
        )
        runner.run()
        db_session.commit()

        # Same source_job_id but different content
        posting_v2 = PublicPosting(
            provider="GREENHOUSE", source_job_id="j5", title="Evolving Role",
            absolute_url="https://url/j5", content_sha256="sha_v2", raw_payload_hash="raw5v2",
        )

        runner2 = WatchRunner(
            db_session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="watchco",
                    api_url="https://api", status="OK", http_status=200,
                    postings=[posting_v2],
                )
            )},
        )
        r2 = runner2.run()
        assert r2.total_changed == 1

    def test_paused_target_skipped(self, db_session: Session) -> None:
        company = CompanyModel(normalized_name="PausedCo")
        db_session.add(company)
        db_session.flush()

        target = TargetCompanyModel(
            company_id=company.id,
            canonical_name="PausedCo",
            priority=1,
            watch_status="PAUSED",
            source_config={"provider": "GREENHOUSE", "source_key": "pausedco"},
            target_role_families=[],
        )
        db_session.add(target)
        db_session.commit()

        fake_source = FakeSource(
            SourceFetchResult(
                provider="GREENHOUSE", source_key="pausedco",
                api_url="https://api", status="OK", http_status=200,
                postings=[PublicPosting(
                    provider="GREENHOUSE", source_job_id="x", title="X",
                    absolute_url="https://url/x", content_sha256="s", raw_payload_hash="r",
                )],
            )
        )

        runner = WatchRunner(db_session, {"GREENHOUSE": fake_source})
        report = runner.run()

        assert len(report.target_reports) == 0
        assert fake_source.fetch_count == 0

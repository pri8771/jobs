"""Tests for the analytics service and embedded dashboard server."""

from __future__ import annotations

import datetime
import io
import json
import os
import uuid
from collections.abc import Generator
from typing import Any, cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.dashboard.analytics import FunnelAnalyticsService
from jobs_automation.dashboard.server import DashboardRequestHandler
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    AuditLogModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    JobSourceModel,
    MessageLinkModel,
    ResumeVariantModel,
    TaskModel,
)


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory


@pytest.fixture
def db_session(db_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    with db_session_factory() as session:
        yield session


def test_funnel_analytics_summary(db_session: Session) -> None:
    # Set up sample company & jobs
    company = CompanyModel(
        id=uuid.uuid4(),
        normalized_name="stripe",
    )
    db_session.add(company)
    db_session.flush()

    job1 = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        normalized_title="Staff Software Engineer",
        description_text="Build infrastructure",
        status="ACTIVE",
    )
    job2 = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        normalized_title="Backend Engineer",
        description_text="API platform",
        status="ACTIVE",
    )
    db_session.add_all([job1, job2])
    db_session.flush()

    # Add source models
    src1 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        provider="GMAIL_ALERT",
        source_job_id="ext-1",
        source_url="https://stripe.com/jobs/1",
    )
    src2 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        provider="LINKEDIN",
        source_job_id="ext-2",
        source_url="https://stripe.com/jobs/2",
    )
    db_session.add_all([src1, src2])

    # Add applications in different states
    app1 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        status="SCREENING",
        policy_decision="allowed",
        application_mode="auto",
    )
    app2 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        status="SUBMITTED",
        policy_decision="assisted",
        application_mode="assisted",
    )
    db_session.add_all([app1, app2])

    # Add a pending review task
    review = TaskModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        task_type="NEEDS_REVIEW",
        payload_json={"field": "sponsorship"},
        status="pending",
    )
    db_session.add(review)
    db_session.commit()

    analytics = FunnelAnalyticsService(db_session)
    summary = analytics.get_funnel_summary()

    assert summary["total_jobs_discovered"] == 2
    assert summary["total_submitted"] == 2
    assert summary["total_screening"] == 1
    assert summary["total_interviewing"] == 0
    assert summary["pending_reviews"] == 1
    assert summary["conversion_rates"]["discovery_to_submission_pct"] == 100.0
    assert summary["conversion_rates"]["submission_to_screen_pct"] == 50.0

    sources = analytics.get_source_breakdown()
    assert sources["GMAIL_ALERT"] == 1
    assert sources["LINKEDIN"] == 1

    board = analytics.get_kanban_board()
    assert len(board["SUBMITTED"]) == 1
    assert len(board["SCREENING"]) == 1
    assert board["SUBMITTED"][0]["company"] == "stripe"


class DummyRequestHandler(DashboardRequestHandler):
    """Test harness that dispatches to DashboardRequestHandler without OS sockets."""

    def __init__(
        self,
        method: str,
        path: str,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        session_factory: Any = None,
        client_address: tuple[str, int] = ("127.0.0.1", 12345),
    ) -> None:
        self.command = method
        self.path = path
        self.request_version = "HTTP/1.1"
        self.headers = cast(Any, headers or {})
        self.rfile = io.BytesIO(body)
        self.mock_wfile = io.BytesIO()
        self.wfile = cast(Any, self.mock_wfile)
        self.session_factory = session_factory
        self.client_address = client_address
        self.status_code: int = 200
        self.response_headers: dict[str, str] = {}

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status_code = code

    def send_header(self, keyword: str, value: str) -> None:
        self.response_headers[keyword] = value

    def end_headers(self) -> None:
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self.status_code = code


def test_dashboard_server_endpoints() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    task_id = uuid.uuid4()
    with session_factory() as session:
        comp = CompanyModel(id=uuid.uuid4(), normalized_name="figma")
        session.add(comp)
        session.flush()

        job = JobModel(
            id=uuid.uuid4(),
            company_id=comp.id,
            normalized_title="Platform Lead",
            description_text="Build core platform",
        )
        session.add(job)
        session.flush()

        review = TaskModel(
            id=task_id,
            job_id=job.id,
            task_type="NEEDS_REVIEW",
            payload_json={"question": "Expected range?"},
            status="pending",
            due_at=datetime.datetime.now(datetime.UTC),
        )
        session.add(review)
        session.commit()

    # 1. GET HTML
    h_index = DummyRequestHandler("GET", "/", session_factory=session_factory)
    h_index.do_GET()
    assert h_index.status_code == 200
    html = h_index.mock_wfile.getvalue().decode("utf-8")
    assert "Jobs Automation OS" in html

    # 2. GET /api/funnel
    h_funnel = DummyRequestHandler("GET", "/api/funnel", session_factory=session_factory)
    h_funnel.do_GET()
    assert h_funnel.status_code == 200
    data = json.loads(h_funnel.mock_wfile.getvalue().decode("utf-8"))
    assert data["pending_reviews"] == 1

    # 3. GET /api/kanban
    h_kanban = DummyRequestHandler("GET", "/api/kanban", session_factory=session_factory)
    h_kanban.do_GET()
    assert h_kanban.status_code == 200
    board = json.loads(h_kanban.mock_wfile.getvalue().decode("utf-8"))
    assert "DISCOVERED" in board
    assert "INTERVIEWING" in board

    # 4. GET /api/reviews
    h_reviews = DummyRequestHandler("GET", "/api/reviews", session_factory=session_factory)
    h_reviews.do_GET()
    assert h_reviews.status_code == 200
    reviews = json.loads(h_reviews.mock_wfile.getvalue().decode("utf-8"))
    assert len(reviews) == 1
    assert reviews[0]["id"] == str(task_id)

    # 5. POST /api/reviews/{id}/resolve
    resolve_body = json.dumps({"resolution_notes": "Approved range 200k-250k"}).encode("utf-8")
    h_resolve = DummyRequestHandler(
        "POST",
        f"/api/reviews/{task_id}/resolve",
        body=resolve_body,
        headers={"Content-Length": str(len(resolve_body))},
        session_factory=session_factory,
    )
    h_resolve.do_POST()
    assert h_resolve.status_code == 200
    res = json.loads(h_resolve.mock_wfile.getvalue().decode("utf-8"))
    assert res["status"] == "completed"

    # Verify task is resolved in db
    with session_factory() as session:
        task = session.get(TaskModel, task_id)
        assert task is not None
        assert task.status == "completed"
        assert task.payload_json["resolution_notes"] == "Approved range 200k-250k"

    # 6. GET /api/jobs
    h_jobs = DummyRequestHandler("GET", "/api/jobs", session_factory=session_factory)
    h_jobs.do_GET()
    assert h_jobs.status_code == 200
    jobs_data = json.loads(h_jobs.mock_wfile.getvalue().decode("utf-8"))
    assert len(jobs_data) == 1
    assert jobs_data[0]["title"] == "Platform Lead"

    # 7. GET /api/audit
    h_audit = DummyRequestHandler("GET", "/api/audit", session_factory=session_factory)
    h_audit.do_GET()
    assert h_audit.status_code == 200
    audit_data = json.loads(h_audit.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(audit_data, list)

    # 8. GET /api/health
    h_health = DummyRequestHandler("GET", "/api/health", session_factory=session_factory)
    h_health.do_GET()
    assert h_health.status_code == 200
    health_data = json.loads(h_health.mock_wfile.getvalue().decode("utf-8"))
    assert "overall_status" in health_data
    assert "components" in health_data

    # 9. GET /api/followups
    h_followups = DummyRequestHandler("GET", "/api/followups", session_factory=session_factory)
    h_followups.do_GET()
    assert h_followups.status_code == 200
    followups_data = json.loads(h_followups.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(followups_data, list)

    # 10. GET /api/analytics/sources
    h_an_src = DummyRequestHandler("GET", "/api/analytics/sources", session_factory=session_factory)
    h_an_src.do_GET()
    assert h_an_src.status_code == 200
    an_src_data = json.loads(h_an_src.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(an_src_data, list)

    # 11. GET /api/analytics/roles
    h_an_roles = DummyRequestHandler("GET", "/api/analytics/roles", session_factory=session_factory)
    h_an_roles.do_GET()
    assert h_an_roles.status_code == 200
    an_roles_data = json.loads(h_an_roles.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(an_roles_data, list)

    # 12. GET /api/analytics/resumes
    h_an_res = DummyRequestHandler("GET", "/api/analytics/resumes", session_factory=session_factory)
    h_an_res.do_GET()
    assert h_an_res.status_code == 200
    an_res_data = json.loads(h_an_res.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(an_res_data, list)

    # 13. GET /api/analytics/time-to-stage
    h_an_tts = DummyRequestHandler("GET", "/api/analytics/time-to-stage", session_factory=session_factory)
    h_an_tts.do_GET()
    assert h_an_tts.status_code == 200
    tts_data = json.loads(h_an_tts.mock_wfile.getvalue().decode("utf-8"))
    assert "sample_sizes" in tts_data

    # 14. GET /api/timeline
    h_timeline = DummyRequestHandler("GET", "/api/timeline", session_factory=session_factory)
    h_timeline.do_GET()
    assert h_timeline.status_code == 200
    timeline_data = json.loads(h_timeline.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(timeline_data, list)

    # 15. GET /api/offers-rejections
    h_off_rej = DummyRequestHandler("GET", "/api/offers-rejections", session_factory=session_factory)
    h_off_rej.do_GET()
    assert h_off_rej.status_code == 200
    off_rej_data = json.loads(h_off_rej.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(off_rej_data, list)

    # 16. GET /api/policies
    h_policies = DummyRequestHandler("GET", "/api/policies", session_factory=session_factory)
    h_policies.do_GET()
    assert h_policies.status_code == 200
    policies_data = json.loads(h_policies.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(policies_data, list)

    # 17. GET /api/worker
    h_worker = DummyRequestHandler("GET", "/api/worker", session_factory=session_factory)
    h_worker.do_GET()
    assert h_worker.status_code == 200
    worker_data = json.loads(h_worker.mock_wfile.getvalue().decode("utf-8"))
    assert isinstance(worker_data, list)


def test_funnel_analytics_advanced_metrics(db_session: Session) -> None:
    # 1. Setup Company and Jobs
    comp = CompanyModel(id=uuid.uuid4(), normalized_name="openai")
    db_session.add(comp)
    db_session.flush()

    job1 = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Research Engineer",
        description_text="AI models",
        status="ACTIVE",
    )
    job2 = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Infrastructure Lead",
        description_text="GPU clusters",
        status="ACTIVE",
    )
    db_session.add_all([job1, job2])
    db_session.flush()

    # 2. Setup Sources
    src1 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        provider="LINKEDIN",
        source_job_id="li-1",
        source_url="https://linkedin.com/jobs/1",
    )
    src2 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        provider="GMAIL_ALERT",
        source_job_id="gm-1",
        source_url="https://mail.google.com/1",
    )
    db_session.add_all([src1, src2])
    db_session.flush()

    # 3. Setup Resume Variants and Packets
    res1 = ResumeVariantModel(
        id=uuid.uuid4(),
        name="ai_research_v1",
        resume_family="ai_ml",
        version=1,
        content_hash="hash-1",
    )
    res2 = ResumeVariantModel(
        id=uuid.uuid4(),
        name="infra_v1",
        resume_family="systems",
        version=1,
        content_hash="hash-2",
    )
    db_session.add_all([res1, res2])
    db_session.flush()

    packet1 = ApplicationPacketModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        candidate_profile_version=1,
        resume_variant_id=res1.id,
        packet_hash="hash-pkt-1",
    )
    packet2 = ApplicationPacketModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        candidate_profile_version=1,
        resume_variant_id=res2.id,
        packet_hash="hash-pkt-2",
    )
    db_session.add_all([packet1, packet2])
    db_session.flush()

    # 4. Setup Applications & Events
    now = datetime.datetime.now(datetime.UTC)
    app1 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        packet_id=packet1.id,
        status="INTERVIEWING",
        applied_at=now - datetime.timedelta(days=10),
        last_activity_at=now - datetime.timedelta(days=2),
    )
    app2 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        packet_id=packet2.id,
        status="REJECTED",
        applied_at=now - datetime.timedelta(days=20),
        closed_at=now - datetime.timedelta(days=5),
        last_activity_at=now - datetime.timedelta(days=5),
    )
    db_session.add_all([app1, app2])
    db_session.flush()

    # Events for app1: recruiter contacted at +2d, interview at +5d
    ev1_1 = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app1.id,
        event_type="RECRUITER_CONTACTED",
        occurred_at=now - datetime.timedelta(days=8),
        source="email",
    )
    ev1_2 = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app1.id,
        event_type="INTERVIEW_REQUESTED",
        occurred_at=now - datetime.timedelta(days=5),
        source="email",
    )
    # Events for app2: rejected at +15d
    ev2_1 = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app2.id,
        event_type="APPLICATION_REJECTED",
        occurred_at=now - datetime.timedelta(days=5),
        source="email",
    )
    db_session.add_all([ev1_1, ev1_2, ev2_1])
    db_session.commit()

    analytics = FunnelAnalyticsService(db_session)

    # Test get_source_performance()
    sources = analytics.get_source_performance()
    assert len(sources) == 2
    li_perf = next(s for s in sources if s["provider"] == "LINKEDIN")
    assert li_perf["jobs_discovered"] == 1
    assert li_perf["applications_submitted"] == 1
    assert li_perf["interviews"] == 1
    assert li_perf["low_sample_size"] is True  # N=1 < 5
    assert "Low sample size" in li_perf["note"]

    # Test get_role_family_performance()
    roles = analytics.get_role_family_performance()
    assert len(roles) == 2
    re_role = next(r for r in roles if r["role_family"] == "Research Engineer")
    assert re_role["applications_count"] == 1
    assert re_role["interviews"] == 1
    assert re_role["low_sample_size"] is True

    # Test get_resume_performance()
    resumes = analytics.get_resume_performance()
    assert len(resumes) == 2
    ai_resume = next(r for r in resumes if r["resume_family"] == "ai_ml")
    assert ai_resume["variant_name"] == "ai_research_v1"
    assert ai_resume["interviews"] == 1
    assert ai_resume["low_sample_size"] is True
    assert "Low sample size" in ai_resume["confidence_label"]

    # Test get_time_to_stage()
    tts = analytics.get_time_to_stage()
    assert tts["avg_days_to_first_response"] == 2.0
    assert tts["avg_days_to_interview"] == 5.0
    assert tts["avg_days_to_rejection"] == 15.0
    assert tts["avg_days_to_offer"] is None
    assert tts["sample_sizes"]["first_response"] == 1
    assert tts["sample_sizes"]["interview"] == 1
    assert tts["sample_sizes"]["rejection"] == 1
    assert tts["sample_sizes"]["offer"] == 0


def test_historical_outcomes_and_real_submission_denominator(db_session: Session) -> None:
    """Tests B-R20-01 (event-driven historical funnel) and B-R20-02 (real submission denominator)."""
    comp = CompanyModel(id=uuid.uuid4(), normalized_name="anthropic")
    db_session.add(comp)
    db_session.flush()

    job1 = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Safety Researcher",
        description_text="Alignment",
        status="ACTIVE",
    )
    job2 = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Systems Engineer",
        description_text="Infra",
        status="ACTIVE",
    )
    db_session.add_all([job1, job2])
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)

    # Multiple sources for job1: Greenhouse first, then LinkedIn
    src1_1 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        provider="GREENHOUSE",
        source_job_id="gh-101",
        source_url="https://boards.greenhouse.io/anthropic/jobs/101",
        first_seen_at=now - datetime.timedelta(days=15),
    )
    src1_2 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        provider="LINKEDIN",
        source_job_id="li-202",
        source_url="https://linkedin.com/jobs/view/202",
        first_seen_at=now - datetime.timedelta(days=10),
    )
    # Source for job2
    src2 = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        provider="COMPANY_CAREERS",
        source_job_id="cc-303",
        source_url="https://anthropic.com/careers/303",
        first_seen_at=now - datetime.timedelta(days=12),
    )
    db_session.add_all([src1_1, src1_2, src2])
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)

    # App A: Interviewed then REJECTED (B-R20-01)
    # Status is currently REJECTED, but event history has INTERVIEW_REQUESTED
    app_a = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        status="REJECTED",
        applied_at=now - datetime.timedelta(days=14),
        closed_at=now - datetime.timedelta(days=2),
    )
    ev_a_screen = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app_a.id,
        event_type="SCREENING_SCHEDULED",
        occurred_at=now - datetime.timedelta(days=12),
        source="email",
    )
    ev_a_interview = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app_a.id,
        event_type="INTERVIEW_REQUESTED",
        occurred_at=now - datetime.timedelta(days=8),
        source="email",
    )
    ev_a_reject = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app_a.id,
        event_type="APPLICATION_REJECTED",
        occurred_at=now - datetime.timedelta(days=2),
        source="email",
    )

    # App B: Offered then DECLINED / WITHDRAWN (B-R20-01)
    # Status is currently WITHDRAWN, but event history has OFFER_EXTENDED
    app_b = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        status="WITHDRAWN",
        applied_at=now - datetime.timedelta(days=20),
        closed_at=now - datetime.timedelta(days=1),
    )
    ev_b_offer = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app_b.id,
        event_type="OFFER_EXTENDED",
        occurred_at=now - datetime.timedelta(days=5),
        source="email",
    )
    ev_b_withdraw = ApplicationEventModel(
        id=uuid.uuid4(),
        application_id=app_b.id,
        event_type="APPLICATION_WITHDRAWN",
        occurred_at=now - datetime.timedelta(days=1),
        source="email",
    )

    # App C: Unsubmitted / draft row (B-R20-02)
    # Status is DRAFT, applied_at is None -> MUST NOT be in submitted denominator
    app_c = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        status="DRAFT",
        applied_at=None,
    )

    # App D: Simulation mode (B-R20-02)
    # MUST NOT be counted as real submission
    app_d = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        status="INTERVIEWING",
        applied_at=now - datetime.timedelta(days=3),
        application_mode="simulation",
    )

    db_session.add_all([
        app_a, app_b, app_c, app_d,
        ev_a_screen, ev_a_interview, ev_a_reject,
        ev_b_offer, ev_b_withdraw,
    ])
    db_session.commit()

    analytics = FunnelAnalyticsService(db_session)

    # Check App A historical outcomes
    outcomes_a = analytics._get_application_historical_outcomes(app_a)
    assert outcomes_a["ever_screened"] is True
    assert outcomes_a["ever_interviewed"] is True
    assert outcomes_a["ever_rejected"] is True
    assert outcomes_a["ever_offered"] is False

    # Check App B historical outcomes
    outcomes_b = analytics._get_application_historical_outcomes(app_b)
    assert outcomes_b["ever_offered"] is True
    assert outcomes_b["ever_withdrawn"] is True

    # Check submission filtering
    assert analytics._is_real_submission(app_a) is True
    assert analytics._is_real_submission(app_b) is True
    assert analytics._is_real_submission(app_c) is False  # DRAFT & no applied_at
    assert analytics._is_real_submission(app_d) is False  # simulation mode

    # Check source performance
    sources = analytics.get_source_performance()
    # job1 had GREENHOUSE (earliest) and LINKEDIN.
    # app_a (job1) should be attributed to GREENHOUSE (primary source) and not double-counted on LINKEDIN.
    gh_perf = next((s for s in sources if s["provider"] == "GREENHOUSE"), None)
    assert gh_perf is not None
    assert gh_perf["applications_submitted"] == 1
    assert gh_perf["interviews"] == 1  # Retained even though current status is REJECTED
    assert gh_perf["rejections"] == 1

    li_perf = next((s for s in sources if s["provider"] == "LINKEDIN"), None)
    assert li_perf is not None
    assert li_perf["jobs_discovered"] == 1
    assert li_perf["applications_submitted"] == 0  # Not double-counted!


def test_neutral_statistical_wording_and_sample_sizes(db_session: Session) -> None:
    """Tests B-R20-03 (neutral statistical wording, no 'statistically robust' overclaim)."""
    comp = CompanyModel(id=uuid.uuid4(), normalized_name="google")
    db_session.add(comp)
    db_session.flush()

    res = ResumeVariantModel(
        id=uuid.uuid4(),
        name="swe_v1",
        resume_family="software_eng",
        version=1,
        content_hash="swe_hash_1",
    )
    db_session.add(res)
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)

    # Create 6 jobs and submitted applications with resume variant `res` (N=6 >= 5)
    for i in range(6):
        j = JobModel(
            id=uuid.uuid4(),
            company_id=comp.id,
            normalized_title=f"SWE {i}",
            description_text="Coding",
            status="ACTIVE",
        )
        db_session.add(j)
        db_session.flush()

        src = JobSourceModel(
            id=uuid.uuid4(),
            job_id=j.id,
            provider="GOOGLE_CAREERS",
            source_job_id=f"g-{i}",
        )
        db_session.add(src)

        pkt = ApplicationPacketModel(
            id=uuid.uuid4(),
            job_id=j.id,
            candidate_profile_version=1,
            resume_variant_id=res.id,
            packet_hash=f"pkt-hash-{i}",
        )
        db_session.add(pkt)
        db_session.flush()

        app = ApplicationModel(
            id=uuid.uuid4(),
            job_id=j.id,
            packet_id=pkt.id,
            status="INTERVIEWING",
            applied_at=now - datetime.timedelta(days=i + 1),
        )
        db_session.add(app)

    db_session.commit()

    analytics = FunnelAnalyticsService(db_session)
    resumes = analytics.get_resume_performance()
    swe_res = next(r for r in resumes if r["resume_family"] == "software_eng")

    assert swe_res["applications_count"] == 6
    assert swe_res["low_sample_size"] is False
    # Must be descriptive, NOT 'statistically robust'
    assert swe_res["confidence_label"] == "Descriptive (N=6)"
    assert "statistically robust" not in swe_res["confidence_label"].lower()

    # Also verify source performance wording for N=6
    sources = analytics.get_source_performance()
    g_src = next(s for s in sources if s["provider"] == "GOOGLE_CAREERS")
    assert g_src["low_sample_size"] is False
    assert g_src["note"] == "Descriptive (N=6)"
    assert "statistically robust" not in g_src["note"].lower()


def test_dashboard_write_safety_loopback_and_token(
    db_session_factory: sessionmaker[Session],
) -> None:
    """Tests B-R20-06 (dashboard write safety):
    - Non-loopback requests without authorization fail closed (403 Forbidden).
    - Non-loopback requests with invalid token fail closed (401 Unauthorized).
    - Non-loopback requests with valid token succeed.
    - Loopback requests (127.0.0.1) succeed.
    """
    with db_session_factory() as session:
        task = TaskModel(
            id=uuid.uuid4(),
            task_type="CLASSIFIER_REVIEW",
            status="pending",
            payload_json={"msg": "review required"},
        )
        session.add(task)
        session.commit()
        task_id = str(task.id)

    resolve_body = json.dumps({"notes": "resolved by lead"}).encode("utf-8")

    # 1. Non-loopback client (192.168.1.50) without token -> 403 Forbidden
    handler_remote_no_token = DummyRequestHandler(
        method="POST",
        path=f"/api/reviews/{task_id}/resolve",
        body=resolve_body,
        session_factory=db_session_factory,
        client_address=("192.168.1.50", 54321),
    )
    handler_remote_no_token.do_POST()
    assert handler_remote_no_token.status_code == 403
    resp_403 = json.loads(handler_remote_no_token.mock_wfile.getvalue().decode("utf-8"))
    assert "forbidden" in resp_403["error"].lower()

    # 2. Non-loopback client with invalid token -> 401 Unauthorized
    os.environ["DASHBOARD_WRITE_TOKEN"] = "secret-token-12345"
    try:
        handler_remote_bad_token = DummyRequestHandler(
            method="POST",
            path=f"/api/reviews/{task_id}/resolve",
            body=resolve_body,
            headers={"X-Operator-Token": "wrong-token"},
            session_factory=db_session_factory,
            client_address=("192.168.1.50", 54321),
        )
        handler_remote_bad_token.do_POST()
        assert handler_remote_bad_token.status_code == 401
        resp_401 = json.loads(handler_remote_bad_token.mock_wfile.getvalue().decode("utf-8"))
        assert "unauthorized" in resp_401["error"].lower()

        # 3. Non-loopback client with valid token -> 200 OK
        handler_remote_valid_token = DummyRequestHandler(
            method="POST",
            path=f"/api/reviews/{task_id}/resolve",
            body=resolve_body,
            headers={"X-Operator-Token": "secret-token-12345"},
            session_factory=db_session_factory,
            client_address=("192.168.1.50", 54321),
        )
        handler_remote_valid_token.do_POST()
        assert handler_remote_valid_token.status_code == 200
        resp_200 = json.loads(handler_remote_valid_token.mock_wfile.getvalue().decode("utf-8"))
        assert resp_200["success"] is True
    finally:
        del os.environ["DASHBOARD_WRITE_TOKEN"]

    # 4. Loopback client (127.0.0.1) without token -> 200 OK (trusted local operator)
    with db_session_factory() as session:
        task2 = TaskModel(
            id=uuid.uuid4(),
            task_type="CLASSIFIER_REVIEW",
            status="pending",
            payload_json={"msg": "another review"},
        )
        session.add(task2)
        session.commit()
        task2_id = str(task2.id)

    handler_loopback = DummyRequestHandler(
        method="POST",
        path=f"/api/reviews/{task2_id}/resolve",
        body=resolve_body,
        session_factory=db_session_factory,
        client_address=("127.0.0.1", 12345),
    )
    handler_loopback.do_POST()
    assert handler_loopback.status_code == 200
    resp_loopback = json.loads(handler_loopback.mock_wfile.getvalue().decode("utf-8"))
    assert resp_loopback["success"] is True


def test_simulation_modes_excluded_from_real_submissions(db_session: Session) -> None:
    """B-R20-07: Applications with SIMULATED status or auto_simulated/mock/test modes are excluded.

    Ensures that auto-simulated applications or test fixtures never pollute real
    funnel metrics or application submission counts.
    """
    company = CompanyModel(id=uuid.uuid4(), normalized_name="openai")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        normalized_title="Research Scientist",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="linkedin",
        first_seen_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(source)
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)

    # 1. Real submission
    app_real = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SUBMITTED",
        applied_at=now,
        application_mode="live",
    )
    # 2. SIMULATED status with applied_at populated -> must be excluded
    app_sim_status = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SIMULATED",
        applied_at=now,
        application_mode="live",
    )
    # 3. auto_simulated mode with applied_at populated -> must be excluded
    app_auto_sim = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SUBMITTED",
        applied_at=now,
        application_mode="auto_simulated",
    )
    # 4. mock mode with applied_at populated -> must be excluded
    app_mock = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SUBMITTED",
        applied_at=now,
        application_mode="mock",
    )
    # 5. test mode with applied_at populated -> must be excluded
    app_test = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SUBMITTED",
        applied_at=now,
        application_mode="test",
    )
    db_session.add_all([app_real, app_sim_status, app_auto_sim, app_mock, app_test])
    db_session.commit()

    service = FunnelAnalyticsService(db_session)
    assert service._is_real_submission(app_real) is True
    assert service._is_real_submission(app_sim_status) is False
    assert service._is_real_submission(app_auto_sim) is False
    assert service._is_real_submission(app_mock) is False
    assert service._is_real_submission(app_test) is False

    # Check source performance counts: only 1 real submission
    perf = service.get_source_performance()
    linkedin_perf = next(p for p in perf if p["provider"] == "linkedin")
    assert linkedin_perf["applications_submitted"] == 1


def test_final_interview_evidence_and_accepted_rates(db_session: Session) -> None:
    """B-R20-08: ever_final_interview requires explicit evidence; accepted rates are exposed."""
    company = CompanyModel(id=uuid.uuid4(), normalized_name="anthropic")
    db_session.add(company)
    db_session.flush()

    job = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        normalized_title="Safety Engineer",
    )
    db_session.add(job)
    db_session.flush()

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        first_seen_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(source)
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)

    # App 1: Generic interview only (not final)
    app1 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="INTERVIEWING",
        applied_at=now,
        application_mode="manual",
    )
    # App 2: Final round interview with offer accepted
    app2 = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="OFFER_ACCEPTED",
        applied_at=now,
        application_mode="manual",
    )
    db_session.add_all([app1, app2])
    db_session.flush()

    # App 1 has generic interview event
    ev1 = ApplicationEventModel(
        application_id=app1.id,
        event_type="INTERVIEW_REQUESTED",
        occurred_at=now,
        source="email",
    )
    # App 2 has final interview event and OFFER_ACCEPTED event
    ev2_final = ApplicationEventModel(
        application_id=app2.id,
        event_type="FINAL_INTERVIEW_SCHEDULED",
        occurred_at=now,
        source="email",
    )
    ev2_offer = ApplicationEventModel(
        application_id=app2.id,
        event_type="OFFER_ACCEPTED",
        occurred_at=now,
        source="email",
    )
    db_session.add_all([ev1, ev2_final, ev2_offer])
    db_session.commit()

    service = FunnelAnalyticsService(db_session)
    outcomes1 = service._get_application_historical_outcomes(app1)
    outcomes2 = service._get_application_historical_outcomes(app2)

    # App 1: ever_interviewed=True, ever_final_interview=False
    assert outcomes1["ever_interviewed"] is True
    assert outcomes1["ever_final_interview"] is False
    assert outcomes1["ever_accepted"] is False

    # App 2: ever_final_interview=True, ever_accepted=True
    assert outcomes2["ever_final_interview"] is True
    assert outcomes2["ever_accepted"] is True

    # Performance methods expose final_interviews and accepted
    source_perf = service.get_source_performance()
    gh_perf = next(p for p in source_perf if p["provider"] == "greenhouse")
    assert gh_perf["applications_submitted"] == 2
    assert gh_perf["interviews"] == 2
    assert gh_perf["final_interviews"] == 1
    assert gh_perf["accepted"] == 1
    assert gh_perf["accept_rate_pct"] == 50.0

    role_perf = service.get_role_family_performance()
    safety_perf = next(p for p in role_perf if p["role_family"] == "Safety Engineer")
    assert safety_perf["applications_count"] == 2
    assert safety_perf["final_interviews"] == 1
    assert safety_perf["accepted"] == 1
    assert safety_perf["accept_rate_pct"] == 50.0


def test_funnel_summary_historical_outcomes_with_terminal_rejection(
    db_session: Session,
) -> None:
    """B-R20-01: Headline funnel summary preserves screening/interview stage achievements after rejection."""
    comp = CompanyModel(id=uuid.uuid4(), normalized_name="Anthropic")
    db_session.add(comp)
    db_session.flush()

    job = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Alignment Engineer",
        status="ACTIVE",
    )
    db_session.add(job)
    db_session.flush()

    # Application was submitted, reached screening, reached interview, then rejected
    app = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="REJECTED",
        policy_decision="auto_allowed",
        application_mode="auto",
        applied_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=10),
    )
    db_session.add(app)
    db_session.flush()

    now = datetime.datetime.now(datetime.UTC)
    ev_submit = ApplicationEventModel(
        application_id=app.id,
        event_type="APPLICATION_SUBMITTED",
        occurred_at=now - datetime.timedelta(days=10),
        source="system",
    )
    ev_screen = ApplicationEventModel(
        application_id=app.id,
        event_type="SCREENING_SCHEDULED",
        occurred_at=now - datetime.timedelta(days=7),
        source="email",
    )
    ev_interview = ApplicationEventModel(
        application_id=app.id,
        event_type="INTERVIEW_SCHEDULED",
        occurred_at=now - datetime.timedelta(days=4),
        source="email",
    )
    ev_reject = ApplicationEventModel(
        application_id=app.id,
        event_type="APPLICATION_REJECTED",
        occurred_at=now - datetime.timedelta(days=1),
        source="email",
    )
    db_session.add_all([ev_submit, ev_screen, ev_interview, ev_reject])
    db_session.commit()

    service = FunnelAnalyticsService(db_session)
    summary = service.get_funnel_summary()

    # Even though app.status is REJECTED, historical stages are preserved in headline metrics
    assert summary["total_jobs_discovered"] == 1
    assert summary["total_submitted"] == 1
    assert summary["total_screening"] == 1
    assert summary["total_interviewing"] == 1
    assert summary["total_rejected"] == 1
    assert summary["conversion_rates"]["submission_to_screen_pct"] == 100.0
    assert summary["conversion_rates"]["screen_to_interview_pct"] == 100.0


def test_funnel_summary_excludes_simulation_and_unsubmitted(
    db_session: Session,
) -> None:
    """B-R20-02: Headline funnel denominator excludes simulation, mock, auto_simulated, and unsubmitted apps."""
    comp = CompanyModel(id=uuid.uuid4(), normalized_name="OpenAI")
    db_session.add(comp)
    db_session.flush()

    job1 = JobModel(id=uuid.uuid4(), company_id=comp.id, normalized_title="Research Scientist 1")
    job2 = JobModel(id=uuid.uuid4(), company_id=comp.id, normalized_title="Research Scientist 2")
    job3 = JobModel(id=uuid.uuid4(), company_id=comp.id, normalized_title="Research Scientist 3")
    job4 = JobModel(id=uuid.uuid4(), company_id=comp.id, normalized_title="Research Scientist 4")
    db_session.add_all([job1, job2, job3, job4])
    db_session.flush()

    # 1. Real submission
    app_real = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job1.id,
        status="SUBMITTED",
        application_mode="assisted",
        applied_at=datetime.datetime.now(datetime.UTC),
    )
    # 2. Simulated status
    app_sim_status = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job2.id,
        status="SIMULATED",
        application_mode="auto",
        applied_at=datetime.datetime.now(datetime.UTC),
    )
    # 3. Simulated mode (auto_simulated)
    app_sim_mode = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job3.id,
        status="SUBMITTED",
        application_mode="auto_simulated",
        applied_at=datetime.datetime.now(datetime.UTC),
    )
    # 4. Unsubmitted draft / discovered
    app_unsubmitted = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job4.id,
        status="DISCOVERED",
        application_mode="manual",
    )
    db_session.add_all([app_real, app_sim_status, app_sim_mode, app_unsubmitted])
    db_session.commit()

    service = FunnelAnalyticsService(db_session)
    summary = service.get_funnel_summary()

    assert summary["total_jobs_discovered"] == 4
    # Only app_real is a real submission
    assert summary["total_submitted"] == 1






def test_dashboard_quarantines_historical_durable_canary_derivatives(
    db_session_factory: sessionmaker[Session],
) -> None:
    """A later durable tag hides, but never deletes or resolves, historical derivatives."""
    now = datetime.datetime.now(datetime.UTC)
    with db_session_factory() as session:
        company = CompanyModel(normalized_name="Dashboard containment company")
        session.add(company)
        session.flush()

        canary_job = JobModel(
            company_id=company.id,
            normalized_title="Canary-only executive role",
            status="discovered",
        )
        genuine_job = JobModel(
            company_id=company.id,
            normalized_title="Genuine platform role",
            status="discovered",
        )
        session.add_all([canary_job, genuine_job])
        session.flush()
        session.add_all(
            [
                JobSourceModel(job_id=canary_job.id, provider="CANARY_SOURCE"),
                JobSourceModel(job_id=genuine_job.id, provider="GENUINE_SOURCE"),
            ]
        )

        canary_variant = ResumeVariantModel(
            resume_family="canary_family",
            name="canary_variant",
            version=1,
            content_hash="canary-variant-hash",
            target_job_id=canary_job.id,
        )
        genuine_variant = ResumeVariantModel(
            resume_family="genuine_family",
            name="genuine_variant",
            version=1,
            content_hash="genuine-variant-hash",
            target_job_id=genuine_job.id,
        )
        session.add_all([canary_variant, genuine_variant])
        session.flush()
        canary_packet = ApplicationPacketModel(
            job_id=canary_job.id,
            candidate_profile_version=1,
            resume_variant_id=canary_variant.id,
            packet_hash="canary-packet-hash",
        )
        genuine_packet = ApplicationPacketModel(
            job_id=genuine_job.id,
            candidate_profile_version=1,
            resume_variant_id=genuine_variant.id,
            packet_hash="genuine-packet-hash",
        )
        session.add_all([canary_packet, genuine_packet])
        session.flush()

        canary_application = ApplicationModel(
            job_id=canary_job.id,
            packet_id=canary_packet.id,
            status="OFFER_RECEIVED",
            applied_at=now - datetime.timedelta(days=7),
        )
        genuine_application = ApplicationModel(
            job_id=genuine_job.id,
            packet_id=genuine_packet.id,
            status="REJECTED",
            applied_at=now - datetime.timedelta(days=7),
            closed_at=now,
        )
        session.add_all([canary_application, genuine_application])
        session.flush()

        canary_message = InboundMessageModel(
            provider_message_id="canary-dashboard-message",
            provider_thread_id="canary-dashboard-thread",
            received_at=now,
            sender="Owner Canary <owner-canary@example.test>",
            subject="PRIVATE CANARY SUBJECT",
            headers_json={},
            body_text="PRIVATE CANARY BODY",
            classification="INTERVIEW_REQUEST",
        )
        genuine_message = InboundMessageModel(
            provider_message_id="genuine-dashboard-message",
            provider_thread_id="genuine-dashboard-thread",
            received_at=now,
            sender="Recruiter <recruiter@example.test>",
            subject="Genuine application update",
            headers_json={},
            body_text="Genuine message body",
            classification="REJECTION",
        )
        session.add_all([canary_message, genuine_message])
        session.flush()
        session.add_all(
            [
                MessageLinkModel(
                    inbound_message_id=canary_message.id,
                    job_id=canary_job.id,
                    application_id=canary_application.id,
                    company_id=company.id,
                    confidence=1.0,
                    method="historical_canary_link",
                ),
                MessageLinkModel(
                    inbound_message_id=genuine_message.id,
                    job_id=genuine_job.id,
                    application_id=genuine_application.id,
                    company_id=company.id,
                    confidence=1.0,
                    method="genuine_link",
                ),
            ]
        )
        session.add_all(
            [
                ApplicationEventModel(
                    application_id=canary_application.id,
                    event_type="INTERVIEW_REQUESTED",
                    occurred_at=now,
                    source="email_lifecycle",
                    source_reference=canary_message.provider_message_id,
                ),
                ApplicationEventModel(
                    application_id=genuine_application.id,
                    event_type="INTERVIEW_REQUESTED",
                    occurred_at=now,
                    source="email_lifecycle",
                    source_reference=genuine_message.provider_message_id,
                ),
            ]
        )
        session.add_all(
            [
                InterviewModel(
                    application_id=canary_application.id,
                    round_type="Canary interview",
                    scheduled_start=now,
                    scheduled_end=now + datetime.timedelta(hours=1),
                    location_or_link="https://canary.example.test/private",
                ),
                InterviewModel(
                    application_id=genuine_application.id,
                    round_type="Genuine interview",
                    scheduled_start=now,
                    scheduled_end=now + datetime.timedelta(hours=1),
                ),
            ]
        )
        canary_contact = ContactModel(
            company_id=company.id,
            name="Owner Canary",
            email="owner-canary@example.test",
            source="email",
        )
        genuine_contact = ContactModel(
            company_id=company.id,
            name="Genuine Recruiter",
            email="recruiter@example.test",
            source="email",
        )
        session.add_all([canary_contact, genuine_contact])
        session.flush()
        canary_review = TaskModel(
            task_type="NEEDS_REVIEW",
            status="pending",
            payload_json={
                "provider_message_id": canary_message.provider_message_id,
                "subject": canary_message.subject,
            },
        )
        genuine_review = TaskModel(
            job_id=genuine_job.id,
            task_type="NEEDS_REVIEW",
            status="pending",
            payload_json={"question": "Genuine review"},
        )
        canary_followup = TaskModel(
            task_type="UNANSWERED_RECRUITER",
            status="pending",
            payload_json={
                "latest_message_id": canary_message.provider_message_id,
                "subject": canary_message.subject,
            },
        )
        session.add_all([canary_review, genuine_review, canary_followup])
        session.flush()
        session.add_all(
            [
                AuditLogModel(
                    action_type="canary_audit",
                    entity_type="message",
                    entity_id=canary_message.id,
                    result="success",
                    external_reference=canary_message.provider_message_id,
                    metadata_json={
                        "provider_message_id": canary_message.provider_message_id,
                        "subject": canary_message.subject,
                    },
                ),
                AuditLogModel(
                    action_type="genuine_audit",
                    entity_type="message",
                    entity_id=genuine_message.id,
                    result="success",
                    external_reference=genuine_message.provider_message_id,
                    metadata_json={"provider_message_id": genuine_message.provider_message_id},
                ),
            ]
        )
        canary_application_id = canary_application.id
        genuine_application_id = genuine_application.id
        canary_message_id = canary_message.id
        canary_contact_id = canary_contact.id
        canary_review_id = canary_review.id
        session.commit()

    # Model the actual repair case: dependent records already existed before the
    # mailbox policy durably reclassified the historical message as a canary.
    with db_session_factory() as session:
        reclassified_message = session.get(InboundMessageModel, canary_message_id)
        assert reclassified_message is not None
        reclassified_message.headers_json = {"_provider": {"canary": True}}
        session.commit()

    with db_session_factory() as session:
        analytics = FunnelAnalyticsService(session)
        summary = analytics.get_funnel_summary()
        assert summary["total_jobs_discovered"] == 1
        assert summary["total_submitted"] == 1
        assert summary["pending_reviews"] == 1
        assert analytics.get_source_breakdown() == {"GENUINE_SOURCE": 1}
        assert [row["provider"] for row in analytics.get_source_performance()] == [
            "GENUINE_SOURCE"
        ]
        assert [row["role_family"] for row in analytics.get_role_family_performance()] == [
            "Genuine platform role"
        ]
        assert [row["variant_name"] for row in analytics.get_resume_performance()] == [
            "genuine_variant"
        ]
        assert analytics.get_time_to_stage()["sample_sizes"]["interview"] == 1
        board = analytics.get_kanban_board()
        visible_card_ids = {
            card["id"] for cards in board.values() for card in cards
        }
        assert str(genuine_application_id) in visible_card_ids
        assert str(canary_application_id) not in visible_card_ids

    def response_json(handler: DummyRequestHandler) -> Any:
        return json.loads(handler.mock_wfile.getvalue().decode("utf-8"))

    endpoints = {
        "/api/jobs": "Canary-only executive role",
        "/api/reviews": "PRIVATE CANARY SUBJECT",
        "/api/followups": "PRIVATE CANARY SUBJECT",
        "/api/interviews": "Canary interview",
        "/api/contacts": "owner-canary@example.test",
        "/api/audit": "PRIVATE CANARY SUBJECT",
        "/api/offers-rejections": "Canary-only executive role",
    }
    for path, forbidden in endpoints.items():
        handler = DummyRequestHandler("GET", path, session_factory=db_session_factory)
        handler.do_GET()
        assert handler.status_code == 200
        assert forbidden not in json.dumps(response_json(handler))

    canary_app_timeline = DummyRequestHandler(
        "GET",
        f"/api/timeline?application_id={canary_application_id}",
        session_factory=db_session_factory,
    )
    canary_app_timeline.do_GET()
    assert canary_app_timeline.status_code == 200
    assert response_json(canary_app_timeline) == []

    canary_contact_timeline = DummyRequestHandler(
        "GET",
        f"/api/timeline?contact_id={canary_contact_id}",
        session_factory=db_session_factory,
    )
    canary_contact_timeline.do_GET()
    assert canary_contact_timeline.status_code == 200
    assert response_json(canary_contact_timeline) == []

    body = json.dumps({"resolution_notes": "must not be written"}).encode("utf-8")
    resolve = DummyRequestHandler(
        "POST",
        f"/api/reviews/{canary_review_id}/resolve",
        body=body,
        headers={"Content-Length": str(len(body))},
        session_factory=db_session_factory,
    )
    resolve.do_POST()
    assert resolve.status_code == 409
    assert "reconciliation" in response_json(resolve)["error"].lower()

    with db_session_factory() as session:
        preserved_task = session.get(TaskModel, canary_review_id)
        assert preserved_task is not None
        assert preserved_task.status == "pending"
        assert "resolution_notes" not in preserved_task.payload_json

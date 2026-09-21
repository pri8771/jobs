"""Tests for the analytics service and embedded dashboard server."""

from __future__ import annotations

import datetime
import io
import json
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
    CompanyModel,
    JobModel,
    JobSourceModel,
    ResumeVariantModel,
    TaskModel,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
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
    ) -> None:
        self.command = method
        self.path = path
        self.request_version = "HTTP/1.1"
        self.headers = cast(Any, headers or {})
        self.rfile = io.BytesIO(body)
        self.mock_wfile = io.BytesIO()
        self.wfile = cast(Any, self.mock_wfile)
        self.session_factory = session_factory
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
    assert "Sample size warning" in li_perf["note"]

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
    assert "Descriptive" in ai_resume["confidence_label"]

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



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
    ApplicationModel,
    CompanyModel,
    JobModel,
    JobSourceModel,
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


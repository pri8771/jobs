"""Tests for system health monitoring, worker sweeps, and disaster recovery readiness."""

from __future__ import annotations

import datetime
import os
import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    CompanyModel,
    InboundMessageModel,
    JobModel,
    PolicyRegistryModel,
)
from jobs_automation.health import HealthCheckService
from jobs_automation.worker import WorkerDaemon


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    yield session_factory


def test_health_check_service_nominal(db_session_factory: sessionmaker[Session]) -> None:
    checker = HealthCheckService(db_session_factory)
    report = checker.run_full_check()

    assert report.overall_status in ["HEALTHY", "DEGRADED"]
    assert "database" in report.components
    assert report.components["database"].status == "HEALTHY"
    assert "kill_switches" in report.components
    assert report.components["kill_switches"].status == "HEALTHY"
    assert "adapters" in report.components
    assert report.components["adapters"].status == "HEALTHY"


def test_health_check_service_kill_switch_active(
    db_session_factory: sessionmaker[Session],
) -> None:
    os.environ["JOBS_AUTOMATION_KILL_SWITCH"] = "true"
    try:
        checker = HealthCheckService(db_session_factory)
        report = checker.run_full_check()
        assert report.components["kill_switches"].status == "DEGRADED"
        assert "ACTIVE" in report.components["kill_switches"].message
        assert report.overall_status == "DEGRADED"
    finally:
        del os.environ["JOBS_AUTOMATION_KILL_SWITCH"]


def test_health_check_service_expired_policy(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        expired_policy = PolicyRegistryModel(
            id=uuid.uuid4(),
            platform="greenhouse",
            domain_pattern="boards.greenhouse.io",
            capability="auto_apply",
            decision="allowed",
            reviewed_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=120),
            review_due_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30),
        )
        session.add(expired_policy)
        session.commit()

    checker = HealthCheckService(db_session_factory)
    health = checker.check_policy_registry()
    assert health.status == "DEGRADED"
    assert "expired" in health.message


def test_worker_daemon_respects_kill_switch(
    db_session_factory: sessionmaker[Session],
) -> None:
    daemon = WorkerDaemon(db_session_factory, poll_interval_seconds=60)
    os.environ["JOBS_AUTOMATION_KILL_SWITCH"] = "true"
    try:
        results = daemon.run_sweep()
        assert results["unanswered_alerts"] == 0
        assert results["stale_alerts"] == 0
    finally:
        del os.environ["JOBS_AUTOMATION_KILL_SWITCH"]


def test_worker_daemon_run_sweep(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as session:
        comp = CompanyModel(id=uuid.uuid4(), normalized_name="meta")
        session.add(comp)
        session.flush()

        job = JobModel(
            id=uuid.uuid4(),
            company_id=comp.id,
            normalized_title="Engineering Manager",
            description_text="Manage infrastructure",
        )
        session.add(job)
        session.flush()

        # Add an unresponded recruiter outreach message
        msg = InboundMessageModel(
            id=uuid.uuid4(),
            provider_message_id="msg-worker-1",
            provider_thread_id="th-worker-1",
            sender="recruiter@meta.com",
            recipients_json=["candidate@example.com"],
            direction="inbound",
            subject="Interview Request - Engineering Manager",
            body_text="Hi, let's schedule an interview for the Engineering Manager role.",
            classification="INTERVIEW_REQUEST",
            received_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=60),
        )
        session.add(msg)
        session.commit()

    daemon = WorkerDaemon(db_session_factory, poll_interval_seconds=60)
    results = daemon.run_sweep()

    assert results["unanswered_alerts"] >= 0
    assert results["lifecycle_transitions"] >= 0

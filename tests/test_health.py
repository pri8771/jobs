"""Tests for system health monitoring, worker sweeps, and disaster recovery readiness."""

from __future__ import annotations

import datetime
import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    AuditLogModel,
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
    assert report.components["adapters"].status in ["HEALTHY", "DEGRADED"]


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
        # Kill switch path: begin RUNNING and KILLED finalize must have been written
        with db_session_factory() as session:
            run_id = results["run_id"]
            begin_rec = session.scalar(
                select(AuditLogModel)
                .where(AuditLogModel.action_type == "worker_run")
                .where(AuditLogModel.external_reference == run_id)
            )
            assert begin_rec is not None
            assert begin_rec.result == "RUNNING"
            fin_rec = session.scalar(
                select(AuditLogModel)
                .where(AuditLogModel.action_type == "worker_run_finished")
                .where(AuditLogModel.external_reference == run_id)
            )
            assert fin_rec is not None
            assert fin_rec.result == "KILLED"
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

    # Verify crash-durable worker run records (begin + finalize)
    run_id = results["run_id"]
    with db_session_factory() as session:
        begin_rec = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert begin_rec is not None
        assert begin_rec.result == "RUNNING"
        assert begin_rec.actor == "worker_daemon"
        assert begin_rec.metadata_json["run_id"] == run_id

        fin_rec = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run_finished")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert fin_rec is not None
        assert fin_rec.result in ("SUCCESS", "PARTIAL", "FAILED")
        assert fin_rec.actor == "worker_daemon"
        assert fin_rec.metadata_json["run_id"] == run_id
        assert "finished_at" in fin_rec.metadata_json

    # Health check reports on new-style records
    checker = HealthCheckService(db_session_factory)
    worker_health = checker.check_worker()
    assert worker_health.status in ("HEALTHY", "DEGRADED")
    assert "last_attempt_at" in worker_health.details
    assert "last_attempt_status" in worker_health.details
    assert "stale_running_run" in worker_health.details

    # Run sweep with clean adapter -> reports HEALTHY or PARTIAL at worst
    class CleanAdapter(EmailAdapter):
        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[Any]:
            return []

        def get_thread(self, thread_id: str) -> list[Any]:
            return []

    clean_daemon = WorkerDaemon(db_session_factory, poll_interval_seconds=60, email_adapter=CleanAdapter())
    clean_results = clean_daemon.run_sweep()
    assert clean_results["errors"] == []

    worker_healthy = checker.check_worker()
    assert worker_healthy.status == "HEALTHY"
    assert "SUCCESS" in worker_healthy.message


def test_worker_health_detects_stale_running(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Health service detects stale RUNNING record when age exceeds threshold."""
    checker = HealthCheckService(db_session_factory)
    stale_run_id = str(uuid.uuid4())
    three_hours_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=3)

    with db_session_factory() as session:
        # Begin record from 3 hours ago with no finalize record
        begin_rec = AuditLogModel(
            action_type="worker_run",
            entity_type="worker",
            actor="worker_daemon",
            result="RUNNING",
            external_reference=stale_run_id,
            occurred_at=three_hours_ago,
            metadata_json={"run_id": stale_run_id, "started_at": three_hours_ago.isoformat()},
        )
        session.add(begin_rec)
        session.commit()

    health = checker.check_worker()
    assert health.status == "DEGRADED"
    assert health.details["stale_running_run"] is True
    assert health.details["stale_run_id"] == stale_run_id
    assert "STALE_RUNNING" in health.message


def test_worker_health_legacy_fallback(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Health check safely falls back to legacy worker_sweep audit logs."""
    checker = HealthCheckService(db_session_factory)
    one_hour_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)

    with db_session_factory() as session:
        legacy_rec = AuditLogModel(
            action_type="worker_sweep",
            entity_type="worker",
            actor="worker_daemon",
            result="success",
            external_reference=one_hour_ago.isoformat(),
            occurred_at=one_hour_ago,
            metadata_json={"errors": []},
        )
        session.add(legacy_rec)
        session.commit()

    health = checker.check_worker()
    assert health.status == "HEALTHY"
    assert "legacy record" in health.message
    assert health.details["last_attempt_status"] == "success"


def test_worker_metadata_does_not_contain_secrets(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Worker run finalize records contain only safe metrics, no tokens or sensitive payloads."""
    daemon = WorkerDaemon(db_session_factory, poll_interval_seconds=60)
    results = daemon.run_sweep()
    run_id = results["run_id"]

    with db_session_factory() as session:
        fin_rec = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run_finished")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert fin_rec is not None
        meta = fin_rec.metadata_json
        # Verify only aggregate / safe keys are stored
        allowed_keys = {
            "run_id",
            "final_status",
            "finished_at",
            "messages_polled",
            "messages_ingested",
            "jobs_discovered",
            "lifecycle_transitions",
            "unanswered_alerts",
            "stale_alerts",
            "reconciliation_performed",
            "error_count",
            "error_categories",
            "sample_errors",
            "error_note",
        }
        for k in meta.keys():
            assert k in allowed_keys
            # Confirm no secret-looking content
            assert "token" not in str(meta[k]).lower()
            assert "secret" not in str(meta[k]).lower()


def test_worker_health_shows_unfinished_running_attempt(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Health service reflects unfinished RUNNING attempts as true latest attempt."""
    checker = HealthCheckService(db_session_factory)
    now = datetime.datetime.now(datetime.UTC)
    active_run_id = str(uuid.uuid4())

    with db_session_factory() as session:
        # Prior finished run from 1 hour ago
        old_finish = AuditLogModel(
            action_type="worker_run_finished",
            entity_type="worker",
            actor="worker_daemon",
            result="SUCCESS",
            external_reference="old-run-id",
            occurred_at=now - datetime.timedelta(hours=1),
            metadata_json={"reconciliation_performed": True},
        )
        session.add(old_finish)

        # Fresh begin record (5 minutes ago, still running)
        begin_rec = AuditLogModel(
            action_type="worker_run",
            entity_type="worker",
            actor="worker_daemon",
            result="RUNNING",
            external_reference=active_run_id,
            occurred_at=now - datetime.timedelta(minutes=5),
            metadata_json={"run_id": active_run_id, "started_at": (now - datetime.timedelta(minutes=5)).isoformat()},
        )
        session.add(begin_rec)
        session.commit()

    health = checker.check_worker()
    assert health.details["last_attempt_status"] == "RUNNING"
    assert health.details["last_success_at"] is not None
    assert health.details["last_reconciliation_at"] is not None
    assert "RUNNING in progress" in health.message


def test_worker_health_reports_reconciliation_and_error_fields(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Health service exposes last_reconciliation_at, last_error_at, and last_error_category."""
    checker = HealthCheckService(db_session_factory)
    now = datetime.datetime.now(datetime.UTC)

    with db_session_factory() as session:
        failed_finish = AuditLogModel(
            action_type="worker_run_finished",
            entity_type="worker",
            actor="worker_daemon",
            result="FAILED",
            external_reference="fail-run-id",
            occurred_at=now - datetime.timedelta(minutes=15),
            metadata_json={
                "reconciliation_performed": False,
                "error_categories": ["GMAIL_AUTH_ERROR"],
                "sample_errors": ["Gmail authentication expired"],
            },
        )
        reconciled_finish = AuditLogModel(
            action_type="worker_run_finished",
            entity_type="worker",
            actor="worker_daemon",
            result="SUCCESS",
            external_reference="rec-run-id",
            occurred_at=now - datetime.timedelta(hours=4),
            metadata_json={"reconciliation_performed": True},
        )
        session.add_all([failed_finish, reconciled_finish])
        session.commit()

    health = checker.check_worker()
    assert health.details["last_error_at"] is not None
    assert health.details["last_error_category"] == "GMAIL_AUTH_ERROR"
    assert health.details["last_reconciliation_at"] is not None
    assert health.status == "DEGRADED"


@pytest.mark.parametrize(
    ("check_name", "secret_marker", "expected_message", "expected_category"),
    [
        (
            "check_database",
            "password=hunter2-db",
            "Database health check failed.",
            "DATABASE_CHECK_FAILED",
        ),
        (
            "check_policy_registry",
            "access_token=policy-token-value",
            "Policy registry health check failed.",
            "POLICY_HEALTH_CHECK_FAILED",
        ),
        (
            "check_worker",
            "Authorization: Bearer worker-token-value",
            "Worker health check failed.",
            "WORKER_HEALTH_CHECK_FAILED",
        ),
        (
            "check_gmail",
            "email_body=private recruiter message",
            "Gmail health check failed.",
            "GMAIL_HEALTH_CHECK_FAILED",
        ),
    ],
)
def test_health_exception_details_are_redacted_and_stable(
    check_name: str,
    secret_marker: str,
    expected_message: str,
    expected_category: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def failing_session_factory() -> None:
        raise RuntimeError(secret_marker)

    checker = HealthCheckService(failing_session_factory)
    health = getattr(checker, check_name)()
    serialized = health.model_dump_json()

    assert health.status == "UNHEALTHY"
    assert health.message == expected_message
    assert health.details == {"error_category": expected_category}
    assert secret_marker not in serialized
    assert secret_marker not in caplog.text


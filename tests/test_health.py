"""Tests for system health monitoring, worker sweeps, and disaster recovery readiness."""

from __future__ import annotations

import datetime
import os
import pathlib
import subprocess
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
    # In current release, greenhouse and lever adapters return NOT_IMPLEMENTED for live submission,
    # so health service correctly reports DEGRADED (simulation-only) rather than falsely claiming live HEALTHY.
    assert report.components["adapters"].status == "DEGRADED"
    assert "greenhouse" in report.components["adapters"].details["registered_platforms"]
    assert report.components["adapters"].details["live_capable_platforms"] == []
    assert "worker" in report.components
    assert report.components["worker"].status == "DEGRADED"  # no sweeps run yet
    assert "gmail" in report.components


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

    # Verify durable worker sweep audit record was written (error due to missing Gmail credentials)
    with db_session_factory() as session:
        audit = session.scalar(
            select(AuditLogModel).where(AuditLogModel.action_type == "worker_sweep")
        )
        assert audit is not None
        assert audit.actor == "worker_daemon"
        assert audit.result == "error"
        assert "unanswered_alerts" in audit.metadata_json

    # Health check correctly reports DEGRADED when sweep had errors
    checker = HealthCheckService(db_session_factory)
    worker_health = checker.check_worker()
    assert worker_health.status == "DEGRADED"
    assert "Last worker sweep" in worker_health.message

    # Run sweep with configured adapter -> reports HEALTHY
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
    assert "success" in worker_healthy.message


def test_gmail_health_check(db_session_factory: sessionmaker[Session]) -> None:
    checker = HealthCheckService(db_session_factory)
    # Default without credentials configured -> DEGRADED (mock mode)
    health = checker.check_gmail()
    assert health.status == "DEGRADED"
    assert "mock adapter" in health.message

    # With credentials configured -> HEALTHY
    os.environ["GMAIL_CREDENTIALS_JSON"] = '{"type": "service_account"}'
    try:
        health_configured = checker.check_gmail()
        assert health_configured.status == "HEALTHY"
        assert health_configured.details["credentials_configured"] is True
    finally:
        del os.environ["GMAIL_CREDENTIALS_JSON"]


def test_backup_restore_script_security(tmp_path: pathlib.Path) -> None:
    repo_root = pathlib.Path(__file__).parent.parent
    restore_script = repo_root / "scripts" / "restore_db.sh"
    backup_script = repo_root / "scripts" / "backup_db.sh"

    # 1. Restore without arguments fails
    res = subprocess.run(["bash", str(restore_script)], capture_output=True, text=True)
    assert res.returncode == 1
    assert "Usage:" in res.stdout or "Usage:" in res.stderr

    # 2. Restore with nonexistent file fails
    res = subprocess.run(
        ["bash", str(restore_script), str(tmp_path / "nonexistent.sql.gz")],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "does not exist" in res.stdout or "does not exist" in res.stderr

    # 3. Restore with missing checksum fails closed
    dummy_backup = tmp_path / "test_backup.sql.gz"
    dummy_backup.write_bytes(b"dummy gz content")
    res = subprocess.run(
        ["bash", str(restore_script), str(dummy_backup)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Restore failed closed" in res.stdout or "Restore failed closed" in res.stderr

    # 4. Emergency override passes checksum check but fails closed on missing DB_PASSWORD
    clean_env = {k: v for k, v in os.environ.items() if k not in ("DB_PASSWORD", "ALLOW_DEFAULT_DEV_CREDENTIALS")}
    res = subprocess.run(
        ["bash", str(restore_script), str(dummy_backup), "--skip-checksum-emergency-override"],
        capture_output=True,
        text=True,
        env=clean_env,
    )
    assert res.returncode == 1
    assert "DB_PASSWORD must be set" in res.stdout or "DB_PASSWORD must be set" in res.stderr

    # 5. Backup script fails closed when DB_PASSWORD not set
    res_backup = subprocess.run(
        ["bash", str(backup_script)],
        capture_output=True,
        text=True,
        env=clean_env,
    )
    assert res_backup.returncode == 1
    assert "DB_PASSWORD must be set" in res_backup.stdout or "DB_PASSWORD must be set" in res_backup.stderr

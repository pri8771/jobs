"""Tests for background WorkerDaemon scheduling, ingestion call-order, and safety controls."""

from __future__ import annotations

import datetime
import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
)
from jobs_automation.health import HealthCheckService
from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.worker import WorkerDaemon


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    yield session_factory


def test_worker_default_cadence(db_session_factory: sessionmaker[Session]) -> None:
    daemon = WorkerDaemon(db_session_factory)
    assert daemon.poll_interval_seconds == 14400  # 4 hours
    assert daemon.reconciliation_interval_seconds == 86400  # 24 hours


def test_worker_call_order_ingestion_before_lifecycle(
    db_session_factory: sessionmaker[Session],
) -> None:
    now = datetime.datetime.now(datetime.UTC)

    # Pre-create company, job, and submitted application in database
    with db_session_factory() as session:
        comp = CompanyModel(normalized_name="stripe")
        session.add(comp)
        session.flush()

        job = JobModel(
            company_id=comp.id,
            normalized_title="Staff Solutions Architect",
            status="shortlisted",
        )
        session.add(job)
        session.flush()

        app = ApplicationModel(
            job_id=job.id,
            destination_domain="stripe.com",
            status="SUBMITTED",
            policy_decision="auto_allowed",
            application_mode="auto",
            applied_at=now - datetime.timedelta(days=1),
            last_activity_at=now - datetime.timedelta(days=1),
        )
        session.add(app)
        session.commit()

    # Raw email that is an interview request for Stripe
    interview_email = RawEmailMessage(
        provider_message_id="msg-worker-order-1",
        provider_thread_id="th-worker-order-1",
        received_at=now,
        sender="recruiter@stripe.com",
        recipients=["candidate@example.com"],
        subject="Interview Request - Stripe Staff Solutions Architect",
        body_text="Hi, we would like to schedule an initial interview for the Staff Solutions Architect role.",
    )

    adapter = MockEmailAdapter([interview_email])
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=adapter,
        candidate_emails=["candidate@example.com"],
    )

    results = daemon.run_sweep(reconcile=False)

    # Ingestion ran first and ingested the message
    assert results["messages_polled"] == 1
    assert results["messages_ingested"] == 1

    # Lifecycle processing ran on the freshly ingested message in the same sweep
    assert results["lifecycle_transitions"] >= 1

    # Verify message is persisted in DB
    with db_session_factory() as session:
        msg = session.scalars(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "msg-worker-order-1"
            )
        ).first()
        assert msg is not None
        assert msg.classification == "INTERVIEW_REQUEST"


def test_worker_reconciliation_not_every_sweep(
    db_session_factory: sessionmaker[Session],
) -> None:
    adapter = MockEmailAdapter([])
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=adapter,
        candidate_emails=["candidate@example.com"],
    )

    # Sweep 1: initial sweep performs reconciliation
    res1 = daemon.run_sweep()
    assert res1["reconciliation_performed"] is True

    # Sweep 2: immediately afterwards, reconciliation is False (24h haven't elapsed)
    res2 = daemon.run_sweep()
    assert res2["reconciliation_performed"] is False

    # Sweep 3: explicit reconcile=True overrides schedule
    res3 = daemon.run_sweep(reconcile=True)
    assert res3["reconciliation_performed"] is True


def test_worker_respects_kill_switch(
    db_session_factory: sessionmaker[Session],
) -> None:
    adapter = MockEmailAdapter([])
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=adapter,
    )

    os.environ["JOBS_AUTOMATION_KILL_SWITCH"] = "true"
    try:
        results = daemon.run_sweep()
        assert results["messages_polled"] == 0
        assert results["messages_ingested"] == 0
        assert results["lifecycle_transitions"] == 0
    finally:
        del os.environ["JOBS_AUTOMATION_KILL_SWITCH"]


def test_worker_gmail_failure_fails_closed_without_fixtures(
    db_session_factory: sessionmaker[Session],
) -> None:
    # Worker initialized without email_adapter will attempt GmailAdapter.
    # In this test environment, Gmail credentials do not exist.
    # It must fail closed, record error, and NOT write any mock fixtures to DB.
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=None,
    )

    results = daemon.run_sweep(reconcile=False)

    assert any("Gmail adapter unavailable" in err for err in results["errors"])
    assert results["messages_ingested"] == 0
    assert results["jobs_discovered"] == 0

    with db_session_factory() as session:
        messages = session.scalars(select(InboundMessageModel)).all()
        jobs = session.scalars(select(JobModel)).all()
        assert len(messages) == 0
        assert len(jobs) == 0


def test_worker_polling_exception_does_not_crash(
    db_session_factory: sessionmaker[Session],
) -> None:
    class FailingAdapter(EmailAdapter):
        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            raise TimeoutError("Network timeout connecting to mail server")

        def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
            return []

    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=FailingAdapter(),
        candidate_emails=["candidate@example.com"],
    )

    results = daemon.run_sweep()
    assert any("Network timeout" in err for err in results["errors"])
    assert results["messages_ingested"] == 0


def test_worker_reconciliation_remains_due_when_adapter_unavailable(
    db_session_factory: sessionmaker[Session],
) -> None:
    # When email adapter is unavailable, reconciliation must NOT be recorded as performed
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=None,
    )

    assert daemon.last_reconciliation_at is None
    res1 = daemon.run_sweep()
    assert res1["reconciliation_performed"] is False
    assert daemon.last_reconciliation_at is None

    # Next sweep without arguments must still attempt reconciliation
    res2 = daemon.run_sweep()
    assert res2["reconciliation_performed"] is False
    assert daemon.last_reconciliation_at is None


def test_worker_reconciliation_remains_due_when_polling_fails(
    db_session_factory: sessionmaker[Session],
) -> None:
    class FailingAdapter(EmailAdapter):
        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            raise ConnectionResetError("Connection lost during reconciliation")

        def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
            return []

    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=FailingAdapter(),
        candidate_emails=["candidate@example.com"],
    )

    assert daemon.last_reconciliation_at is None
    res1 = daemon.run_sweep()
    assert res1["reconciliation_performed"] is False
    assert daemon.last_reconciliation_at is None
    assert any("Connection lost" in err for err in res1["errors"])

    # Reconciliation remains due
    res2 = daemon.run_sweep()
    assert res2["reconciliation_performed"] is False
    assert daemon.last_reconciliation_at is None


def test_worker_begin_persistence_failure_fails_closed(
    db_session_factory: sessionmaker[Session],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A transient begin failure persists one safe FAILED record and never runs work."""
    now = datetime.datetime.now(datetime.UTC)
    with db_session_factory() as session:
        session.add_all(
            [
                AuditLogModel(
                    action_type="worker_run",
                    entity_type="worker",
                    actor="worker_daemon",
                    result="RUNNING",
                    external_reference="prior-success",
                    occurred_at=now - datetime.timedelta(minutes=11),
                    metadata_json={"run_id": "prior-success"},
                ),
                AuditLogModel(
                    action_type="worker_run_finished",
                    entity_type="worker",
                    actor="worker_daemon",
                    result="SUCCESS",
                    external_reference="prior-success",
                    occurred_at=now - datetime.timedelta(minutes=10),
                    metadata_json={
                        "run_id": "prior-success",
                        "final_status": "SUCCESS",
                        "error_count": 0,
                        "error_categories": [],
                        "sample_errors": [],
                    },
                ),
            ]
        )
        session.commit()

    class FailingSessionFactory:
        def __init__(self, real_factory: sessionmaker[Session]) -> None:
            self.real_factory = real_factory
            self.calls = 0

        def __call__(self) -> Session:
            self.calls += 1
            # First call is for begin record: simulate DB failure
            if self.calls == 1:
                raise RuntimeError("Database password=raw-secret-value during begin commit")
            return self.real_factory()

    class CountingAdapter(MockEmailAdapter):
        def __init__(self) -> None:
            super().__init__([])
            self.poll_calls = 0

        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            self.poll_calls += 1
            return super().poll_messages(query, since_timestamp, max_results)

    failing_factory = FailingSessionFactory(db_session_factory)
    adapter = CountingAdapter()
    daemon = WorkerDaemon(
        session_factory=failing_factory,
        poll_interval_seconds=60,
        email_adapter=adapter,
    )

    results = daemon.run_sweep()
    assert any("begin_record_failed" in err for err in results["errors"])
    assert results["messages_polled"] == 0
    assert results["messages_ingested"] == 0
    assert results["jobs_discovered"] == 0
    assert results["final_status"] == "FAILED"
    assert results["operational_evidence_durable"] is True
    assert results["warnings"] == []
    assert failing_factory.calls == 2
    assert adapter.poll_calls == 0

    with db_session_factory() as session:
        failed_finishes = session.scalars(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run_finished")
            .where(AuditLogModel.external_reference == results["run_id"])
        ).all()
        fabricated_begins = session.scalars(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run")
            .where(AuditLogModel.external_reference == results["run_id"])
        ).all()
        assert len(failed_finishes) == 1
        assert fabricated_begins == []
        failed = failed_finishes[0]
        assert failed.result == "FAILED"
        assert failed.metadata_json["run_id"] == results["run_id"]
        assert failed.metadata_json["started_at"]
        datetime.datetime.fromisoformat(failed.metadata_json["started_at"])
        assert failed.metadata_json["final_status"] == "FAILED"
        assert failed.metadata_json["error_count"] == 1
        assert failed.metadata_json["error_categories"] == ["BEGIN_RECORD_FAILED"]
        assert failed.metadata_json["sample_errors"] == [
            "begin_record_failed: operational evidence store unavailable"
        ]
        serialized = str(failed.metadata_json)
        assert "raw-secret-value" not in serialized
        assert "password=" not in serialized.lower()

    # A new health service reads only durable records after the failed process returns.
    health = HealthCheckService(db_session_factory).check_worker()
    assert health.status == "DEGRADED"
    assert health.details["last_attempt_status"] == "FAILED"
    assert health.details["last_error_category"] == "BEGIN_RECORD_FAILED"
    assert health.details["last_success_at"] is not None
    assert "raw-secret-value" not in caplog.text


def test_worker_begin_and_fallback_write_failure_is_explicitly_undurable(
    db_session_factory: sessionmaker[Session],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two evidence-write failures stop after one fallback and report undurable truth."""

    class TwoWriteFailures:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self) -> Session:
            self.calls += 1
            if self.calls <= 2:
                raise RuntimeError("session access_token=raw-secret-value unavailable")
            return db_session_factory()

    class ForbiddenAdapter(MockEmailAdapter):
        def __init__(self) -> None:
            super().__init__([])
            self.poll_calls = 0

        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            self.poll_calls += 1
            pytest.fail("pipeline must not poll after begin evidence failure")

    failing_factory = TwoWriteFailures()
    adapter = ForbiddenAdapter()
    results = WorkerDaemon(failing_factory, email_adapter=adapter).run_sweep(reconcile=False)

    assert results["final_status"] == "FAILED"
    assert results["operational_evidence_durable"] is False
    assert any("begin_record_failed" in error for error in results["errors"])
    assert results["warnings"]
    assert any("durable" in warning.lower() for warning in results["warnings"])
    assert failing_factory.calls == 2
    assert adapter.poll_calls == 0
    assert "raw-secret-value" not in str(results)
    assert "access_token=" not in str(results).lower()
    assert "raw-secret-value" not in caplog.text

    with db_session_factory() as session:
        assert session.scalars(select(AuditLogModel)).all() == []


def test_worker_distinct_run_ids_per_sweep(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Distinct sweeps have distinct unique run_ids."""
    adapter = MockEmailAdapter([])
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=adapter,
    )

    res1 = daemon.run_sweep()
    res2 = daemon.run_sweep()

    assert res1["run_id"] != res2["run_id"]

    with db_session_factory() as session:
        from jobs_automation.db.models import AuditLogModel

        runs = session.scalars(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run")
            .order_by(AuditLogModel.occurred_at.asc())
        ).all()
        assert len(runs) == 2
        assert runs[0].external_reference == res1["run_id"]
        assert runs[1].external_reference == res2["run_id"]


def test_worker_pipeline_rollback_preserves_run_evidence(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Pipeline exception and rollback cannot erase operational begin and finish audit evidence."""

    class CrashingEmailAdapter(EmailAdapter):
        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            raise ValueError("Critical unexpected parsing explosion")

        def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
            return []

    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=CrashingEmailAdapter(),
    )

    results = daemon.run_sweep()
    run_id = results["run_id"]
    assert any("Critical unexpected parsing explosion" in err for err in results["errors"])

    with db_session_factory() as session:
        from jobs_automation.db.models import AuditLogModel

        begin_audit = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert begin_audit is not None
        assert begin_audit.result == "RUNNING"

        finish_audit = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run_finished")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert finish_audit is not None
        assert finish_audit.result in ("PARTIAL", "FAILED")


def test_worker_error_sanitization_removes_secrets_and_categorizes(
    db_session_factory: sessionmaker[Session],
) -> None:
    """B-R20-05: Raw secrets, OAuth tokens, and passwords are sanitized in finalize records."""

    class SecretLeakingAdapter(EmailAdapter):
        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[RawEmailMessage]:
            raise RuntimeError(
                "OAuth failure with token ya29.a0AfH6SMBabc123456789xyz and Bearer my-secret-jwt-token"
            )

        def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
            return []

    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        email_adapter=SecretLeakingAdapter(),
    )

    results = daemon.run_sweep()
    run_id = results["run_id"]

    with db_session_factory() as session:
        from jobs_automation.db.models import AuditLogModel

        finish_audit = session.scalar(
            select(AuditLogModel)
            .where(AuditLogModel.action_type == "worker_run_finished")
            .where(AuditLogModel.external_reference == run_id)
        )
        assert finish_audit is not None
        meta = finish_audit.metadata_json
        sample_errors_str = " ".join(meta.get("sample_errors", []))

        # Secrets must be redacted
        assert "ya29.a0AfH6SMBabc123456789xyz" not in sample_errors_str
        assert "Bearer my-secret-jwt-token" not in sample_errors_str
        assert "[REDACTED_SECRET]" in sample_errors_str
        assert "GMAIL_AUTH_ERROR" in meta.get("error_categories", [])

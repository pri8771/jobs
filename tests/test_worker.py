"""Tests for background WorkerDaemon scheduling, ingestion call-order, and safety controls."""

from __future__ import annotations

import datetime
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
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


def test_worker_configured_canary_is_tagged_before_shared_lifecycle_pass(
    db_session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    """A scheduled worker must apply its durable canary policy before lifecycle work."""
    now = datetime.datetime.now(datetime.UTC)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "platforms.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "email:",
                "  provider: gmail",
                "  polling_minutes: 240",
                "  polling_policy: periodic",
                "  intended_interval_hours_min: 3",
                "  intended_interval_hours_max: 4",
                "  daily_reconciliation: true",
                "  realtime_push_required: false",
                "  readonly: true",
                "  canary_identities:",
                "    - Owner Alias <recruiter@stripe.com>",
                "platforms:",
                "  linkedin: {}",
                "  indeed: {}",
                "  ziprecruiter: {}",
                "  dice: {}",
                "gmail_queries: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with db_session_factory() as session:
        company = CompanyModel(normalized_name="stripe")
        session.add(company)
        session.flush()
        job = JobModel(
            company_id=company.id, normalized_title="Staff Solutions Architect", status="active"
        )
        session.add(job)
        session.flush()
        application = ApplicationModel(
            job_id=job.id,
            status="SUBMITTED",
            last_activity_at=now - datetime.timedelta(days=2),
        )
        session.add(application)
        session.commit()
        application_id = application.id
        activity_before = application.last_activity_at

    canary_email = RawEmailMessage(
        provider_message_id="worker-fresh-canary",
        provider_thread_id="worker-fresh-canary-thread",
        received_at=now,
        sender="recruiter@stripe.com",
        recipients=["candidate@example.com"],
        subject="Interview Request - Stripe Staff Solutions Architect",
        body_text="Please schedule an interview for the Staff Solutions Architect role.",
    )
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        config_dir=str(config_dir),
        email_adapter=MockEmailAdapter([canary_email]),
        candidate_emails=["candidate@example.com"],
    )

    result = daemon.run_sweep(reconcile=False)
    assert result["messages_ingested"] == 1
    assert result["lifecycle_transitions"] == 0
    assert result["unanswered_alerts"] == 0

    with db_session_factory() as session:
        message = session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "worker-fresh-canary"
            )
        )
        reloaded_application = session.get(ApplicationModel, application_id)
        assert message is not None
        assert (message.headers_json or {}).get("_provider", {}).get("canary") is True
        assert reloaded_application is not None
        assert reloaded_application.status == "SUBMITTED"
        assert reloaded_application.last_activity_at == activity_before
        assert session.scalars(select(MessageLinkModel)).all() == []
        assert session.scalars(select(ApplicationEventModel)).all() == []
        assert session.scalars(select(ContactModel)).all() == []
        assert session.scalars(select(InterviewModel)).all() == []
        assert (
            session.scalars(
                select(TaskModel).where(TaskModel.task_type != "email_checkpoint")
            ).all()
            == []
        )


def test_worker_reclassifies_historical_alias_before_lifecycle_without_a_poll(
    db_session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    """A policy added after ingestion must protect old linked rows on a worker sweep."""
    now = datetime.datetime.now(datetime.UTC)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "platforms.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "email:",
                "  provider: gmail",
                "  polling_minutes: 240",
                "  polling_policy: periodic",
                "  intended_interval_hours_min: 3",
                "  intended_interval_hours_max: 4",
                "  daily_reconciliation: true",
                "  realtime_push_required: false",
                "  readonly: true",
                "  canary_identities:",
                "    - Owner Alias <recruiter@stripe.com>",
                "platforms:",
                "  linkedin: {}",
                "  indeed: {}",
                "  ziprecruiter: {}",
                "  dice: {}",
                "gmail_queries: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with db_session_factory() as session:
        company = CompanyModel(normalized_name="stripe")
        session.add(company)
        session.flush()
        job = JobModel(company_id=company.id, normalized_title="Staff Solutions Architect")
        session.add(job)
        session.flush()
        application = ApplicationModel(
            job_id=job.id,
            status="SUBMITTED",
            last_activity_at=now,
        )
        session.add(application)
        session.flush()
        historical = InboundMessageModel(
            provider_message_id="worker-historical-canary",
            provider_thread_id="worker-historical-canary-thread",
            received_at=now,
            sender="Owner Alias <recruiter@stripe.com>",
            recipients_json=["candidate@example.com"],
            direction="inbound",
            subject="Interview Request",
            headers_json={},
            body_text="Please schedule an interview.",
            classification="INTERVIEW_REQUEST",
            confidence=0.99,
        )
        session.add(historical)
        session.flush()
        session.add(
            MessageLinkModel(
                inbound_message_id=historical.id,
                job_id=job.id,
                application_id=application.id,
                company_id=company.id,
                confidence=0.99,
                method="historical_fixture",
            )
        )
        application_id = application.id
        session.commit()

    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        config_dir=str(config_dir),
        email_adapter=MockEmailAdapter([]),
    )
    result = daemon.run_sweep(reconcile=False)

    assert result["canary_messages_reclassified"] == 1
    assert result["lifecycle_transitions"] == 0
    with db_session_factory() as session:
        reloaded_message = session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "worker-historical-canary"
            )
        )
        reloaded_application = session.get(ApplicationModel, application_id)
        assert reloaded_message is not None
        assert (reloaded_message.headers_json or {}).get("_provider", {}).get("canary") is True
        assert reloaded_application is not None
        assert reloaded_application.status == "SUBMITTED"
        assert session.scalars(select(ApplicationEventModel)).all() == []


def test_worker_does_not_ingest_when_present_canary_policy_config_is_invalid(
    db_session_factory: sessionmaker[Session], tmp_path: Path
) -> None:
    """A broken policy file must not silently disable tagging on a scheduled sweep."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "platforms.yaml").write_text(
        "version: 1\nemail: {}\nplatforms: {}\n", encoding="utf-8"
    )

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

    adapter = CountingAdapter()
    daemon = WorkerDaemon(
        session_factory=db_session_factory,
        poll_interval_seconds=60,
        config_dir=str(config_dir),
        email_adapter=adapter,
    )

    result = daemon.run_sweep(reconcile=False)

    assert adapter.poll_calls == 0
    assert result["messages_ingested"] == 0
    assert any("canary policy configuration unavailable" in error for error in result["errors"])


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
) -> None:
    """B-R20-05: Worker fails closed and does not execute pipeline if begin record cannot be persisted."""

    class FailingSessionFactory:
        def __init__(self, real_factory: sessionmaker[Session]) -> None:
            self.real_factory = real_factory
            self.calls = 0

        def __call__(self) -> Session:
            self.calls += 1
            # First call is for begin record: simulate DB failure
            if self.calls == 1:
                raise RuntimeError("Database disk full during begin record commit")
            return self.real_factory()

    failing_factory = FailingSessionFactory(db_session_factory)
    adapter = MockEmailAdapter([])
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
    # Pipeline did not execute further
    assert failing_factory.calls == 1


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

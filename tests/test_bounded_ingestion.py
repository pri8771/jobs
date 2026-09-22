"""V17-M04 / V17-R05: bounded, replayable ingestion runs through production services.

Uses the synthetic fixtures adapter (clearly labelled synthetic) to exercise the bounded
runner, the recorded evidence, canary exclusion, incomplete-poll handling, dry runs,
mailbox binding and replay idempotency, plus the installed ``ingest-mailbox`` and
``lifecycle-timeline`` entry points in separate processes (restart + replay).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Generator, Iterable
from email.utils import getaddresses
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import jobs_automation.ingestion.engine as ingestion_module
from jobs_automation.adapters.gmail import GmailAdapter, MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.db.session import get_engine, get_sessionmaker, init_db
from jobs_automation.ingestion.bounded import (
    BOUNDED_AUDIT_SCHEMA_VERSION,
    BOUNDED_RUN_ACTION,
    BoundedIngestionError,
    BoundedIngestionRequest,
    BoundedIngestionRunner,
    compute_logical_state_digests,
    is_valid_bounded_audit_metadata,
)
from jobs_automation.ingestion.fixtures import get_sample_email_fixtures
from jobs_automation.lifecycle.timeline import build_timeline_export, timeline_digest
from tests.test_gmail_adapter_bounded import (
    CANDIDATE,
    NOW,
    FakeGmailService,
    _five_messages,
    _message,
)
from tests.test_real_proof_verifier import engineering_profile_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MAILBOX = "priyansh.chordia@gmail.com"
WINDOW_START = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
WINDOW_END = datetime.datetime(2040, 1, 1, tzinfo=datetime.UTC)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed_application(session: Session, company_name: str = "Viatris") -> ApplicationModel:
    """An existing submitted application the fixture recruiter thread can link to."""
    company = CompanyModel(normalized_name=company_name)
    session.add(company)
    session.flush()
    job = JobModel(company_id=company.id, normalized_title="Solutions Architect", status="active")
    session.add(job)
    session.flush()
    app = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="assisted",
        destination_domain="boards.greenhouse.io",
        applied_at=datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC),
        last_activity_at=datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC),
    )
    session.add(app)
    session.commit()
    return app


def _request(**overrides: Any) -> BoundedIngestionRequest:
    base: dict[str, Any] = {
        "mailbox": MAILBOX,
        "query": "label:recruiting",
        "window_start": WINDOW_START,
        "window_end": WINDOW_END,
        "cap": 50,
    }
    base.update(overrides)
    return BoundedIngestionRequest(**base)


def _runner(session: Session, adapter: Any = None, **kwargs: Any) -> BoundedIngestionRunner:
    return BoundedIngestionRunner(
        session,
        adapter or MockEmailAdapter(get_sample_email_fixtures()),
        candidate_emails=[MAILBOX],
        canary_identities=kwargs.pop("canary_identities", []),
        adapter_kind=kwargs.pop("adapter_kind", "mock_fixtures"),
        synthetic=kwargs.pop("synthetic", True),
        identity={"git_sha": "engineering", "package_version": "0.1.0"},
    )


def _bind_bounded_audits_to_application(session: Session, application_id: object) -> None:
    """Model the secret-safe application association emitted by the bounded-run writer."""
    application_sha256 = hashlib.sha256(str(application_id).encode("utf-8")).hexdigest()
    audits = session.scalars(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    ).all()
    for audit in audits:
        audit.metadata_json = {
            **audit.metadata_json,
            "schema_version": BOUNDED_AUDIT_SCHEMA_VERSION,
            "application_id_sha256": [application_sha256],
        }
    session.commit()


def test_bounded_run_records_secret_free_evidence_and_does_not_move_checkpoint(
    db_session: Session,
) -> None:
    app = _seed_application(db_session)
    result = _runner(db_session).run(_request())
    assert result.status == "SUCCESS", result.errors
    assert result.complete is True
    assert result.messages_ingested == 7
    assert result.lifecycle_transitions == 2
    assert result.synthetic is True and result.adapter == "mock_fixtures"
    assert result.provider_query.startswith("label:recruiting before:")

    db_session.refresh(app)
    # The production classifier reads "available for a brief introductory call" as an
    # INTERVIEW_REQUEST; without an explicit schedule that also opens a human review task.
    assert app.status == "INTERVIEWING"
    events = db_session.scalars(
        select(ApplicationEventModel).where(ApplicationEventModel.application_id == app.id)
    ).all()
    event_types = [event.event_type for event in events]
    assert sorted(event_types) == ["CANDIDATE_REPLIED", "INTERVIEW_REQUESTED"]
    assert event_types.count("INTERVIEW_REQUESTED") == 1
    assert event_types.count("CANDIDATE_REPLIED") == 1
    review_tasks = db_session.scalars(
        select(TaskModel).where(TaskModel.task_type == "NEEDS_REVIEW")
    ).all()
    assert len(review_tasks) == 1
    # No incremental checkpoint was created by the bounded run.
    assert (
        db_session.scalar(select(TaskModel).where(TaskModel.task_type == "email_checkpoint"))
        is None
    )

    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None and audit.result == "SUCCESS"
    metadata = audit.metadata_json
    assert metadata["run_id"] == result.run_id
    assert metadata["mailbox_domain"] == "gmail.com"
    assert metadata["schema_version"] == BOUNDED_AUDIT_SCHEMA_VERSION
    assert is_valid_bounded_audit_metadata(metadata, external_reference=result.run_id)
    assert MAILBOX not in json.dumps(metadata)
    assert result.query not in json.dumps(metadata)
    assert result.provider_query not in json.dumps(metadata)
    assert "query" not in metadata and "provider_query" not in metadata
    assert metadata["digests_after"]["counts"]["messages"] == 7
    assert metadata["code_identity"]["git_sha"] == "engineering"
    assert metadata["poll"]["complete"] is True
    assert metadata["provider_message_id_sha256"] == sorted(
        hashlib.sha256(message_id.encode("utf-8")).hexdigest()
        for message_id in (
            "gmail_alert_linkedin_001",
            "gmail_alert_indeed_001",
            "gmail_alert_zip_001",
            "gmail_alert_dice_001",
            "gmail_recruiter_001",
            "gmail_candidate_001",
            "gmail_conf_001",
        )
    )
    assert metadata["application_id_sha256"] == [
        hashlib.sha256(str(app.id).encode("utf-8")).hexdigest()
    ]
    assert metadata["application_id_sha256"] == result.application_id_sha256
    assert metadata["provider_message_id_sha256"] == result.provider_message_id_sha256
    metadata_text = json.dumps(metadata, sort_keys=True)
    assert str(app.id) not in metadata_text
    assert all(
        raw_message_id not in metadata_text
        for raw_message_id in (
            "gmail_alert_linkedin_001",
            "gmail_alert_indeed_001",
            "gmail_alert_zip_001",
            "gmail_alert_dice_001",
            "gmail_recruiter_001",
            "gmail_candidate_001",
            "gmail_conf_001",
        )
    )


def test_replay_preserves_identical_logical_state(db_session: Session) -> None:
    _seed_application(db_session)
    runner = _runner(db_session)
    first = runner.run(_request())
    events_before = db_session.scalars(select(ApplicationEventModel)).all()
    tasks_before = db_session.scalars(select(TaskModel)).all()

    replay = runner.replay(first.run_id, _request(), allow_stateful_replay=True)
    assert replay.status == "SUCCESS", replay.errors
    assert replay.replay_of_run_id == first.run_id
    assert replay.messages_ingested == 0
    assert replay.messages_skipped_duplicate == 7
    assert replay.lifecycle_transitions == 0
    assert replay.replay_identical is True
    assert replay.replay_matches_original is True
    assert replay.digests_after == first.digests_after
    assert len(db_session.scalars(select(ApplicationEventModel)).all()) == len(events_before)
    assert len(db_session.scalars(select(TaskModel)).all()) == len(tasks_before)
    assert compute_logical_state_digests(db_session) == first.digests_after


def test_replay_rejects_wrong_mailbox_or_unknown_run(db_session: Session) -> None:
    runner = _runner(db_session)
    first = runner.run(_request())
    with pytest.raises(BoundedIngestionError, match="REPLAY_MAILBOX_MISMATCH"):
        runner.replay(
            first.run_id,
            _request(mailbox="someone.else@gmail.com"),
            allow_stateful_replay=True,
        )
    with pytest.raises(BoundedIngestionError, match="REPLAY_RUN_NOT_FOUND"):
        runner.replay(
            "00000000-0000-0000-0000-000000000000",
            _request(),
            allow_stateful_replay=True,
        )


def test_replay_rejects_legacy_audit_rows_without_safe_request_schema(db_session: Session) -> None:
    db_session.add(
        AuditLogModel(
            action_type=BOUNDED_RUN_ACTION,
            entity_type="mailbox",
            actor="legacy_test",
            result="SUCCESS",
            external_reference="legacy-run",
            metadata_json={"run_id": "legacy-run", "query": "raw legacy query"},
        )
    )
    db_session.commit()

    with pytest.raises(BoundedIngestionError, match="REPLAY_EVIDENCE_SCHEMA_UNSUPPORTED"):
        _runner(db_session).replay("legacy-run", _request(), allow_stateful_replay=True)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("schema_version", 2),
        ("run_id", "different-run-id"),
        ("provider_message_id_sha256", ["not-a-sha256"]),
        ("digests_after", {}),
        ("canary_policy_sha256", "not-a-sha256"),
    ],
)
def test_replay_rejects_malformed_v3_evidence_before_polling(
    db_session: Session, field: str, invalid_value: Any
) -> None:
    """Audit corruption must fail before a replay can touch the provider."""
    first = _runner(db_session).run(_request())
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.external_reference == first.run_id)
    )
    assert audit is not None
    audit.metadata_json = {**audit.metadata_json, field: invalid_value}
    db_session.commit()

    class CountingAdapter(MockEmailAdapter):
        def __init__(self) -> None:
            super().__init__(get_sample_email_fixtures())
            self.poll_calls = 0

        def poll_messages(
            self,
            query: str | None = None,
            since_timestamp: str | None = None,
            max_results: int = 100,
        ) -> list[Any]:
            self.poll_calls += 1
            return super().poll_messages(query, since_timestamp, max_results)

    adapter = CountingAdapter()
    runner = _runner(db_session, adapter=adapter)
    with pytest.raises(BoundedIngestionError, match="REPLAY_EVIDENCE_SCHEMA_UNSUPPORTED"):
        runner.replay(first.run_id, _request(), allow_stateful_replay=True)
    assert adapter.poll_calls == 0


def test_public_run_rejects_direct_replay_request_before_polling(db_session: Session) -> None:
    """Only the replay API may create a replay request and authorize its side effects."""
    first = _runner(db_session).run(_request())

    class TrapAdapter(MockEmailAdapter):
        def poll_messages(self, *args: Any, **kwargs: Any) -> list[Any]:
            raise AssertionError("direct replay request must not poll")

    with pytest.raises(BoundedIngestionError, match="REPLAY_MUST_USE_REPLAY_API"):
        _runner(db_session, adapter=TrapAdapter()).run(_request(replay_of_run_id=first.run_id))


def test_private_run_cannot_bypass_replay_authorization_before_polling(
    db_session: Session,
) -> None:
    """The implementation method itself cannot mint a stateful replay capability."""
    first = _runner(db_session).run(_request())

    class TrapAdapter(MockEmailAdapter):
        def poll_messages(self, *args: Any, **kwargs: Any) -> list[Any]:
            raise AssertionError("direct implementation replay must not poll")

    with pytest.raises(BoundedIngestionError, match="REPLAY_MUST_USE_REPLAY_API"):
        _runner(db_session, adapter=TrapAdapter())._run(_request(replay_of_run_id=first.run_id))


def test_replay_same_policy_rejects_currently_reclassified_canary_evidence(
    db_session: Session,
) -> None:
    """A durable canary tag invalidates old proof even when the replay policy is unchanged."""
    initial = _runner(db_session).run(_request())
    reclassifier = _runner(db_session, canary_identities=["sarah.connor@viatris.com"])
    reclassification = reclassifier.run(_request())
    assert reclassification.canary_messages == 2

    with pytest.raises(BoundedIngestionError, match="REPLAY_EVIDENCE_CANARY_RECLASSIFIED"):
        _runner(db_session).replay(initial.run_id, _request(dry_run=True))


def test_replay_accepts_semantically_equivalent_canary_policy_inputs(db_session: Session) -> None:
    """Display names, case, ordering, and duplicate aliases cannot cause false policy drift."""
    initial_runner = _runner(
        db_session,
        canary_identities=[
            "Owner <SARAH.CONNOR@VIATRIS.COM>",
            "other.alias@example.test",
            "sarah.connor@viatris.com",
        ],
    )
    initial = initial_runner.run(_request())

    equivalent_runner = _runner(
        db_session,
        canary_identities=[
            "other.alias@example.test",
            "Sarah Connor <sarah.connor@viatris.com>",
        ],
    )
    replay = equivalent_runner.replay(initial.run_id, _request(), allow_stateful_replay=True)

    assert replay.status == "SUCCESS", replay.errors
    assert replay.replay_identical is True
    assert replay.replay_matches_original is True


def test_cap_smaller_than_evidence_is_incomplete_and_recorded(db_session: Session) -> None:
    result = _runner(db_session).run(_request(cap=3))
    assert result.status == "FAILED"
    assert result.complete is False
    assert result.poll is not None and result.poll.truncated_by_cap is True
    assert result.messages_ingested == 0
    assert result.errors == ["POLL_INCOMPLETE"]
    assert db_session.scalars(select(InboundMessageModel)).all() == []
    assert db_session.scalars(select(TaskModel)).all() == []
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None and audit.result == "FAILED"
    assert audit.metadata_json["error_codes"] == ["POLL_INCOMPLETE"]


def test_dry_run_persists_no_messages_but_records_the_attempt(db_session: Session) -> None:
    result = _runner(db_session).run(_request(dry_run=True))
    assert result.status == "DRY_RUN"
    assert db_session.scalars(select(InboundMessageModel)).all() == []
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None and audit.result == "DRY_RUN"


class _ExplodingAdapter:
    """Deliberately emits sensitive-looking provider text to test audit redaction."""

    def poll_messages(
        self, query: str | None = None, since_timestamp: str | None = None, max_results: int = 100
    ) -> list[object]:
        raise RuntimeError("provider failure: token=not-for-audit; query=private recruiting")

    def get_thread(self, thread_id: str) -> list[object]:
        return []

    def last_poll_report(self) -> None:
        return None


def test_audit_metadata_redacts_raw_queries_and_provider_exception_text(
    db_session: Session,
) -> None:
    request = _request(query="from:private-recruiter@example.test")
    result = _runner(db_session, adapter=_ExplodingAdapter()).run(request)

    assert result.status == "FAILED"
    assert result.errors == ["INGESTION_ERROR"]
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None
    metadata_text = json.dumps(audit.metadata_json, sort_keys=True)
    assert request.query not in metadata_text
    assert result.provider_query not in metadata_text
    assert "token=not-for-audit" not in metadata_text
    assert "errors" not in audit.metadata_json
    assert audit.metadata_json["error_codes"] == ["INGESTION_ERROR"]
    assert (
        audit.metadata_json["query_sha256"]
        == hashlib.sha256(request.query.encode("utf-8")).hexdigest()
    )


def test_replay_requires_explicit_stateful_authorization_but_allows_safe_dry_override(
    db_session: Session,
) -> None:
    _seed_application(db_session)
    runner = _runner(db_session)
    first = runner.run(_request())

    with pytest.raises(
        BoundedIngestionError, match="REPLAY_STATEFUL_REQUIRES_EXPLICIT_AUTHORIZATION"
    ):
        runner.replay(first.run_id, _request())

    safe_replay = runner.replay(first.run_id, _request(dry_run=True))
    assert safe_replay.status == "DRY_RUN", safe_replay.errors
    assert safe_replay.dry_run is True
    assert safe_replay.replay_identical is True
    assert safe_replay.replay_matches_original is True


def test_recorded_dry_run_cannot_be_promoted_to_mutation_by_replay_override(
    db_session: Session,
) -> None:
    runner = _runner(db_session)
    original = runner.run(_request(dry_run=True))
    assert original.status == "DRY_RUN"
    assert db_session.scalars(select(InboundMessageModel)).all() == []

    replay = runner.replay(
        original.run_id,
        _request(dry_run=False),
        allow_stateful_replay=True,
    )
    assert replay.status == "DRY_RUN", replay.errors
    assert replay.dry_run is True
    assert replay.replay_identical is True
    assert replay.replay_matches_original is True
    assert db_session.scalars(select(InboundMessageModel)).all() == []


def test_replay_digest_mismatch_is_recorded_as_failed(db_session: Session) -> None:
    _seed_application(db_session)
    runner = _runner(db_session)
    original = runner.run(_request())
    db_session.add(
        InboundMessageModel(
            provider_message_id="unrelated-state-after-original",
            provider_thread_id="unrelated-state-thread",
            received_at=datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC),
            sender="unrelated@example.test",
            recipients_json=[MAILBOX],
            direction="inbound",
            subject="Unrelated state change",
            headers_json={},
            body_text="Not part of the replayed batch.",
            classification="UNKNOWN_REVIEW_REQUIRED",
            confidence=0.5,
        )
    )
    db_session.commit()

    replay = runner.replay(original.run_id, _request(), allow_stateful_replay=True)

    assert replay.replay_identical is True
    assert replay.replay_matches_original is False
    assert replay.status == "FAILED"
    assert "REPLAY_LOGICAL_STATE_MISMATCH" in replay.errors
    audit = db_session.scalar(
        select(AuditLogModel)
        .where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
        .order_by(AuditLogModel.occurred_at.desc())
    )
    assert audit is not None and audit.result == "FAILED"


def test_bounded_lifecycle_and_alerts_ignore_unrelated_historical_state(
    db_session: Session,
) -> None:
    _seed_application(db_session)  # the fixture's admitted Viatris application
    unrelated = _seed_application(db_session, company_name="Unrelated Employer")
    unrelated.last_activity_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
    old_rejection = InboundMessageModel(
        provider_message_id="unrelated-old-rejection",
        provider_thread_id="unrelated-rejection-thread",
        received_at=datetime.datetime(2020, 1, 2, tzinfo=datetime.UTC),
        sender="recruiter@unrelated.example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Application update",
        headers_json={},
        body_text="We will not be moving forward.",
        classification="REJECTION",
        confidence=0.99,
    )
    unrelated_outreach = InboundMessageModel(
        provider_message_id="unrelated-old-outreach",
        provider_thread_id="unrelated-alert-thread",
        received_at=datetime.datetime(2020, 1, 3, tzinfo=datetime.UTC),
        sender="recruiter@unrelated.example.test",
        recipients_json=[MAILBOX],
        direction="inbound",
        subject="Unrelated recruiter outreach",
        headers_json={},
        body_text="Would you like to talk?",
        classification="RECRUITER_OUTREACH",
        confidence=0.99,
    )
    unrelated_reply = InboundMessageModel(
        provider_message_id="unrelated-old-reply",
        provider_thread_id="unrelated-alert-thread",
        received_at=datetime.datetime(2020, 1, 4, tzinfo=datetime.UTC),
        sender=MAILBOX,
        recipients_json=["recruiter@unrelated.example.test"],
        direction="outbound",
        subject="Re: Unrelated recruiter outreach",
        headers_json={},
        body_text="Thank you.",
        classification="CANDIDATE_REPLY",
        confidence=0.99,
    )
    db_session.add_all([old_rejection, unrelated_outreach, unrelated_reply])
    db_session.flush()
    db_session.add(
        MessageLinkModel(
            inbound_message_id=old_rejection.id,
            application_id=unrelated.id,
            job_id=unrelated.job_id,
            confidence=0.99,
            method="historical_test_link",
        )
    )
    historical_alert = TaskModel(
        application_id=unrelated.id,
        job_id=unrelated.job_id,
        task_type="UNANSWERED_RECRUITER",
        status="pending",
        payload_json={
            "thread_id": unrelated_outreach.provider_thread_id,
            "message_id": str(unrelated_outreach.id),
        },
    )
    db_session.add(historical_alert)
    db_session.commit()

    result = _runner(db_session).run(_request())

    assert result.status == "SUCCESS", result.errors
    db_session.refresh(unrelated)
    db_session.refresh(historical_alert)
    assert unrelated.status == "SUBMITTED"
    assert historical_alert.status == "pending"
    assert (
        db_session.scalars(
            select(ApplicationEventModel).where(
                ApplicationEventModel.source_reference == old_rejection.provider_message_id
            )
        ).all()
        == []
    )
    assert hashlib.sha256(old_rejection.provider_message_id.encode("utf-8")).hexdigest() not in (
        result.provider_message_id_sha256
    )
    assert hashlib.sha256(str(unrelated.id).encode("utf-8")).hexdigest() not in (
        result.application_id_sha256
    )


def test_canary_mail_is_tagged_counted_and_excluded_from_lifecycle(db_session: Session) -> None:
    app = _seed_application(db_session)
    activity_before = app.last_activity_at
    # Treat the fixture recruiter as a canary alias: its mail must not move the application.
    result = _runner(db_session, canary_identities=["sarah.connor@viatris.com"]).run(_request())
    assert result.canary_messages == 2  # inbound recruiter + candidate reply in that thread
    assert result.application_id_sha256 == []
    canary_provider_hashes = {
        hashlib.sha256(message_id.encode()).hexdigest()
        for message_id in ("gmail_recruiter_001", "gmail_candidate_001")
    }
    assert canary_provider_hashes.isdisjoint(result.provider_message_id_sha256)
    db_session.refresh(app)
    assert app.status == "SUBMITTED"
    assert app.last_activity_at == activity_before
    assert result.lifecycle_transitions == 0
    assert (
        db_session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.application_id == app.id)
        ).all()
        == []
    )
    export = build_timeline_export(
        db_session, app.id, identity={"git_sha": "x", "package_version": "0"}
    )
    # Fresh canaries are quarantined before links or activity are created. They
    # therefore have no association with this application-scoped timeline.
    assert app.last_activity_at == activity_before
    assert (
        db_session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.application_id == app.id)
        ).all()
        == []
    )
    assert export["genuine_evidence"]["canary_excluded_count"] == 0
    assert export["genuine_evidence"]["source_count"] == 0
    canaries = db_session.scalars(
        select(InboundMessageModel).where(
            InboundMessageModel.provider_message_id.in_(
                ["gmail_recruiter_001", "gmail_candidate_001"]
            )
        )
    ).all()
    assert len(canaries) == 2
    assert all(message.headers_json["_provider"]["canary"] is True for message in canaries)
    assert all(
        not s["canary"] for s in export["sources"] if s["provider_message_id"] == "gmail_conf_001"
    )


def test_preexisting_canary_duplicates_are_reclassified_before_bounded_proof(
    db_session: Session,
) -> None:
    """A newly configured owner alias cannot inherit genuine proof from an older ingest."""

    app = _seed_application(db_session)
    initial = _runner(db_session).run(_request())
    assert initial.status == "SUCCESS", initial.errors

    result = _runner(
        db_session,
        canary_identities=["sarah.connor@viatris.com"],
    ).run(_request())

    # Retagging a historical source changes the durable logical state and removes
    # the source from all new bounded-proof associations.
    assert result.status == "SUCCESS", result.errors
    assert result.digests_after != initial.digests_after
    assert result.messages_ingested == 0
    assert result.messages_skipped_duplicate == 7
    assert result.canary_messages == 2
    canary_provider_hashes = {
        hashlib.sha256(message_id.encode("utf-8")).hexdigest()
        for message_id in ("gmail_recruiter_001", "gmail_candidate_001")
    }
    assert canary_provider_hashes.isdisjoint(result.provider_message_id_sha256)
    assert hashlib.sha256(str(app.id).encode("utf-8")).hexdigest() not in (
        result.application_id_sha256
    )
    for provider_message_id in ("gmail_recruiter_001", "gmail_candidate_001"):
        message = db_session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == provider_message_id
            )
        )
        assert message is not None
        assert (message.headers_json or {}).get("_provider", {}).get("canary") is True

    # A replay's policy is an evidence boundary.  A dry-run replay with a newly
    # supplied canary alias must fail before polling instead of claiming identical
    # logical state after excluding sources from the original proof.
    with pytest.raises(BoundedIngestionError, match="REPLAY_CANARY_POLICY_MISMATCH"):
        _runner(
            db_session,
            canary_identities=["sarah.connor@viatris.com"],
        ).replay(initial.run_id, _request(dry_run=True))


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "HELD DEPENDENCY: application-bound timeline replay selection needs the canary-side "
        "lifecycle/timeline.py + db/canary_provenance.py composition (not released in COMP-3A)"
    ),
)
def test_fresh_canary_run_is_not_application_timeline_replay(db_session: Session) -> None:
    app = _seed_application(db_session)
    result = _runner(db_session, canary_identities=["sarah.connor@viatris.com"]).run(_request())
    assert result.status == "SUCCESS", result.errors
    assert result.application_id_sha256 == []
    export = build_timeline_export(
        db_session, app.id, identity={"git_sha": "x", "package_version": "0"}
    )
    # A canary-only run never binds to this application, so it is not its replay evidence.
    assert export["replay"] is None


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "HELD DEPENDENCY: reclassified-canary timeline exclusion needs the canary-side "
        "lifecycle/timeline.py + db/canary_provenance.py composition (not released in COMP-3A)"
    ),
)
def test_reclassified_canary_audit_is_not_timeline_replay_evidence(db_session: Session) -> None:
    app = _seed_application(db_session)
    initial = _runner(db_session).run(_request())
    assert initial.status == "SUCCESS", initial.errors
    result = _runner(db_session, canary_identities=["sarah.connor@viatris.com"]).run(_request())
    assert result.status == "SUCCESS", result.errors

    export = build_timeline_export(
        db_session, app.id, identity={"git_sha": "x", "package_version": "0"}
    )
    assert export["genuine_evidence"]["canary_excluded_count"] >= 2
    assert export["genuine_evidence"]["source_count"] == 0
    # The old application-bound audit and its lifecycle rows are no longer evidence
    # after their provider sources are reclassified as canary traffic.
    assert export["replay"] is None
    assert export["events"] == []
    assert export["tasks"] == []
    assert export["contacts"] == []
    assert export["uncertainty"]["canary_lifecycle_events_excluded"] >= 1
    assert export["uncertainty"]["canary_lifecycle_tasks_excluded"] >= 1
    assert export["uncertainty"]["canary_message_links_excluded"] >= 1
    assert export["uncertainty"]["canary_lifecycle_state_requires_reconciliation"] is True


def test_dry_run_duplicate_canaries_never_enter_result_or_audit_hashes(
    db_session: Session,
) -> None:
    """Rollback must not turn a transient canary tag back into genuine dry-run evidence."""

    app = _seed_application(db_session)
    initial = _runner(db_session).run(_request())
    assert initial.status == "SUCCESS", initial.errors

    result = _runner(
        db_session,
        canary_identities=["sarah.connor@viatris.com"],
    ).run(_request(dry_run=True))

    assert result.status == "DRY_RUN", result.errors
    assert result.canary_messages == 2
    assert result.digests_before == result.digests_after
    canary_provider_hashes = {
        hashlib.sha256(message_id.encode("utf-8")).hexdigest()
        for message_id in ("gmail_recruiter_001", "gmail_candidate_001")
    }
    application_hash = hashlib.sha256(str(app.id).encode("utf-8")).hexdigest()
    assert canary_provider_hashes.isdisjoint(result.provider_message_id_sha256)
    assert application_hash not in result.application_id_sha256

    audit = db_session.scalars(
        select(AuditLogModel)
        .where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
        .order_by(AuditLogModel.occurred_at.desc())
    ).first()
    assert audit is not None and audit.result == "DRY_RUN"
    metadata = audit.metadata_json
    assert canary_provider_hashes.isdisjoint(metadata["provider_message_id_sha256"])
    assert application_hash not in metadata["application_id_sha256"]
    # The dry run is nonpersistent even though its result uses the in-run canary set.
    for provider_message_id in ("gmail_recruiter_001", "gmail_candidate_001"):
        message = db_session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == provider_message_id
            )
        )
        assert message is not None
        assert (message.headers_json or {}).get("_provider", {}).get("canary") is not True


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"mailbox": "not-an-address"}, "MAILBOX_REQUIRED"),
        ({"query": "   "}, "QUERY_REQUIRED"),
        ({"window_start": WINDOW_END, "window_end": WINDOW_START}, "WINDOW_EMPTY"),
        ({"window_start": WINDOW_START.replace(tzinfo=None)}, "WINDOW_MUST_BE_TIMEZONE_AWARE"),
    ],
)
def test_invalid_requests_are_rejected_before_any_access(
    db_session: Session, overrides: dict[str, Any], code: str
) -> None:
    with pytest.raises(BoundedIngestionError, match=code):
        _runner(db_session).run(_request(**overrides))
    assert db_session.scalars(select(AuditLogModel)).all() == []


def test_cap_outside_bounds_is_rejected() -> None:
    with pytest.raises(ValueError):
        _request(cap=0)
    with pytest.raises(ValueError):
        _request(cap=501)


def test_live_adapter_must_be_bound_to_the_named_mailbox(db_session: Session) -> None:
    service = FakeGmailService(_five_messages(), profile_address=CANDIDATE)
    adapter = GmailAdapter(service=service, verified_identities=[CANDIDATE])
    runner = _runner(db_session, adapter=adapter, adapter_kind="gmail", synthetic=False)
    with pytest.raises(BoundedIngestionError, match="MAILBOX_MISMATCH"):
        runner.run(_request(mailbox="other.person@invalid"))
    assert service.list_calls == []  # nothing was polled

    result = runner.run(_request(mailbox=CANDIDATE, cap=10))
    assert result.status == "SUCCESS", result.errors
    assert result.synthetic is False and result.adapter == "gmail"
    assert result.messages_ingested == 5


def test_mailbox_mismatch_leaves_no_durable_canary_reclassification(db_session: Session) -> None:
    """A run the bound adapter cannot serve must not commit historical canary tags."""
    _seed_application(db_session)
    assert _runner(db_session).run(_request()).status == "SUCCESS"
    service = FakeGmailService(_five_messages(), profile_address=CANDIDATE)
    adapter = GmailAdapter(service=service, verified_identities=[CANDIDATE])
    runner = _runner(
        db_session,
        adapter=adapter,
        adapter_kind="gmail",
        synthetic=False,
        canary_identities=["sarah.connor@viatris.com"],
    )
    with pytest.raises(BoundedIngestionError, match="MAILBOX_MISMATCH"):
        runner.run(_request(mailbox="other.person@invalid"))
    assert service.list_calls == []
    db_session.expire_all()
    for provider_message_id in ("gmail_recruiter_001", "gmail_candidate_001"):
        message = db_session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == provider_message_id
            )
        )
        assert message is not None
        assert not (message.headers_json or {}).get("_provider", {}).get("canary")


def test_timeline_export_is_redacted_and_digest_stable(db_session: Session) -> None:
    app = _seed_application(db_session)
    _runner(db_session).run(_request())
    _bind_bounded_audits_to_application(db_session, app.id)
    identity = {"git_sha": "engineering", "package_version": "0.1.0"}
    export = build_timeline_export(db_session, app.id, identity=identity)
    again = build_timeline_export(db_session, app.id, identity=identity)
    assert export["export_sha256"] == again["export_sha256"] == timeline_digest(export)
    serialized = json.dumps(export)
    assert "sarah.connor" not in serialized
    assert "Solutions Architecture Opportunity" not in serialized
    assert "impressed" not in serialized  # no body text
    assert export["application"]["status"] == "INTERVIEWING"
    by_id = {s["provider_message_id"]: s for s in export["sources"]}
    assert set(by_id) == {"gmail_recruiter_001", "gmail_candidate_001"}
    assert by_id["gmail_recruiter_001"]["link_method"] == "company_match"
    assert by_id["gmail_recruiter_001"]["direction"] == "inbound"
    assert by_id["gmail_candidate_001"]["link_method"] == "thread_reply_attribution"
    assert by_id["gmail_candidate_001"]["direction"] == "outbound"
    assert {event["event_type"] for event in export["events"]} == {
        "INTERVIEW_REQUESTED",
        "CANDIDATE_REPLIED",
    }
    assert export["uncertainty"]["pending_review_tasks"] == 1
    assert export["genuine_evidence"] == {
        "source_count": 2,
        "canary_excluded_count": 0,
        "inbound_count": 1,
        "outbound_count": 1,
    }
    assert export["replay"]["status"] == "SUCCESS" and export["replay"]["synthetic"] is True
    assert export["logical_state_digests"]["counts"]["messages"] == 7


def _run_cli(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from jobs_automation.cli.main import cli; sys.exit(cli())",
            *args,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _installed_bounded_setup(
    tmp_path: Path,
) -> tuple[Path, str, dict[str, str], str, list[str]]:
    """Private config + sqlite DB + seeded application for installed entrypoint runs."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    resume = tmp_path / "resume_ai_software_engineer.md"
    resume.write_text("# resume\n", encoding="utf-8")
    profile_yaml = engineering_profile_yaml(resume.resolve()).replace(
        'email: "engineering-candidate@invalid"', f'email: "{MAILBOX}"'
    )
    (config_dir / "candidate_profile.yaml").write_text(profile_yaml, encoding="utf-8")
    (config_dir / "platforms.yaml").write_text(
        (REPO_ROOT / "config" / "platforms.example.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    db_url = f"sqlite:///{tmp_path / 'bounded.db'}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    with get_sessionmaker(engine)() as session:
        app = _seed_application(session)
        app_id = str(app.id)
    engine.dispose()
    env = {**os.environ, "DATABASE_URL": db_url}
    common = [
        "ingest-mailbox",
        "--mailbox",
        MAILBOX,
        "--query",
        "label:recruiting",
        "--window-start",
        "2020-01-01T00:00:00Z",
        "--window-end",
        "2040-01-01T00:00:00Z",
        "--cap",
        "50",
        "--mock-fixtures",
        "--config-dir",
        str(config_dir),
    ]
    return config_dir, db_url, env, app_id, common


def _installed_first_run(common: list[str], env: dict[str, str]) -> str:
    first = _run_cli(common, env)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "SYNTHETIC ENGINEERING RUN" in first.stdout
    run_id_match = re.search(r"Run ID\s*│?\s*([0-9a-f-]{36})", first.stdout)
    assert run_id_match is not None, first.stdout
    return run_id_match.group(1)


def test_installed_entrypoints_run_restart_and_timeline_bounded_batch(tmp_path: Path) -> None:
    """Enforced legs: installed run, then separate-process DB readback and timeline CLI."""
    _, db_url, env, app_id, common = _installed_bounded_setup(tmp_path)
    run_id = _installed_first_run(common, env)

    engine = get_engine(db_url)
    try:
        with get_sessionmaker(engine)() as session:
            runs = session.scalars(
                select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
            ).all()
            assert len(runs) == 1
            assert is_valid_bounded_audit_metadata(
                runs[0].metadata_json, external_reference=runs[0].metadata_json["run_id"]
            )
            events = session.scalars(select(ApplicationEventModel)).all()
            event_types = [event.event_type for event in events]
            assert sorted(event_types) == ["CANDIDATE_REPLIED", "INTERVIEW_REQUESTED"]
            application = session.get(ApplicationModel, uuid.UUID(app_id))
            assert application is not None and application.status == "INTERVIEWING"
            _bind_bounded_audits_to_application(session, app_id)
    finally:
        engine.dispose()

    export_path = tmp_path / "timeline.json"
    timeline = _run_cli(
        ["lifecycle-timeline", "--application-id", app_id, "--json-output", str(export_path)], env
    )
    assert timeline.returncode == 0, timeline.stdout + timeline.stderr
    assert "INTERVIEWING" in timeline.stdout
    export = json.loads(export_path.read_text(encoding="utf-8"))
    assert export["application"]["id"] == app_id
    assert export["application"]["status"] == "INTERVIEWING"
    assert export["genuine_evidence"]["source_count"] == 2
    assert "sarah.connor" not in export_path.read_text(encoding="utf-8")

    # A replay must choose --dry-run or explicit --apply-replay; otherwise the installed
    # entrypoint fails closed before any config, database or provider access.
    ambiguous_replay = _run_cli([*common, "--replay-run", run_id], env)
    assert ambiguous_replay.returncode == 1, ambiguous_replay.stdout + ambiguous_replay.stderr
    assert "replay requires --dry-run" in ambiguous_replay.stdout + ambiguous_replay.stderr
    engine = get_engine(db_url)
    try:
        with get_sessionmaker(engine)() as session:
            audits = session.scalars(
                select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
            ).all()
            assert len(audits) == 1
    finally:
        engine.dispose()


def test_installed_entrypoints_restart_and_replay_bounded_batch(tmp_path: Path) -> None:
    """Separate processes: run, restart, replay, inspect — identical logical state."""
    config_dir, db_url, env, app_id, common = _installed_bounded_setup(tmp_path)
    run_id = _installed_first_run(common, env)

    replay = _run_cli(
        [
            "ingest-mailbox",
            "--mailbox",
            MAILBOX,
            "--query",
            "label:recruiting",
            "--window-start",
            "2020-01-01",
            "--window-end",
            "2040-01-01",
            "--cap",
            "50",
            "--mock-fixtures",
            "--replay-run",
            run_id,
            "--apply-replay",
            "--config-dir",
            str(config_dir),
        ],
        env,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert "Replay identical" in replay.stdout and "True" in replay.stdout

    engine = get_engine(db_url)
    try:
        with get_sessionmaker(engine)() as session:
            runs = session.scalars(
                select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
            ).all()
            assert len(runs) == 2
            replay_meta = next(
                r.metadata_json for r in runs if r.metadata_json.get("replay_of_run_id")
            )
            assert replay_meta["replay_identical"] is True
            assert replay_meta["replay_matches_original"] is True
            assert replay_meta["messages_ingested"] == 0
            events = session.scalars(select(ApplicationEventModel)).all()
            event_types = [event.event_type for event in events]
            assert sorted(event_types) == ["CANDIDATE_REPLIED", "INTERVIEW_REQUESTED"]
            assert event_types.count("INTERVIEW_REQUESTED") == 1
            assert event_types.count("CANDIDATE_REPLIED") == 1
            application = session.get(ApplicationModel, uuid.UUID(app_id))
            assert application is not None and application.status == "INTERVIEWING"
            _bind_bounded_audits_to_application(session, app_id)
    finally:
        engine.dispose()

    export_path = tmp_path / "timeline.json"
    timeline = _run_cli(
        ["lifecycle-timeline", "--application-id", app_id, "--json-output", str(export_path)], env
    )
    assert timeline.returncode == 0, timeline.stdout + timeline.stderr
    assert "INTERVIEWING" in timeline.stdout
    export = json.loads(export_path.read_text(encoding="utf-8"))
    assert export["application"]["id"] == app_id
    assert export["application"]["status"] == "INTERVIEWING"
    assert export["genuine_evidence"]["source_count"] == 2
    assert export["replay"]["replay_identical"] is True
    assert "sarah.connor" not in export_path.read_text(encoding="utf-8")


def test_replay_canonicalizes_policy_before_any_poll_of_legacy_canary(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = ["Owner <OWNER+CANARY@example.com>"]
    payload = _message(
        "legacy-missed-canary",
        sender="a@b.com;c@d.com",
        to="owner+canary@example.com",
        subject="Recruiter followup",
        body="Can we discuss this role?",
        internal=NOW,
    )
    service = FakeGmailService([payload])
    adapter = GmailAdapter(service=service)
    request = _request(mailbox=CANDIDATE)

    # Produce a writer-shaped historical audit with the actual pre-repair parser.
    # Its unchanged policy fingerprint must not authorize a new mailbox poll.
    def legacy_addresses(values: Iterable[object]) -> set[str]:
        return {
            address.strip().lower()
            for _, address in getaddresses([str(value) for value in values if value])
            if "@" in address and address.strip()
        }

    with monkeypatch.context() as historical:
        historical.setattr(ingestion_module, "canonical_email_addresses", legacy_addresses)
        initial = BoundedIngestionRunner(
            db_session, adapter, canary_identities=policy, synthetic=True
        ).run(request)
    assert initial.status == "SUCCESS"
    assert initial.canary_messages == 0
    calls_before = len(service.list_calls)
    runner = BoundedIngestionRunner(db_session, adapter, canary_identities=policy, synthetic=True)
    assert runner.canary_policy_sha256 == initial.canary_policy_sha256
    with pytest.raises(BoundedIngestionError, match="REPLAY_EVIDENCE_CANARY_RECLASSIFIED"):
        runner.replay(initial.run_id, request, allow_stateful_replay=True)
    assert len(service.list_calls) == calls_before

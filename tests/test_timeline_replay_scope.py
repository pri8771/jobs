"""V17-R04: application-scoped, secret-safe bounded-run timeline evidence."""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.models import (
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    JobModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.bounded import BOUNDED_AUDIT_SCHEMA_VERSION, BOUNDED_RUN_ACTION
from jobs_automation.lifecycle.timeline import build_timeline_export

_EMPTY_CANARY_POLICY_SHA256 = hashlib.sha256(b"[]").hexdigest()
_DIGEST_FIELDS = ("messages", "links", "events", "tasks", "interviews", "contacts")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _empty_digests() -> dict[str, Any]:
    return {
        **{field: _sha256(f"empty:{field}") for field in _DIGEST_FIELDS},
        "counts": {field: 0 for field in _DIGEST_FIELDS},
    }


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed_application(session: Session, company_name: str) -> ApplicationModel:
    company = CompanyModel(normalized_name=company_name)
    session.add(company)
    session.flush()
    job = JobModel(
        company_id=company.id, normalized_title="Scoped Timeline Engineer", status="active"
    )
    session.add(job)
    session.flush()
    application = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="assisted",
        destination_domain="boards.example.invalid",
    )
    session.add(application)
    session.commit()
    return application


def _application_sha256(application_id: uuid.UUID) -> str:
    return hashlib.sha256(str(application_id).encode("utf-8")).hexdigest()


def _record_bounded_audit(
    session: Session,
    *,
    run_id: str,
    occurred_at: datetime.datetime,
    application_ids: list[uuid.UUID] | None,
    schema_version: int | None = BOUNDED_AUDIT_SCHEMA_VERSION,
    replay_of_run_id: str | None = None,
    replay_identical: bool | None = None,
    replay_matches_original: bool | None = None,
    canary_policy_sha256: str | None = _EMPTY_CANARY_POLICY_SHA256,
) -> None:
    window_start = datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC)
    window_end = datetime.datetime(2026, 10, 1, tzinfo=datetime.UTC)
    mailbox_sha256 = _sha256("candidate@example.test")
    query_sha256 = _sha256("label:recruiting")
    provider_query_sha256 = _sha256(f"label:recruiting before:{int(window_end.timestamp())}")
    immutable_request = {
        "mailbox_sha256": mailbox_sha256,
        "query_sha256": query_sha256,
        "provider_query_sha256": provider_query_sha256,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "cap": 50,
    }
    started_at = occurred_at.astimezone(datetime.UTC)
    finished_at = started_at + datetime.timedelta(seconds=1)
    metadata: dict[str, Any] = {
        "run_id": run_id,
        "status": "SUCCESS",
        "adapter": "mock_fixtures",
        "synthetic": True,
        "mailbox_sha256": mailbox_sha256,
        "mailbox_domain": "example.test",
        "request_sha256": _sha256(
            json.dumps(immutable_request, sort_keys=True, separators=(",", ":"))
        ),
        "query_sha256": query_sha256,
        "provider_query_sha256": provider_query_sha256,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "cap": 50,
        "dry_run": False,
        "run_label_sha256": None,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "poll": {
            "adapter": "mock",
            "synthetic": True,
            "max_results": 50,
            "pages_fetched": 1,
            "listed_count": 0,
            "fetched_count": 0,
            "missing_message_count": 0,
            "truncated_by_cap": False,
            "complete": True,
        },
        "complete": True,
        "messages_polled": 0,
        "messages_ingested": 0,
        "messages_skipped_duplicate": 0,
        "canary_messages": 0,
        "review_tasks_created": 0,
        "lifecycle_transitions": 0,
        "interviews_scheduled": 0,
        "unanswered_alerts": 0,
        "stale_alerts": 0,
        "digests_before": _empty_digests(),
        "digests_after": _empty_digests(),
        "replay_of_run_id": replay_of_run_id,
        "replay_identical": replay_identical,
        "replay_matches_original": replay_matches_original,
        "error_codes": [],
        "code_identity": {"git_sha": "engineering", "package_version": "0.1.0"},
        "provider_message_id_sha256": [],
        "application_id_sha256": [],
    }
    if schema_version is not None:
        metadata["schema_version"] = schema_version
    if canary_policy_sha256 is not None:
        metadata["canary_policy_sha256"] = canary_policy_sha256
    if application_ids is not None:
        metadata["application_id_sha256"] = sorted(
            _application_sha256(application_id) for application_id in application_ids
        )
    session.add(
        AuditLogModel(
            action_type=BOUNDED_RUN_ACTION,
            entity_type="mailbox",
            actor="bounded_ingestion",
            result="SUCCESS",
            external_reference=run_id,
            occurred_at=occurred_at,
            metadata_json=metadata,
        )
    )
    session.commit()


def test_timeline_replay_is_null_for_legacy_or_other_application_batches(
    db_session: Session,
) -> None:
    application = _seed_application(db_session, "Target Company")
    other_application = _seed_application(db_session, "Other Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="legacy-no-association",
        occurred_at=start,
        application_ids=None,
    )
    _record_bounded_audit(
        db_session,
        run_id="legacy-associated-without-schema-version",
        occurred_at=start + datetime.timedelta(seconds=30),
        application_ids=[application.id],
        schema_version=None,
    )
    _record_bounded_audit(
        db_session,
        run_id="legacy-v2-associated-batch",
        occurred_at=start + datetime.timedelta(seconds=45),
        application_ids=[application.id],
        schema_version=2,
    )
    _record_bounded_audit(
        db_session,
        run_id="other-application-batch",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[other_application.id],
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is None


def test_timeline_selects_the_latest_audit_for_its_own_application(db_session: Session) -> None:
    application = _seed_application(db_session, "Target Company")
    other_application = _seed_application(db_session, "Other Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="target-application-batch",
        occurred_at=start,
        application_ids=[application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="other-application-batch",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[other_application.id],
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is not None
    assert export["replay"]["run_id"] == "target-application-batch"


def test_replay_requires_an_associated_original_audit(db_session: Session) -> None:
    application = _seed_application(db_session, "Target Company")
    other_application = _seed_application(db_session, "Other Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="original-for-other-application",
        occurred_at=start,
        application_ids=[other_application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="replay-claiming-target-application",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
        replay_of_run_id="original-for-other-application",
        replay_identical=True,
        replay_matches_original=True,
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is None


@pytest.mark.parametrize(
    ("replay_identical", "replay_matches_original"),
    [(False, True), (True, False)],
)
def test_replay_requires_true_comparison_flags(
    db_session: Session, replay_identical: bool, replay_matches_original: bool
) -> None:
    application = _seed_application(db_session, "Target Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="original-target-application",
        occurred_at=start,
        application_ids=[application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="replay-target-application",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
        replay_of_run_id="original-target-application",
        replay_identical=replay_identical,
        replay_matches_original=replay_matches_original,
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is None


def test_associated_successful_replay_is_exported(db_session: Session) -> None:
    application = _seed_application(db_session, "Target Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="original-target-application",
        occurred_at=start,
        application_ids=[application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="replay-target-application",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
        replay_of_run_id="original-target-application",
        replay_identical=True,
        replay_matches_original=True,
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is not None
    assert export["replay"]["run_id"] == "replay-target-application"
    assert export["replay"]["replay_of_run_id"] == "original-target-application"
    assert export["replay"]["replay_identical"] is True
    assert export["replay"]["replay_matches_original"] is True


@pytest.mark.parametrize("invalid_policy", [None, "not-a-sha256", "A" * 64])
def test_timeline_rejects_latest_audit_without_canonical_canary_policy(
    db_session: Session, invalid_policy: str | None
) -> None:
    application = _seed_application(db_session, "Target Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="older-valid-audit",
        occurred_at=start,
        application_ids=[application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="latest-unbound-audit",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
        canary_policy_sha256=invalid_policy,
    )

    export = build_timeline_export(db_session, application.id)

    # Do not silently fall back to older proof when the newest association is malformed.
    assert export["replay"] is None


def test_timeline_rejects_replay_when_canary_policy_differs_from_original(
    db_session: Session,
) -> None:
    application = _seed_application(db_session, "Target Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    changed_policy = hashlib.sha256(b'["owner-alias@example.test"]').hexdigest()
    _record_bounded_audit(
        db_session,
        run_id="original-target-application",
        occurred_at=start,
        application_ids=[application.id],
    )
    _record_bounded_audit(
        db_session,
        run_id="replay-with-different-policy",
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
        replay_of_run_id="original-target-application",
        replay_identical=True,
        replay_matches_original=True,
        canary_policy_sha256=changed_policy,
    )

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is None


@pytest.mark.parametrize(
    "corruption",
    [
        "bare_application_hash",
        "request_hash",
        "missing_started_at",
        "extra_metadata_field",
        "noncanonical_provider_hashes",
        "incomplete_poll",
        "mismatched_run_id",
    ],
)
def test_timeline_rejects_noncanonical_v3_writer_shape_without_falling_back(
    db_session: Session, corruption: str
) -> None:
    """A malformed latest association cannot surface itself or resurrect older proof."""
    application = _seed_application(db_session, "Target Company")
    start = datetime.datetime(2026, 9, 22, tzinfo=datetime.UTC)
    _record_bounded_audit(
        db_session,
        run_id="older-valid-audit",
        occurred_at=start,
        application_ids=[application.id],
    )
    latest_run_id = "latest-malformed-audit"
    _record_bounded_audit(
        db_session,
        run_id=latest_run_id,
        occurred_at=start + datetime.timedelta(minutes=1),
        application_ids=[application.id],
    )
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.external_reference == latest_run_id)
    )
    assert audit is not None
    metadata = dict(audit.metadata_json)
    application_hash = _application_sha256(application.id)
    if corruption == "bare_application_hash":
        metadata["application_id_sha256"] = application_hash
    elif corruption == "request_hash":
        metadata["request_sha256"] = "0" * 64
    elif corruption == "missing_started_at":
        metadata.pop("started_at")
    elif corruption == "extra_metadata_field":
        metadata["unexpected"] = "not writer shaped"
    elif corruption == "noncanonical_provider_hashes":
        metadata["provider_message_id_sha256"] = ["b" * 64, "a" * 64]
    elif corruption == "incomplete_poll":
        metadata["poll"] = {"complete": True}
    elif corruption == "mismatched_run_id":
        metadata["run_id"] = "different-run-id"
    else:  # pragma: no cover - exhaustive parameterization guard
        raise AssertionError(corruption)
    audit.metadata_json = metadata
    db_session.commit()

    export = build_timeline_export(db_session, application.id)

    assert export["replay"] is None

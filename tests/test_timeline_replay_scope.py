"""V17-R04: application-scoped, secret-safe bounded-run timeline evidence."""

from __future__ import annotations

import datetime
import hashlib
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.models import (
    ApplicationModel,
    AuditLogModel,
    CompanyModel,
    JobModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.bounded import BOUNDED_RUN_ACTION
from jobs_automation.lifecycle.timeline import build_timeline_export


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
    job = JobModel(company_id=company.id, normalized_title="Scoped Timeline Engineer", status="active")
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
    schema_version: int | None = 2,
    replay_of_run_id: str | None = None,
    replay_identical: bool | None = None,
    replay_matches_original: bool | None = None,
) -> None:
    metadata: dict[str, Any] = {
        "run_id": run_id,
        "status": "SUCCESS",
        "adapter": "mock_fixtures",
        "synthetic": True,
        "complete": True,
        "replay_of_run_id": replay_of_run_id,
        "replay_identical": replay_identical,
        "replay_matches_original": replay_matches_original,
    }
    if schema_version is not None:
        metadata["schema_version"] = schema_version
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

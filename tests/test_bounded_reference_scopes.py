"""Engineering-only reference semantics; not accepted-source composition or live proof."""

from __future__ import annotations

import datetime
import hashlib
from typing import Any

import pytest
from sqlalchemy.orm import Session

from jobs_automation.db.models import InboundMessageModel, MessageLinkModel
from jobs_automation.ingestion.engine import EmailIngestionEngine, IngestionSweepSummary
from jobs_automation.ingestion.models import PollReport
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.engine import LifecycleEngine
from tests.test_bounded_ingestion import _request, _runner, _seed_application, db_session

__all__ = ["db_session"]


def _message(
    session: Session, name: str, *, job_alert: bool = False, canary: bool = False
) -> InboundMessageModel:
    message = InboundMessageModel(
        provider_message_id=name,
        provider_thread_id=f"thread-{name}",
        received_at=datetime.datetime(2026, 9, 20, tzinfo=datetime.UTC),
        sender="recruiter@example.com",
        subject="Engineering fixture",
        body_text="Engineering fixture",
        classification="JOB_ALERT" if job_alert else "RECRUITER_FOLLOWUP",
        headers_json={"_provider": {"canary": True}} if canary else {},
    )
    session.add(message)
    session.flush()
    return message


def _link(session: Session, message: InboundMessageModel, app: Any) -> MessageLinkModel:
    link = MessageLinkModel(
        inbound_message_id=message.id,
        application_id=app.id if app else None,
        confidence=1.0,
        method="engineering-fixture",
    )
    session.add(link)
    session.flush()
    return link


def _sweep(
    monkeypatch: pytest.MonkeyPatch, messages: list[InboundMessageModel], runtime: list[str]
) -> None:
    now = datetime.datetime.now(datetime.UTC)
    summary = IngestionSweepSummary(
        started_at=now,
        completed_at=now,
        messages_polled=len(messages),
        messages_skipped_duplicate=len(messages),
        batch_message_ids=[m.id for m in messages],
        batch_canary_provider_message_ids=runtime,
        poll_report=PollReport(
            max_results=50,
            listed_count=len(messages),
            fetched_count=len(messages),
            complete=True,
            adapter="mock_fixtures",
            synthetic=True,
        ),
    )
    monkeypatch.setattr(EmailIngestionEngine, "run_sweep", lambda *args, **kwargs: summary)


def _sha(value: object) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()


@pytest.mark.parametrize("dry_run", [False, True])
def test_proof_and_alert_scopes_are_distinct_and_batch_confined(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, dry_run: bool
) -> None:
    messages = [
        _message(db_session, "alert", job_alert=True),
        _message(db_session, "lifecycle"),
        _message(db_session, "runtime-canary"),
        _message(db_session, "durable-canary", canary=True),
        _message(db_session, "outside-batch"),
    ]
    apps = [_seed_application(db_session, f"Fixture {i}") for i in range(len(messages))]
    for message, app in zip(messages, apps, strict=True):
        _link(db_session, message, app)
    db_session.commit()
    _sweep(monkeypatch, messages[:4], [messages[2].provider_message_id])
    observed: dict[str, Any] = {"lifecycle": [], "threads": None, "applications": None}

    def process(self: Any, message: InboundMessageModel) -> None:
        observed["lifecycle"].append(message.id)

    def recruiters(self: Any, *, thread_ids: Any) -> list[Any]:
        observed["threads"] = thread_ids
        return []

    def stale(self: Any, *, application_ids: Any) -> list[Any]:
        observed["applications"] = application_ids
        return []

    monkeypatch.setattr(LifecycleEngine, "process_message", process)
    monkeypatch.setattr(LifecycleAlertService, "check_unanswered_recruiters", recruiters)
    monkeypatch.setattr(LifecycleAlertService, "check_stale_applications", stale)
    result = _runner(db_session).run(_request(dry_run=dry_run))
    assert result.status == ("DRY_RUN" if dry_run else "SUCCESS"), result.errors
    assert result.provider_message_id_sha256 == sorted(
        _sha(m.provider_message_id) for m in messages[:2]
    )
    assert result.application_id_sha256 == sorted(_sha(a.id) for a in apps[:2])
    assert observed == {
        "lifecycle": [] if dry_run else [messages[1].id],
        "threads": None if dry_run else {messages[1].provider_thread_id},
        "applications": None if dry_run else {apps[1].id},
    }


@pytest.mark.parametrize("repair_existing", [False, True])
def test_lifecycle_link_is_resolved_after_processing_for_alerts_and_proof(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, repair_existing: bool
) -> None:
    message = _message(db_session, "new-lifecycle-link")
    app = _seed_application(db_session, "Lifecycle linked company")
    link = _link(db_session, message, None) if repair_existing else None
    db_session.commit()
    _sweep(monkeypatch, [message], [])
    observed: list[set[Any]] = []

    def process(self: Any, actual: InboundMessageModel) -> None:
        assert actual.id == message.id
        if link:
            link.application_id = app.id
        else:
            _link(db_session, actual, app)
        db_session.flush()

    def stale(self: Any, *, application_ids: set[Any]) -> list[Any]:
        observed.append(application_ids)
        return []

    monkeypatch.setattr(LifecycleEngine, "process_message", process)
    monkeypatch.setattr(LifecycleAlertService, "check_stale_applications", stale)
    result = _runner(db_session).run(_request())
    assert result.status == "SUCCESS", result.errors
    assert observed == [{app.id}]
    assert result.application_id_sha256 == [_sha(app.id)]

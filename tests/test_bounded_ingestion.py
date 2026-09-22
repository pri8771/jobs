"""V17-M04 / V17-R05: bounded, replayable ingestion runs through production services.

Uses the synthetic fixtures adapter (clearly labelled synthetic) to exercise the bounded
runner, the recorded evidence, canary exclusion, incomplete-poll handling, dry runs,
mailbox binding and replay idempotency, plus the installed ``ingest-mailbox`` and
``lifecycle-timeline`` entry points in separate processes (restart + replay).
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

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
    BOUNDED_RUN_ACTION,
    BoundedIngestionError,
    BoundedIngestionRequest,
    BoundedIngestionRunner,
    compute_logical_state_digests,
)
from jobs_automation.ingestion.fixtures import get_sample_email_fixtures
from jobs_automation.lifecycle.timeline import build_timeline_export, timeline_digest
from tests.test_gmail_adapter_bounded import CANDIDATE, FakeGmailService, _five_messages
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
    assert MAILBOX not in json.dumps(metadata)
    assert metadata["digests_after"]["counts"]["messages"] == 7
    assert metadata["code_identity"]["git_sha"] == "engineering"
    assert metadata["poll"]["complete"] is True


def test_replay_preserves_identical_logical_state(db_session: Session) -> None:
    _seed_application(db_session)
    runner = _runner(db_session)
    first = runner.run(_request())
    events_before = db_session.scalars(select(ApplicationEventModel)).all()
    tasks_before = db_session.scalars(select(TaskModel)).all()

    replay = runner.replay(first.run_id, MAILBOX)
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
        runner.replay(first.run_id, "someone.else@gmail.com")
    with pytest.raises(BoundedIngestionError, match="REPLAY_RUN_NOT_FOUND"):
        runner.replay("00000000-0000-0000-0000-000000000000", MAILBOX)


def test_cap_smaller_than_evidence_is_incomplete_and_recorded(db_session: Session) -> None:
    result = _runner(db_session).run(_request(cap=3))
    assert result.status == "FAILED"
    assert result.complete is False
    assert result.poll is not None and result.poll.truncated_by_cap is True
    assert result.messages_ingested == 0
    assert db_session.scalars(select(InboundMessageModel)).all() == []
    assert db_session.scalars(select(TaskModel)).all() == []
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None and audit.result == "FAILED"


def test_dry_run_persists_no_messages_but_records_the_attempt(db_session: Session) -> None:
    result = _runner(db_session).run(_request(dry_run=True))
    assert result.status == "DRY_RUN"
    assert db_session.scalars(select(InboundMessageModel)).all() == []
    audit = db_session.scalar(
        select(AuditLogModel).where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
    )
    assert audit is not None and audit.result == "DRY_RUN"


def test_canary_mail_is_tagged_counted_and_excluded_from_lifecycle(db_session: Session) -> None:
    app = _seed_application(db_session)
    activity_before = app.last_activity_at
    # Treat the fixture recruiter as a canary alias: its mail must not move the application.
    result = _runner(db_session, canary_identities=["sarah.connor@viatris.com"]).run(_request())
    assert result.canary_messages == 2  # inbound recruiter + candidate reply in that thread
    db_session.refresh(app)
    assert app.status == "SUBMITTED"
    assert result.lifecycle_transitions == 0
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


def test_timeline_export_is_redacted_and_digest_stable(db_session: Session) -> None:
    app = _seed_application(db_session)
    _runner(db_session).run(_request())
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


def test_installed_entrypoints_restart_and_replay_bounded_batch(tmp_path: Path) -> None:
    """Separate processes: run, restart, replay, inspect — identical logical state."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    resume = tmp_path / "resume_ai_software_engineer.md"
    resume.write_text("# resume\n", encoding="utf-8")
    profile_yaml = engineering_profile_yaml(resume.resolve()).replace(
        'email: "engineering-candidate@invalid"', f'email: "{MAILBOX}"'
    )
    (config_dir / "candidate_profile.yaml").write_text(profile_yaml, encoding="utf-8")

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
    first = _run_cli(common, env)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "SYNTHETIC ENGINEERING RUN" in first.stdout
    run_id_match = re.search(r"Run ID\s*│?\s*([0-9a-f-]{36})", first.stdout)
    assert run_id_match is not None, first.stdout
    run_id = run_id_match.group(1)

    replay = _run_cli(
        [
            "ingest-mailbox",
            "--mailbox",
            MAILBOX,
            "--query",
            "x",
            "--window-start",
            "2020-01-01",
            "--window-end",
            "2040-01-01",
            "--cap",
            "50",
            "--mock-fixtures",
            "--replay-run",
            run_id,
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

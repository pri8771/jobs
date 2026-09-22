"""Tests for CLI commands."""

import datetime
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy import select

from jobs_automation.cli import main as cli_main
from jobs_automation.cli.main import cli
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.db.session import get_engine, get_sessionmaker, init_db


def test_cli_validate_config() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["validate-config", "--config-dir", "config"])
    assert result.exit_code == 0
    assert "All configuration files validated successfully" in result.output


def test_cli_status() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--config-dir", "config"])
    assert result.exit_code == 0
    assert "Jobs Automation — System Status" in result.output
    assert "Enterprise Automation & Solutions Architect" in result.output
    assert "Every 4 hours (240 min)" in result.output


def test_cli_generate_profile_worksheet(tmp_path: Path) -> None:
    runner = CliRunner()
    out_file = tmp_path / "test_worksheet.md"
    result = runner.invoke(
        cli,
        [
            "generate-profile-worksheet",
            "--config-dir",
            "config",
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "LinkedIn" in content
    assert "Indeed" in content
    assert "ZipRecruiter" in content
    assert "Dice" in content
    assert "Enterprise Automation & Solutions Architect" in content


def test_poll_emails_cli_propagates_canary_identity_to_generic_ingestion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The direct polling CLI must tag a fresh alias before later lifecycle passes."""
    database_url = f"sqlite:///{tmp_path / 'poll-emails.sqlite'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    db_engine = get_engine(database_url)
    init_db(db_engine)

    result = CliRunner().invoke(
        cli,
        [
            "poll-emails",
            "--mock-fixtures",
            "--config-dir",
            "config",
            "--canary-identity",
            "Owner Alias <sarah.connor@viatris.com>",
        ],
    )

    assert result.exit_code == 0, result.output
    with get_sessionmaker(get_engine(database_url))() as session:
        recruiter = session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "gmail_recruiter_001"
            )
        )
        assert recruiter is not None
        assert (recruiter.headers_json or {}).get("_provider", {}).get("canary") is True


def test_update_lifecycle_reclassifies_historical_alias_before_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A direct lifecycle CLI pass must not transition a previously untagged alias."""
    database_url = f"sqlite:///{tmp_path / 'update-lifecycle.sqlite'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    db_engine = get_engine(database_url)
    init_db(db_engine)
    now = datetime.datetime.now(datetime.UTC)

    with get_sessionmaker(db_engine)() as session:
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
            provider_message_id="historical-cli-canary",
            provider_thread_id="historical-cli-canary-thread",
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

    result = CliRunner().invoke(
        cli,
        [
            "update-lifecycle",
            "--config-dir",
            "config",
            "--canary-identity",
            "Owner Alias <recruiter@stripe.com>",
        ],
    )

    assert result.exit_code == 0, result.output
    with get_sessionmaker(get_engine(database_url))() as session:
        reloaded_message = session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "historical-cli-canary"
            )
        )
        reloaded_application = session.get(ApplicationModel, application_id)
        assert reloaded_message is not None
        assert (reloaded_message.headers_json or {}).get("_provider", {}).get("canary") is True
        assert reloaded_application is not None
        assert reloaded_application.status == "SUBMITTED"
        assert session.scalars(select(ApplicationEventModel)).all() == []


def test_evaluate_jobs_reclassifies_configured_historical_alias_before_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Direct job evaluation must not select a job linked to a newly configured alias."""
    config_dir = tmp_path / "config"
    shutil.copytree("config", config_dir)
    platforms_path = config_dir / "platforms.example.yaml"
    platforms_path.write_text(
        platforms_path.read_text(encoding="utf-8").replace(
            "  canary_identities: []",
            "  canary_identities:\n    - Owner Alias <alerts@canary.example.test>",
        ),
        encoding="utf-8",
    )
    database_url = f"sqlite:///{tmp_path / 'evaluate-jobs.sqlite'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    db_engine = get_engine(database_url)
    init_db(db_engine)
    now = datetime.datetime.now(datetime.UTC)

    with get_sessionmaker(db_engine)() as session:
        job = JobModel(normalized_title="Historical Canary Job", status="discovered")
        session.add(job)
        session.flush()
        historical = InboundMessageModel(
            provider_message_id="historical-evaluation-canary",
            provider_thread_id="historical-evaluation-canary-thread",
            received_at=now,
            sender="Owner Alias <alerts@canary.example.test>",
            recipients_json=["candidate@example.com"],
            direction="inbound",
            subject="New role alert",
            headers_json={},
            body_text="A historical owner-controlled job alert.",
            classification="JOB_ALERT",
            confidence=0.99,
        )
        session.add(historical)
        session.flush()
        session.add(
            MessageLinkModel(
                inbound_message_id=historical.id,
                job_id=job.id,
                confidence=0.99,
                method="historical_fixture",
            )
        )
        job_id = job.id
        session.commit()

    result = CliRunner().invoke(cli, ["evaluate-jobs", "--config-dir", str(config_dir)])

    assert result.exit_code == 0, result.output
    with get_sessionmaker(get_engine(database_url))() as session:
        reloaded_message = session.scalar(
            select(InboundMessageModel).where(
                InboundMessageModel.provider_message_id == "historical-evaluation-canary"
            )
        )
        reloaded_job = session.get(JobModel, job_id)
        assert reloaded_message is not None
        assert (reloaded_message.headers_json or {}).get("_provider", {}).get("canary") is True
        assert reloaded_job is not None
        assert reloaded_job.status == "discovered"


def test_read_only_cli_views_exclude_durable_canary_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Status views show only ordinary evidence after a durable canary reclassification."""
    database_url = f"sqlite:///{tmp_path / 'canary-visibility.sqlite'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    db_engine = get_engine(database_url)
    init_db(db_engine)
    now = datetime.datetime.now(datetime.UTC)

    with get_sessionmaker(db_engine)() as session:
        company = CompanyModel(normalized_name="Visibility Company")
        session.add(company)
        session.flush()
        canary_job = JobModel(
            company_id=company.id,
            normalized_title="CANARYROLE",
            status="discovered",
        )
        genuine_job = JobModel(
            company_id=company.id,
            normalized_title="REALROLE",
            status="discovered",
        )
        session.add_all([canary_job, genuine_job])
        session.flush()
        canary_application = ApplicationModel(
            job_id=canary_job.id,
            status="INTERVIEWING",
            last_activity_at=now,
        )
        genuine_application = ApplicationModel(
            job_id=genuine_job.id,
            status="SUBMITTED",
            last_activity_at=now - datetime.timedelta(minutes=1),
        )
        session.add_all([canary_application, genuine_application])
        session.flush()
        canary_message = InboundMessageModel(
            provider_message_id="cli-canary-message",
            provider_thread_id="cli-canary-thread",
            received_at=now,
            sender="canary-owner@example.test",
            recipients_json=["candidate@example.test"],
            direction="inbound",
            subject="Canary role",
            headers_json={"_provider": {"canary": True}},
            body_text="Owner-controlled canary evidence.",
            classification="CANARY_ONLY_CLASS",
            confidence=1.0,
        )
        genuine_message = InboundMessageModel(
            provider_message_id="cli-genuine-message",
            provider_thread_id="cli-genuine-thread",
            received_at=now - datetime.timedelta(minutes=1),
            sender="recruiter@example.test",
            recipients_json=["candidate@example.test"],
            direction="inbound",
            subject="Genuine role",
            headers_json={},
            body_text="Ordinary recruiting evidence.",
            classification="GENUINE_VISIBLE_CLASS",
            confidence=1.0,
        )
        session.add_all([canary_message, genuine_message])
        session.flush()
        session.add_all(
            [
                MessageLinkModel(
                    inbound_message_id=canary_message.id,
                    job_id=canary_job.id,
                    application_id=canary_application.id,
                    company_id=company.id,
                    confidence=1.0,
                    method="canary_fixture",
                ),
                MessageLinkModel(
                    inbound_message_id=genuine_message.id,
                    job_id=genuine_job.id,
                    application_id=genuine_application.id,
                    company_id=company.id,
                    confidence=1.0,
                    method="genuine_fixture",
                ),
                TaskModel(
                    job_id=canary_job.id,
                    application_id=canary_application.id,
                    task_type="NEEDS_REVIEW",
                    status="pending",
                    due_at=now,
                    payload_json={"reason": "CANARYREASON"},
                ),
                TaskModel(
                    job_id=genuine_job.id,
                    application_id=genuine_application.id,
                    task_type="NEEDS_REVIEW",
                    status="pending",
                    due_at=now,
                    payload_json={"reason": "REALREASON"},
                ),
                ContactModel(
                    company_id=company.id,
                    name="CANARYCONTACT",
                    email="canary-owner@example.test",
                    role="Recruiter",
                    source="fixture",
                    last_contact_at=now,
                ),
                ContactModel(
                    company_id=company.id,
                    name="REALCONTACT",
                    email="recruiter@example.test",
                    role="Recruiter",
                    source="fixture",
                    last_contact_at=now - datetime.timedelta(minutes=1),
                ),
            ]
        )
        session.commit()

    runner = CliRunner()
    mailbox = runner.invoke(cli, ["mailbox-status", "--config-dir", "config"])
    assert mailbox.exit_code == 0, mailbox.output
    assert "GENUINE_VISIBLE_CLASS" in mailbox.output
    assert "CANARY_ONLY_CLASS" not in mailbox.output
    assert "Reconciliation-only Canary Messages Excluded" in mailbox.output

    lifecycle = runner.invoke(cli, ["lifecycle-status", "--config-dir", "config"])
    assert lifecycle.exit_code == 0, lifecycle.output
    assert "REALROLE" in lifecycle.output
    assert "CANARYROLE" not in lifecycle.output

    contacts = runner.invoke(cli, ["contacts", "--config-dir", "config"])
    assert contacts.exit_code == 0, contacts.output
    assert "REALCONTACT" in contacts.output
    assert "CANARYCONTACT" not in contacts.output

    reviews = runner.invoke(cli, ["review-queue", "--config-dir", "config"])
    assert reviews.exit_code == 0, reviews.output
    assert "REALREASON" in reviews.output
    assert "CANARYREASON" not in reviews.output


def test_mailbox_status_fails_closed_when_canary_policy_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A status command never falls back to unfiltered evidence after policy failure."""
    database_url = f"sqlite:///{tmp_path / 'missing-policy.sqlite'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    init_db(get_engine(database_url))

    result = CliRunner().invoke(
        cli,
        ["mailbox-status", "--config-dir", str(tmp_path / "missing-config")],
    )

    assert result.exit_code != 0
    assert "Canary policy configuration unavailable" in result.output
    assert "Mailbox & Ingestion Overview" not in result.output


def _bounded_ingest_args(*extra: str) -> list[str]:
    return [
        "ingest-mailbox",
        "--mailbox",
        "candidate@example.com",
        "--query",
        "label:recruiting",
        "--window-start",
        "2026-01-01T00:00:00Z",
        "--window-end",
        "2026-01-02T00:00:00Z",
        "--cap",
        "10",
        *extra,
    ]


def test_invalid_bounded_input_fails_before_configuration_or_gmail_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args: object, **kwargs: object) -> None:
        reached_config.append(True)
        raise AssertionError("configuration must not load after invalid bounded input")

    monkeypatch.setattr(cli_main, "ConfigLoader", unexpected_config)
    args = _bounded_ingest_args()
    args[args.index("label:recruiting")] = " "
    result = CliRunner().invoke(cli, args)

    assert result.exit_code != 0
    assert "QUERY_REQUIRED" in result.output
    assert reached_config == []


def test_replay_requires_explicit_safe_or_stateful_mode_before_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args: object, **kwargs: object) -> None:
        reached_config.append(True)
        raise AssertionError("configuration must not load before replay intent is explicit")

    monkeypatch.setattr(cli_main, "ConfigLoader", unexpected_config)
    result = CliRunner().invoke(cli, _bounded_ingest_args("--replay-run", "run-123"))

    assert result.exit_code != 0
    assert "replay requires --dry-run" in result.output
    assert reached_config == []


def test_replay_rejects_conflicting_modes_before_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args: object, **kwargs: object) -> None:
        reached_config.append(True)
        raise AssertionError("configuration must not load for conflicting replay modes")

    monkeypatch.setattr(cli_main, "ConfigLoader", unexpected_config)
    result = CliRunner().invoke(
        cli,
        _bounded_ingest_args("--replay-run", "run-123", "--dry-run", "--apply-replay"),
    )

    assert result.exit_code != 0
    assert "--dry-run and --apply-replay cannot be combined" in result.output
    assert reached_config == []

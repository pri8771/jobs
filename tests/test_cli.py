"""Tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from jobs_automation.cli import main as cli_main
from jobs_automation.cli.main import cli


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


def test_invalid_bounded_input_fails_before_configuration_or_gmail_access(monkeypatch) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args, **kwargs):
        reached_config.append(True)
        raise AssertionError("configuration must not load after invalid bounded input")

    monkeypatch.setattr(cli_main, "ConfigLoader", unexpected_config)
    args = _bounded_ingest_args()
    args[args.index("label:recruiting")] = " "
    result = CliRunner().invoke(cli, args)

    assert result.exit_code != 0
    assert "QUERY_REQUIRED" in result.output
    assert reached_config == []


def test_replay_requires_explicit_safe_or_stateful_mode_before_configuration(monkeypatch) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args, **kwargs):
        reached_config.append(True)
        raise AssertionError("configuration must not load before replay intent is explicit")

    monkeypatch.setattr(cli_main, "ConfigLoader", unexpected_config)
    result = CliRunner().invoke(cli, _bounded_ingest_args("--replay-run", "run-123"))

    assert result.exit_code != 0
    assert "replay requires --dry-run" in result.output
    assert reached_config == []


def test_replay_rejects_conflicting_modes_before_configuration(monkeypatch) -> None:
    reached_config: list[bool] = []

    def unexpected_config(*args, **kwargs):
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

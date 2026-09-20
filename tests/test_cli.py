"""Tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

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
    assert "Jobs Automation — System Status (V0.1)" in result.output
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

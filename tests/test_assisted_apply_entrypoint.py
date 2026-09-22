"""Installed-entrypoint test for ``jobs-automation assisted-apply`` (F145-11).

Runs the documented CLI command against a SQLite runtime database and the mock browser
runner, with ``--auto-confirm`` supplied: the command must stop at review and must not
print or persist a submitted application.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select

from jobs_automation.db.base import Base
from jobs_automation.db.models import ApplicationEventModel, ApplicationModel
from jobs_automation.db.session import get_engine, get_sessionmaker
from tests.test_assisted_prefill_boundary import _persist_live_ready_packet
from tests.test_real_proof_verifier import engineering_profile_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

POLICY_YAML = """version: 1

default:
  capability: "submit_application"
  decision: "blocked"
  reason: "deny_by_default"

entries:
  - platform: "greenhouse"
    domain_pattern: "*.greenhouse.io"
    capability: "submit_application"
    decision: "assisted"
    reviewed_at: "2026-09-20"
"""


def test_assisted_apply_entrypoint_stops_at_review_with_mock_browser(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    resume_path = tmp_path / "resume_ai_software_engineer.md"
    resume_path.write_text("# Engineering resume\n", encoding="utf-8")
    (config_dir / "candidate_profile.yaml").write_text(
        engineering_profile_yaml(resume_path.resolve()), encoding="utf-8"
    )
    (config_dir / "policy_registry.yaml").write_text(POLICY_YAML, encoding="utf-8")
    # Stateful application entrypoints load the durable canary policy before they
    # select a job.  This fixture models a complete operator configuration rather
    # than silently running without that safety boundary.
    shutil.copy(REPO_ROOT / "config" / "platforms.example.yaml", config_dir / "platforms.yaml")

    db_url = f"sqlite:///{tmp_path / 'entrypoint.db'}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    with get_sessionmaker(engine)() as session:
        job, packet, _, _ = _persist_live_ready_packet(session, tmp_path)
        job_id, packet_id = str(job.id), str(packet.id)
    engine.dispose()

    env = {**os.environ, "DATABASE_URL": db_url}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from jobs_automation.cli.main import cli; sys.exit(cli())",
            "assisted-apply",
            "--job-id",
            job_id,
            "--packet-id",
            packet_id,
            "--mock-browser",
            "--auto-confirm",
            "--receipt",
            "Application received ref 123",
            "--config-dir",
            str(config_dir),
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Review Required" in result.stdout
    assert "Successfully Submitted" not in result.stdout
    assert "Post-fill evidence" in result.stdout
    assert "submit performed=False" in result.stdout

    engine = get_engine(db_url)
    try:
        with get_sessionmaker(engine)() as session:
            app = session.scalar(select(ApplicationModel).where(ApplicationModel.job_id == job.id))
            assert app is not None
            assert app.status.startswith("ASSISTED_PREFILL")
            assert app.applied_at is None
            events = session.scalars(
                select(ApplicationEventModel).where(ApplicationEventModel.application_id == app.id)
            ).all()
            assert [e.event_type for e in events] == []
    finally:
        engine.dispose()

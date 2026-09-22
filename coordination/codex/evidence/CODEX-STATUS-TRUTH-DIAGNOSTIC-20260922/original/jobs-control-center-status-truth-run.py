"""Exact-source disposable PostgreSQL wrapper for status-truth reproduction."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

import psycopg
from psycopg import sql


SOURCE = Path("/Users/pchordia/Downloads/swarm_codex/review/jobs-worker-history-source")
VENV = SOURCE.parent / "jobs-source/.venv/bin"
SOCKET = "/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd"
EXPECTED = [
    "b462e17b48c286dc4bdee5b958217b42da8e701e",
    "f0694f58e4feef9846c21a608dc7bbdeca4be39d",
]
DATABASE = "jobs_status_truth_" + uuid.uuid4().hex[:12]
OUT = Path("/tmp/jobs-control-center-status-truth-root-20260922")
OUT.mkdir(exist_ok=True)

identity = subprocess.check_output(
    ["git", "rev-parse", "HEAD", "HEAD^{tree}"], cwd=SOURCE, text=True
).splitlines()
assert identity == EXPECTED
assert subprocess.check_output(["git", "status", "--porcelain"], cwd=SOURCE, text=True) == ""

env = dict(
    os.environ,
    DATABASE_URL=f"postgresql+psycopg:///{DATABASE}?host={SOCKET}&port=56422",
    SOURCE_SHA=identity[0],
    SOURCE_TREE=identity[1],
    PYTHONPATH=f"{SOURCE / 'src'}:{SOURCE}",
)
result = {"source_sha": identity[0], "tree": identity[1], "database": DATABASE}
with psycopg.connect(dbname="postgres", host=SOCKET, port=56422, autocommit=True) as admin:
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE)))
    try:
        with (OUT / "migration.log").open("w") as log:
            proc = subprocess.run(
                [str(VENV / "alembic"), "upgrade", "head"],
                cwd=SOURCE,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        result["migration_exit"] = proc.returncode
        assert proc.returncode == 0
        with (OUT / "workflow.log").open("w") as log:
            proc = subprocess.run(
                [str(VENV / "python"), "/tmp/jobs-control-center-status-truth-repro.py"],
                cwd=SOURCE,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        result["workflow_exit"] = proc.returncode
        assert proc.returncode == 0
        raw = (OUT / "workflow.log").read_text()
        report = json.JSONDecoder().raw_decode(raw[raw.index("{") :])[0]
        (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    finally:
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(DATABASE)))
        result["remaining_database_count"] = admin.execute(
            "SELECT count(*) FROM pg_database WHERE datname=%s", (DATABASE,)
        ).fetchone()[0]
        (OUT / "run.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))

import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path

import psycopg
from psycopg import sql

source = Path("/Users/pchordia/Downloads/swarm_codex/review/jobs-worker-history-source")
venv = Path("/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin")
socket = "/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd"
database = "jobs_worker_history_" + uuid.uuid4().hex[:12]
out = Path("/tmp/jobs-worker-history-pg-evidence-final-20260922")
out.mkdir(exist_ok=True)

head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=source, text=True).strip()
status_before = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=source, text=True)
assert head == "b462e17b48c286dc4bdee5b958217b42da8e701e"
assert tree == "f0694f58e4feef9846c21a608dc7bbdeca4be39d"
assert status_before == ""
diff = subprocess.check_output(["git", "diff", "--", "src/jobs_automation/dashboard/server.py"], cwd=source, text=True)
(out / "candidate.diff").write_text(diff)
source_id = f"HEAD={head};index_tree={tree};uncommitted_server_diff_sha256={hashlib.sha256(diff.encode()).hexdigest()}"
env = dict(
    os.environ,
    PYTHONPATH=f"{source / 'src'}:{source}",
    DATABASE_URL=f"postgresql+psycopg:///{database}?host={socket}&port=56422",
    SOURCE_ID=source_id,
)
summary = {"database": database, "source_id": source_id, "status_before": status_before, "commands": []}

with psycopg.connect(dbname="postgres", host=socket, port=56422, autocommit=True) as admin:
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    try:
        migration = subprocess.run(
            [str(venv / "alembic"), "upgrade", "head"],
            cwd=source,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (out / "migration.log").write_text(migration.stdout)
        summary["commands"].append({"command": "alembic upgrade head", "exit": migration.returncode})
        assert migration.returncode == 0

        workflow = subprocess.run(
            [str(venv / "python"), "/tmp/jobs-worker-history-pg-case.py"],
            cwd=source,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (out / "workflow.log").write_text(workflow.stdout)
        summary["commands"].append({"command": "python /tmp/jobs-worker-history-pg-case.py", "exit": workflow.returncode})
        assert workflow.returncode == 0, workflow.stdout
        start = workflow.stdout.index("{")
        parsed, _ = json.JSONDecoder().raw_decode(workflow.stdout[start:])
        (out / "report.json").write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n")
    finally:
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
        remaining = admin.execute("SELECT count(*) FROM pg_database WHERE datname=%s", (database,)).fetchone()[0]
        summary["cleanup_remaining_database_count"] = remaining
        summary["status_after"] = subprocess.check_output(
            ["git", "status", "--porcelain=v1"], cwd=source, text=True
        )
        (out / "run-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        assert remaining == 0
        assert summary["status_after"] == ""

print(json.dumps(summary, indent=2, sort_keys=True))

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import subprocess
import sys
from typing import Any

from sqlalchemy import URL, create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationModel,
    AuditLogModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.health import HealthCheckService
from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.worker import WorkerDaemon


SOCKET = "/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd"
PORT = 56422
DB = os.environ["JOBS_HEALTH_DB"]
URL_OBJ = URL.create(
    "postgresql+psycopg", username="pchordia", database=DB,
    query={"host": SOCKET, "port": str(PORT)},
)
engine = create_engine(URL_OBJ)
Base.metadata.create_all(engine)
Factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
out: dict[str, Any] = {"source_sha": os.environ["JOBS_SOURCE_SHA"], "database": DB}


def fresh_health() -> dict[str, Any]:
    code = r'''
import json, os
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from jobs_automation.health import HealthCheckService
u=URL.create("postgresql+psycopg", username="pchordia", database=os.environ["JOBS_HEALTH_DB"], query={"host":os.environ["JOBS_PG_SOCKET"],"port":os.environ["JOBS_PG_PORT"]})
f=sessionmaker(bind=create_engine(u), autoflush=False, autocommit=False)
h=HealthCheckService(f).check_worker()
print(h.model_dump_json())
'''
    env = dict(os.environ)
    env.update(JOBS_PG_SOCKET=SOCKET, JOBS_PG_PORT=str(PORT))
    cp = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True)
    if cp.returncode:
        raise AssertionError({"fresh_health_exit": cp.returncode, "stderr": cp.stderr})
    return json.loads(cp.stdout.strip().splitlines()[-1])


def counts() -> dict[str, int]:
    models = [InboundMessageModel, MessageLinkModel, TaskModel, JobModel, ApplicationModel]
    with Factory() as s:
        return {m.__tablename__: s.scalar(select(func.count()).select_from(m)) or 0 for m in models}


class TimeoutAdapter(EmailAdapter):
    def poll_messages(self, query=None, since_timestamp=None, max_results=100):
        raise TimeoutError("synthetic timeout")
    def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
        return []


partial = WorkerDaemon(
    Factory, email_adapter=TimeoutAdapter(), candidate_emails=["candidate@invalid"]
).run_sweep(reconcile=False)
partial_health = fresh_health()
assert partial["errors"] == ["synthetic timeout"]
assert partial_health["status"] == "DEGRADED"
assert partial_health["details"]["last_attempt_status"] == "PARTIAL"
assert partial_health["details"]["last_error_category"] == "GMAIL_API_ERROR"
out["worker_partial_product_path"] = {
    "run_id": partial["run_id"], "result_errors": partial["errors"],
    "fresh_process_health": partial_health,
}


def b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode()


class Executable:
    def __init__(self, value: Any): self.value = value
    def execute(self):
        if isinstance(self.value, Exception): raise self.value
        return self.value


class FakeGmail:
    def __init__(self):
        now = dt.datetime.now(dt.UTC)
        self.rows = []
        for i in range(1, 6):
            self.rows.append({
                "id": f"incomplete-{i}", "threadId": f"thread-{i}",
                "internalDate": str(int((now-dt.timedelta(minutes=i)).timestamp()*1000)),
                "labelIds": ["INBOX"],
                "payload": {"mimeType":"text/plain", "headers":[
                    {"name":"From","value":f"recruiter{i}@invalid"},
                    {"name":"To","value":"candidate@invalid"},
                    {"name":"Subject","value":f"Interview {i}"}],
                    "body":{"data":b64("PRIVATE-BODY-MARKER access_token=RAW-J20-SECRET")}},
            })
    def users(self): return self
    def messages(self): return self
    def threads(self): return self
    def getProfile(self, userId): return Executable({"emailAddress":"candidate@invalid"})
    def list(self, **kwargs):
        return Executable({"messages":[{"id":r["id"],"threadId":r["threadId"]} for r in self.rows]})
    def get(self, userId, id, format="full"):
        if id == "incomplete-2": return Executable(RuntimeError("HttpError 500 synthetic"))
        return Executable(next(r for r in self.rows if r["id"] == id))


before = counts()
gmail = GmailAdapter(service=FakeGmail(), verified_identities=["candidate@invalid"])
incomplete = WorkerDaemon(
    Factory, email_adapter=gmail, candidate_emails=["candidate@invalid"]
).run_sweep(reconcile=False)
after = counts()
incomplete_health = fresh_health()
assert before == after, (before, after)
assert incomplete["messages_ingested"] == 0
assert incomplete_health["status"] == "DEGRADED"
assert incomplete_health["details"]["last_attempt_status"] == "PARTIAL"
with Factory() as s:
    fin = s.scalar(select(AuditLogModel).where(
        AuditLogModel.action_type == "worker_run_finished",
        AuditLogModel.external_reference == incomplete["run_id"],
    ))
    persisted = json.dumps(fin.metadata_json, sort_keys=True)
assert "PRIVATE-BODY-MARKER" not in persisted
assert "RAW-J20-SECRET" not in persisted
out["incomplete_poll_product_path"] = {
    "run_id": incomplete["run_id"], "result_errors": incomplete["errors"],
    "counts_before": before, "counts_after": after,
    "persisted_finish_metadata": fin.metadata_json,
    "fresh_process_health": incomplete_health,
}


adapter_health = HealthCheckService(Factory).check_adapters().model_dump()
assert adapter_health["status"] == "DEGRADED"
assert adapter_health["details"]["live_capable_platforms"] == []
assert sorted(adapter_health["details"]["registered_platforms"]) == sorted(adapter_health["details"]["simulation_only_platforms"])
out["adapter_details"] = adapter_health


# The following records are direct synthetic health-selection seeds, not WorkerDaemon output.
now = dt.datetime.now(dt.UTC)
with Factory() as s:
    s.execute(delete(AuditLogModel))
    s.add_all([
        AuditLogModel(action_type="worker_run_finished", entity_type="worker", actor="synthetic_health_selection", result="SUCCESS", external_reference="seed-success", occurred_at=now-dt.timedelta(minutes=20), metadata_json={"error_count":0}),
        AuditLogModel(action_type="worker_run", entity_type="worker", actor="synthetic_health_selection", result="RUNNING", external_reference="seed-fresh-running", occurred_at=now-dt.timedelta(minutes=5), metadata_json={"run_id":"seed-fresh-running"}),
    ])
    s.commit()
fresh = fresh_health()
assert fresh["details"]["last_attempt_status"] == "RUNNING"
assert fresh["details"]["stale_running_run"] is False
assert fresh["details"]["last_success_at"] is not None

with Factory() as s:
    s.execute(delete(AuditLogModel))
    s.add_all([
        AuditLogModel(action_type="worker_run_finished", entity_type="worker", actor="synthetic_health_selection", result="SUCCESS", external_reference="seed-success-2", occurred_at=now-dt.timedelta(hours=4), metadata_json={"error_count":0}),
        AuditLogModel(action_type="worker_run", entity_type="worker", actor="synthetic_health_selection", result="RUNNING", external_reference="seed-stale-running", occurred_at=now-dt.timedelta(hours=3), metadata_json={"run_id":"seed-stale-running"}),
    ])
    s.commit()
stale = fresh_health()
assert stale["status"] == "DEGRADED"
assert stale["details"]["last_attempt_status"] == "RUNNING"
assert stale["details"]["stale_running_run"] is True
assert stale["details"]["stale_run_id"] == "seed-stale-running"
out["direct_seed_health_selection"] = {"fresh_running": fresh, "stale_running": stale}

print(json.dumps(out, indent=2, sort_keys=True))

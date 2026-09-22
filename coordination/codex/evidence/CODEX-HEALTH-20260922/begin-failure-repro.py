from __future__ import annotations

import datetime
import json
import os

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import AuditLogModel
from jobs_automation.health import HealthCheckService
from jobs_automation.worker import WorkerDaemon

SOURCE_SHA = "7345f1e0fc7153ba40c3628910ebd58266635421"
SOCKET = "/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd"
PORT = 56422
DB_NAME = os.environ["JOBS_HEALTH_DIAGNOSTIC_DB"]
url = URL.create(
    "postgresql+psycopg", username="pchordia", database=DB_NAME,
    query={"host": SOCKET, "port": str(PORT)},
)
engine = create_engine(url)
factory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

now = datetime.datetime.now(datetime.UTC)
prior_id = "prior-success"
with factory() as session:
    session.add_all([
        AuditLogModel(
            action_type="worker_run", entity_type="worker", actor="worker_daemon",
            result="RUNNING", external_reference=prior_id,
            occurred_at=now - datetime.timedelta(minutes=11),
            metadata_json={"run_id": prior_id, "started_at": (now-datetime.timedelta(minutes=11)).isoformat()},
        ),
        AuditLogModel(
            action_type="worker_run_finished", entity_type="worker", actor="worker_daemon",
            result="SUCCESS", external_reference=prior_id,
            occurred_at=now - datetime.timedelta(minutes=10),
            metadata_json={"run_id": prior_id, "final_status": "SUCCESS", "finished_at": (now-datetime.timedelta(minutes=10)).isoformat(), "error_count": 0, "error_categories": [], "sample_errors": [], "reconciliation_performed": True},
        ),
    ])
    session.commit()


class FailFirstFactory:
    def __init__(self) -> None:
        self.calls = 0
    def __call__(self) -> Session:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("synthetic begin evidence store unavailable")
        return factory()


class CountingAdapter(MockEmailAdapter):
    def __init__(self) -> None:
        super().__init__([])
        self.poll_calls = 0
    def poll_messages(self, *args, **kwargs):
        self.poll_calls += 1
        return super().poll_messages(*args, **kwargs)


failing_factory = FailFirstFactory()
adapter = CountingAdapter()
result = WorkerDaemon(failing_factory, email_adapter=adapter).run_sweep(reconcile=False)

with factory() as session:
    begins = session.scalars(select(AuditLogModel).where(AuditLogModel.action_type == "worker_run")).all()
    finishes = session.scalars(select(AuditLogModel).where(AuditLogModel.action_type == "worker_run_finished")).all()

# A new service instance simulates restart/readback from durable DB state only.
health = HealthCheckService(factory).check_worker()

observed = {
    "source_sha": SOURCE_SHA,
    "returned_errors": result["errors"],
    "failed_run_id": result["run_id"],
    "factory_calls": failing_factory.calls,
    "pipeline_poll_calls": adapter.poll_calls,
    "durable_begin_run_ids": [r.external_reference for r in begins],
    "durable_finish_run_ids": [r.external_reference for r in finishes],
    "fresh_health_status": health.status,
    "fresh_health_last_attempt_status": health.details.get("last_attempt_status"),
    "fresh_health_last_attempt_at": health.details.get("last_attempt_at"),
    "fresh_health_message": health.message,
}
print(json.dumps(observed, indent=2, sort_keys=True))

assert any("begin_record_failed" in e for e in result["errors"])
assert adapter.poll_calls == 0 and failing_factory.calls == 1
assert result["run_id"] not in observed["durable_begin_run_ids"]
assert result["run_id"] not in observed["durable_finish_run_ids"]
assert health.status == "HEALTHY" and health.details["last_attempt_status"] == "SUCCESS"

engine.dispose()

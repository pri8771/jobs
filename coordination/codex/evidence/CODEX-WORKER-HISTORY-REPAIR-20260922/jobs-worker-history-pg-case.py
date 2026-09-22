import datetime
import json
import os
import uuid

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import AuditLogModel
from jobs_automation.health import HealthCheckService
from jobs_automation.worker import WorkerDaemon
from tests.test_dashboard import DummyRequestHandler


engine = create_engine(os.environ["DATABASE_URL"])
factory = sessionmaker(bind=engine)


def endpoint():
    handler = DummyRequestHandler("GET", "/api/worker", session_factory=factory)
    handler.do_GET()
    assert handler.status_code == 200
    return json.loads(handler.mock_wfile.getvalue())


def health():
    return HealthCheckService(factory).check_worker().model_dump(mode="json")


def rows_for(run_id):
    with factory() as session:
        rows = session.scalars(
            select(AuditLogModel)
            .where(AuditLogModel.external_reference == run_id)
            .order_by(AuditLogModel.occurred_at, AuditLogModel.id)
        ).all()
        return [
            {
                "action_type": row.action_type,
                "result": row.result,
                "run_id": row.external_reference,
                "metadata": row.metadata_json,
            }
            for row in rows
        ]


def clear_audit():
    with factory() as session:
        session.execute(delete(AuditLogModel))
        session.commit()


report = {"source": os.environ["SOURCE_ID"], "cases": {}}

# Genuine daemon success, using only the in-memory synthetic adapter with no messages.
success = WorkerDaemon(factory, email_adapter=MockEmailAdapter([]), candidate_emails=[]).run_sweep(
    reconcile=False
)
success_rows = rows_for(success["run_id"])
success_api = endpoint()
success_health = health()
assert success["errors"] == []
assert [(r["action_type"], r["result"]) for r in success_rows] == [
    ("worker_run", "RUNNING"),
    ("worker_run_finished", "SUCCESS"),
]
assert all(r["run_id"] == success["run_id"] for r in success_rows)
assert {r["record_type"] for r in success_api if r["run_id"] == success["run_id"]} == {
    "run_begin",
    "run_finished",
}
assert success_health["details"]["last_attempt_status"] == "SUCCESS"
report["cases"]["actual_daemon_success"] = {
    "daemon_result": success,
    "durable_rows": success_rows,
    "api": success_api,
    "health": success_health,
}

# Genuine daemon PARTIAL caused by a bounded synthetic adapter failure.
class FailingMockAdapter(MockEmailAdapter):
    def poll_messages(self, query=None, since_timestamp=None, max_results=100):
        raise RuntimeError("synthetic bounded poll failure")


partial = WorkerDaemon(
    factory, email_adapter=FailingMockAdapter([]), candidate_emails=[]
).run_sweep(reconcile=False)
partial_rows = rows_for(partial["run_id"])
partial_api = endpoint()
assert partial["errors"] == ["synthetic bounded poll failure"]
assert [(r["action_type"], r["result"]) for r in partial_rows] == [
    ("worker_run", "RUNNING"),
    ("worker_run_finished", "PARTIAL"),
]
assert any(
    r["record_type"] == "run_finished" and r["result"] == "PARTIAL"
    for r in partial_api
    if r["run_id"] == partial["run_id"]
)
report["cases"]["actual_daemon_partial"] = {
    "daemon_result": partial,
    "durable_rows": partial_rows,
    "api": partial_api,
    "health": health(),
}

# Genuine fail-closed daemon path: first factory call fails, fallback finalize uses real PG.
class FirstCallFailureFactory:
    def __init__(self, real_factory):
        self.real_factory = real_factory
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("synthetic begin persistence failure")
        return self.real_factory()


failing_factory = FirstCallFailureFactory(factory)
failed = WorkerDaemon(
    failing_factory, email_adapter=MockEmailAdapter([]), candidate_emails=[]
).run_sweep(reconcile=False)
failed_rows = rows_for(failed["run_id"])
failed_api = endpoint()
assert failed["final_status"] == "FAILED"
assert failed["operational_evidence_durable"] is True
assert failing_factory.calls == 2
assert [(r["action_type"], r["result"]) for r in failed_rows] == [
    ("worker_run_finished", "FAILED")
]
assert any(
    r["record_type"] == "run_finished" and r["result"] == "FAILED"
    for r in failed_api
    if r["run_id"] == failed["run_id"]
)
report["cases"]["actual_daemon_begin_failure"] = {
    "daemon_result": failed,
    "durable_rows": failed_rows,
    "api": failed_api,
    "health": health(),
}

# Seeded legacy readback only. It deliberately has no genuine run reference.
clear_audit()
with factory() as session:
    session.add(
        AuditLogModel(
            action_type="worker_sweep",
            entity_type="worker",
            actor="legacy_worker",
            result="SUCCESS",
            external_reference=None,
            metadata_json={"fixture": "seeded_legacy_readback"},
        )
    )
    session.commit()
legacy_api = endpoint()
assert len(legacy_api) == 1
assert legacy_api[0]["record_type"] == "legacy_sweep"
assert legacy_api[0]["run_id"] is None
report["cases"]["seeded_legacy_readback"] = {"api": legacy_api, "health": health()}

# Seeded unfinished rows solely to compare dashboard history with existing health semantics.
clear_audit()
now = datetime.datetime.now(datetime.UTC)
with factory() as session:
    session.add(
        AuditLogModel(
            action_type="worker_run",
            entity_type="worker",
            actor="fixture",
            result="RUNNING",
            external_reference="seeded-stale-run",
            occurred_at=now - datetime.timedelta(hours=3),
            metadata_json={"run_id": "seeded-stale-run", "fixture": "stale_parity"},
        )
    )
    session.commit()
stale_api, stale_health = endpoint(), health()
assert stale_api[0]["record_type"] == "run_begin"
assert stale_api[0]["result"] == "RUNNING"
assert stale_health["details"]["last_attempt_status"] == "RUNNING"
assert stale_health["details"]["stale_running_run"] is True
assert stale_health["details"]["stale_run_id"] == "seeded-stale-run"
report["cases"]["seeded_stale_running_parity"] = {"api": stale_api, "health": stale_health}

clear_audit()
with factory() as session:
    session.add(
        AuditLogModel(
            action_type="worker_run",
            entity_type="worker",
            actor="fixture",
            result="RUNNING",
            external_reference="seeded-fresh-run",
            occurred_at=datetime.datetime.now(datetime.UTC),
            metadata_json={"run_id": "seeded-fresh-run", "fixture": "fresh_parity"},
        )
    )
    session.commit()
fresh_api, fresh_health = endpoint(), health()
assert fresh_api[0]["record_type"] == "run_begin"
assert fresh_api[0]["result"] == "RUNNING"
assert fresh_health["details"]["last_attempt_status"] == "RUNNING"
assert fresh_health["details"]["stale_running_run"] is False
assert fresh_health["details"]["stale_run_id"] is None
report["cases"]["seeded_fresh_running_parity"] = {"api": fresh_api, "health": fresh_health}

print(json.dumps(report, indent=2, sort_keys=True))
engine.dispose()

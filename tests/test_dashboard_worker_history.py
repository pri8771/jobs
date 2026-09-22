"""Focused regressions for the bounded dashboard worker-history feed."""

from __future__ import annotations

import datetime
import io
import json
import uuid
from collections.abc import Generator
from typing import Any, cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.dashboard.server import DashboardRequestHandler
from jobs_automation.db.base import Base
from jobs_automation.db.models import AuditLogModel
from jobs_automation.health import HealthCheckService
from jobs_automation.worker import WorkerDaemon


class WorkerHistoryHandler(DashboardRequestHandler):
    """Dispatch GET requests without opening a socket."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.command = "GET"
        self.path = "/api/worker"
        self.request_version = "HTTP/1.1"
        self.headers = cast(Any, {})
        self.mock_wfile = io.BytesIO()
        self.wfile = cast(Any, self.mock_wfile)
        self.session_factory = factory
        self.client_address = ("127.0.0.1", 12345)
        self.status_code = 200

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status_code = code

    def send_header(self, keyword: str, value: str) -> None:
        pass

    def end_headers(self) -> None:
        pass

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        self.status_code = code


@pytest.fixture
def history_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()


def get_worker_history(factory: sessionmaker[Session]) -> tuple[int, list[dict[str, Any]]]:
    handler = WorkerHistoryHandler(factory)
    handler.do_GET()
    return handler.status_code, json.loads(handler.mock_wfile.getvalue())


def audit(
    *,
    audit_id: str,
    action_type: str,
    result: str,
    occurred_at: datetime.datetime,
    external_reference: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLogModel:
    return AuditLogModel(
        id=uuid.UUID(audit_id),
        action_type=action_type,
        entity_type="worker",
        actor="worker_daemon",
        result=result,
        external_reference=external_reference,
        occurred_at=occurred_at,
        metadata_json=metadata or {},
    )


def test_actual_worker_success_returns_begin_and_finish(history_factory: sessionmaker[Session]) -> None:
    result = WorkerDaemon(
        history_factory,
        email_adapter=MockEmailAdapter([]),
        candidate_emails=["synthetic@example.invalid"],
    ).run_sweep(reconcile=False)

    assert result["errors"] == []
    health_before = HealthCheckService(history_factory).check_worker().model_dump(mode="json")
    status, rows = get_worker_history(history_factory)
    health_after = HealthCheckService(history_factory).check_worker().model_dump(mode="json")

    assert status == 200
    assert [row["record_type"] for row in rows] == ["run_finished", "run_begin"]
    assert [row["result"] for row in rows] == ["SUCCESS", "RUNNING"]
    assert {row["run_id"] for row in rows} == {result["run_id"]}
    assert rows[0]["metrics"]["final_status"] == "SUCCESS"
    assert rows[1]["metrics"]["run_id"] == result["run_id"]
    assert health_before["status"] == health_after["status"] == "HEALTHY"
    assert health_before["details"]["last_attempt_status"] == "SUCCESS"
    assert health_after["details"]["last_attempt_status"] == "SUCCESS"
    assert health_before["details"]["metrics"] == health_after["details"]["metrics"]
    assert health_after["details"]["metrics"]["run_id"] == result["run_id"]


def test_current_states_and_run_id_fallback_preserve_metadata(
    history_factory: sessionmaker[Session],
) -> None:
    now = datetime.datetime.now(datetime.UTC)
    partial_metrics = {"run_id": "partial-from-metadata", "error_count": 1, "marker": "keep"}
    failed_metrics = {"run_id": "ignored-metadata-id", "error_count": 2}
    running_metrics = {"started_at": now.isoformat()}
    with history_factory() as session:
        session.add_all(
            [
                audit(
                    audit_id="00000000-0000-0000-0000-000000000001",
                    action_type="worker_run_finished",
                    result="PARTIAL",
                    occurred_at=now - datetime.timedelta(seconds=2),
                    metadata=partial_metrics,
                ),
                audit(
                    audit_id="00000000-0000-0000-0000-000000000002",
                    action_type="worker_run_finished",
                    result="FAILED",
                    occurred_at=now - datetime.timedelta(seconds=1),
                    external_reference="failed-external-id",
                    metadata=failed_metrics,
                ),
                audit(
                    audit_id="00000000-0000-0000-0000-000000000003",
                    action_type="worker_run",
                    result="RUNNING",
                    occurred_at=now,
                    metadata=running_metrics,
                ),
            ]
        )
        session.commit()

    _, rows = get_worker_history(history_factory)

    assert [(row["record_type"], row["result"]) for row in rows] == [
        ("run_begin", "RUNNING"),
        ("run_finished", "FAILED"),
        ("run_finished", "PARTIAL"),
    ]
    assert rows[0]["run_id"] is None
    assert rows[1]["run_id"] == "failed-external-id"
    assert rows[2]["run_id"] == "partial-from-metadata"
    assert rows[0]["metrics"] == running_metrics
    assert rows[1]["metrics"] == failed_metrics
    assert rows[2]["metrics"] == partial_metrics


def test_legacy_fallback_combined_bound_and_tie_order(
    history_factory: sessionmaker[Session],
) -> None:
    base = datetime.datetime(2026, 9, 22, 12, 0, tzinfo=datetime.UTC)
    with history_factory() as session:
        for index in range(22):
            action_type = ("worker_run", "worker_run_finished", "worker_sweep")[index % 3]
            session.add(
                audit(
                    audit_id=f"00000000-0000-0000-0000-{index + 1:012d}",
                    action_type=action_type,
                    result=("RUNNING" if action_type == "worker_run" else "SUCCESS"),
                    occurred_at=base + datetime.timedelta(minutes=index),
                    external_reference=(f"run-{index}" if index % 2 == 0 else None),
                    metadata={"run_id": f"metadata-{index}", "ordinal": index},
                )
            )
        # Same newest timestamp: higher UUID must sort first.
        for suffix in (23, 24):
            session.add(
                audit(
                    audit_id=f"00000000-0000-0000-0000-{suffix:012d}",
                    action_type="worker_sweep",
                    result="SUCCESS",
                    occurred_at=base + datetime.timedelta(hours=1),
                    metadata={"ordinal": suffix},
                )
            )
        session.commit()

    status, rows = get_worker_history(history_factory)

    assert status == 200
    assert len(rows) == 20
    assert [row["metrics"]["ordinal"] for row in rows[:2]] == [24, 23]
    assert rows[0]["record_type"] == rows[1]["record_type"] == "legacy_sweep"
    assert rows[0]["run_id"] is None
    assert rows[1]["run_id"] is None
    assert {row["record_type"] for row in rows} == {
        "run_begin",
        "run_finished",
        "legacy_sweep",
    }
    assert all(set(row) == {"id", "result", "occurred_at", "metrics", "record_type", "run_id"} for row in rows)


def test_empty_worker_history_returns_ok(history_factory: sessionmaker[Session]) -> None:
    status, rows = get_worker_history(history_factory)

    assert status == 200
    assert rows == []

"""Safe, read-only dashboard projection of configuration validation status."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from test_dashboard import DummyRequestHandler

import jobs_automation.dashboard.server as dashboard_server

UNAVAILABLE = {
    "state": "UNAVAILABLE",
    "error_count": 0,
    "warning_count": 0,
    "loaded_config_count": 0,
    "loaded_config_names": [],
    "unresolved_fact_counts": {},
}


class _NoDatabase:
    def __call__(self) -> Any:
        raise AssertionError("config_status_must_not_open_database")


def _get(
    monkeypatch: pytest.MonkeyPatch, loader_type: type[Any]
) -> tuple[int, bytes, dict[str, Any]]:
    monkeypatch.setattr(dashboard_server, "ConfigLoader", loader_type, raising=False)
    handler = DummyRequestHandler("GET", "/api/config-status", session_factory=_NoDatabase())
    handler.do_GET()
    raw = handler.mock_wfile.getvalue()
    return handler.status_code, raw, json.loads(raw)


def test_config_status_valid_exact_allowlist_and_single_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"construct": 0, "validate": 0}
    report = SimpleNamespace(
        success=True,
        errors=[],
        warnings=["review required"],
        loaded_files={
            "platforms": "/private/config/platforms.yaml",
            "candidate_profile": "/private/config/candidate_profile.yaml",
            "job_search": "/private/config/job_search.yaml",
        },
        unresolved_facts={"work_authorization": [], "compensation": ["private fact"]},
    )

    class Loader:
        def __init__(self) -> None:
            calls["construct"] += 1

        def validate_all(self) -> Any:
            calls["validate"] += 1
            return report

    status, raw, body = _get(monkeypatch, Loader)

    assert status == 200
    assert body == {
        "state": "VALID",
        "error_count": 0,
        "warning_count": 1,
        "loaded_config_count": 3,
        "loaded_config_names": ["candidate_profile", "job_search", "platforms"],
        "unresolved_fact_counts": {"compensation": 1, "work_authorization": 0},
    }
    assert calls == {"construct": 1, "validate": 1}
    assert b"/private/config" not in raw
    assert b"private fact" not in raw


@pytest.mark.parametrize("success", [False, 1, "true", None])
def test_config_status_is_valid_only_for_literal_true(
    monkeypatch: pytest.MonkeyPatch, success: Any
) -> None:
    report = SimpleNamespace(
        success=success,
        errors=[],
        warnings=[],
        loaded_files={},
        unresolved_facts={},
    )

    class Loader:
        def validate_all(self) -> Any:
            return report

    status, _raw, body = _get(monkeypatch, Loader)
    assert status == 200
    assert body["state"] == "INVALID"


def test_config_status_invalid_exposes_counts_and_logical_names_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markers = (
        "gmail-secret-abc",
        "/Users/private/candidate.yaml",
        "postgresql://user:password@private/jobs",
        "candidate@example.test",
        "https://apply.private.test/job",
    )
    report = SimpleNamespace(
        success=False,
        errors=[markers[0], markers[1]],
        warnings=[markers[2], markers[3]],
        loaded_files={"policy_registry": markers[1], "model_routing": "/secret/model.yaml"},
        unresolved_facts={"identity": [markers[3]], "source": [markers[4], "token-raw"]},
    )

    class Loader:
        def validate_all(self) -> Any:
            return report

    status, raw, body = _get(monkeypatch, Loader)

    assert status == 200
    assert body == {
        "state": "INVALID",
        "error_count": 2,
        "warning_count": 2,
        "loaded_config_count": 2,
        "loaded_config_names": ["model_routing", "policy_registry"],
        "unresolved_fact_counts": {"identity": 1, "source": 2},
    }
    assert set(body) == {
        "state",
        "error_count",
        "warning_count",
        "loaded_config_count",
        "loaded_config_names",
        "unresolved_fact_counts",
    }
    for marker in (*markers, "/secret/model.yaml", "token-raw"):
        assert marker.encode() not in raw


@pytest.mark.parametrize("failure_at", ["constructor", "validation"])
def test_config_status_unexpected_exception_is_sanitized(
    monkeypatch: pytest.MonkeyPatch, failure_at: str
) -> None:
    marker = "Bearer private-token from /Users/private/config body=candidate-secret"

    class Loader:
        def __init__(self) -> None:
            if failure_at == "constructor":
                raise RuntimeError(marker)

        def validate_all(self) -> Any:
            raise RuntimeError(marker)

    status, raw, body = _get(monkeypatch, Loader)
    assert status == 200
    assert body == UNAVAILABLE
    assert marker.encode() not in raw


def test_config_status_has_no_post_mutation_route(monkeypatch: pytest.MonkeyPatch) -> None:
    class Loader:
        def __init__(self) -> None:
            raise AssertionError("POST must not construct ConfigLoader")

    monkeypatch.setattr(dashboard_server, "ConfigLoader", Loader, raising=False)
    handler = DummyRequestHandler("POST", "/api/config-status", session_factory=_NoDatabase())
    handler.do_POST()
    assert handler.status_code == 404
    assert handler.mock_wfile.getvalue() == b""

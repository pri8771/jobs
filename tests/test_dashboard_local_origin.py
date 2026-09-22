"""Focused tokenless-loopback write authority regressions."""

from __future__ import annotations

import json
import uuid
from email.message import Message
from typing import Any

import pytest

from tests.test_dashboard import DummyRequestHandler


class SessionFactorySpy:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> Any:
        self.calls += 1
        raise AssertionError("authorization denial must precede database access")


@pytest.fixture(autouse=True)
def local_write_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DASHBOARD_WRITE_TOKEN", raising=False)
    monkeypatch.setenv("DASHBOARD_ALLOW_LOCAL_WRITE", "true")


def handler(
    headers: Any,
    *,
    peer: str = "127.0.0.1",
    session_factory: Any = None,
) -> DummyRequestHandler:
    body = json.dumps({"resolution_notes": "synthetic"}).encode()
    request_headers = (
        {"Content-Length": str(len(body)), **headers} if isinstance(headers, dict) else headers
    )
    return DummyRequestHandler(
        method="POST",
        path=f"/api/reviews/{uuid.uuid4()}/resolve",
        body=body,
        headers=request_headers,
        session_factory=session_factory,
        client_address=(peer, 43210),
    )


@pytest.mark.parametrize(
    ("headers", "peer"),
    [
        ({"Host": "localhost"}, "127.0.0.1"),
        ({"Host": "127.0.0.1:8765"}, "127.0.0.1"),
        ({"Host": "[::1]:8765"}, "::1"),
        (
            {"Host": "localhost:8765", "Origin": "http://localhost:8765"},
            "127.0.0.1",
        ),
        (
            {"Host": "localhost", "Origin": "http://localhost"},
            "127.0.0.1",
        ),
        (
            {"Host": "localhost:80", "Origin": "http://localhost"},
            "127.0.0.1",
        ),
        (
            {"Host": "[0:0:0:0:0:0:0:1]:8765", "Origin": "http://[::1]:8765"},
            "::1",
        ),
        (
            {
                "Host": "localhost:8765",
                "Origin": "http://localhost:8765",
                "Sec-Fetch-Site": "same-origin",
            },
            "127.0.0.1",
        ),
        ({"Host": "localhost", "Sec-Fetch-Site": "none"}, "127.0.0.1"),
    ],
)
def test_tokenless_local_authority_accepts_only_valid_local_shapes(
    headers: dict[str, str], peer: str
) -> None:
    subject = handler(headers, peer=peer)
    assert subject._authorize_write_operation() is True


@pytest.mark.parametrize(
    ("headers", "peer"),
    [
        ({}, "127.0.0.1"),
        ({"Host": ""}, "127.0.0.1"),
        ({"Host": "localhost/path"}, "127.0.0.1"),
        ({"Host": "user@localhost"}, "127.0.0.1"),
        ({"Host": "localhost:bad"}, "127.0.0.1"),
        ({"Host": "localhost:0"}, "127.0.0.1"),
        ({"Host": "localhost:65536"}, "127.0.0.1"),
        ({"Host": "::1"}, "::1"),
        ({"Host": "example.test"}, "127.0.0.1"),
        ({"Host": "localhoſt"}, "127.0.0.1"),
        ({"Host": "127.0.0.1", "Origin": "https://foreign.example"}, "127.0.0.1"),
        ({"Host": "127.0.0.1", "Origin": "null"}, "127.0.0.1"),
        ({"Host": "127.0.0.1", "Origin": "http://127.0.0.1 http://localhost"}, "127.0.0.1"),
        ({"Host": "127.0.0.1", "Origin": "not an origin"}, "127.0.0.1"),
        ({"Host": "localhost", "Origin": "http://localhost/path"}, "127.0.0.1"),
        ({"Host": "localhost", "Origin": "https://localhost"}, "127.0.0.1"),
        ({"Host": "localhost:8765", "Origin": "http://localhost:8766"}, "127.0.0.1"),
        ({"Host": "localhost", "Sec-Fetch-Site": "cross-site"}, "127.0.0.1"),
        ({"Host": "localhost", "Sec-Fetch-Site": "same-site"}, "127.0.0.1"),
        ({"Host": "localhost", "Sec-Fetch-Site": "unexpected"}, "127.0.0.1"),
        ({"Host": "localhost", "Origin": "http://localhost"}, "192.0.2.10"),
        ({"Host": "localhost"}, "testclient"),
    ],
)
def test_tokenless_invalid_authority_denied_before_database(
    headers: dict[str, str], peer: str
) -> None:
    sessions = SessionFactorySpy()
    subject = handler(headers, peer=peer, session_factory=sessions)
    subject.do_POST()
    assert subject.status_code == 403
    assert sessions.calls == 0


def test_tokenless_local_write_disable_denied_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHBOARD_ALLOW_LOCAL_WRITE", "false")
    sessions = SessionFactorySpy()
    subject = handler({"Host": "localhost"}, session_factory=sessions)
    subject.do_POST()
    assert subject.status_code == 403
    assert sessions.calls == 0


@pytest.mark.parametrize("duplicate", ["Host", "Origin", "Sec-Fetch-Site"])
def test_duplicate_authority_headers_fail_closed(duplicate: str) -> None:
    headers = Message()
    headers["Content-Length"] = "2"
    headers["Host"] = "localhost"
    headers["Origin"] = "http://localhost"
    headers["Sec-Fetch-Site"] = "same-origin"
    headers[duplicate] = headers[duplicate]
    subject = handler(headers)
    assert subject._authorize_write_operation() is False
    assert subject.status_code == 403


def test_exact_token_branch_ignores_tokenless_host_origin_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHBOARD_WRITE_TOKEN", "exact-secret")
    subject = handler(
        {
            "Host": "foreign.example",
            "Origin": "https://foreign.example",
            "Sec-Fetch-Site": "cross-site",
            "X-Operator-Token": "exact-secret",
        },
        peer="192.0.2.10",
    )
    assert subject._authorize_write_operation() is True


@pytest.mark.parametrize("provided", [None, "wrong-secret"])
def test_configured_missing_or_wrong_token_is_401_without_fallback(
    monkeypatch: pytest.MonkeyPatch, provided: str | None
) -> None:
    monkeypatch.setenv("DASHBOARD_WRITE_TOKEN", "exact-secret")
    headers = {"Host": "localhost", "Origin": "http://localhost"}
    if provided is not None:
        headers["X-Operator-Token"] = provided
    sessions = SessionFactorySpy()
    subject = handler(headers, session_factory=sessions)
    subject.do_POST()
    assert subject.status_code == 401
    assert sessions.calls == 0


def test_unsupported_mutation_path_remains_unavailable() -> None:
    subject = handler({"Host": "localhost"})
    subject.path = "/api/config-status"
    subject.do_POST()
    assert subject.status_code == 404

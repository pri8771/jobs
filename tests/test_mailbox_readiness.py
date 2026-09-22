"""V17-M03: secret-safe Gmail readiness states without OAuth or mailbox access."""

from __future__ import annotations

import datetime
import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.core.config import AppSettings
from jobs_automation.db.models import AuditLogModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.readiness import (
    BOUNDED_RUN_ACTION,
    READONLY_SCOPE,
    assess_gmail_readiness,
)

SECRET_ACCESS = "ya29.synthetic-access-token-value"
SECRET_REFRESH = "1//synthetic-refresh-token-value"
SECRET_CLIENT = "synthetic-client-secret-value"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _no_network_or_oauth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Readiness must never launch OAuth, refresh tokens or build an API client."""
    import google_auth_oauthlib.flow as flow_module
    import googleapiclient.discovery as discovery_module

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("readiness assessment must not launch OAuth or call the API")

    monkeypatch.setattr(flow_module.InstalledAppFlow, "from_client_config", _forbidden)
    monkeypatch.setattr(discovery_module, "build", _forbidden)


def _settings(tmp_path: Path, *, configured: bool = True) -> AppSettings:
    return AppSettings(
        gmail_client_id="synthetic-client-id" if configured else None,
        gmail_client_secret=SECRET_CLIENT if configured else None,
        gmail_token_path=str(tmp_path / "gmail_token.json"),
    )


def _write_token(tmp_path: Path, *, scopes: list[str], expiry: str | None, refresh: bool) -> None:
    payload = {
        "token": SECRET_ACCESS,
        "refresh_token": SECRET_REFRESH if refresh else None,
        "client_id": "synthetic-client-id",
        "client_secret": SECRET_CLIENT,
        "scopes": scopes,
        "expiry": expiry,
        "account": "owner.person@gmail.com",
    }
    (tmp_path / "gmail_token.json").write_text(json.dumps(payload), encoding="utf-8")


def _record_run(
    session: Session, *, adapter: str, synthetic: bool, complete: bool, result: str
) -> None:
    session.add(
        AuditLogModel(
            action_type=BOUNDED_RUN_ACTION,
            entity_type="mailbox",
            actor="bounded_ingestion",
            result=result,
            external_reference="run-1",
            metadata_json={
                "run_id": "run-1",
                "adapter": adapter,
                "synthetic": synthetic,
                "complete": complete,
                "status": result,
            },
        )
    )
    session.commit()


def test_not_configured_without_client(tmp_path: Path) -> None:
    report = assess_gmail_readiness(_settings(tmp_path, configured=False))
    assert report.state == "NOT_CONFIGURED"
    assert report.live_capable is False
    assert report.error_category == "CLIENT_NOT_CONFIGURED"


def test_configured_without_token_is_not_connected(tmp_path: Path) -> None:
    report = assess_gmail_readiness(_settings(tmp_path))
    assert report.state == "CONFIGURED"
    assert report.token_present is False
    assert report.error_category == "TOKEN_MISSING"


def test_alias_or_config_file_alone_is_not_an_oauth_grant(tmp_path: Path) -> None:
    (tmp_path / "gmail_token.json").write_text(
        "mailbox: unsubscriber+alias@gmail.com\nnote: this is an alias config, not a token\n",
        encoding="utf-8",
    )
    report = assess_gmail_readiness(_settings(tmp_path))
    assert report.state == "CONFIGURED"
    assert report.credentials_parseable is False
    assert report.error_category == "TOKEN_UNPARSEABLE"
    assert any("not an OAuth grant" in note for note in report.notes)


def test_broader_scope_is_not_a_readonly_grant(tmp_path: Path) -> None:
    _write_token(
        tmp_path,
        scopes=[READONLY_SCOPE, "https://www.googleapis.com/auth/gmail.modify"],
        expiry=None,
        refresh=True,
    )
    report = assess_gmail_readiness(_settings(tmp_path))
    assert report.state == "CONFIGURED"
    assert report.scope_is_readonly_only is False
    assert report.error_category == "SCOPE_NOT_READONLY_ONLY"


def test_expired_token_without_refresh_is_not_connected(tmp_path: Path) -> None:
    _write_token(tmp_path, scopes=[READONLY_SCOPE], expiry="2020-01-01T00:00:00Z", refresh=False)
    report = assess_gmail_readiness(_settings(tmp_path))
    assert report.state == "CONFIGURED"
    assert report.token_expired is True
    assert report.error_category == "TOKEN_EXPIRED_NO_REFRESH"


def test_readonly_token_is_connected_but_not_proven(tmp_path: Path, db_session: Session) -> None:
    _write_token(tmp_path, scopes=[READONLY_SCOPE], expiry="2020-01-01T00:00:00Z", refresh=True)
    report = assess_gmail_readiness(_settings(tmp_path), db_session)
    assert report.state == "CONNECTED"
    assert report.live_capable is True
    assert report.api_canary_ok is None
    assert report.mailbox_identity_hint == "o***@gmail.com"
    assert report.last_proven_run_id is None


def test_synthetic_or_incomplete_runs_do_not_prove(tmp_path: Path, db_session: Session) -> None:
    _write_token(tmp_path, scopes=[READONLY_SCOPE], expiry=None, refresh=True)
    _record_run(
        db_session, adapter="mock_fixtures", synthetic=True, complete=True, result="SUCCESS"
    )
    assert assess_gmail_readiness(_settings(tmp_path), db_session).state == "CONNECTED"
    _record_run(db_session, adapter="gmail", synthetic=False, complete=False, result="INCOMPLETE")
    assert assess_gmail_readiness(_settings(tmp_path), db_session).state == "CONNECTED"


def test_real_complete_run_proves(tmp_path: Path, db_session: Session) -> None:
    _write_token(tmp_path, scopes=[READONLY_SCOPE], expiry=None, refresh=True)
    _record_run(db_session, adapter="gmail", synthetic=False, complete=True, result="SUCCESS")
    report = assess_gmail_readiness(_settings(tmp_path), db_session)
    assert report.state == "PROVEN"
    assert report.last_proven_run_id == "run-1"
    assert report.api_canary_ok is True
    assert report.error_category is None
    assert report.to_health_result()["status"] == "HEALTHY"


def test_report_never_serializes_secrets(tmp_path: Path, db_session: Session) -> None:
    _write_token(tmp_path, scopes=[READONLY_SCOPE], expiry=None, refresh=True)
    report = assess_gmail_readiness(_settings(tmp_path), db_session)
    serialized = report.model_dump_json() + json.dumps(report.to_health_result())
    for secret in (SECRET_ACCESS, SECRET_REFRESH, SECRET_CLIENT, "owner.person@gmail.com"):
        assert secret not in serialized
    assert report.token_path.endswith("gmail_token.json")
    assert datetime.datetime.fromisoformat(report.checked_at).tzinfo is not None

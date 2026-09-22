"""Secret-safe Gmail mailbox readiness (V17-M03).

Readiness is assessed without launching OAuth, refreshing tokens or touching the mailbox:
it inspects configuration, the on-disk authorized-user token (structure and scopes only)
and the recorded outcome of previous real bounded ingestion runs. It never reads or
serializes the client secret, access token or refresh token.

States:

* ``NOT_CONFIGURED`` — no OAuth client configured.
* ``CONFIGURED``     — client configured; no usable token (an alias or config file alone is
                       never a successful OAuth grant).
* ``CONNECTED``      — a parseable authorized-user token exists with exactly the
                       ``gmail.readonly`` scope and is refreshable or unexpired.
* ``PROVEN``         — CONNECTED and a real (non-synthetic), complete bounded ingestion run
                       against the mailbox is on record.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.core.config import AppSettings
from jobs_automation.db.models import AuditLogModel

logger = logging.getLogger(__name__)

READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
BOUNDED_RUN_ACTION = "mailbox_ingestion_run"
ReadinessState = Literal["NOT_CONFIGURED", "CONFIGURED", "CONNECTED", "PROVEN"]


class GmailReadinessReport(BaseModel):
    """Typed, secret-free readiness boundary (J20G-03 shape, V17-M03 semantics)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["REAL"] = "REAL"
    state: ReadinessState
    configured: bool
    token_path: str
    token_present: bool
    credentials_parseable: bool
    scopes: list[str] = Field(default_factory=list)
    scope_is_readonly_only: bool = False
    refresh_token_present: bool = False
    token_expired: bool | None = None
    refresh_ok: bool | None = None
    api_canary_ok: bool | None = None
    mailbox_identity_hint: str | None = None
    last_proven_run_id: str | None = None
    last_proven_at: str | None = None
    error_category: str | None = None
    checked_at: str
    notes: list[str] = Field(default_factory=list)

    @property
    def live_capable(self) -> bool:
        return self.state in ("CONNECTED", "PROVEN")

    def to_health_result(self) -> dict[str, Any]:
        """Shape consumed by ``HealthCheckService.check_gmail(readiness_result=...)``."""
        status = "HEALTHY" if self.state == "PROVEN" else "DEGRADED"
        return {
            "status": status,
            "message": f"Gmail readiness: {self.state}",
            "readiness_state": self.state,
            "live_capable": self.live_capable,
            "configured": self.configured,
            "token_present": self.token_present,
            "credentials_parseable": self.credentials_parseable,
            "scope_is_readonly_only": self.scope_is_readonly_only,
            "last_proven_run_id": self.last_proven_run_id,
            "last_proven_at": self.last_proven_at,
            "error_category": self.error_category,
            "checked_at": self.checked_at,
        }


def mask_identity(address: str | None) -> str | None:
    """Keep only the first character of the local part plus the domain."""
    if not address or "@" not in address:
        return None
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain.lower()}" if local else f"***@{domain.lower()}"


def _parse_token_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Return (structure, error_category); never returns secret values."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "TOKEN_UNPARSEABLE"
    if not isinstance(raw, dict):
        return None, "TOKEN_UNPARSEABLE"
    has_credential_shape = any(key in raw for key in ("token", "refresh_token", "scopes"))
    if not has_credential_shape:
        return None, "TOKEN_UNPARSEABLE"
    scopes_raw = raw.get("scopes")
    scopes = [str(scope) for scope in scopes_raw] if isinstance(scopes_raw, list) else []
    structure: dict[str, Any] = {
        "scopes": scopes,
        "refresh_token_present": bool(raw.get("refresh_token")),
        "access_token_present": bool(raw.get("token")),
        "expiry": str(raw["expiry"]) if raw.get("expiry") else None,
        "account": str(raw["account"]) if raw.get("account") else None,
    }
    return structure, None


def _latest_proven_run(session: Session | None) -> tuple[str | None, str | None]:
    if session is None:
        return None, None
    rows = session.scalars(
        select(AuditLogModel)
        .where(AuditLogModel.action_type == BOUNDED_RUN_ACTION)
        .order_by(AuditLogModel.occurred_at.desc())
    ).all()
    for row in rows:
        metadata = row.metadata_json or {}
        if (
            row.result == "SUCCESS"
            and metadata.get("adapter") == "gmail"
            and metadata.get("synthetic") is False
            and metadata.get("complete") is True
        ):
            return str(metadata.get("run_id") or row.external_reference or row.id), (
                row.occurred_at.isoformat() if row.occurred_at else None
            )
    return None, None


def assess_gmail_readiness(
    settings: AppSettings | None = None,
    session: Session | None = None,
    token_path: str | Path | None = None,
    now: datetime.datetime | None = None,
) -> GmailReadinessReport:
    """Assess readiness from configuration, token structure and recorded real runs only."""
    settings = settings or AppSettings()
    now = now or datetime.datetime.now(datetime.UTC)
    path = Path(token_path or settings.gmail_token_path)
    notes: list[str] = []

    configured = bool(settings.gmail_client_id and settings.gmail_client_secret)
    token_present = path.is_file()
    structure: dict[str, Any] | None = None
    error_category: str | None = None
    if token_present:
        structure, error_category = _parse_token_file(path)
        if structure is None:
            notes.append(
                "token file is not an authorized-user credential; an alias or config file is "
                "not an OAuth grant"
            )

    scopes = list(structure["scopes"]) if structure else []
    scope_is_readonly_only = bool(scopes) and set(scopes) == {READONLY_SCOPE}
    refresh_token_present = bool(structure and structure["refresh_token_present"])
    token_expired: bool | None = None
    if structure and structure.get("expiry"):
        try:
            expiry = datetime.datetime.fromisoformat(
                str(structure["expiry"]).replace("Z", "+00:00")
            )
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.UTC)
            token_expired = expiry <= now
        except ValueError:
            token_expired = None

    if structure is not None and not scope_is_readonly_only:
        error_category = "SCOPE_NOT_READONLY_ONLY"
        notes.append("token scopes must be exactly gmail.readonly")
    if structure is not None and token_expired and not refresh_token_present:
        error_category = "TOKEN_EXPIRED_NO_REFRESH"
        notes.append("access token expired and no refresh token is present")

    connected = (
        configured
        and token_present
        and structure is not None
        and scope_is_readonly_only
        and (refresh_token_present or token_expired is False)
    )

    last_run_id, last_run_at = (None, None)
    if connected:
        last_run_id, last_run_at = _latest_proven_run(session)
        if session is None:
            notes.append("no database session: PROVEN cannot be assessed")

    if not configured:
        state: ReadinessState = "NOT_CONFIGURED"
        if error_category is None:
            error_category = "CLIENT_NOT_CONFIGURED"
    elif not connected:
        state = "CONFIGURED"
        if error_category is None:
            error_category = "TOKEN_MISSING" if not token_present else "TOKEN_NOT_USABLE"
    elif last_run_id:
        state = "PROVEN"
    else:
        state = "CONNECTED"
        notes.append("no real complete bounded ingestion run recorded yet")

    return GmailReadinessReport(
        state=state,
        configured=configured,
        token_path=str(path),
        token_present=token_present,
        credentials_parseable=structure is not None,
        scopes=scopes,
        scope_is_readonly_only=scope_is_readonly_only,
        refresh_token_present=refresh_token_present,
        token_expired=token_expired,
        refresh_ok=None,
        api_canary_ok=True if state == "PROVEN" else None,
        mailbox_identity_hint=mask_identity(structure.get("account")) if structure else None,
        last_proven_run_id=last_run_id,
        last_proven_at=last_run_at,
        error_category=error_category if state != "PROVEN" else None,
        checked_at=now.isoformat(),
        notes=notes,
    )

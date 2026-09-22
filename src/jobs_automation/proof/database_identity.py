"""Private proof DB identity; credentials stay in runtime configuration.

This module does not connect to a database or validate proof rows. It prevents
using a password-masked display URL as a connection string. The calling verifier
must still open and independently validate the persisted proof database.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.engine import URL, make_url

SUPPORTED_PROOF_DRIVERS = frozenset(
    {"postgresql", "postgresql+psycopg", "postgresql+psycopg2", "sqlite", "sqlite+pysqlite"}
)


class ProofDatabaseIdentityError(ValueError):
    """Safe reason code only: never echo an input URL or driver exception."""


def _url(value: str | URL) -> URL:
    try:
        result = value if isinstance(value, URL) else make_url(value)
        if result.password == "***":
            raise ProofDatabaseIdentityError("MASKED_DATABASE_CREDENTIAL")
        return result
    except ProofDatabaseIdentityError:
        raise
    except Exception:
        raise ProofDatabaseIdentityError("INVALID_DATABASE_URL") from None


def database_identity(value: str | URL) -> dict[str, Any]:
    """Return private non-secret target metadata; never use this to connect.

    SQLAlchemy driver, username, endpoint and route options are bound. Passwords
    may rotate without changing target identity. Query-string credentials are
    rejected rather than copied into evidence. Result belongs in the PRIVATE
    proof bundle, not the public/redacted receipt.
    """
    url = _url(value)
    driver = url.drivername
    if driver in {"postgres", "postgresql"}:
        driver = "postgresql"
    if driver not in SUPPORTED_PROOF_DRIVERS:
        raise ProofDatabaseIdentityError("UNSUPPORTED_PROOF_DATABASE_DRIVER")
    for key in url.query:
        if any(
            token in key.lower()
            for token in ("password", "secret", "token", "credential", "api_key")
        ):
            raise ProofDatabaseIdentityError("QUERY_CREDENTIALS_NOT_ALLOWED")
    if not url.database:
        raise ProofDatabaseIdentityError("DATABASE_NAME_REQUIRED")
    route = {key: list(values) for key, values in sorted(url.normalized_query.items())}
    route_hash = hashlib.sha256(
        json.dumps(route, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if driver.startswith("sqlite"):
        if url.database == ":memory:" or route:
            raise ProofDatabaseIdentityError("PERSISTED_PLAIN_SQLITE_REQUIRED")
        database = str(Path(url.database).expanduser().resolve())
        port = None
    else:
        database = url.database
        port = url.port or 5432
    return {
        "version": 1,
        "driver": driver,
        "host": (url.host or "").lower(),
        "port": port,
        "database": database,
        "username": url.username or "",
        "route_options_sha256": route_hash,
    }


def resolve_runtime_database(reference: dict[str, Any], runtime_url: str | URL) -> URL:
    """Resolve from trusted runtime config and verify exact private target binding.

    Return the URL object, not str(URL), so its password is not replaced by ***.
    The caller must not log/render it with credentials or serialize it to proof.
    If its engine factory requires str, use render_as_string(hide_password=False)
    only at the private connection call, with no logging or receipt serialization.
    """
    url = _url(runtime_url)
    if reference != database_identity(url):
        raise ProofDatabaseIdentityError("PROOF_DATABASE_TARGET_MISMATCH")
    if url.drivername == "postgres":
        url = url.set(drivername="postgresql")
    return url

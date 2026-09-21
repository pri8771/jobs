import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.engine import make_url

from scripts.proof_database_identity import (
    ProofDatabaseIdentityError,
    database_identity,
    resolve_runtime_database,
)

URL = 'postgresql+psycopg://jobs:only-a-test-secret@localhost:5432/jobs'


def test_reference_contains_no_password_and_roundtrip_retains_runtime_credential() -> None:
    ref = database_identity(URL)
    assert 'only-a-test-secret' not in json.dumps(ref)
    actual = resolve_runtime_database(ref, URL)
    assert actual.password == 'only-a-test-secret'


def test_sqlalchemy_display_string_is_not_connection_roundtrip() -> None:
    original = make_url(URL)
    assert make_url(str(original)).password == '***'
    with pytest.raises(ProofDatabaseIdentityError, match='MASKED_DATABASE_CREDENTIAL'):
        resolve_runtime_database(database_identity(original), str(original))


def test_password_rotation_does_not_change_db_identity() -> None:
    rotated = make_url(URL).set(password='rotated-test-only-secret')
    assert database_identity(rotated) == database_identity(URL)
    assert resolve_runtime_database(database_identity(URL), rotated).password == 'rotated-test-only-secret'


@pytest.mark.parametrize('change', [
    {'host': 'other'}, {'database': 'other'}, {'username': 'other'},
    {'port': 5433}, {'drivername': 'postgresql+psycopg2'},
    {'query': {'sslmode': 'require'}},
])
def test_mismatched_database_target_rejected(change: dict[str, Any]) -> None:
    with pytest.raises(ProofDatabaseIdentityError, match='TARGET_MISMATCH'):
        resolve_runtime_database(database_identity(URL), make_url(URL).set(**change))


def test_default_port_and_explicit_port_are_same_identity() -> None:
    assert database_identity(URL) == database_identity(make_url(URL).set(port=None)._replace(port=None))


@pytest.mark.parametrize('target', [
    'postgresql+asyncpg://u:p@host/db', 'mysql+pymysql://u:p@host/db',
    'sqlite:///:memory:', 'postgresql+psycopg://u:p@host',
    'postgresql+psycopg://u:p@host/db?password=hidden-test-only',
])
def test_invalid_or_unsupported_targets_fail_without_values(target: str) -> None:
    with pytest.raises(ProofDatabaseIdentityError) as exc:
        database_identity(target)
    assert target not in str(exc.value)
    assert 'hidden-test-only' not in str(exc.value)


def test_private_sqlite_path_binding_is_canonical(tmp_path: Path) -> None:
    path = tmp_path / 'proof.db'
    ref = database_identity('sqlite:///' + str(path))
    assert ref['database'] == str(path.resolve())
    assert resolve_runtime_database(ref, 'sqlite:///' + str(path)).database == str(path)


def test_extra_reference_field_rejected() -> None:
    ref = database_identity(URL) | {'pass': True}
    with pytest.raises(ProofDatabaseIdentityError, match='TARGET_MISMATCH'):
        resolve_runtime_database(ref, URL)


def test_missing_reference_field_rejected() -> None:
    ref = database_identity(URL)
    del ref['database']
    with pytest.raises(ProofDatabaseIdentityError, match='TARGET_MISMATCH'):
        resolve_runtime_database(ref, URL)


def test_postgres_alias_normalizes_without_masking() -> None:
    value = 'postgres://jobs:test-only@localhost/jobs'
    result = resolve_runtime_database(database_identity(value), value)
    assert result.drivername == 'postgresql'
    assert result.password == 'test-only'

"""Producer-to-consumer engineering integration test for the V1.4 real-proof chain (F145-06).

This test drives the *actual* production services end to end, on SQLite and on a real,
password-protected PostgreSQL database when ``PROOF_TEST_PG_ADMIN_URL`` is available:

1. ``scripts/import_v14_proof_job.py`` (Greenhouse fetch monkeypatched to a canonical
   engineering payload) persists Company/Job/JobSource through its own code path;
2. ``scripts/run_v14_real_proof.py`` runs as a subprocess against the trusted runtime
   ``DATABASE_URL`` and emits the redacted candidate + private bundle;
3. ``scripts/verify_v14_real_proof.py`` runs as a subprocess with only ``DATABASE_URL``
   as its database knowledge and must reach ``REAL_PROOF_PASS``;
4. adversarial cases on the very same evidence must fail: runtime target mismatch,
   stale credential after password rotation, missing runtime configuration, and
   single-field database mutations (answers, unresolved list, variant version).

Engineering evidence namespace
------------------------------
Everything is written under ``.local/engineering_proof_<id>/`` inside the repository
(gitignored), never under ``coordination/proofs``. The candidate bundle produced here
is engineering evidence for compatibility only and is never published as REAL_PROOF.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationPacketModel,
    JobSourceModel,
    ResumeVariantModel,
)
from jobs_automation.db.session import get_engine, get_sessionmaker
from scripts import import_v14_proof_job
from scripts.verify_v14_real_proof import validate_redacted_bundle_schema
from tests.test_real_proof_verifier import engineering_profile_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER_SCRIPT = REPO_ROOT / "scripts" / "run_v14_real_proof.py"
VERIFIER_SCRIPT = REPO_ROOT / "scripts" / "verify_v14_real_proof.py"

ENGINEERING_GREENHOUSE_JOB_ID = "999000111"
ENGINEERING_JOB_URL = (
    f"https://job-boards.greenhouse.io/opensesame/jobs/{ENGINEERING_GREENHOUSE_JOB_ID}"
)
ENGINEERING_CONTENT_HTML = (
    "<div><p>OpenSesame is hiring an AI Automation Engineer to design, build and operate "
    "production automation for enterprise learning workflows.</p>"
    "<p>You will own resilient ingestion pipelines, public job board API integrations, "
    "deterministic packet generation and independent evidence verification. The role "
    "requires strong Python, careful data modelling, and a bias toward verifiable "
    "systems over demos.</p>"
    "<ul><li>Build and maintain automation services with exact provenance.</li>"
    "<li>Design database schemas and migrations for auditable state.</li>"
    "<li>Partner with recruiting operations on measurable lifecycle outcomes.</li>"
    "<li>Document runbooks so that every production step can be reproduced.</li></ul>"
    "<p>This engineering posting text exists only to exercise the proof chain end to end "
    "against the production importer, packet builder and verifier.</p></div>"
)


def _engineering_payload() -> dict[str, Any]:
    return {
        "id": int(ENGINEERING_GREENHOUSE_JOB_ID),
        "title": "AI Automation Engineer",
        "location": {"name": "Remote, US"},
        "content": ENGINEERING_CONTENT_HTML,
        "questions": [
            {"label": "First Name*"},
            {"label": "Last Name*"},
            {"label": "Email*"},
            {"label": "Resume/CV*"},
            {"label": "Are you legally authorized to work in the United States?*"},
            {
                "label": (
                    "Will you now or in the future require sponsorship for employment visa status?*"
                )
            },
            {"label": "Describe a reusable automation system you built.*"},
        ],
    }


@dataclasses.dataclass
class RuntimeBackend:
    """One trusted runtime database for a full producer-to-consumer run."""

    name: str
    url: str
    # A runtime URL on the same server/file layout that names a *different* database.
    mismatched_url: str
    # PostgreSQL only: rotate the role password and return the new runtime URL.
    rotate_password: Callable[[], str] | None = None
    # PostgreSQL only: the runtime URL with the credential that was valid before rotation.
    stale_url: str | None = None


@pytest.fixture
def engineering_namespace() -> Iterator[Path]:
    namespace = REPO_ROOT / ".local" / f"engineering_proof_{uuid.uuid4().hex[:10]}"
    namespace.mkdir(parents=True, exist_ok=False)
    try:
        yield namespace
    finally:
        shutil.rmtree(namespace, ignore_errors=True)


@pytest.fixture
def engineering_private_profile_namespace() -> Iterator[Path]:
    """Create disposable profile inputs at a path accepted by the production guard.

    The runner must reject temporary and pytest-owned profile paths in a real invocation.
    This integration test itself runs from an isolated temporary checkout, so its
    engineering-only candidate profile and resume live under a unique cache directory
    outside that checkout.  The fixture owns and removes only its UUID-named child.
    """
    namespace = (
        Path.home()
        / ".cache"
        / "jobs-automation"
        / "engineering-real-proof-inputs"
        / f"private_profile_{uuid.uuid4().hex}"
    )
    lowered = str(namespace).lower()
    if "tmp" in namespace.parts or "pytest" in lowered:
        raise RuntimeError(
            "Engineering proof profile fixture requires a non-temporary, non-pytest path"
        )
    namespace.mkdir(parents=True, exist_ok=False)
    try:
        yield namespace
    finally:
        shutil.rmtree(namespace, ignore_errors=True)


def _sqlite_backend(namespace: Path) -> Iterator[RuntimeBackend]:
    db_file = namespace / "engineering_proof.db"
    url = f"sqlite:///{db_file}"
    engine = get_engine(url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    other_file = namespace / "other_runtime.db"
    other_engine = get_engine(f"sqlite:///{other_file}")
    Base.metadata.create_all(bind=other_engine)
    other_engine.dispose()
    yield RuntimeBackend(name="sqlite", url=url, mismatched_url=f"sqlite:///{other_file}")


def _postgres_backend() -> Iterator[RuntimeBackend]:
    admin_raw = os.environ.get("PROOF_TEST_PG_ADMIN_URL")
    if not admin_raw:
        pytest.skip(
            "PROOF_TEST_PG_ADMIN_URL not set: the PostgreSQL production-path integration "
            "needs an admin connection that can create a throwaway role and database"
        )
    admin_url = make_url(admin_raw)
    token = uuid.uuid4().hex[:10]
    role = f"proof_it_role_{token}"
    database = f"proof_it_{token}"
    password_a = f"a{uuid.uuid4().hex}"
    password_b = f"b{uuid.uuid4().hex}"

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            # Identifiers and passwords are hex tokens generated above: safe to inline.
            conn.execute(text(f"CREATE ROLE \"{role}\" LOGIN PASSWORD '{password_a}'"))
            conn.execute(text(f'CREATE DATABASE "{database}" OWNER "{role}"'))
            conn.execute(text(f'CREATE DATABASE "{database}_other" OWNER "{role}"'))

        runtime_url = admin_url.set(
            drivername="postgresql+psycopg", username=role, password=password_a, database=database
        )
        runtime_a = runtime_url.render_as_string(hide_password=False)
        upgrade = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=REPO_ROOT,
            env={**os.environ, "DATABASE_URL": runtime_a},
            check=False,
            capture_output=True,
            text=True,
        )
        assert upgrade.returncode == 0, upgrade.stderr[-2000:]

        def rotate_password() -> str:
            with admin_engine.connect() as conn:
                conn.execute(text(f"ALTER ROLE \"{role}\" PASSWORD '{password_b}'"))
            return runtime_url.set(password=password_b).render_as_string(hide_password=False)

        yield RuntimeBackend(
            name="postgresql",
            url=runtime_a,
            mismatched_url=runtime_url.set(database=f"{database}_other").render_as_string(
                hide_password=False
            ),
            rotate_password=rotate_password,
            stale_url=runtime_a,
        )
    finally:
        with admin_engine.connect() as conn:
            for name in (database, f"{database}_other"):
                conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            conn.execute(text(f'DROP ROLE IF EXISTS "{role}"'))
        admin_engine.dispose()


@pytest.fixture(params=["sqlite", "postgresql"])
def runtime_backend(
    request: pytest.FixtureRequest, engineering_namespace: Path
) -> Iterator[RuntimeBackend]:
    if request.param == "sqlite":
        yield from _sqlite_backend(engineering_namespace)
    else:
        yield from _postgres_backend()


def _subprocess_env(runtime_url: str | None) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    if runtime_url is not None:
        env["DATABASE_URL"] = runtime_url
    return env


def _run_import(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_url: str,
    namespace: Path,
) -> tuple[str, Path]:
    """Run the production importer in-process with the Greenhouse fetch stubbed."""
    questions_output = namespace / "questions.json"

    def fake_fetch(url: str) -> dict[str, Any]:
        assert url == (
            "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/"
            f"{ENGINEERING_GREENHOUSE_JOB_ID}?questions=true"
        )
        return _engineering_payload()

    monkeypatch.setattr(import_v14_proof_job, "_fetch_json", fake_fetch)
    monkeypatch.setenv("DATABASE_URL", runtime_url)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "import_v14_proof_job.py",
            "--job-id",
            ENGINEERING_GREENHOUSE_JOB_ID,
            "--job-url",
            ENGINEERING_JOB_URL,
            "--questions-output",
            str(questions_output),
        ],
    )
    exit_code = import_v14_proof_job.main()
    captured = capsys.readouterr()
    assert exit_code == 0, captured.out
    assert "REAL_PROOF_JOB_IMPORT_PASS" in captured.out
    match = re.search(r"^job_id=([0-9a-f-]{36})$", captured.out, flags=re.MULTILINE)
    assert match is not None, captured.out
    return match.group(1), questions_output


def _run_runner(
    runtime_url: str, namespace: Path, job_id: str, profile_path: Path, questions_path: Path
) -> tuple[Path, Path, str]:
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_SCRIPT),
            "--job-id",
            job_id,
            "--candidate-profile",
            str(profile_path),
            "--questions-json",
            str(questions_path),
            "--redacted-output-dir",
            str(namespace / "redacted"),
            "--private-output-dir",
            str(namespace / "private"),
        ],
        cwd=REPO_ROOT,
        env=_subprocess_env(runtime_url),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "REAL_PROOF_RUN_COMPLETE" in result.stdout
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    return (
        Path(fields["candidate_bundle"]),
        Path(fields["private_bundle"]),
        fields["candidate_bundle_sha256"],
    )


def _run_verifier(
    runtime_url: str | None, candidate_path: Path, private_path: Path, receipt_path: Path
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    result = subprocess.run(
        [
            sys.executable,
            str(VERIFIER_SCRIPT),
            str(candidate_path),
            "--local-full-bundle",
            str(private_path),
            "--receipt-output",
            str(receipt_path),
        ],
        cwd=REPO_ROOT,
        env=_subprocess_env(runtime_url),
        check=False,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return result, receipt


def _mutate(runtime_url: str, mutate: Callable[[Any], None]) -> None:
    engine = get_engine(runtime_url)
    try:
        with get_sessionmaker(engine)() as session:
            mutate(session)
            session.commit()
    finally:
        engine.dispose()


def test_v14_proof_chain_producer_to_consumer_on_production_services(
    runtime_backend: RuntimeBackend,
    engineering_namespace: Path,
    engineering_private_profile_namespace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    namespace = engineering_namespace
    private_profile_namespace = engineering_private_profile_namespace
    runtime_url = runtime_backend.url

    # 1. Production importer persists the job through its own code path.
    job_id, questions_path = _run_import(monkeypatch, capsys, runtime_url, namespace)
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    assert len(questions) == 3

    # 2. Canonical engineering profile + genuine-shaped resume file in a disposable
    # private-looking namespace accepted by the production path guard.
    resume_path = private_profile_namespace / "engineering_resume_ai_software_engineer.md"
    resume_path.write_text(
        "# Engineering Candidate\n\nBuilds verifiable automation systems.\n", encoding="utf-8"
    )
    profile_path = private_profile_namespace / "candidate_profile.yaml"
    profile_path.write_text(engineering_profile_yaml(resume_path.resolve()), encoding="utf-8")

    # 3. Production runner (subprocess) against the trusted runtime database.
    candidate_path, private_path, candidate_sha = _run_runner(
        runtime_url, namespace, job_id, profile_path, questions_path
    )
    assert candidate_path.resolve().is_relative_to(namespace.resolve())
    assert private_path.resolve().is_relative_to(namespace.resolve())

    redacted = json.loads(candidate_path.read_text(encoding="utf-8"))
    private_bundle = json.loads(private_path.read_text(encoding="utf-8"))
    validate_redacted_bundle_schema(redacted)
    assert redacted["result"] == "REAL_PROOF_CANDIDATE"
    assert redacted["resume_variant"] == "resume_ai_software_engineer"
    assert redacted["resolved_answers_count"] == 2
    assert len(redacted["unresolved_questions"]) == 1
    assert redacted["questions_count"] == 3

    # FR14-02: the private bundle carries a database identity, never a connection string.
    assert "database_url" not in private_bundle
    assert private_bundle["proof_database"]["driver"] in {"sqlite", "postgresql+psycopg"}
    private_text = private_path.read_text(encoding="utf-8")
    assert "://" not in json.dumps(private_bundle["proof_database"])
    runtime_password = make_url(runtime_url).password
    if runtime_password:
        assert runtime_password not in private_text

    # 4. Production verifier (subprocess) knows the database only through DATABASE_URL.
    verify_url = runtime_url
    if runtime_backend.rotate_password is not None:
        # FR14-02: password rotation keeps the target identity; the verifier still connects.
        verify_url = runtime_backend.rotate_password()
    receipt_path = namespace / "receipt.json"
    result, receipt = _run_verifier(verify_url, candidate_path, private_path, receipt_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout
    assert receipt["result"] == "REAL_PROOF_PASS"
    assert receipt["candidate_bundle_sha256"] == candidate_sha
    assert receipt["candidate_bundle_sha256"] == private_bundle["candidate_bundle_sha256"]
    assert receipt["schema_validated"] is True
    assert receipt["database_evidence_verified"] is True
    assert receipt["rejection_reasons"] == []
    receipt_text = receipt_path.read_text(encoding="utf-8")
    for secret in filter(None, (runtime_password, make_url(verify_url).password)):
        assert secret not in receipt_text
        assert secret not in result.stdout + result.stderr

    # 5a. The bundle cannot steer the verifier to a different database on the same runtime.
    result, receipt = _run_verifier(
        runtime_backend.mismatched_url, candidate_path, private_path, receipt_path
    )
    assert result.returncode == 1
    assert "PROOF_DATABASE_TARGET_MISMATCH" in result.stderr
    assert receipt["result"] == "REAL_PROOF_FAIL"

    # 5b. Missing runtime configuration: nothing is guessed from the evidence.
    result, receipt = _run_verifier(None, candidate_path, private_path, receipt_path)
    assert result.returncode == 1
    assert "PROOF_DATABASE_TARGET_MISMATCH" in result.stderr

    # 5c. PostgreSQL only: a stale credential fails at read time without leaking anything.
    if runtime_backend.stale_url is not None:
        result, receipt = _run_verifier(
            runtime_backend.stale_url, candidate_path, private_path, receipt_path
        )
        assert result.returncode == 1
        assert "could not be read from the configured runtime database" in result.stderr
        stale_password = make_url(runtime_backend.stale_url).password
        assert stale_password is not None
        assert stale_password not in receipt_path.read_text(encoding="utf-8")
        assert stale_password not in result.stdout + result.stderr

    # 6. Single-field database mutations against the production-built rows.
    packet_id = uuid.UUID(private_bundle["packet_id"])
    variant_id = uuid.UUID(private_bundle["resume_variant_id"])
    original: dict[str, Any] = {}

    def _capture(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_id)
        original["answers"] = json.loads(json.dumps(packet.answers_json))
        original["unresolved"] = list(packet.unresolved_questions_json)

    _mutate(verify_url, _capture)

    def _flip_answer(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_id)
        answers = dict(packet.answers_json)
        first = next(iter(answers))
        answers[first] = "No" if answers[first] != "No" else "Yes"
        packet.answers_json = answers

    def _restore_answers(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_id)
        packet.answers_json = original["answers"]

    def _clear_unresolved(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_id)
        packet.unresolved_questions_json = []

    def _restore_unresolved(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_id)
        packet.unresolved_questions_json = original["unresolved"]

    def _bump_variant_version(session: Any) -> None:
        session.get(ResumeVariantModel, variant_id).version = 2

    def _restore_variant_version(session: Any) -> None:
        session.get(ResumeVariantModel, variant_id).version = 1

    def _repoint_source(session: Any) -> None:
        source = (
            session.query(JobSourceModel)
            .filter_by(source_job_id=ENGINEERING_GREENHOUSE_JOB_ID)
            .one()
        )
        source.requisition_id = "0000001"

    def _restore_source(session: Any) -> None:
        source = (
            session.query(JobSourceModel)
            .filter_by(source_job_id=ENGINEERING_GREENHOUSE_JOB_ID)
            .one()
        )
        source.requisition_id = ENGINEERING_GREENHOUSE_JOB_ID

    cases: list[tuple[str, Callable[[Any], None], Callable[[Any], None], str]] = [
        ("answers", _flip_answer, _restore_answers, "packet hash recomputed from persisted DB"),
        ("unresolved", _clear_unresolved, _restore_unresolved, "unresolved_questions_json"),
        (
            "variant_version",
            _bump_variant_version,
            _restore_variant_version,
            "ResumeVariantModel.version",
        ),
        ("requisition", _repoint_source, _restore_source, "JobSource.requisition_id"),
    ]
    for label, apply, restore, expected in cases:
        _mutate(verify_url, apply)
        try:
            result, receipt = _run_verifier(verify_url, candidate_path, private_path, receipt_path)
            assert result.returncode == 1, f"{label}: mutation was accepted"
            assert expected in result.stderr, f"{label}: {result.stderr}"
            assert receipt["result"] == "REAL_PROOF_FAIL"
        finally:
            _mutate(verify_url, restore)

    # 7. With every mutation restored the same evidence passes again.
    result, receipt = _run_verifier(verify_url, candidate_path, private_path, receipt_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt["result"] == "REAL_PROOF_PASS"

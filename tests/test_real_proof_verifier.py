"""Tests for the redacted V1.4 real-proof evidence verifier and receipt generation.

Engineering fixture namespace
-----------------------------
Every full-run fixture here is built through the *production* services (ConfigLoader,
ApplicationPacketBuilder, ArtifactStore, the runner's bundle assembler) from a valid
canonical synthetic engineering profile under ``tmp_path``. Such evidence lives only in
the test's temporary directory and is never exported as REAL_PROOF; the lead decides
genuineness of any real run separately.

Trusted runtime emulation
-------------------------
The verifier connects only to the database named by its trusted runtime configuration
(``DATABASE_URL``) and requires the private bundle's database identity to match it. The
test helpers export the fixture database as ``DATABASE_URL`` for the verifier subprocess,
exactly as an operator would on the proof host.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from jobs_automation.adapters.models import DeterministicModelGateway
from jobs_automation.core.config import AppSettings, ConfigLoader
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationPacketModel,
    ArtifactModel,
    CompanyModel,
    JobModel,
    JobSourceModel,
    ResumeVariantModel,
)
from jobs_automation.db.session import get_engine, get_sessionmaker
from jobs_automation.preparation.packet_builder import (
    ApplicationPacketBuilder,
    compute_questions_sha256,
)
from jobs_automation.proof.database_identity import database_identity
from jobs_automation.proof.profile_fingerprint import candidate_profile_fingerprint
from jobs_automation.storage.artifact_store import ArtifactStore
from scripts.run_v14_real_proof import assemble_proof_bundles, serialize_redacted_bundle
from scripts.verify_v14_real_proof import (
    ProofValidationError,
    compute_job_snapshot_sha256,
    receipt_filename,
    resolve_proof_db_url,
    sanitize_reason,
    validate_redacted_bundle_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIER_SCRIPT = REPO_ROOT / "scripts" / "verify_v14_real_proof.py"


def _valid_bundle() -> dict[str, Any]:
    """A production-shape redacted candidate for structural (no local bundle) tests."""
    sha = "a" * 64
    return {
        "result": "REAL_PROOF_CANDIDATE",
        "proof_run_id": "proof-run-1",
        "run_timestamp_utc": "2026-09-21T02:45:00Z",
        "code_commit_sha": "8a0cdb4",
        "job_url": "https://job-boards.greenhouse.io/opensesame/jobs/7967740",
        "job_title": "AI Automation Engineer",
        "company": "OpenSesame",
        "job_snapshot_sha256": sha,
        "candidate_profile_source_class": "PRIVATE_LOCAL",
        "candidate_profile_version": 1,
        "candidate_unresolved_fact_categories": {},
        "resume_family": "Senior Software Engineer / AI Automation Engineer",
        "resume_variant": "resume_ai_software_engineer",
        "resume_version": 1,
        "resume_source_sha256": sha,
        "resume_source_byte_count": 1024,
        "model_provider": None,
        "model_name": "DeterministicModelGateway",
        "model_origin": "deterministic",
        "generation_origin": "deterministic",
        "generation_engine": "deterministic-canonical-renderer",
        "packet_id": "11111111-1111-1111-1111-111111111111",
        "packet_hash": sha,
        "resume_artifact_sha256": sha,
        "cover_letter_artifact_sha256": sha,
        "manifest_sha256": sha,
        "is_live_ready": False,
        "resolved_answers_count": 2,
        "unresolved_questions": ["Unconfirmed work authorization question"],
        "questions_count": 3,
        "read_back_verification": True,
        "mock_or_fixture_inputs_present": False,
    }


def _candidate_sha(bundle: dict[str, Any]) -> str:
    """SHA-256 of the exact bytes the runner writes and the verifier hashes."""
    return hashlib.sha256(serialize_redacted_bundle(bundle).encode("utf-8")).hexdigest()


def _run_verifier(
    tmp_path: Path,
    bundle: dict[str, Any],
    local_bundle_path: Path | None = None,
    receipt_path: Path | None = None,
    runtime_database_url: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the verifier entry point as a subprocess with an explicit trusted runtime."""
    path = tmp_path / "proof.json"
    path.write_text(serialize_redacted_bundle(bundle), encoding="utf-8")
    cmd = [sys.executable, str(VERIFIER_SCRIPT), str(path)]
    if local_bundle_path is not None:
        cmd.extend(["--local-full-bundle", str(local_bundle_path)])
    if receipt_path is not None:
        cmd.extend(["--receipt-output", str(receipt_path)])
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    if runtime_database_url is not None:
        env["DATABASE_URL"] = runtime_database_url
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


def test_real_proof_verifier_omitting_local_bundle_fails_closed_without_pass(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "receipt.json"
    result = _run_verifier(tmp_path, _valid_bundle(), receipt_path=receipt)
    assert result.returncode == 1
    assert "REAL_PROOF_VALIDATION_STRUCTURAL_ONLY" in result.stderr
    assert receipt.exists()
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["local_full_bundle_verified"] is False
    assert receipt_data["schema_validated"] is True
    assert receipt_data["database_evidence_verified"] is False
    assert any("local full bundle required" in r for r in receipt_data["rejection_reasons"])
    assert len(receipt_data["candidate_bundle_sha256"]) == 64
    assert len(receipt_data["evidence_schema_sha256"]) == 64


def test_real_proof_verifier_rejects_candidate_self_labeled_pass(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["result"] = "REAL_PROOF_PASS"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert (
        "schema violation at #/result" in result.stderr
        or "result must be REAL_PROOF_CANDIDATE" in result.stderr
    )


def test_real_proof_verifier_rejects_candidate_self_labeled_fail(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["result"] = "REAL_PROOF_FAIL"
    receipt = tmp_path / "receipt.json"
    result = _run_verifier(tmp_path, bundle, receipt_path=receipt)
    assert result.returncode == 1
    assert "schema violation at #/result" in result.stderr
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["schema_validated"] is False


def test_real_proof_verifier_generates_default_receipt_on_failure(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["result"] = "REAL_PROOF_PASS"
    proof_run_id = str(bundle["proof_run_id"])
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    default_receipt = tmp_path / f"v14_real_proof_receipt_{proof_run_id}.json"
    assert default_receipt.exists()
    receipt_data = json.loads(default_receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["proof_run_id"] == proof_run_id


def test_real_proof_verifier_rejects_mock_or_test_origins(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["model_origin"] = "mock"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert (
        "schema violation at #/model_origin" in result.stderr
        or "model_origin must be 'deterministic'" in result.stderr
    )

    bundle2 = _valid_bundle()
    bundle2["generation_origin"] = "real"
    result2 = _run_verifier(tmp_path, bundle2)
    assert result2.returncode == 1
    assert (
        "schema violation at #/generation_origin" in result2.stderr
        or "generation_origin must be 'deterministic'" in result2.stderr
    )

    bundle3 = _valid_bundle()
    bundle3["generation_engine"] = "custom-llm"
    result3 = _run_verifier(tmp_path, bundle3)
    assert result3.returncode == 1
    assert (
        "schema violation at #/generation_engine" in result3.stderr
        or "generation_engine must be 'deterministic-canonical-renderer'" in result3.stderr
    )


def test_real_proof_verifier_rejects_fixture_marker(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["resume_variant"] = "test_resume_fixture"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "forbidden mock/fixture marker" in result.stderr


def test_real_proof_verifier_rejects_private_content_field(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["resume_text"] = "private resume contents"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "disallowed extra field(s) ['resume_text']" in result.stderr
    assert "private resume contents" not in result.stderr


def test_real_proof_verifier_rejects_nested_private_field(tmp_path: Path) -> None:
    """A private key nested inside an allowed object must not reach the receipt as data."""
    bundle = _valid_bundle()
    bundle["candidate_unresolved_fact_categories"] = {"candidate_email": 1}
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "private field must not be committed" in result.stderr


def test_real_proof_verifier_rejects_disallowed_extra_keys(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["arbitrary_custom_notes"] = "some note"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "disallowed extra field(s) ['arbitrary_custom_notes']" in result.stderr


def test_real_proof_verifier_rejects_unverified_readback(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["read_back_verification"] = False
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert (
        "schema violation at #/read_back_verification" in result.stderr
        or "read_back_verification must be true" in result.stderr
    )


# ---------------------------------------------------------------------------
# F145-01: the entry point executes the evidence schema, including format checks,
# and every malformed input ends in a bound REAL_PROOF_FAIL receipt, never a traceback.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "bad_value", "pointer"),
    [
        ("run_timestamp_utc", "yesterday", "/run_timestamp_utc"),
        ("run_timestamp_utc", "2026-13-45T99:99:99Z", "/run_timestamp_utc"),
        ("job_url", "https://job-boards.greenhouse.io/opensesame/jobs/79 67740", "/job_url"),
        ("packet_id", "not-a-uuid", "/packet_id"),
        ("questions_count", "3", "/questions_count"),
        ("questions_count", -1, "/questions_count"),
        ("resolved_answers_count", 2.5, "/resolved_answers_count"),
        ("is_live_ready", "false", "/is_live_ready"),
        ("unresolved_questions", "not a list", "/unresolved_questions"),
        (
            "candidate_unresolved_fact_categories",
            {"identity": "two"},
            "/candidate_unresolved_fact_categories/identity",
        ),
        ("code_commit_sha", "not-a-sha", "/code_commit_sha"),
        ("resume_source_byte_count", "abc", "/resume_source_byte_count"),
    ],
)
def test_real_proof_verifier_entry_point_rejects_malformed_values_through_schema(
    tmp_path: Path, key: str, bad_value: Any, pointer: str
) -> None:
    bundle = _valid_bundle()
    bundle[key] = bad_value
    receipt = tmp_path / "receipt.json"
    result = _run_verifier(tmp_path, bundle, receipt_path=receipt)
    assert result.returncode == 1, result.stdout
    assert "Traceback" not in result.stderr
    assert f"schema violation at #{pointer}" in result.stderr
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["schema_validated"] is False
    assert receipt_data["candidate_bundle_sha256"] == _candidate_sha(bundle)


@pytest.mark.parametrize(
    "missing_key",
    ["proof_run_id", "packet_hash", "questions_count", "mock_or_fixture_inputs_present"],
)
def test_real_proof_verifier_entry_point_rejects_missing_required_field(
    tmp_path: Path, missing_key: str
) -> None:
    bundle = _valid_bundle()
    del bundle[missing_key]
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert f"missing required field(s) ['{missing_key}']" in result.stderr


def test_real_proof_verifier_entry_point_rejects_non_object_and_non_json_bundles(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "receipt.json"
    for raw in ("[]", "null", "{not json", "\xff\xfe"):
        path = tmp_path / "proof.json"
        path.write_text(raw, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(VERIFIER_SCRIPT), str(path), "--receipt-output", str(receipt)],
            check=False,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 1, raw
        assert "Traceback" not in result.stderr
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        assert receipt_data["result"] == "REAL_PROOF_FAIL"


def test_schema_validation_fails_closed_when_schema_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(ProofValidationError, match="evidence schema file is missing"):
        validate_redacted_bundle_schema(_valid_bundle(), schema_path=tmp_path / "absent.json")


def test_schema_validation_fails_closed_when_declared_format_cannot_be_checked(
    tmp_path: Path,
) -> None:
    schema = json.loads(
        (REPO_ROOT / "coordination" / "proofs" / "v14_real_proof.schema.json").read_text(
            encoding="utf-8"
        )
    )
    schema["properties"]["proof_run_id"]["format"] = "no-such-format-checker"
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(ProofValidationError, match="format checker unavailable"):
        validate_redacted_bundle_schema(_valid_bundle(), schema_path=schema_path)


def test_schema_validation_binds_the_enforced_schema_hash() -> None:
    schema_path = REPO_ROOT / "coordination" / "proofs" / "v14_real_proof.schema.json"
    digest = validate_redacted_bundle_schema(_valid_bundle())
    assert digest == hashlib.sha256(schema_path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# F145-05: sanitized reasons and receipt naming
# ---------------------------------------------------------------------------


def test_sanitize_reason_strips_credentials_and_private_paths() -> None:
    secret = "synthetic-not-a-real-password"
    reason = sanitize_reason(
        f"could not read postgresql+psycopg://jobs:{secret}@db.internal:5432/jobs_proof and "
        "/home/someone/private/candidate_profile.yaml while checking "
        "https://job-boards.greenhouse.io/opensesame/jobs/7967740"
    )
    assert secret not in reason
    assert "postgresql+psycopg://***@db.internal:5432/jobs_proof" in reason
    assert "/home/someone" not in reason
    assert "<path:candidate_profile.yaml>" in reason
    assert "https://job-boards.greenhouse.io/opensesame/jobs/7967740" in reason


def test_sanitize_reason_caps_length() -> None:
    assert len(sanitize_reason("x" * 5000)) <= 400


def test_receipt_filename_never_uses_untrusted_path_components() -> None:
    sha = "f" * 64
    assert receipt_filename("proof-run-1", sha) == "v14_real_proof_receipt_proof-run-1.json"
    for hostile in ("../../etc/passwd", "a/b", "..", ".hidden", "", "x" * 200, "id with space"):
        name = receipt_filename(hostile, sha)
        assert "/" not in name and ".." not in name
        assert name == f"v14_real_proof_receipt_unbound_{sha[:16]}.json"


def test_real_proof_verifier_default_receipt_ignores_hostile_proof_run_id(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["proof_run_id"] = "../../hostile"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    expected = tmp_path / f"v14_real_proof_receipt_unbound_{_candidate_sha(bundle)[:16]}.json"
    assert expected.exists()
    assert not (tmp_path.parent.parent / "hostile").exists()
    assert not (tmp_path.parent.parent / "v14_real_proof_receipt_../../hostile.json").exists()


# ---------------------------------------------------------------------------
# Engineering full-run fixture built through the production services.
# ---------------------------------------------------------------------------

GREENHOUSE_PUBLIC_JOB_ID = "7967740"
GREENHOUSE_API_URL = (
    "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740?questions=true"
)
GREENHOUSE_CANONICAL_URL = "https://job-boards.greenhouse.io/opensesame/jobs/7967740"
GREENHOUSE_FETCHED_AT = "2026-09-21T02:45:00Z"
PROOF_DESCRIPTION_TEXT = (
    "OpenSesame is hiring an AI Automation Engineer to build production automation for "
    "enterprise learning workflows, including resilient pipelines and public job board "
    "API integrations."
)
ENGINEERING_QUESTIONS = [
    "Are you legally authorized to work in the United States?",
    "Will you now or in the future require sponsorship for employment visa status?",
    "Describe a reusable automation system you built.",
]
ENGINEERING_RESUME_TEXT = (
    "# Engineering Candidate\n\n"
    "Senior software engineer building AI workflow automation and enterprise integrations.\n"
)
ENGINEERING_VARIANT = "resume_ai_software_engineer"
ENGINEERING_FAMILY = "Senior Software Engineer / AI Automation Engineer"


def engineering_profile_yaml(resume_path: Path, *, full_name: str = "Engineering Candidate") -> str:
    """A valid canonical candidate profile for engineering runs (not a real person)."""
    return f"""version: 1

identity:
  full_name: "{full_name}"
  preferred_name: "Engineering"
  email: "engineering-candidate@invalid"
  phone: "+1-000-000-0000"
  city: "Pittsburgh"
  state: "PA"
  country: "US"

links:
  linkedin: null
  github: null
  portfolio: null
  personal_site: null

target:
  primary_headline: "Senior Software Engineer - AI Workflow Automation"
  alternate_headlines: []
  target_role_families:
    - "Senior Software Engineering / AI Workflow Automation"
  target_compensation_usd_min: 150000
  compensation_basis: "base"
  remote_preference: "remote"
  relocation: false
  travel_percent_max: 10

positioning:
  summary: "Engineer who builds production automation with verifiable evidence."
  differentiators:
    - "Software engineering + enterprise systems"
  avoid_positioning_as:
    - "generic IT generalist"

work_authorization:
  authorized_to_work_in_us: true
  requires_sponsorship_now: false
  requires_sponsorship_future: false
  notes: null

experience:
  current_role:
    company: "Engineering Co"
    role: "Senior Software Engineer"
    start: "2024-10"
  roles:
    - company: "Prior Co"
      role: "Software Engineer"
      start: "2019"
      end: "2024"

education:
  - school: "Engineering University"
    credential: "B.S. Computer Science"

skills:
  primary:
    - "Python"
    - "FastAPI"
  secondary:
    - "TypeScript"
  certifications: []

resume:
  strategy: "maintain_targeted_versions"
  recommended_versions:
    - id: "{ENGINEERING_VARIANT}"
      priority: 1
      emphasize:
        - "Python"
  base_resume_paths: []
  resume_sources:
    {ENGINEERING_VARIANT}: "{resume_path}"
  default_resume_id: "{ENGINEERING_VARIANT}"

application_answers:
  willing_to_relocate: false
  willing_to_travel: true
  notice_period_days: 14
  earliest_start_date: "2026-11-01"
  salary_expectation_text: null
  custom_answers: {{}}

demographic_answers:
  policy: "do_not_guess"
  values: {{}}

notes: []
"""


def _greenhouse_source_payload(questions: list[str], description_sha: str) -> dict[str, Any]:
    """Mirror of the payload scripts/import_v14_proof_job.py persists on JobSource."""
    return {
        "api_url": GREENHOUSE_API_URL,
        "fetched_at_utc": GREENHOUSE_FETCHED_AT,
        "content_sha256": description_sha,
        "screening_question_count": len(questions),
        "question_list_sha256": compute_questions_sha256(questions),
        "source_kind": "greenhouse_public_job_board_api",
        "provider": "GREENHOUSE",
        "public_job_id": GREENHOUSE_PUBLIC_JOB_ID,
    }


def _persist_proof_job(session: Any, questions: list[str]) -> JobModel:
    """Persist the Company/Job/JobSource rows the importer would write."""
    description_sha = hashlib.sha256(PROOF_DESCRIPTION_TEXT.encode("utf-8")).hexdigest()
    company = CompanyModel(normalized_name="OpenSesame", domain="opensesame.com")
    session.add(company)
    session.flush()
    job = JobModel(
        company_id=company.id,
        normalized_title="AI Automation Engineer",
        location_text="Remote, US",
        remote_type="remote",
        description_text=PROOF_DESCRIPTION_TEXT,
        description_hash=description_sha,
        status="active",
    )
    session.add(job)
    session.flush()
    session.add(
        JobSourceModel(
            job_id=job.id,
            provider="GREENHOUSE",
            source_job_id=GREENHOUSE_PUBLIC_JOB_ID,
            source_url=GREENHOUSE_CANONICAL_URL,
            canonical_apply_url=GREENHOUSE_CANONICAL_URL,
            requisition_id=GREENHOUSE_PUBLIC_JOB_ID,
            source_payload_json=_greenhouse_source_payload(questions, description_sha),
        )
    )
    session.flush()
    session.refresh(job)
    return job


def _setup_valid_full_run(
    tmp_path: Path, questions: list[str] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one complete, internally consistent engineering proof run.

    Returns ``(redacted_bundle, local_bundle_data)``. ``local_bundle_data`` carries one
    test-only key, ``_runtime_database_url``, that ``_write_private_bundle`` strips: the
    verifier never learns the connection string from the bundle.
    """
    questions = list(questions or ENGINEERING_QUESTIONS)
    resume_file = tmp_path / "engineering_resume_ai_software_engineer.md"
    resume_file.write_text(ENGINEERING_RESUME_TEXT, encoding="utf-8")
    profile_file = tmp_path / "candidate_private_profile.yaml"
    profile_file.write_text(engineering_profile_yaml(resume_file.resolve()), encoding="utf-8")
    questions_file = tmp_path / "job_questions.json"
    questions_file.write_text(json.dumps(questions), encoding="utf-8")

    db_file = tmp_path / "proof_evidence.db"
    if db_file.exists():
        # Tests that loop over several setups in one tmp_path always start clean.
        db_file.unlink()
    db_url = f"sqlite:///{db_file}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_sessionmaker(engine)
    try:
        with session_factory() as session:
            job = _persist_proof_job(session, questions)
            profile, _ = ConfigLoader(REPO_ROOT / "config").load_candidate_profile(profile_file)
            builder = ApplicationPacketBuilder(
                session=session,
                candidate_profile=profile,
                model_gateway=DeterministicModelGateway(),
                artifact_store=ArtifactStore(tmp_path / "artifacts"),
            )
            packet, result = builder.build_packet(job=job, questions=questions)
            session.commit()
            redacted, private_bundle = assemble_proof_bundles(
                session=session,
                job=job,
                profile=profile,
                profile_path=profile_file,
                questions=questions,
                questions_path=questions_file,
                packet=packet,
                result=result,
                resume_source_path=resume_file.resolve(),
                proof_run_id="proof-run-local-1",
                code_sha="8a0cdb4",
            )
    finally:
        engine.dispose()

    private_bundle["_runtime_database_url"] = db_url
    return redacted, private_bundle


def _write_private_bundle(tmp_path: Path, local_bundle_data: dict[str, Any]) -> Path:
    payload = {k: v for k, v in local_bundle_data.items() if not str(k).startswith("_")}
    path = tmp_path / "private_bundle.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


_DEFAULT_RUNTIME = object()


def _run_full_verifier(
    tmp_path: Path,
    bundle: dict[str, Any],
    local_bundle_data: dict[str, Any],
    receipt_path: Path | None = None,
    runtime_database_url: Any = _DEFAULT_RUNTIME,
) -> subprocess.CompletedProcess[str]:
    """Write the private bundle and run the verifier with the fixture DB as the runtime."""
    local_bundle_path = _write_private_bundle(tmp_path, local_bundle_data)
    if runtime_database_url is _DEFAULT_RUNTIME:
        runtime_database_url = local_bundle_data["_runtime_database_url"]
    return _run_verifier(
        tmp_path,
        bundle,
        local_bundle_path=local_bundle_path,
        receipt_path=receipt_path,
        runtime_database_url=runtime_database_url,
    )


def _mutate_proof_database(db_url: str, mutate: Any) -> None:
    """Apply an adversarial mutation to an already-persisted proof database."""
    engine = get_engine(db_url)
    session_factory = get_sessionmaker(engine)
    try:
        with session_factory() as session:
            mutate(session)
            session.commit()
    finally:
        engine.dispose()


def _rebind_candidate(bundle: dict[str, Any], local_bundle_data: dict[str, Any]) -> None:
    """Re-bind the private bundle to an edited redacted bundle (what a forger would do)."""
    local_bundle_data["candidate_bundle_sha256"] = _candidate_sha(bundle)


def _rebind_profile(local_bundle_data: dict[str, Any]) -> None:
    """Re-bind the private bundle to an edited profile file (what a forger would do)."""
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    local_bundle_data["candidate_profile_sha256"] = hashlib.sha256(
        profile_path.read_bytes()
    ).hexdigest()
    profile, _ = ConfigLoader(REPO_ROOT / "config").load_candidate_profile(profile_path)
    local_bundle_data["candidate_profile_fingerprint_sha256"] = candidate_profile_fingerprint(
        profile
    )
    local_bundle_data["candidate_profile_version"] = profile.version


def _manifest_path(local_bundle_data: dict[str, Any]) -> Path:
    entries = {item["type"]: item for item in local_bundle_data["local_artifacts"]}
    return Path(entries["manifest"]["path"])


def _rewrite_manifest(
    bundle: dict[str, Any], local_bundle_data: dict[str, Any], mutate: Any
) -> None:
    """Edit the manifest and re-bind its hash everywhere a forger controls."""
    path = _manifest_path(local_bundle_data)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutate(manifest)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    new_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    for item in local_bundle_data["local_artifacts"]:
        if item["type"] == "manifest":
            item["sha256"] = new_sha
    bundle["manifest_sha256"] = new_sha
    _rebind_candidate(bundle, local_bundle_data)


def _persisted_job_snapshot_sha256(db_url: str, job_id: str) -> str:
    engine = get_engine(db_url)
    try:
        with get_sessionmaker(engine)() as session:
            job = session.get(JobModel, uuid.UUID(job_id))
            assert job is not None
            return compute_job_snapshot_sha256(job)
    finally:
        engine.dispose()


def test_engineering_fixture_is_internally_consistent(tmp_path: Path) -> None:
    """The production services produce exactly the shape the verifier expects."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    assert bundle["resume_variant"] == ENGINEERING_VARIANT
    assert bundle["resume_family"] == ENGINEERING_FAMILY
    assert bundle["generation_origin"] == "deterministic"
    assert bundle["resolved_answers_count"] == 2
    assert len(bundle["unresolved_questions"]) == 1
    assert bundle["questions_count"] == 3
    assert bundle["is_live_ready"] is False
    assert bundle["candidate_unresolved_fact_categories"] == {}
    assert local_bundle_data["candidate_bundle_sha256"] == _candidate_sha(bundle)
    assert "database_url" not in local_bundle_data
    assert local_bundle_data["proof_database"]["driver"] == "sqlite"
    assert local_bundle_data["selected_resume_variant"] == ENGINEERING_VARIANT
    assert local_bundle_data["resume_variant_version"] == 1
    assert local_bundle_data["resume_source_byte_count"] == len(
        ENGINEERING_RESUME_TEXT.encode("utf-8")
    )


def test_real_proof_verifier_validates_complete_local_bundle_and_cross_binding(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    receipt_file = tmp_path / "receipt.json"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data, receipt_path=receipt_file)
    assert result.returncode == 0, result.stderr
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_PASS"
    assert receipt_data["local_full_bundle_verified"] is True
    assert receipt_data["schema_validated"] is True
    assert receipt_data["database_evidence_verified"] is True
    assert receipt_data["candidate_bundle_sha256"] == local_bundle_data["candidate_bundle_sha256"]
    assert receipt_data["rejection_reasons"] == []


def test_real_proof_verifier_rejects_missing_candidate_bundle_sha_in_local_bundle(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    del local_bundle_data["candidate_bundle_sha256"]
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "missing mandatory candidate_bundle_sha256" in result.stderr


def test_real_proof_verifier_rejects_mismatched_candidate_bundle_sha_in_local_bundle(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_bundle_sha256"] = "0" * 64
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate_bundle_sha256 in local bundle does not match" in result.stderr


def test_real_proof_verifier_rejects_example_profile_sha_in_local_bundle(tmp_path: Path) -> None:
    repo_example = REPO_ROOT / "config" / "candidate_profile.example.yaml"
    assert repo_example.exists()
    example_sha = hashlib.sha256(repo_example.read_bytes()).hexdigest()

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_profile_path"] = str(repo_example)
    local_bundle_data["candidate_profile_sha256"] = example_sha
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "matches repository example file" in result.stderr
        or "candidate profile file name indicates test/example fixture" in result.stderr
    )


def test_real_proof_verifier_rejects_missing_or_invalid_greenhouse_source_attestation(
    tmp_path: Path,
) -> None:
    # 1. Missing source attestation
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    del local_bundle_data["source_attestation"]
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "missing mandatory source_attestation" in result.stderr

    # 2. Invalid provider
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["provider"] = "MANUAL"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "provider must be GREENHOUSE" in result.stderr

    # 3. Invalid api_url
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["api_url"] = "https://example.com/api"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "has invalid api_url" in result.stderr

    # 4. Invalid or missing fetched_at_utc
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["fetched_at_utc"] = "not-a-timestamp"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "fetched_at_utc" in result.stderr

    # 5. Mismatched canonical_apply_url vs redacted.job_url
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["canonical_apply_url"] = (
        "https://job-boards.greenhouse.io/other/jobs/7967740"
    )
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not match source_attestation canonical_apply_url" in result.stderr


def test_real_proof_verifier_rejects_tampered_or_missing_questions_json(tmp_path: Path) -> None:
    # 1. Missing questions file
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["questions_json_path"] = str(tmp_path / "non_existent_questions.json")
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "questions_json_path file not found on disk" in result.stderr

    # 2. Tampered questions content (hash mismatch)
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    q_file = Path(local_bundle_data["questions_json_path"])
    q_file.write_text(json.dumps(["Tampered Q1", "Tampered Q2", "Tampered Q3"]), encoding="utf-8")
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "questions JSON on disk hash mismatch" in result.stderr

    # 3. Question count mismatch
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    q_file = Path(local_bundle_data["questions_json_path"])
    four_questions = ["Q1", "Q2", "Q3", "Q4"]
    q_file.write_text(json.dumps(four_questions), encoding="utf-8")
    local_bundle_data["source_attestation"]["question_list_sha256"] = compute_questions_sha256(
        four_questions
    )
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "questions count in questions JSON" in result.stderr
        and "does not match redacted evidence" in result.stderr
    )


def test_real_proof_verifier_rejects_missing_or_tampered_candidate_profile(tmp_path: Path) -> None:
    # 1. Missing profile file
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_profile_path"] = str(tmp_path / "non_existent_profile.yaml")
    receipt = tmp_path / "receipt.json"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data, receipt_path=receipt)
    assert result.returncode == 1
    assert "candidate_profile_path file not found on disk" in result.stderr
    # F145-05: the private absolute path never reaches the committed receipt.
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert str(tmp_path) not in json.dumps(receipt_data)
    assert "<path:non_existent_profile.yaml>" in result.stderr

    # 2. Tampered profile content (hash mismatch)
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    prof_file = Path(local_bundle_data["candidate_profile_path"])
    prof_file.write_text("name: Tampered Profile\n", encoding="utf-8")
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate profile file on disk hash mismatch" in result.stderr


def test_real_proof_verifier_rejects_profile_that_is_not_canonical(tmp_path: Path) -> None:
    """A name-only YAML with a matching digest is not a canonical candidate profile."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    prof_file = Path(local_bundle_data["candidate_profile_path"])
    prof_file.write_text("name: Private Candidate\n", encoding="utf-8")
    local_bundle_data["candidate_profile_sha256"] = hashlib.sha256(
        prof_file.read_bytes()
    ).hexdigest()
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not parse as a canonical candidate profile" in result.stderr
    assert "Private Candidate" not in result.stderr


def test_real_proof_verifier_rejects_missing_or_invalid_local_uuids(tmp_path: Path) -> None:
    for field in (
        "job_id",
        "packet_id",
        "resume_variant_id",
        "resume_artifact_id",
        "cover_letter_artifact_id",
    ):
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        del local_bundle_data[field]
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
        assert result.returncode == 1
        assert f"missing mandatory valid UUID {field}" in result.stderr


def test_real_proof_verifier_rejects_forged_canonical_packet_hash(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    bundle["packet_hash"] = "9" * 64

    def _forge(manifest: dict[str, Any]) -> None:
        manifest["packet_hash"] = "9" * 64

    _rewrite_manifest(bundle, local_bundle_data, _forge)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "canonical packet hash recomputation mismatch" in result.stderr
        or "manifest packet_hash does not match recomputed canonical hash" in result.stderr
    )


def test_real_proof_verifier_rejects_mismatched_manifest_linkage(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["job_id"] = "99999999-9999-9999-9999-999999999999"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "manifest job_id" in result.stderr and "does not match local job_id" in result.stderr


def test_real_proof_verifier_rejects_malformed_private_bundle_without_traceback(
    tmp_path: Path,
) -> None:
    cases: list[tuple[str, Any]] = [
        ("resume_source_byte_count", "abc"),
        ("local_artifacts", "not-a-list"),
        ("local_artifacts", [42]),
        ("source_attestation", "GREENHOUSE"),
        ("proof_database", "sqlite:///somewhere.db"),
    ]
    for key, value in cases:
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        local_bundle_data[key] = value
        receipt = tmp_path / "receipt.json"
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data, receipt_path=receipt)
        assert result.returncode == 1, f"{key}={value!r} was accepted"
        assert "Traceback" not in result.stderr, f"{key}={value!r}: {result.stderr}"
        receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
        assert receipt_data["result"] == "REAL_PROOF_FAIL"

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    broken = tmp_path / "private_bundle.json"
    broken.write_text("{not json", encoding="utf-8")
    result = _run_verifier(
        tmp_path,
        bundle,
        local_bundle_path=broken,
        runtime_database_url=local_bundle_data["_runtime_database_url"],
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# F145-02: the verifier connects only to the trusted runtime database and requires
# the private bundle's database identity to match it. No credential lives in evidence.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_validates_database_records_via_runtime_identity(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    assert local_bundle_data["proof_database"] == database_identity(
        local_bundle_data["_runtime_database_url"]
    )
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 0, result.stderr
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


def test_private_bundle_records_identity_without_any_connection_string() -> None:
    secret = "synthetic-pg-proof-password"
    identity = database_identity(f"postgresql+psycopg://jobs:{secret}@db.internal:5432/jobs_proof")
    serialized = json.dumps(identity)
    assert secret not in serialized
    assert "://" not in serialized
    assert identity["database"] == "jobs_proof" and identity["username"] == "jobs"


def test_real_proof_verifier_rejects_identity_that_does_not_match_runtime_database(
    tmp_path: Path,
) -> None:
    """The bundle cannot steer the verifier to a database other than the trusted runtime."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    other_db = tmp_path / "other_runtime.db"
    engine = get_engine(f"sqlite:///{other_db}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    receipt = tmp_path / "receipt.json"
    result = _run_full_verifier(
        tmp_path,
        bundle,
        local_bundle_data,
        receipt_path=receipt,
        runtime_database_url=f"sqlite:///{other_db}",
    )
    assert result.returncode == 1
    assert "PROOF_DATABASE_TARGET_MISMATCH" in result.stderr
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["database_evidence_verified"] is False


def test_real_proof_verifier_rejects_when_runtime_database_is_not_configured(
    tmp_path: Path,
) -> None:
    """Without a trusted runtime target the identity cannot reconcile; nothing is guessed."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data, runtime_database_url=None)
    assert result.returncode == 1
    assert "PROOF_DATABASE_TARGET_MISMATCH" in result.stderr


@pytest.mark.parametrize(
    "change",
    [
        {"database": "other_database"},
        {"username": "someone_else"},
        {"driver": "postgresql+psycopg"},
        {"host": "db.internal"},
    ],
)
def test_real_proof_verifier_rejects_tampered_identity_reference(
    tmp_path: Path, change: dict[str, Any]
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["proof_database"] = {**local_bundle_data["proof_database"], **change}
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "PROOF_DATABASE_TARGET_MISMATCH" in result.stderr


def test_real_proof_verifier_rejects_masked_legacy_database_url(tmp_path: Path) -> None:
    """A str(URL) with a masked password is never reconstructed into a connection."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data.pop("proof_database")
    masked = "postgresql+psycopg://jobs:***@127.0.0.1:59999/jobs_proof"
    local_bundle_data["database_url"] = masked
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data, runtime_database_url=masked)
    assert result.returncode == 1
    assert "MASKED_DATABASE_CREDENTIAL" in result.stderr


def test_real_proof_verifier_accepts_legacy_sqlite_target_matching_runtime(tmp_path: Path) -> None:
    """Legacy string targets still work when they name the same trusted runtime database."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data.pop("proof_database")
    local_bundle_data["database_url"] = local_bundle_data["_runtime_database_url"]
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 0, result.stderr


def test_real_proof_verifier_fails_closed_when_no_database_target_is_configured(
    tmp_path: Path,
) -> None:
    """A complete local bundle with no DB target must not reach REAL_PROOF_PASS."""
    receipt_file = tmp_path / "receipt.json"
    for absent in ({}, {"database_url": ""}, {"db_path": "   "}):
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        local_bundle_data.pop("proof_database", None)
        local_bundle_data.update(absent)
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data, receipt_path=receipt_file)
        assert result.returncode == 1
        assert "must explicitly configure a proof database target" in result.stderr
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
        assert receipt_data["result"] == "REAL_PROOF_FAIL"
        assert receipt_data["local_full_bundle_verified"] is False


def test_real_proof_verifier_rejects_absent_proof_database_file(tmp_path: Path) -> None:
    missing_db = tmp_path / "absent_proof_evidence.db"
    missing_url = f"sqlite:///{missing_db}"

    # Legacy string form: rejected while normalizing the declared target.
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data.pop("proof_database")
    local_bundle_data["database_url"] = missing_url
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "proof database file not found on disk" in result.stderr

    # Identity form: rejected after reconciling with a runtime that names the absent file.
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["proof_database"] = database_identity(missing_url)
    result = _run_full_verifier(
        tmp_path, bundle, local_bundle_data, runtime_database_url=missing_url
    )
    assert result.returncode == 1
    assert "proof database file not found on disk" in result.stderr


def test_real_proof_verifier_rejects_unopenable_proof_database(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    corrupt_db = tmp_path / "corrupt_proof_evidence.db"
    corrupt_db.write_bytes(b"not a database at all" * 16)
    corrupt_url = f"sqlite:///{corrupt_db}"
    local_bundle_data["proof_database"] = database_identity(corrupt_url)
    result = _run_full_verifier(
        tmp_path, bundle, local_bundle_data, runtime_database_url=corrupt_url
    )
    assert result.returncode == 1
    assert "is not an openable SQLite database" in result.stderr


def test_real_proof_verifier_rejects_in_memory_database_target(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data.pop("proof_database")
    local_bundle_data["database_url"] = "sqlite:///:memory:"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "in-memory SQLite is not acceptable persisted proof evidence" in result.stderr


def test_real_proof_verifier_rejects_unrelated_proof_database(tmp_path: Path) -> None:
    """A schema-valid but unrelated database holds none of the proof rows."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    unrelated_db = tmp_path / "unrelated.db"
    unrelated_url = f"sqlite:///{unrelated_db}"
    engine = get_engine(unrelated_url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    local_bundle_data["proof_database"] = database_identity(unrelated_url)
    result = _run_full_verifier(
        tmp_path, bundle, local_bundle_data, runtime_database_url=unrelated_url
    )
    assert result.returncode == 1
    assert "JobModel not found in DB" in result.stderr


def test_real_proof_verifier_rejects_tampered_persisted_packet_row(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _forge_packet_hash(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.packet_hash = "9" * 64

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_packet_hash)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "DB ApplicationPacketModel packet_hash mismatch" in result.stderr


def test_real_proof_verifier_rejects_missing_persisted_resume_variant_row(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    variant_uuid = uuid.UUID(local_bundle_data["resume_variant_id"])

    def _drop_variant(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
        packet.resume_variant_id = None
        session.flush()
        session.delete(session.get(ResumeVariantModel, variant_uuid))

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _drop_variant)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "resume_variant_id" in result.stderr


def test_real_proof_verifier_rejects_tampered_persisted_artifact_hash(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    resume_art_uuid = uuid.UUID(local_bundle_data["resume_artifact_id"])

    def _forge_artifact_sha(session: Any) -> None:
        artifact = session.get(ArtifactModel, resume_art_uuid)
        artifact.sha256 = "7" * 64

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_artifact_sha)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "DB resume ArtifactModel sha256 mismatch" in result.stderr


def test_real_proof_verifier_rejects_missing_persisted_cover_letter_artifact_row(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    cl_art_uuid = uuid.UUID(local_bundle_data["cover_letter_artifact_id"])

    def _drop_cover_letter_artifact(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
        packet.cover_letter_artifact_id = None
        session.flush()
        session.delete(session.get(ArtifactModel, cl_art_uuid))

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _drop_cover_letter_artifact)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "cover_letter_artifact_id" in result.stderr


def test_real_proof_verifier_rejects_packet_persisted_under_a_different_job(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    other_job_uuid = uuid.uuid4()

    def _relink_packet(session: Any) -> None:
        session.add(
            JobModel(
                id=other_job_uuid,
                normalized_title="AI Automation Engineer",
                description_text=PROOF_DESCRIPTION_TEXT,
                description_hash=hashlib.sha256(PROOF_DESCRIPTION_TEXT.encode("utf-8")).hexdigest(),
            )
        )
        session.flush()
        packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
        packet.job_id = other_job_uuid

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _relink_packet)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "DB ApplicationPacketModel job_id" in result.stderr


# ---------------------------------------------------------------------------
# F145-03: packet identity is re-derived from persisted answers/provenance/unresolved.
# Each case mutates exactly one persisted component while every stored hash is retained.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_rejects_mutated_persisted_answers_only(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _flip_answer(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        answers = dict(packet.answers_json)
        first = next(iter(answers))
        answers[first] = "No" if answers[first] != "No" else "Yes"
        packet.answers_json = answers

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _flip_answer)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "packet hash recomputed from persisted DB components" in result.stderr


def test_real_proof_verifier_rejects_mutated_persisted_provenance_only(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _forge_provenance(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        provenance = json.loads(json.dumps(packet.answer_provenance_json))
        first = next(iter(provenance))
        provenance[first]["sources"] = ["forged.source"]
        packet.answer_provenance_json = provenance

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_provenance)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "packet hash recomputed from persisted DB components" in result.stderr


def test_real_proof_verifier_rejects_mutated_persisted_unresolved_questions_only(
    tmp_path: Path,
) -> None:
    """The unresolved list is outside the packet hash, so it needs its own binding."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _clear_unresolved(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.unresolved_questions_json = []

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _clear_unresolved)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "unresolved_questions_json does not match" in result.stderr


def test_real_proof_verifier_rejects_persisted_answer_for_unattested_question(
    tmp_path: Path,
) -> None:
    """Rewriting answers, provenance and hash consistently still cannot invent a question."""
    from jobs_automation.preparation.packet_builder import compute_canonical_packet_hash

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])
    forged_hash = ""

    def _add_question(session: Any) -> None:
        nonlocal forged_hash
        packet = session.get(ApplicationPacketModel, packet_uuid)
        answers = dict(packet.answers_json)
        provenance = json.loads(json.dumps(packet.answer_provenance_json))
        answers["Invented question?"] = "Yes"
        provenance["Invented question?"] = {
            "method": "deterministic",
            "sources": ["forged"],
            "confidence": 1.0,
        }
        packet.answers_json = answers
        packet.answer_provenance_json = provenance
        packet.unresolved_questions_json = []
        resume_art = session.get(ArtifactModel, packet.resume_artifact_id)
        cl_art = session.get(ArtifactModel, packet.cover_letter_artifact_id)
        forged_hash = compute_canonical_packet_hash(
            job_id=packet.job_id,
            profile_version=packet.candidate_profile_version,
            resume_variant_id=packet.resume_variant_id,
            resume_sha=resume_art.sha256,
            cover_letter_sha=cl_art.sha256,
            answers=answers,
            answer_provenance=provenance,
        )
        packet.packet_hash = forged_hash

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _add_question)
    bundle["packet_hash"] = forged_hash
    bundle["resolved_answers_count"] = 3
    bundle["unresolved_questions"] = []

    def _forge_manifest(manifest: dict[str, Any]) -> None:
        manifest["packet_hash"] = forged_hash
        manifest["answers"]["Invented question?"] = "Yes"
        manifest["answer_provenance"]["Invented question?"] = {
            "method": "deterministic",
            "sources": ["forged"],
            "confidence": 1.0,
        }
        manifest["unresolved_questions"] = []

    _rewrite_manifest(bundle, local_bundle_data, _forge_manifest)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "do not account for the" in result.stderr
        or "not in the attested question list" in result.stderr
    )


def test_real_proof_verifier_rejects_live_ready_packet_with_unresolved_questions(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _promote(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.is_live_ready = True

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _promote)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "is_live_ready" in result.stderr


# ---------------------------------------------------------------------------
# F145-04: parsed profile, version, selected resume mapping, variant version and
# artifact types are bound end to end. Each case rebinds everything a forger controls.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_rejects_mutated_persisted_profile_version(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _bump_version(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.candidate_profile_version = 2

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _bump_version)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate_profile_version" in result.stderr


def test_real_proof_verifier_rejects_edited_profile_version_with_full_rebinding(
    tmp_path: Path,
) -> None:
    """Editing the profile version and rebinding the private bundle still fails on DB rows."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace("version: 1", "version: 2", 1),
        encoding="utf-8",
    )
    _rebind_profile(local_bundle_data)
    bundle["candidate_profile_version"] = 2
    _rebind_candidate(bundle, local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate_profile_version" in result.stderr or "fingerprint" in result.stderr


def test_real_proof_verifier_rejects_edited_profile_content_with_full_rebinding(
    tmp_path: Path,
) -> None:
    """A profile fact change survives every rebinding a forger can do except the DB row."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace(
            "Engineering Candidate", "Different Candidate", 1
        ),
        encoding="utf-8",
    )
    _rebind_profile(local_bundle_data)
    new_fingerprint = local_bundle_data["candidate_profile_fingerprint_sha256"]

    def _forge_manifest(manifest: dict[str, Any]) -> None:
        manifest["candidate_profile_fingerprint_sha256"] = new_fingerprint

    _rewrite_manifest(bundle, local_bundle_data, _forge_manifest)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "persisted candidate_profile_fingerprint_sha256 does not match" in result.stderr


def test_real_proof_verifier_rejects_profile_fingerprint_not_matching_parsed_profile(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_profile_fingerprint_sha256"] = "b" * 64
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate_profile_fingerprint_sha256 in local bundle does not match" in result.stderr


def test_real_proof_verifier_rejects_selected_resume_mapping_change(tmp_path: Path) -> None:
    """Re-mapping the selected variant to another file (with rebinding) is not the proven resume."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    other_resume = tmp_path / "another_resume.md"
    other_resume.write_text("# Another resume\n", encoding="utf-8")
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    original = Path(local_bundle_data["resume_source_path"])
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace(
            str(original), str(other_resume.resolve())
        ),
        encoding="utf-8",
    )
    _rebind_profile(local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "resume_source artifact does not match the resume file the candidate profile maps" in (
        result.stderr
    )


def test_real_proof_verifier_rejects_profile_without_mapping_for_selected_variant(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    text = profile_path.read_text(encoding="utf-8")
    text = text.replace(f"    {ENGINEERING_VARIANT}: ", "    resume_enterprise_automation: ")
    profile_path.write_text(text, encoding="utf-8")
    _rebind_profile(local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not map the selected resume variant" in result.stderr


def test_real_proof_verifier_rejects_relabelled_variant_that_selector_would_not_choose(
    tmp_path: Path,
) -> None:
    """Relabelling variant/family everywhere still fails: the selector derives it from the job."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    other_variant = "resume_enterprise_automation"
    other_family = "Enterprise Automation & Solutions Architect"
    profile_path = Path(local_bundle_data["candidate_profile_path"])
    # Re-key the variant everywhere in the profile except inside the resume file path.
    text = profile_path.read_text(encoding="utf-8")
    text = text.replace(f'"{ENGINEERING_VARIANT}"', f'"{other_variant}"')
    text = text.replace(f"    {ENGINEERING_VARIANT}: ", f"    {other_variant}: ")
    profile_path.write_text(text, encoding="utf-8")
    _rebind_profile(local_bundle_data)
    local_bundle_data["selected_resume_variant"] = other_variant
    bundle["resume_variant"] = other_variant
    bundle["resume_family"] = other_family

    def _relabel_manifest(manifest: dict[str, Any]) -> None:
        manifest["resume_variant_name"] = other_variant
        manifest["resume_family"] = other_family
        manifest["candidate_profile_fingerprint_sha256"] = local_bundle_data[
            "candidate_profile_fingerprint_sha256"
        ]

    _rewrite_manifest(bundle, local_bundle_data, _relabel_manifest)

    def _relabel_rows(session: Any) -> None:
        variant = session.get(ResumeVariantModel, uuid.UUID(local_bundle_data["resume_variant_id"]))
        variant.name = other_variant
        variant.resume_family = other_family
        packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
        metadata = dict(packet.generation_metadata_json)
        metadata["candidate_profile_fingerprint_sha256"] = local_bundle_data[
            "candidate_profile_fingerprint_sha256"
        ]
        packet.generation_metadata_json = metadata
        artifact = session.get(ArtifactModel, packet.resume_artifact_id)
        artifact_metadata = dict(artifact.metadata_json)
        artifact_metadata["variant"] = other_variant
        artifact.metadata_json = artifact_metadata

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _relabel_rows)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "is not the variant the production selector derives" in result.stderr


def test_real_proof_verifier_rejects_mutated_persisted_resume_variant_version(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _bump(session: Any) -> None:
        variant = session.get(ResumeVariantModel, uuid.UUID(local_bundle_data["resume_variant_id"]))
        variant.version = 2

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _bump)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "ResumeVariantModel.version" in result.stderr


def test_real_proof_verifier_rejects_claimed_resume_version_with_rebinding(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    bundle["resume_version"] = 2
    local_bundle_data["resume_variant_version"] = 2
    _rebind_candidate(bundle, local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "ResumeVariantModel.version" in result.stderr


def test_real_proof_verifier_rejects_wrong_resume_byte_count_with_rebinding(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    bundle["resume_source_byte_count"] = int(bundle["resume_source_byte_count"]) + 1
    local_bundle_data["resume_source_byte_count"] = bundle["resume_source_byte_count"]
    _rebind_candidate(bundle, local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not match the byte count of the mapped resume file" in result.stderr


def test_real_proof_verifier_rejects_mutated_persisted_artifact_size(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _shrink(session: Any) -> None:
        artifact = session.get(ArtifactModel, uuid.UUID(local_bundle_data["resume_artifact_id"]))
        metadata = dict(artifact.metadata_json)
        metadata["size_bytes"] = int(metadata["size_bytes"]) - 1
        artifact.metadata_json = metadata

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _shrink)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "persisted resume artifact size_bytes" in result.stderr


def test_real_proof_verifier_rejects_swapped_persisted_artifact_types(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _swap(session: Any) -> None:
        artifact = session.get(ArtifactModel, uuid.UUID(local_bundle_data["resume_artifact_id"]))
        artifact.type = "cover_letter"

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _swap)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "persisted resume ArtifactModel.type" in result.stderr


def test_real_proof_verifier_rejects_mutated_variant_source_reference(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _repoint(session: Any) -> None:
        variant = session.get(ResumeVariantModel, uuid.UUID(local_bundle_data["resume_variant_id"]))
        variant.source_reference = str(tmp_path / "some_other_resume.md")

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _repoint)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "ResumeVariantModel.source_reference" in result.stderr


def test_real_proof_verifier_rejects_unresolved_category_claims_not_derived_from_profile(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    bundle["candidate_unresolved_fact_categories"] = {"work_authorization": 3}
    _rebind_candidate(bundle, local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "candidate_unresolved_fact_categories" in result.stderr


# ---------------------------------------------------------------------------
# Defect 2: source_attestation must be bound to persisted Greenhouse evidence.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_rejects_forged_self_consistent_source_attestation(
    tmp_path: Path,
) -> None:
    """A locally self-consistent attestation with no persisted Greenhouse row must fail."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _demote_greenhouse_source(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        source.provider = "MANUAL"
        source.source_payload_json = {"source_kind": "manual_paste"}

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _demote_greenhouse_source)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "no persisted GREENHOUSE JobSource row" in result.stderr


def test_real_proof_verifier_rejects_forged_attestation_with_no_persisted_job_source(
    tmp_path: Path,
) -> None:
    """With the JobSource row deleted entirely there is nothing to corroborate."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _drop_greenhouse_source(session: Any) -> None:
        for source in session.query(JobSourceModel).all():
            session.delete(source)

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _drop_greenhouse_source)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "no persisted GREENHOUSE JobSource row" in result.stderr
        or "DB JobModel apply_url" in result.stderr
    )


def test_real_proof_verifier_rejects_source_attestation_without_persisted_payload(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _blank_payload(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        source.source_payload_json = {}

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _blank_payload)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "source_payload_json is missing or not an object" in result.stderr


def test_real_proof_verifier_rejects_fabricated_description_sha(tmp_path: Path) -> None:
    """A fabricated description SHA cannot be corroborated by the persisted job text."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["description_sha256"] = "e" * 64
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not match SHA-256 of the persisted job description" in result.stderr


def test_real_proof_verifier_rejects_persisted_description_hash_tampering(
    tmp_path: Path,
) -> None:
    """Rewriting the persisted description without its hashes must fail."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    job_uuid = uuid.UUID(local_bundle_data["job_id"])

    def _tamper_description(session: Any) -> None:
        job = session.get(JobModel, job_uuid)
        job.description_text = "Rewritten description that was never fetched from Greenhouse."

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _tamper_description)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not match SHA-256 of the persisted job description" in result.stderr


def test_real_proof_verifier_rejects_forged_questions_file_and_attestation_pair(
    tmp_path: Path,
) -> None:
    """A self-consistent forged questions file + attestation SHA must not pass."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    forged_questions = ["Forged Q1", "Forged Q2", "Forged Q3"]
    Path(local_bundle_data["questions_json_path"]).write_text(
        json.dumps(forged_questions), encoding="utf-8"
    )
    local_bundle_data["source_attestation"]["question_list_sha256"] = compute_questions_sha256(
        forged_questions
    )
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert (
        "persisted Greenhouse question_list_sha256" in result.stderr
        or "not in the attested question list" in result.stderr
    )


def test_real_proof_verifier_rejects_attestation_fields_not_matching_persisted_source(
    tmp_path: Path,
) -> None:
    """Each attested Greenhouse provenance field must match the persisted capture."""
    cases = [
        (
            "api_url",
            "https://boards-api.greenhouse.io/v1/boards/forged/jobs/7967740?questions=true",
            "API URL",
        ),
        ("fetched_at_utc", "2020-01-01T00:00:00Z", "fetched_at_utc"),
    ]
    for field, forged_value, expected_fragment in cases:
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        local_bundle_data["source_attestation"][field] = forged_value
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
        assert result.returncode == 1, f"{field} forgery was accepted"
        assert expected_fragment in result.stderr, f"{field}: {result.stderr}"


def test_real_proof_verifier_rejects_persisted_source_payload_provenance_gaps(
    tmp_path: Path,
) -> None:
    """Missing or non-Greenhouse provenance in the persisted payload must fail."""
    cases = [
        ("source_kind", None, "missing source_kind"),
        ("source_kind", "manual_paste", "source kind"),
        ("provider", "MANUAL", "provider"),
        ("fetched_at_utc", None, "missing or invalid fetched_at_utc"),
        ("content_sha256", None, "missing content_sha256"),
        ("question_list_sha256", None, "missing question_list_sha256"),
    ]
    for payload_key, forged_value, expected_fragment in cases:
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

        def _forge_payload(session: Any, key: str = payload_key, value: Any = forged_value) -> None:
            source = session.query(JobSourceModel).one()
            payload = dict(source.source_payload_json)
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value
            source.source_payload_json = payload

        _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_payload)
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
        assert result.returncode == 1, f"{payload_key}={forged_value!r} was accepted"
        assert expected_fragment in result.stderr, f"{payload_key}: {result.stderr}"


def test_real_proof_verifier_rejects_attestation_for_unrelated_persisted_job_posting(
    tmp_path: Path,
) -> None:
    """The persisted Greenhouse row must carry the attested public job id."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _repoint_source_job_id(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        source.source_job_id = "1234567"

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _repoint_source_job_id)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "expected exactly one persisted GREENHOUSE JobSource" in result.stderr


def test_real_proof_verifier_rejects_persisted_screening_question_count_mismatch(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _forge_question_count(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        payload = dict(source.source_payload_json)
        payload["screening_question_count"] = 99
        source.source_payload_json = payload

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_question_count)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "persisted Greenhouse screening_question_count" in result.stderr


def test_real_proof_verifier_rejects_persisted_canonical_apply_url_divergence(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _forge_canonical_url(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        source.canonical_apply_url = "https://job-boards.greenhouse.io/forged/jobs/7967740"
        source.source_url = "https://job-boards.greenhouse.io/forged/jobs/7967740"

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _forge_canonical_url)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "DB JobModel apply_url" in result.stderr or "canonical_apply_url" in result.stderr


# ---------------------------------------------------------------------------
# Defect 3: the verifier must validate the production generation-origin metadata key.
# ---------------------------------------------------------------------------


def _persist_generation_metadata(local_bundle_data: dict[str, Any], metadata: Any) -> None:
    """Overwrite the persisted packet's generation_metadata_json with arbitrary evidence."""
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _replace(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.generation_metadata_json = metadata

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _replace)


def test_real_proof_verifier_accepts_production_generation_metadata_shape(
    tmp_path: Path,
) -> None:
    """Evidence persisted by the real production builder must validate as-is."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    engine = get_engine(local_bundle_data["_runtime_database_url"])
    try:
        with get_sessionmaker(engine)() as session:
            packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
            assert packet is not None
            metadata = packet.generation_metadata_json
            assert metadata["generation_origin"] == "deterministic"
            assert metadata["cover_letter_origin"] == "deterministic"
            assert (
                metadata["candidate_profile_fingerprint_sha256"]
                == (local_bundle_data["candidate_profile_fingerprint_sha256"])
            )
            # The production builder never writes a bare "origin" key.
            assert "origin" not in metadata
    finally:
        engine.dispose()

    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 0, result.stderr
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


def test_real_proof_verifier_rejects_generation_metadata_without_production_key(
    tmp_path: Path,
) -> None:
    """Metadata lacking the production generation_origin key must not reach PASS."""
    for metadata in (
        {"origin": "deterministic"},
        {},
        {"cover_letter_origin": "deterministic", "cover_letter_model": "x"},
    ):
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        _persist_generation_metadata(local_bundle_data, metadata)
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
        assert result.returncode == 1, f"{metadata!r} was accepted as proof evidence"
        assert "missing the production generation_origin key" in result.stderr


def test_real_proof_verifier_rejects_generation_metadata_without_profile_fingerprint(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    _persist_generation_metadata(
        local_bundle_data,
        {
            "generation_origin": "deterministic",
            "cover_letter_origin": "deterministic",
            "cover_letter_model": "DeterministicModelGateway",
        },
    )
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "missing the production candidate_profile_fingerprint_sha256 key" in result.stderr


def test_real_proof_verifier_rejects_wrong_persisted_generation_origin(
    tmp_path: Path,
) -> None:
    """Adversarial non-deterministic persisted origins must still fail closed."""
    for origin in ("mock", "real", "test", "adversarial_mock", ""):
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        _persist_generation_metadata(
            local_bundle_data,
            {
                "generation_origin": origin,
                "cover_letter_origin": origin,
                "cover_letter_model": "DeterministicModelGateway",
                "candidate_profile_fingerprint_sha256": local_bundle_data[
                    "candidate_profile_fingerprint_sha256"
                ],
            },
        )
        result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
        assert result.returncode == 1, f"origin {origin!r} was accepted as proof evidence"
        assert "generation origin in metadata must be deterministic" in result.stderr


# ---------------------------------------------------------------------------
# Defect 4: resolve_proof_db_url must accept the application's real SQLAlchemy URLs
# while still failing closed on unsupported or unusable DB targets.
# ---------------------------------------------------------------------------

APP_SETTINGS_DEFAULT_DB_URL = str(AppSettings.model_fields["database_url"].default)


def _sqlite_shaped_file(tmp_path: Path, name: str = "resolve_probe.db") -> Path:
    path = tmp_path / name
    path.write_bytes(b"SQLite format 3\x00" + bytes(64))
    return path


def test_resolve_proof_db_url_accepts_application_postgres_url_forms() -> None:
    """The real AppSettings PostgreSQL URL form must be a usable proof DB target."""
    assert APP_SETTINGS_DEFAULT_DB_URL.startswith("postgresql+psycopg://")
    assert resolve_proof_db_url(APP_SETTINGS_DEFAULT_DB_URL) == APP_SETTINGS_DEFAULT_DB_URL

    for url in (
        "postgresql+psycopg://jobs:jobs@localhost:5432/jobs",
        "postgresql+psycopg2://jobs:jobs@db.internal:5432/jobs_proof",
        "postgresql://jobs@localhost:5432/jobs",
        "postgresql+psycopg:///jobs",
    ):
        assert resolve_proof_db_url(url) == url

    # SQLAlchemy 2.x dropped the legacy "postgres" alias, so it is normalized.
    assert (
        resolve_proof_db_url("postgres://jobs:jobs@localhost:5432/jobs")
        == "postgresql://jobs:jobs@localhost:5432/jobs"
    )


def test_resolve_proof_db_url_retains_sqlite_persistence_checks(tmp_path: Path) -> None:
    sqlite_file = _sqlite_shaped_file(tmp_path)
    url = f"sqlite:///{sqlite_file}"
    assert resolve_proof_db_url(url) == url
    assert resolve_proof_db_url(f"{url}?check_same_thread=False") == (
        f"{url}?check_same_thread=False"
    )
    # A bare on-disk path is normalized to a SQLite URL after the file is checked.
    assert resolve_proof_db_url(str(sqlite_file)) == f"sqlite:///{sqlite_file.resolve()}"

    corrupt = tmp_path / "corrupt_probe.db"
    corrupt.write_bytes(b"not a database at all")
    with pytest.raises(ProofValidationError, match="is not an openable SQLite database"):
        resolve_proof_db_url(f"sqlite:///{corrupt}")


def test_resolve_proof_db_url_fails_closed_on_unsupported_or_unusable_targets(
    tmp_path: Path,
) -> None:
    cases = [
        ("", "proof database target is empty"),
        ("   ", "proof database target is empty"),
        # Async drivers cannot be read by this synchronous verifier.
        ("postgresql+asyncpg://jobs:jobs@localhost:5432/jobs", "unsupported PostgreSQL driver"),
        ("sqlite+aiosqlite:///proof_evidence.db", "unsupported SQLite driver"),
        # A PostgreSQL target that names no database cannot hold identified proof rows.
        ("postgresql+psycopg://jobs:jobs@localhost:5432", "must name the database"),
        ("postgresql+psycopg://", "must name the database"),
        # Other backends are not verifiable proof evidence.
        ("mysql+pymysql://jobs:jobs@localhost:3306/jobs", "unsupported proof database backend"),
        ("sqlite://", "unsupported SQLite proof database URL"),
        ("sqlite:///:memory:", "in-memory SQLite is not acceptable"),
        (str(tmp_path / "definitely_absent.db"), "proof database file not found on disk"),
    ]
    for target, expected in cases:
        with pytest.raises(ProofValidationError) as excinfo:
            resolve_proof_db_url(target)
        assert expected in str(excinfo.value), f"{target!r}: {excinfo.value}"


def test_resolve_proof_db_url_rejection_does_not_leak_db_credentials() -> None:
    secret = "synthetic-not-a-real-password"
    with pytest.raises(ProofValidationError) as excinfo:
        resolve_proof_db_url(f"postgresql+asyncpg://jobs:{secret}@localhost:5432/jobs")
    message = str(excinfo.value)
    assert secret not in message
    assert "***@localhost:5432/jobs" in message


def test_real_proof_verifier_postgres_target_fails_closed_at_read_time(
    tmp_path: Path,
) -> None:
    """A PostgreSQL target that matches the runtime is opened, then rejected when unreadable.

    The URL must not be misclassified as a missing SQLite file, and the failure
    message must not echo the database password into the receipt or the log.
    """
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    secret = "synthetic-pg-proof-password"
    pg_url = f"postgresql+psycopg://jobs:{secret}@127.0.0.1:59999/jobs_proof_absent"
    local_bundle_data["proof_database"] = database_identity(pg_url)
    receipt_file = tmp_path / "receipt.json"
    result = _run_full_verifier(
        tmp_path, bundle, local_bundle_data, receipt_path=receipt_file, runtime_database_url=pg_url
    )
    assert result.returncode == 1
    assert "proof database file not found on disk" not in result.stderr
    assert "unsupported proof database backend" not in result.stderr
    assert "PROOF_DATABASE_TARGET_MISMATCH" not in result.stderr
    assert (
        "proof database evidence could not be read" in result.stderr
        or "could not be opened as a SQLAlchemy engine" in result.stderr
    )
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert secret not in json.dumps(receipt_data)
    assert secret not in result.stderr
    assert secret not in result.stdout


# ---------------------------------------------------------------------------
# Persisted job identity: title, company, requisition and the runner's snapshot digest
# must be re-derivable from the database rows the proof claims to describe.
# ---------------------------------------------------------------------------


def test_job_snapshot_digest_mirrors_runner_snapshot(tmp_path: Path) -> None:
    """The verifier's snapshot recomputation must stay byte-identical to the runner's."""
    from scripts.run_v14_real_proof import job_snapshot

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    engine = get_engine(local_bundle_data["_runtime_database_url"])
    try:
        with get_sessionmaker(engine)() as session:
            job = session.get(JobModel, uuid.UUID(local_bundle_data["job_id"]))
            assert job is not None
            runner_digest = hashlib.sha256(
                json.dumps(job_snapshot(job), sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            assert compute_job_snapshot_sha256(job) == runner_digest
    finally:
        engine.dispose()
    assert bundle["job_snapshot_sha256"] == runner_digest
    assert bundle["job_snapshot_sha256"] == _persisted_job_snapshot_sha256(
        local_bundle_data["_runtime_database_url"], local_bundle_data["job_id"]
    )


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        ("title", "does not match persisted JobModel.normalized_title"),
        ("company", "does not match persisted CompanyModel.normalized_name"),
        ("location", "job_snapshot_sha256"),
        ("employment_type", "job_snapshot_sha256"),
        ("requisition_id", "JobSource.requisition_id"),
    ],
)
def test_real_proof_verifier_rejects_persisted_job_identity_divergence(
    tmp_path: Path, mutation: str, expected_reason: str
) -> None:
    """A bundle whose job identity no longer matches the persisted job cannot PASS."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _mutate(session: Any) -> None:
        job = session.get(JobModel, uuid.UUID(local_bundle_data["job_id"]))
        assert job is not None
        if mutation == "title":
            job.normalized_title = "Senior AI Automation Engineer"
        elif mutation == "company":
            job.company.normalized_name = "OpenSesame Labs"
        elif mutation == "location":
            job.location_text = "Portland, OR"
        elif mutation == "employment_type":
            job.employment_type = "contract"
        elif mutation == "requisition_id":
            job.sources[0].requisition_id = "0000001"
        else:  # pragma: no cover - guard against typos in parametrization
            raise AssertionError(mutation)

    _mutate_proof_database(local_bundle_data["_runtime_database_url"], _mutate)
    receipt_file = tmp_path / "receipt.json"
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data, receipt_path=receipt_file)
    assert result.returncode == 1, result.stdout
    assert expected_reason in result.stderr
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"


def test_real_proof_verifier_rejects_bundle_claiming_a_different_job_title(
    tmp_path: Path,
) -> None:
    """Editing the redacted bundle and its local binding cannot re-label the persisted job."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    bundle["job_title"] = "Staff Platform Engineer"
    _rebind_candidate(bundle, local_bundle_data)
    result = _run_full_verifier(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 1
    assert "does not match persisted JobModel.normalized_title" in result.stderr

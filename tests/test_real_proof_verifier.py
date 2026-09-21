"""Tests for the redacted V1.4 real-proof evidence verifier."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.verify_v14_real_proof import (
    ALLOWED_TOP_LEVEL_KEYS,
    ALLOWED_UNRESOLVED_FACT_CATEGORY_KEYS,
)

SCHEMA_PATH = (
    Path(__file__).parent.parent / "coordination" / "proofs" / "v14_real_proof.schema.json"
)


def _load_schema() -> dict[str, object]:
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _valid_bundle() -> dict[str, object]:
    sha = "a" * 64
    return {
        "result": "REAL_PROOF_PASS",
        "proof_run_id": "proof-run-1",
        "run_timestamp_utc": "2026-09-21T02:45:00Z",
        "code_commit_sha": "8a0cdb4",
        "job_url": "https://job-boards.greenhouse.io/opensesame/jobs/7967740",
        "job_title": "AI Automation Engineer",
        "company": "OpenSesame",
        "job_snapshot_sha256": sha,
        "candidate_profile_source_class": "PRIVATE_LOCAL",
        "candidate_profile_version": 1,
        "resume_family": "Enterprise Automation & Solutions Architect",
        "resume_variant": "resume_enterprise_automation",
        "resume_version": 1,
        "resume_source_sha256": sha,
        "resume_source_byte_count": 1024,
        "model_provider": "local-production-provider",
        "model_name": "production-model",
        "model_origin": "real",
        "generation_origin": "real",
        "packet_id": "11111111-1111-1111-1111-111111111111",
        "packet_hash": sha,
        "resume_artifact_sha256": sha,
        "cover_letter_artifact_sha256": sha,
        "manifest_sha256": sha,
        "is_live_ready": False,
        "resolved_answers_count": 2,
        "unresolved_questions": ["Unconfirmed work authorization question"],
        "read_back_verification": True,
        "mock_or_fixture_inputs_present": False,
    }


def _run_verifier(tmp_path: Path, bundle: dict[str, object]) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "proof.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    script = Path(__file__).parent.parent / "scripts" / "verify_v14_real_proof.py"
    return subprocess.run(
        [sys.executable, str(script), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_real_proof_verifier_accepts_structurally_valid_redacted_bundle(tmp_path: Path) -> None:
    result = _run_verifier(tmp_path, _valid_bundle())
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


def test_real_proof_verifier_rejects_mock_origin(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["model_origin"] = "mock"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "REAL_PROOF_VALIDATION_FAIL" in result.stderr


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
    assert "private field must not be committed" in result.stderr


def test_real_proof_verifier_rejects_unverified_readback(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["read_back_verification"] = False
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "read_back_verification must be true" in result.stderr


# --- RP14-T5: committed redacted evidence is a closed allowlist -------------------------


def test_real_proof_verifier_accepts_full_runtime_evidence_field_set(tmp_path: Path) -> None:
    """Every field the production runner emits must survive the closed allowlist."""
    bundle = _valid_bundle()
    bundle["candidate_unresolved_fact_categories"] = {
        "identity": 1,
        "work_authorization": 3,
        "target": 2,
        "experience_dates": 1,
    }
    bundle["questions_count"] = 7
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


def test_real_proof_verifier_rejects_unexpected_top_level_field(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["operator_notes"] = "arbitrary free text that could carry private content"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "non-allowlisted field must not be committed: operator_notes" in result.stderr


def test_real_proof_verifier_rejects_unexpected_nested_object_field(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["candidate_unresolved_fact_categories"] = {
        "identity": 1,
        "home_address_line": 1,
    }
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert (
        "non-allowlisted field must not be committed: "
        "candidate_unresolved_fact_categories.home_address_line" in result.stderr
    )


def test_real_proof_verifier_rejects_non_count_nested_value(tmp_path: Path) -> None:
    """Category values are counts; a string value could smuggle the private fact itself."""
    bundle = _valid_bundle()
    bundle["candidate_unresolved_fact_categories"] = {"identity": "phone +1-555-0100"}
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "candidate_unresolved_fact_categories.identity must be a non-negative count" in (
        result.stderr
    )


def test_real_proof_verifier_rejects_nested_object_evidence_container(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["candidate_unresolved_fact_categories"] = ["identity"]
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "candidate_unresolved_fact_categories must be an object" in result.stderr


def test_real_proof_verifier_rejects_nested_structure_in_unresolved_questions(
    tmp_path: Path,
) -> None:
    bundle = _valid_bundle()
    bundle["unresolved_questions"] = [
        "Unconfirmed work authorization question",
        {"question": "Salary?", "private_context": "candidate compensation history"},
    ]
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "unresolved_questions[1] must be a string" in result.stderr


def test_real_proof_verifier_rejects_unexpected_field_even_when_otherwise_valid(
    tmp_path: Path,
) -> None:
    """An extra field is fatal, not merely ignored, even with no forbidden token in it."""
    bundle = _valid_bundle()
    bundle["local_resume_path"] = "/home/user/private/resume.pdf"
    bundle["raw_model_output"] = "generated cover letter body"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "non-allowlisted field must not be committed" in result.stderr
    assert "local_resume_path" in result.stderr
    assert "raw_model_output" in result.stderr


def test_committed_schema_is_closed_and_matches_verifier_allowlist() -> None:
    schema = _load_schema()
    assert schema["additionalProperties"] is False

    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == set(ALLOWED_TOP_LEVEL_KEYS)

    required = schema["required"]
    assert isinstance(required, list)
    assert set(required) <= set(ALLOWED_TOP_LEVEL_KEYS)


def test_committed_schema_nested_evidence_object_is_closed() -> None:
    schema = _load_schema()
    properties = schema["properties"]
    assert isinstance(properties, dict)

    categories = properties["candidate_unresolved_fact_categories"]
    assert isinstance(categories, dict)
    assert categories["additionalProperties"] is False

    nested = categories["properties"]
    assert isinstance(nested, dict)
    assert set(nested) == set(ALLOWED_UNRESOLVED_FACT_CATEGORY_KEYS)

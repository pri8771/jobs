"""Tests for the redacted V1.4 real-proof evidence verifier and receipt generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _valid_bundle() -> dict[str, object]:
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
        "resume_family": "Enterprise Automation & Solutions Architect",
        "resume_variant": "resume_enterprise_automation",
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


def _run_verifier(
    tmp_path: Path,
    bundle: dict[str, object],
    local_bundle_path: Path | None = None,
    receipt_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "proof.json"
    path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    script = Path(__file__).parent.parent / "scripts" / "verify_v14_real_proof.py"
    cmd = [sys.executable, str(script), str(path)]
    if local_bundle_path is not None:
        cmd.extend(["--local-full-bundle", str(local_bundle_path)])
    if receipt_path is not None:
        cmd.extend(["--receipt-output", str(receipt_path)])
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_real_proof_verifier_accepts_structurally_valid_candidate_bundle(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    result = _run_verifier(tmp_path, _valid_bundle(), receipt_path=receipt)
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout
    assert receipt.exists()
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_PASS"
    assert receipt_data["local_full_bundle_verified"] is False
    assert len(receipt_data["candidate_bundle_sha256"]) == 64


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
    assert (
        "private field must not be committed" in result.stderr
        or "disallowed extra keys" in result.stderr
    )


def test_real_proof_verifier_rejects_disallowed_extra_keys(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["arbitrary_custom_notes"] = "some note"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "disallowed extra keys" in result.stderr


def test_real_proof_verifier_rejects_unverified_readback(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["read_back_verification"] = False
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "read_back_verification must be true" in result.stderr


def test_real_proof_verifier_validates_local_bundle_cross_binding(tmp_path: Path) -> None:
    # Setup real dummy files
    resume_file = tmp_path / "resume.txt"
    resume_file.write_text("Real resume text", encoding="utf-8")
    resume_sha = hashlib.sha256(resume_file.read_bytes()).hexdigest()

    cover_file = tmp_path / "cover.txt"
    cover_file.write_text("Real cover letter text", encoding="utf-8")
    cover_sha = hashlib.sha256(cover_file.read_bytes()).hexdigest()

    packet_id = "22222222-2222-2222-2222-222222222222"
    packet_hash = "c" * 64

    manifest_file = tmp_path / "manifest.json"
    manifest_data = {
        "packet_id": packet_id,
        "packet_hash": packet_hash,
        "resume_artifact_sha256": resume_sha,
        "cover_letter_artifact_sha256": cover_sha,
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_file.read_bytes()).hexdigest()

    bundle = _valid_bundle()
    bundle["proof_run_id"] = "proof-run-local-1"
    bundle["packet_id"] = packet_id
    bundle["packet_hash"] = packet_hash
    bundle["resume_source_sha256"] = resume_sha
    bundle["resume_artifact_sha256"] = resume_sha
    bundle["cover_letter_artifact_sha256"] = cover_sha
    bundle["manifest_sha256"] = manifest_sha

    candidate_content = json.dumps(bundle, indent=2) + "\n"
    candidate_sha = hashlib.sha256(candidate_content.encode("utf-8")).hexdigest()

    local_bundle_data = {
        "proof_run_id": "proof-run-local-1",
        "candidate_bundle_sha256": candidate_sha,
        "candidate_profile_sha256": "f" * 64,
        "candidate_profile_path": "/path/to/profile.yaml",
        "resume_source_path": str(resume_file),
        "questions_json_path": "/path/to/questions.json",
        "local_artifacts": [
            {"type": "resume_source", "path": str(resume_file), "sha256": resume_sha},
            {"type": "resume_artifact", "path": str(resume_file), "sha256": resume_sha},
            {"type": "cover_letter_artifact", "path": str(cover_file), "sha256": cover_sha},
            {"type": "manifest", "path": str(manifest_file), "sha256": manifest_sha},
        ],
    }
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    receipt_file = tmp_path / "receipt.json"
    result = _run_verifier(
        tmp_path,
        bundle,
        local_bundle_path=local_bundle_file,
        receipt_path=receipt_file,
    )
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_PASS"
    assert receipt_data["local_full_bundle_verified"] is True


def test_real_proof_verifier_rejects_local_bundle_hash_mismatch(tmp_path: Path) -> None:
    resume_file = tmp_path / "resume.txt"
    resume_file.write_text("Real resume text", encoding="utf-8")
    resume_sha = hashlib.sha256(resume_file.read_bytes()).hexdigest()

    bundle = _valid_bundle()
    bundle["proof_run_id"] = "proof-run-local-1"
    bundle["resume_source_sha256"] = resume_sha
    bundle["resume_artifact_sha256"] = resume_sha

    # Forged local bundle with mismatched SHA
    local_bundle_data = {
        "proof_run_id": "proof-run-local-1",
        "local_artifacts": [
            {"type": "resume_source", "path": str(resume_file), "sha256": "0" * 64},
        ],
    }
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "local artifact hash mismatch" in result.stderr

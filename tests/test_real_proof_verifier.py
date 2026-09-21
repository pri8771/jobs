"""Tests for the redacted V1.4 real-proof evidence verifier and receipt generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jobs_automation.preparation.packet_builder import compute_canonical_packet_hash


def _valid_bundle() -> dict[str, Any]:
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
    bundle: dict[str, Any],
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


def test_real_proof_verifier_omitting_local_bundle_fails_closed_without_pass(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    result = _run_verifier(tmp_path, _valid_bundle(), receipt_path=receipt)
    assert result.returncode == 1
    assert "REAL_PROOF_VALIDATION_STRUCTURAL_ONLY" in result.stderr
    assert receipt.exists()
    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_data["result"] == "REAL_PROOF_FAIL"
    assert receipt_data["local_full_bundle_verified"] is False
    assert any("local full bundle required" in r for r in receipt_data["rejection_reasons"])
    assert len(receipt_data["candidate_bundle_sha256"]) == 64


def test_real_proof_verifier_rejects_candidate_self_labeled_pass(tmp_path: Path) -> None:
    bundle = _valid_bundle()
    bundle["result"] = "REAL_PROOF_PASS"
    result = _run_verifier(tmp_path, bundle)
    assert result.returncode == 1
    assert "result must be REAL_PROOF_CANDIDATE" in result.stderr


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
    assert "model_origin must be 'deterministic'" in result.stderr

    bundle2 = _valid_bundle()
    bundle2["generation_origin"] = "real"
    result2 = _run_verifier(tmp_path, bundle2)
    assert result2.returncode == 1
    assert "generation_origin must be 'deterministic'" in result2.stderr

    bundle3 = _valid_bundle()
    bundle3["generation_engine"] = "custom-llm"
    result3 = _run_verifier(tmp_path, bundle3)
    assert result3.returncode == 1
    assert "generation_engine must be 'deterministic-canonical-renderer'" in result3.stderr


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


def _setup_valid_full_run(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resume_file = tmp_path / "resume.txt"
    resume_file.write_text("Real resume text", encoding="utf-8")
    resume_sha = hashlib.sha256(resume_file.read_bytes()).hexdigest()

    cover_file = tmp_path / "cover.txt"
    cover_file.write_text("Real cover letter text", encoding="utf-8")
    cover_sha = hashlib.sha256(cover_file.read_bytes()).hexdigest()

    packet_id = "22222222-2222-2222-2222-222222222222"
    job_id = "33333333-3333-3333-3333-333333333333"
    resume_variant_id = "44444444-4444-4444-4444-444444444444"
    profile_version = 1
    answers = {"screening_q1": "Authorized"}
    answer_provenance = {"screening_q1": {"source": "profile"}}

    canonical_hash = compute_canonical_packet_hash(
        job_id=job_id,
        profile_version=profile_version,
        resume_variant_id=resume_variant_id,
        resume_sha=resume_sha,
        cover_letter_sha=cover_sha,
        answers=answers,
        answer_provenance=answer_provenance,
    )

    manifest_data = {
        "packet_id": packet_id,
        "job_id": job_id,
        "candidate_profile_version": profile_version,
        "resume_family": "Enterprise Automation & Solutions Architect",
        "resume_variant_id": resume_variant_id,
        "resume_variant_name": "resume_enterprise_automation",
        "resume_artifact_sha256": resume_sha,
        "cover_letter_artifact_sha256": cover_sha,
        "answers": answers,
        "answer_provenance": answer_provenance,
        "packet_hash": canonical_hash,
        "generation_origin": "deterministic",
        "is_live_ready": False,
    }
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_file.read_bytes()).hexdigest()

    bundle = _valid_bundle()
    bundle["proof_run_id"] = "proof-run-local-1"
    bundle["packet_id"] = packet_id
    bundle["packet_hash"] = canonical_hash
    bundle["resume_source_sha256"] = resume_sha
    bundle["resume_artifact_sha256"] = resume_sha
    bundle["cover_letter_artifact_sha256"] = cover_sha
    bundle["manifest_sha256"] = manifest_sha
    bundle["candidate_profile_version"] = profile_version
    bundle["resume_variant"] = "resume_enterprise_automation"
    bundle["resume_family"] = "Enterprise Automation & Solutions Architect"

    candidate_content = json.dumps(bundle, indent=2) + "\n"
    candidate_sha = hashlib.sha256(candidate_content.encode("utf-8")).hexdigest()

    local_bundle_data = {
        "proof_run_id": "proof-run-local-1",
        "job_id": job_id,
        "candidate_bundle_sha256": candidate_sha,
        "candidate_profile_sha256": "f" * 64,
        "candidate_profile_path": "/path/to/profile.yaml",
        "candidate_profile_source_class": "PRIVATE_LOCAL",
        "resume_source_path": str(resume_file),
        "questions_json_path": "/path/to/questions.json",
        "source_attestation": {
            "provider": "GREENHOUSE",
            "source_kind": "greenhouse_public_job_board_api",
            "public_job_id": "7967740",
            "api_url": "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740?questions=true",
            "fetched_at_utc": "2026-09-21T02:45:00Z",
            "description_sha256": "e" * 64,
            "question_list_sha256": "d" * 64,
            "canonical_apply_url": "https://job-boards.greenhouse.io/opensesame/jobs/7967740",
        },
        "local_artifacts": [
            {"type": "resume_source", "path": str(resume_file), "sha256": resume_sha},
            {"type": "resume_artifact", "path": str(resume_file), "sha256": resume_sha},
            {"type": "cover_letter_artifact", "path": str(cover_file), "sha256": cover_sha},
            {"type": "manifest", "path": str(manifest_file), "sha256": manifest_sha},
        ],
    }
    return bundle, local_bundle_data


def test_real_proof_verifier_validates_complete_local_bundle_and_cross_binding(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
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


def test_real_proof_verifier_rejects_missing_candidate_bundle_sha_in_local_bundle(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    del local_bundle_data["candidate_bundle_sha256"]
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "missing mandatory candidate_bundle_sha256" in result.stderr


def test_real_proof_verifier_rejects_mismatched_candidate_bundle_sha_in_local_bundle(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_bundle_sha256"] = "0" * 64
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "candidate_bundle_sha256 in local bundle does not match" in result.stderr


def test_real_proof_verifier_rejects_example_profile_sha_in_local_bundle(tmp_path: Path) -> None:
    repo_example = Path(__file__).resolve().parent.parent / "config" / "candidate_profile.example.yaml"
    if not repo_example.exists():
        return
    example_sha = hashlib.sha256(repo_example.read_bytes()).hexdigest()

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_profile_sha256"] = example_sha
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "matches repository example file" in result.stderr


def test_real_proof_verifier_rejects_missing_or_invalid_greenhouse_source_attestation(tmp_path: Path) -> None:
    # 1. Missing source attestation
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    del local_bundle_data["source_attestation"]
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "missing mandatory source_attestation" in result.stderr

    # 2. Invalid provider
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["provider"] = "MANUAL"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "provider must be GREENHOUSE" in result.stderr

    # 3. Invalid api_url
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["api_url"] = "https://example.com/api"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "has invalid api_url" in result.stderr


def test_real_proof_verifier_rejects_forged_canonical_packet_hash(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    # Manifest has forged packet_hash
    manifest_path = Path(local_bundle_data["local_artifacts"][3]["path"])  # manifest is index 3
    manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_json["packet_hash"] = "9" * 64
    manifest_path.write_text(json.dumps(manifest_json), encoding="utf-8")

    # Update manifest hash in artifacts and bundle to pass artifact SHA check
    new_manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    local_bundle_data["local_artifacts"][3]["sha256"] = new_manifest_sha
    bundle["manifest_sha256"] = new_manifest_sha
    bundle["packet_hash"] = "9" * 64

    # Update candidate SHA
    candidate_content = json.dumps(bundle, indent=2) + "\n"
    local_bundle_data["candidate_bundle_sha256"] = hashlib.sha256(candidate_content.encode("utf-8")).hexdigest()

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert (
        "canonical packet hash recomputation mismatch" in result.stderr
        or "manifest packet_hash does not match recomputed canonical hash" in result.stderr
    )


def test_real_proof_verifier_rejects_mismatched_manifest_linkage(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    # Manifest has different job_id than local bundle
    local_bundle_data["job_id"] = "different-job-id-9999"

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "manifest job_id" in result.stderr and "does not match local job_id" in result.stderr

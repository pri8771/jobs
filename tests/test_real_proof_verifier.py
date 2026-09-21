"""Tests for the redacted V1.4 real-proof evidence verifier and receipt generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

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
    compute_canonical_packet_hash,
    compute_questions_sha256,
)


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

    cand_profile_file = tmp_path / "candidate_private_profile.yaml"
    cand_profile_file.write_text("name: Private Candidate\n", encoding="utf-8")
    cand_profile_sha = hashlib.sha256(cand_profile_file.read_bytes()).hexdigest()

    questions = ["Question 1", "Question 2", "Question 3"]
    questions_file = tmp_path / "job_questions.json"
    questions_file.write_text(json.dumps(questions), encoding="utf-8")
    questions_sha = compute_questions_sha256(questions)

    packet_id = "22222222-2222-2222-2222-222222222222"
    job_id = "33333333-3333-3333-3333-333333333333"
    resume_variant_id = "44444444-4444-4444-4444-444444444444"
    resume_artifact_id = "55555555-5555-5555-5555-555555555555"
    cover_letter_artifact_id = "66666666-6666-6666-6666-666666666666"
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
    bundle["job_url"] = "https://job-boards.greenhouse.io/opensesame/jobs/7967740"
    bundle["packet_id"] = packet_id
    bundle["packet_hash"] = canonical_hash
    bundle["resume_source_sha256"] = resume_sha
    bundle["resume_artifact_sha256"] = resume_sha
    bundle["cover_letter_artifact_sha256"] = cover_sha
    bundle["manifest_sha256"] = manifest_sha
    bundle["candidate_profile_version"] = profile_version
    bundle["resume_variant"] = "resume_enterprise_automation"
    bundle["resume_family"] = "Enterprise Automation & Solutions Architect"
    bundle["questions_count"] = len(questions)

    candidate_content = json.dumps(bundle, indent=2) + "\n"
    candidate_sha = hashlib.sha256(candidate_content.encode("utf-8")).hexdigest()

    local_bundle_data = {
        "proof_run_id": "proof-run-local-1",
        "job_id": job_id,
        "packet_id": packet_id,
        "resume_variant_id": resume_variant_id,
        "resume_artifact_id": resume_artifact_id,
        "cover_letter_artifact_id": cover_letter_artifact_id,
        "candidate_bundle_sha256": candidate_sha,
        "candidate_profile_sha256": cand_profile_sha,
        "candidate_profile_path": str(cand_profile_file),
        "candidate_profile_source_class": "PRIVATE_LOCAL",
        "resume_source_path": str(resume_file),
        "questions_json_path": str(questions_file),
        "source_attestation": {
            "provider": "GREENHOUSE",
            "source_kind": "greenhouse_public_job_board_api",
            "public_job_id": "7967740",
            "api_url": "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740?questions=true",
            "fetched_at_utc": "2026-09-21T02:45:00Z",
            "description_sha256": "e" * 64,
            "question_list_sha256": questions_sha,
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


def test_real_proof_verifier_validates_complete_local_bundle_and_cross_binding(
    tmp_path: Path,
) -> None:
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


def test_real_proof_verifier_rejects_missing_candidate_bundle_sha_in_local_bundle(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    del local_bundle_data["candidate_bundle_sha256"]
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "missing mandatory candidate_bundle_sha256" in result.stderr


def test_real_proof_verifier_rejects_mismatched_candidate_bundle_sha_in_local_bundle(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_bundle_sha256"] = "0" * 64
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "candidate_bundle_sha256 in local bundle does not match" in result.stderr


def test_real_proof_verifier_rejects_example_profile_sha_in_local_bundle(tmp_path: Path) -> None:
    repo_example = (
        Path(__file__).resolve().parent.parent / "config" / "candidate_profile.example.yaml"
    )
    if not repo_example.exists():
        return
    example_sha = hashlib.sha256(repo_example.read_bytes()).hexdigest()

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    # Set the candidate profile path to the example file
    local_bundle_data["candidate_profile_path"] = str(repo_example)
    local_bundle_data["candidate_profile_sha256"] = example_sha
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    # 4. Invalid or missing fetched_at_utc
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["fetched_at_utc"] = "not-a-timestamp"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "fetched_at_utc" in result.stderr

    # 5. Mismatched canonical_apply_url vs redacted.job_url
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["canonical_apply_url"] = (
        "https://job-boards.greenhouse.io/other/jobs/7967740"
    )
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "does not match source_attestation canonical_apply_url" in result.stderr


def test_real_proof_verifier_rejects_tampered_or_missing_questions_json(tmp_path: Path) -> None:
    # 1. Missing questions file
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["questions_json_path"] = str(tmp_path / "non_existent_questions.json")
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "questions_json_path file not found on disk" in result.stderr

    # 2. Tampered questions content (hash mismatch)
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    q_file = Path(local_bundle_data["questions_json_path"])
    q_file.write_text(json.dumps(["Tampered Q1", "Tampered Q2", "Tampered Q3"]), encoding="utf-8")
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert (
        "questions count in questions JSON" in result.stderr
        and "does not match redacted evidence" in result.stderr
    )


def test_real_proof_verifier_rejects_missing_or_tampered_candidate_profile(tmp_path: Path) -> None:
    # 1. Missing profile file
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["candidate_profile_path"] = str(tmp_path / "non_existent_profile.yaml")
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "candidate_profile_path file not found on disk" in result.stderr

    # 2. Tampered profile content (hash mismatch)
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    prof_file = Path(local_bundle_data["candidate_profile_path"])
    prof_file.write_text("name: Tampered Profile\n", encoding="utf-8")
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "candidate profile file on disk hash mismatch" in result.stderr


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
        local_bundle_file = tmp_path / "private_bundle.json"
        local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
        result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
        assert result.returncode == 1
        assert f"missing mandatory valid UUID {field}" in result.stderr


def test_real_proof_verifier_rejects_forged_canonical_packet_hash(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    manifest_path = Path(local_bundle_data["local_artifacts"][3]["path"])
    manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_json["packet_hash"] = "9" * 64
    manifest_path.write_text(json.dumps(manifest_json), encoding="utf-8")

    new_manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    local_bundle_data["local_artifacts"][3]["sha256"] = new_manifest_sha
    bundle["manifest_sha256"] = new_manifest_sha
    bundle["packet_hash"] = "9" * 64

    candidate_content = json.dumps(bundle, indent=2) + "\n"
    local_bundle_data["candidate_bundle_sha256"] = hashlib.sha256(
        candidate_content.encode("utf-8")
    ).hexdigest()

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
    local_bundle_data["job_id"] = "99999999-9999-9999-9999-999999999999"

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "manifest job_id" in result.stderr and "does not match local job_id" in result.stderr


def test_real_proof_verifier_validates_database_records_when_database_url_provided(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "proof_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_sessionmaker(engine)

    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    job_uuid = uuid.UUID(local_bundle_data["job_id"])
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])
    variant_uuid = uuid.UUID(local_bundle_data["resume_variant_id"])
    resume_art_uuid = uuid.UUID(local_bundle_data["resume_artifact_id"])
    cl_art_uuid = uuid.UUID(local_bundle_data["cover_letter_artifact_id"])

    with session_factory() as session:
        company = CompanyModel(normalized_name="OpenSesame")
        session.add(company)
        session.flush()

        job = JobModel(
            id=job_uuid,
            company_id=company.id,
            normalized_title="AI Automation Engineer",
            description_text="Real description",
        )
        session.add(job)

        source = JobSourceModel(
            job_id=job_uuid,
            provider="GREENHOUSE",
            source_job_id="7967740",
            source_url=bundle["job_url"],
            canonical_apply_url=bundle["job_url"],
            source_payload_json={
                "source_kind": "greenhouse_public_job_board_api",
                "api_url": "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740?questions=true",
                "fetched_at_utc": "2026-09-21T02:45:00Z",
            },
        )
        session.add(source)

        variant = ResumeVariantModel(
            id=variant_uuid,
            resume_family="Enterprise Automation & Solutions Architect",
            name="resume_enterprise_automation",
            version=1,
            content_hash="a" * 64,
        )
        session.add(variant)

        resume_art = ArtifactModel(
            id=resume_art_uuid,
            type="resume",
            storage_uri=f"file://{local_bundle_data['local_artifacts'][1]['path']}",
            sha256=bundle["resume_artifact_sha256"],
        )
        cl_art = ArtifactModel(
            id=cl_art_uuid,
            type="cover_letter",
            storage_uri=f"file://{local_bundle_data['local_artifacts'][2]['path']}",
            sha256=bundle["cover_letter_artifact_sha256"],
        )
        session.add_all([resume_art, cl_art])

        packet = ApplicationPacketModel(
            id=packet_uuid,
            job_id=job_uuid,
            candidate_profile_version=1,
            resume_variant_id=variant_uuid,
            resume_artifact_id=resume_art_uuid,
            cover_letter_artifact_id=cl_art_uuid,
            packet_hash=bundle["packet_hash"],
            generation_metadata_json={"origin": "deterministic"},
            is_live_ready=False,
        )
        session.add(packet)
        session.commit()

    local_bundle_data["database_url"] = db_url
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


# ---------------------------------------------------------------------------
# Lane 1 V1.4 P0A adversarial coverage for the remaining verifier gaps.
#
# Every test below encodes a requirement the *independent* verifier must enforce
# before P0A can be accepted. Tests carrying ``xfail(strict=True)`` currently
# FAIL against the production verifier in scripts/verify_v14_real_proof.py: they
# document an open proof-integrity gap, not a flaky expectation. When the
# verifier is repaired each one XPASSes, which strict mode turns into a hard
# failure so the marker has to be removed deliberately. Tests without the marker
# are green controls proving the adversarial harness itself is sound.
# ---------------------------------------------------------------------------

_PROOF_DESCRIPTION_TEXT = "Greenhouse job description body for the V1.4 real-proof job."


def _rebind_candidate_bundle_sha(
    bundle: dict[str, Any], local_bundle_data: dict[str, Any]
) -> None:
    """Recompute candidate_bundle_sha256 exactly as ``_run_verifier`` serializes the bundle."""
    content = json.dumps(bundle, indent=2) + "\n"
    local_bundle_data["candidate_bundle_sha256"] = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def _persist_proof_database(
    tmp_path: Path,
    bundle: dict[str, Any],
    local_bundle_data: dict[str, Any],
    questions: list[str],
    *,
    db_name: str = "v14_proof_source.db",
    description_text: str = _PROOF_DESCRIPTION_TEXT,
    source_column_overrides: dict[str, Any] | None = None,
    source_payload_overrides: dict[str, Any] | None = None,
    variant_overrides: dict[str, Any] | None = None,
    resume_artifact_overrides: dict[str, Any] | None = None,
    packet_overrides: dict[str, Any] | None = None,
    omit_packet: bool = False,
) -> str:
    """Persist the production-shaped proof records and return the SQLite database URL.

    Defaults persist an internally honest run: the Greenhouse ``JobSourceModel``
    carries exactly the evidence the local bundle's ``source_attestation`` claims,
    and ``JobModel.description_hash`` matches ``description_text``. Each override
    injects one adversarial divergence.
    """
    db_file = tmp_path / db_name
    db_url = f"sqlite:///{db_file}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_sessionmaker(engine)

    attestation = local_bundle_data["source_attestation"]
    description_sha = hashlib.sha256(description_text.encode("utf-8")).hexdigest()

    job_uuid = uuid.UUID(local_bundle_data["job_id"])
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])
    variant_uuid = uuid.UUID(local_bundle_data["resume_variant_id"])
    resume_art_uuid = uuid.UUID(local_bundle_data["resume_artifact_id"])
    cl_art_uuid = uuid.UUID(local_bundle_data["cover_letter_artifact_id"])

    source_columns: dict[str, Any] = {
        "job_id": job_uuid,
        "provider": "GREENHOUSE",
        "source_job_id": str(attestation["public_job_id"]),
        "source_url": str(attestation["canonical_apply_url"]),
        "canonical_apply_url": str(attestation["canonical_apply_url"]),
    }
    source_columns.update(source_column_overrides or {})

    source_payload: dict[str, Any] = {
        "source_kind": str(attestation["source_kind"]),
        "api_url": str(attestation["api_url"]),
        "fetched_at_utc": str(attestation["fetched_at_utc"]),
        "content_sha256": description_sha,
        "question_list_sha256": compute_questions_sha256(questions),
    }
    source_payload.update(source_payload_overrides or {})

    variant_columns: dict[str, Any] = {
        "id": variant_uuid,
        "resume_family": bundle["resume_family"],
        "name": bundle["resume_variant"],
        "version": 1,
        "content_hash": bundle["resume_source_sha256"],
    }
    variant_columns.update(variant_overrides or {})

    resume_artifact_columns: dict[str, Any] = {
        "id": resume_art_uuid,
        "type": "resume",
        "storage_uri": f"file://{local_bundle_data['local_artifacts'][1]['path']}",
        "sha256": bundle["resume_artifact_sha256"],
    }
    resume_artifact_columns.update(resume_artifact_overrides or {})

    packet_columns: dict[str, Any] = {
        "id": packet_uuid,
        "job_id": job_uuid,
        "candidate_profile_version": bundle["candidate_profile_version"],
        "resume_variant_id": variant_uuid,
        "resume_artifact_id": resume_art_uuid,
        "cover_letter_artifact_id": cl_art_uuid,
        "packet_hash": bundle["packet_hash"],
        "generation_metadata_json": {"origin": "deterministic"},
        "is_live_ready": bundle["is_live_ready"],
    }
    packet_columns.update(packet_overrides or {})

    with session_factory() as session:
        company = CompanyModel(normalized_name=str(bundle["company"]))
        session.add(company)
        session.flush()

        session.add(
            JobModel(
                id=job_uuid,
                company_id=company.id,
                normalized_title=str(bundle["job_title"]),
                description_text=description_text,
                description_hash=description_sha,
            )
        )
        session.add(JobSourceModel(source_payload_json=source_payload, **source_columns))
        session.add(ResumeVariantModel(**variant_columns))
        session.add(ArtifactModel(**resume_artifact_columns))
        session.add(
            ArtifactModel(
                id=cl_art_uuid,
                type="cover_letter",
                storage_uri=f"file://{local_bundle_data['local_artifacts'][2]['path']}",
                sha256=bundle["cover_letter_artifact_sha256"],
            )
        )
        if not omit_packet:
            session.add(ApplicationPacketModel(**packet_columns))
        session.commit()

    return db_url


def _setup_full_run_with_persisted_source(
    tmp_path: Path, **db_kwargs: Any
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Build a complete local/redacted proof pair backed by persisted DB records."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    questions: list[str] = json.loads(
        Path(local_bundle_data["questions_json_path"]).read_text(encoding="utf-8")
    )
    # The honest attestation quotes the SHA of the description actually persisted.
    local_bundle_data["source_attestation"]["description_sha256"] = hashlib.sha256(
        _PROOF_DESCRIPTION_TEXT.encode("utf-8")
    ).hexdigest()
    db_url = _persist_proof_database(
        tmp_path, bundle, local_bundle_data, questions, **db_kwargs
    )
    local_bundle_data["database_url"] = db_url
    _rebind_candidate_bundle_sha(bundle, local_bundle_data)
    return bundle, local_bundle_data, questions


def _verify(
    tmp_path: Path, bundle: dict[str, Any], local_bundle_data: dict[str, Any]
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    receipt_file = tmp_path / "receipt.json"
    result = _run_verifier(
        tmp_path,
        bundle,
        local_bundle_path=local_bundle_file,
        receipt_path=receipt_file,
    )
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    return result, receipt


def _assert_fails_closed(
    result: subprocess.CompletedProcess[str], receipt: dict[str, Any]
) -> None:
    assert result.returncode == 1, (
        f"verifier granted PASS on an adversarial bundle; stdout={result.stdout!r}"
    )
    assert "REAL_PROOF_VALIDATION_PASS" not in result.stdout
    assert receipt["result"] == "REAL_PROOF_FAIL"
    assert receipt["rejection_reasons"], "fail-closed receipt must record a rejection reason"


def test_persisted_source_baseline_passes_so_adversarial_variants_are_isolated(
    tmp_path: Path,
) -> None:
    """Green control: the honest DB-backed run is the only difference-free case."""
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(tmp_path)
    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    assert result.returncode == 0, result.stderr
    assert receipt["result"] == "REAL_PROOF_PASS"
    assert receipt["local_full_bundle_verified"] is True


# Contradictions between the proof bundle and the persisted packet/variant/artifact
# rows. Each must fail closed whether or not the local bundle points at the DB.
_PERSISTED_RECORD_CONTRADICTIONS: dict[str, dict[str, Any]] = {
    "packet_row_absent": {"omit_packet": True},
    "packet_hash": {"packet_overrides": {"packet_hash": "0" * 64}},
    "packet_generation_origin": {
        "packet_overrides": {"generation_metadata_json": {"origin": "llm-authored"}}
    },
    "resume_variant_name": {"variant_overrides": {"name": "resume_unrelated_variant"}},
    "resume_variant_family": {"variant_overrides": {"resume_family": "Unrelated Family"}},
    "resume_artifact_sha256": {"resume_artifact_overrides": {"sha256": "1" * 64}},
}


@pytest.mark.parametrize("contradiction", sorted(_PERSISTED_RECORD_CONTRADICTIONS))
def test_persisted_record_contradiction_fails_when_database_target_is_configured(
    tmp_path: Path, contradiction: str
) -> None:
    """Green control: with database_url present, persisted-record checks do bite."""
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(
        tmp_path, **_PERSISTED_RECORD_CONTRADICTIONS[contradiction]
    )
    assert local_bundle_data["database_url"]
    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)


@pytest.mark.xfail(
    strict=True,
    reason="P0A gap: verify_database_linkage returns silently when the local bundle "
    "declares no database_url/db_path, so REAL_PROOF_PASS is granted with zero "
    "persisted-record verification.",
)
def test_real_proof_pass_requires_a_configured_proof_database_target(tmp_path: Path) -> None:
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(tmp_path)
    del local_bundle_data["database_url"]
    assert "db_path" not in local_bundle_data

    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)


@pytest.mark.parametrize("contradiction", sorted(_PERSISTED_RECORD_CONTRADICTIONS))
@pytest.mark.xfail(
    strict=True,
    reason="P0A gap: omitting database_url/db_path from the local bundle skips the "
    "persisted ApplicationPacketModel/ResumeVariant/Artifact checks entirely, so a "
    "bundle that provably contradicts the database still receives REAL_PROOF_PASS.",
)
def test_omitting_database_target_must_not_bypass_persisted_record_checks(
    tmp_path: Path, contradiction: str
) -> None:
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(
        tmp_path, **_PERSISTED_RECORD_CONTRADICTIONS[contradiction]
    )
    # Same database on disk, same contradicting rows — only the pointer is withheld.
    del local_bundle_data["database_url"]
    assert "db_path" not in local_bundle_data

    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)


# source_attestation fields that must be independently bound to the persisted
# Greenhouse JobSource/Job evidence. Each case leaves the attestation internally
# self-consistent and diverges only the persisted side.
_SOURCE_ATTESTATION_BINDINGS = [
    pytest.param(
        "provider",
        {"source_column_overrides": {"provider": "LEVER"}},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.provider is only string-compared to the "
            "literal 'GREENHOUSE'; no persisted GREENHOUSE JobSource row is required.",
        ),
    ),
    pytest.param(
        "source_kind",
        {"source_payload_overrides": {"source_kind": "manual_paste"}},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.source_kind is never compared with the "
            "persisted JobSource source_payload_json.source_kind.",
        ),
    ),
    pytest.param(
        "public_job_id",
        {"source_column_overrides": {"source_job_id": "1234567"}},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.public_job_id is only checked for "
            "substring presence in self-supplied URLs, never against JobSource.source_job_id.",
        ),
    ),
    pytest.param(
        "api_url",
        {
            "source_payload_overrides": {
                "api_url": "https://boards-api.greenhouse.io/v1/boards/other/jobs/1234567?questions=true"
            }
        },
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.api_url is only prefix-checked, never "
            "compared with the persisted JobSource source_payload_json.api_url.",
        ),
    ),
    pytest.param(
        "fetched_at_utc",
        {"source_payload_overrides": {"fetched_at_utc": "2019-01-01T00:00:00Z"}},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.fetched_at_utc is only parsed for ISO "
            "validity, never compared with the persisted fetch timestamp.",
        ),
    ),
    pytest.param(
        "description_sha256",
        {"description_text": "An entirely different job description body."},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.description_sha256 is only shape-checked "
            "as 64 hex chars, never compared with JobModel.description_hash or the "
            "persisted JobSource content_sha256.",
        ),
    ),
    pytest.param(
        "question_list_sha256",
        {"source_payload_overrides": {"question_list_sha256": "2" * 64}},
        marks=pytest.mark.xfail(
            strict=True,
            reason="P0A gap: source_attestation.question_list_sha256 is only recomputed "
            "from the self-supplied questions file, never compared with the persisted "
            "JobSource question_list_sha256 attestation.",
        ),
    ),
    # Already enforced today, indirectly, via the JobModel.apply_url comparison.
    pytest.param(
        "canonical_apply_url",
        {
            "source_column_overrides": {
                "canonical_apply_url": "https://job-boards.greenhouse.io/opensesame/jobs/1234567",
                "source_url": "https://job-boards.greenhouse.io/opensesame/jobs/1234567",
            }
        },
    ),
]


@pytest.mark.parametrize("field, db_divergence", _SOURCE_ATTESTATION_BINDINGS)
def test_source_attestation_must_bind_to_persisted_greenhouse_evidence(
    tmp_path: Path, field: str, db_divergence: dict[str, Any]
) -> None:
    """Every attested Greenhouse field must be independently bound to the DB record."""
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(
        tmp_path, **db_divergence
    )
    # The attestation itself is untouched and self-consistent; only the persisted
    # Greenhouse evidence disagrees, which must fail closed.
    assert local_bundle_data["source_attestation"]["provider"] == "GREENHOUSE"

    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)


def _forge_questions_and_description(
    bundle: dict[str, Any], local_bundle_data: dict[str, Any]
) -> None:
    """Replace the questions file and description SHA with self-consistent fabrications."""
    forged_questions = [
        "Do you require visa sponsorship now or in the future?",
        "Describe your automation platform experience.",
    ]
    Path(local_bundle_data["questions_json_path"]).write_text(
        json.dumps(forged_questions), encoding="utf-8"
    )
    attestation = local_bundle_data["source_attestation"]
    attestation["question_list_sha256"] = compute_questions_sha256(forged_questions)
    attestation["description_sha256"] = hashlib.sha256(
        b"fabricated job description that was never fetched"
    ).hexdigest()
    bundle["questions_count"] = len(forged_questions)
    _rebind_candidate_bundle_sha(bundle, local_bundle_data)


@pytest.mark.xfail(
    strict=True,
    reason="P0A gap: a forged questions file plus a recomputed question_list_sha256 and "
    "a fabricated description_sha256 are internally self-consistent, and the verifier "
    "never cross-checks either against the persisted Greenhouse evidence.",
)
def test_self_consistent_forged_questions_and_description_sha_cannot_pass(
    tmp_path: Path,
) -> None:
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(tmp_path)
    _forge_questions_and_description(bundle, local_bundle_data)
    assert local_bundle_data["database_url"]

    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)


@pytest.mark.xfail(
    strict=True,
    reason="P0A gap: the same self-consistent questions/description forgery passes with "
    "no proof database target at all, combining the missing-DB-target and "
    "unbound-attestation defects.",
)
def test_self_consistent_forgery_without_database_target_cannot_pass(tmp_path: Path) -> None:
    bundle, local_bundle_data, _ = _setup_full_run_with_persisted_source(tmp_path)
    _forge_questions_and_description(bundle, local_bundle_data)
    del local_bundle_data["database_url"]
    assert "db_path" not in local_bundle_data

    result, receipt = _verify(tmp_path, bundle, local_bundle_data)
    _assert_fails_closed(result, receipt)

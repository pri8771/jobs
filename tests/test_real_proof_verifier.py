"""Tests for the redacted V1.4 real-proof evidence verifier and receipt generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

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


def _build_proof_database(
    tmp_path: Path,
    bundle: dict[str, Any],
    local_bundle_data: dict[str, Any],
    questions: list[str],
    db_name: str = "proof_evidence.db",
) -> str:
    """Persist the full real-proof evidence graph into a fresh SQLite database."""
    db_file = tmp_path / db_name
    if db_file.exists():
        db_file.unlink()
    db_url = f"sqlite:///{db_file}"
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_sessionmaker(engine)

    job_uuid = uuid.UUID(local_bundle_data["job_id"])
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])
    variant_uuid = uuid.UUID(local_bundle_data["resume_variant_id"])
    resume_art_uuid = uuid.UUID(local_bundle_data["resume_artifact_id"])
    cl_art_uuid = uuid.UUID(local_bundle_data["cover_letter_artifact_id"])
    description_sha = hashlib.sha256(PROOF_DESCRIPTION_TEXT.encode("utf-8")).hexdigest()

    artifacts_by_type = {item["type"]: item for item in local_bundle_data["local_artifacts"]}

    try:
        with session_factory() as session:
            company = CompanyModel(normalized_name="OpenSesame", domain="opensesame.com")
            session.add(company)
            session.flush()

            job = JobModel(
                id=job_uuid,
                company_id=company.id,
                normalized_title="AI Automation Engineer",
                description_text=PROOF_DESCRIPTION_TEXT,
                description_hash=description_sha,
            )
            session.add(job)

            session.add(
                JobSourceModel(
                    job_id=job_uuid,
                    provider="GREENHOUSE",
                    source_job_id=GREENHOUSE_PUBLIC_JOB_ID,
                    source_url=bundle["job_url"],
                    canonical_apply_url=bundle["job_url"],
                    requisition_id=GREENHOUSE_PUBLIC_JOB_ID,
                    source_payload_json=_greenhouse_source_payload(questions, description_sha),
                )
            )

            session.add(
                ResumeVariantModel(
                    id=variant_uuid,
                    resume_family=bundle["resume_family"],
                    name=bundle["resume_variant"],
                    version=1,
                    target_job_id=job_uuid,
                    content_hash=bundle["resume_artifact_sha256"],
                )
            )

            session.add_all(
                [
                    ArtifactModel(
                        id=resume_art_uuid,
                        type="resume",
                        storage_uri=f"file://{artifacts_by_type['resume_artifact']['path']}",
                        sha256=bundle["resume_artifact_sha256"],
                    ),
                    ArtifactModel(
                        id=cl_art_uuid,
                        type="cover_letter",
                        storage_uri=f"file://{artifacts_by_type['cover_letter_artifact']['path']}",
                        sha256=bundle["cover_letter_artifact_sha256"],
                    ),
                ]
            )

            session.add(
                ApplicationPacketModel(
                    id=packet_uuid,
                    job_id=job_uuid,
                    candidate_profile_version=bundle["candidate_profile_version"],
                    resume_variant_id=variant_uuid,
                    resume_artifact_id=resume_art_uuid,
                    cover_letter_artifact_id=cl_art_uuid,
                    packet_hash=bundle["packet_hash"],
                    generation_metadata_json={"origin": "deterministic"},
                    is_live_ready=bundle["is_live_ready"],
                )
            )
            session.commit()
    finally:
        engine.dispose()

    return db_url


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
    bundle["job_url"] = GREENHOUSE_CANONICAL_URL
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
            "public_job_id": GREENHOUSE_PUBLIC_JOB_ID,
            "api_url": GREENHOUSE_API_URL,
            "fetched_at_utc": GREENHOUSE_FETCHED_AT,
            "description_sha256": hashlib.sha256(
                PROOF_DESCRIPTION_TEXT.encode("utf-8")
            ).hexdigest(),
            "question_list_sha256": questions_sha,
            "canonical_apply_url": GREENHOUSE_CANONICAL_URL,
        },
        "local_artifacts": [
            {"type": "resume_source", "path": str(resume_file), "sha256": resume_sha},
            {"type": "resume_artifact", "path": str(resume_file), "sha256": resume_sha},
            {"type": "cover_letter_artifact", "path": str(cover_file), "sha256": cover_sha},
            {"type": "manifest", "path": str(manifest_file), "sha256": manifest_sha},
        ],
    }
    local_bundle_data["database_url"] = _build_proof_database(
        tmp_path, bundle, local_bundle_data, questions
    )
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
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    assert local_bundle_data["database_url"].startswith("sqlite:///")

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 0
    assert "REAL_PROOF_VALIDATION_PASS" in result.stdout


# ---------------------------------------------------------------------------
# Defect 1: REAL_PROOF_PASS must fail closed without validated persisted DB evidence.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_fails_closed_when_no_database_target_is_configured(
    tmp_path: Path,
) -> None:
    """A complete local bundle with no DB target must not reach REAL_PROOF_PASS."""
    receipt_file = tmp_path / "receipt.json"
    for absent in ({}, {"database_url": ""}, {"db_path": "   "}):
        bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
        local_bundle_data.pop("database_url", None)
        local_bundle_data.update(absent)
        local_bundle_file = tmp_path / "private_bundle.json"
        local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

        result = _run_verifier(
            tmp_path,
            bundle,
            local_bundle_path=local_bundle_file,
            receipt_path=receipt_file,
        )
        assert result.returncode == 1
        assert "must explicitly configure a proof database target" in result.stderr
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
        assert receipt_data["result"] == "REAL_PROOF_FAIL"
        assert receipt_data["local_full_bundle_verified"] is False


def test_real_proof_verifier_rejects_absent_proof_database_file(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    missing_db = tmp_path / "absent_proof_evidence.db"
    local_bundle_data["database_url"] = f"sqlite:///{missing_db}"
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "proof database file not found on disk" in result.stderr


def test_real_proof_verifier_rejects_unopenable_proof_database(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    corrupt_db = tmp_path / "corrupt_proof_evidence.db"
    corrupt_db.write_bytes(b"not a database at all" * 16)
    local_bundle_data["database_url"] = f"sqlite:///{corrupt_db}"
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "is not an openable SQLite database" in result.stderr


def test_real_proof_verifier_rejects_in_memory_database_target(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["database_url"] = "sqlite:///:memory:"
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "in-memory SQLite is not acceptable persisted proof evidence" in result.stderr


def test_real_proof_verifier_rejects_unrelated_proof_database(tmp_path: Path) -> None:
    """A schema-valid but unrelated database holds none of the proof rows."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    unrelated_db = tmp_path / "unrelated.db"
    engine = get_engine(f"sqlite:///{unrelated_db}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    local_bundle_data["database_url"] = f"sqlite:///{unrelated_db}"
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "JobModel not found in DB" in result.stderr


def test_real_proof_verifier_rejects_tampered_persisted_packet_row(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    packet_uuid = uuid.UUID(local_bundle_data["packet_id"])

    def _forge_packet_hash(session: Any) -> None:
        packet = session.get(ApplicationPacketModel, packet_uuid)
        packet.packet_hash = "9" * 64

    _mutate_proof_database(local_bundle_data["database_url"], _forge_packet_hash)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _drop_variant)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "resume_variant_id" in result.stderr


def test_real_proof_verifier_rejects_tampered_persisted_artifact_hash(tmp_path: Path) -> None:
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    resume_art_uuid = uuid.UUID(local_bundle_data["resume_artifact_id"])

    def _forge_artifact_sha(session: Any) -> None:
        artifact = session.get(ArtifactModel, resume_art_uuid)
        artifact.sha256 = "7" * 64

    _mutate_proof_database(local_bundle_data["database_url"], _forge_artifact_sha)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _drop_cover_letter_artifact)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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
                description_hash=hashlib.sha256(
                    PROOF_DESCRIPTION_TEXT.encode("utf-8")
                ).hexdigest(),
            )
        )
        session.flush()
        packet = session.get(ApplicationPacketModel, uuid.UUID(local_bundle_data["packet_id"]))
        packet.job_id = other_job_uuid

    _mutate_proof_database(local_bundle_data["database_url"], _relink_packet)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "DB ApplicationPacketModel job_id" in result.stderr


# ---------------------------------------------------------------------------
# Defect 2: source_attestation must be bound to persisted Greenhouse evidence.
# ---------------------------------------------------------------------------


def test_real_proof_verifier_rejects_forged_self_consistent_source_attestation(
    tmp_path: Path,
) -> None:
    """A locally self-consistent attestation with no persisted Greenhouse row must fail.

    The persisted source keeps the same URLs (so the job still resolves an apply
    URL) but was never captured from the Greenhouse public job board API, which
    is exactly what the forged attestation claims.
    """
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)

    def _demote_greenhouse_source(session: Any) -> None:
        source = session.query(JobSourceModel).one()
        source.provider = "MANUAL"
        source.source_payload_json = {"source_kind": "manual_paste"}

    _mutate_proof_database(local_bundle_data["database_url"], _demote_greenhouse_source)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _drop_greenhouse_source)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _blank_payload)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "source_payload_json is missing or not an object" in result.stderr


def test_real_proof_verifier_rejects_fabricated_description_sha(tmp_path: Path) -> None:
    """A fabricated description SHA cannot be corroborated by the persisted job text."""
    bundle, local_bundle_data = _setup_valid_full_run(tmp_path)
    local_bundle_data["source_attestation"]["description_sha256"] = "e" * 64
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _tamper_description)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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
    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert "persisted Greenhouse question_list_sha256" in result.stderr


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
        local_bundle_file = tmp_path / "private_bundle.json"
        local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")

        result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

        def _forge_payload(
            session: Any, key: str = payload_key, value: Any = forged_value
        ) -> None:
            source = session.query(JobSourceModel).one()
            payload = dict(source.source_payload_json)
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value
            source.source_payload_json = payload

        _mutate_proof_database(local_bundle_data["database_url"], _forge_payload)

        local_bundle_file = tmp_path / "private_bundle.json"
        local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
        result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _repoint_source_job_id)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _forge_question_count)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
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

    _mutate_proof_database(local_bundle_data["database_url"], _forge_canonical_url)

    local_bundle_file = tmp_path / "private_bundle.json"
    local_bundle_file.write_text(json.dumps(local_bundle_data), encoding="utf-8")
    result = _run_verifier(tmp_path, bundle, local_bundle_path=local_bundle_file)
    assert result.returncode == 1
    assert (
        "DB JobModel apply_url" in result.stderr
        or "canonical_apply_url" in result.stderr
    )

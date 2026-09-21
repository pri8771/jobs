"""Tests for the V1.4 real-proof runner input validation and binding checks."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from jobs_automation.db.models import CompanyModel, JobModel, JobSourceModel
from jobs_automation.preparation.packet_builder import compute_questions_sha256
from scripts.run_v14_real_proof import RealProofError, validate_job, validate_profile_path


def test_validate_profile_path_rejects_example_filename(tmp_path: Path) -> None:
    example_path = tmp_path / "candidate_profile.example.yaml"
    example_path.write_text("name: Test", encoding="utf-8")
    with pytest.raises(RealProofError, match="matches repository example file|Example candidate profile is forbidden"):
        validate_profile_path(example_path)


def test_validate_profile_path_rejects_example_content_even_when_renamed(tmp_path: Path) -> None:
    repo_example = Path(__file__).resolve().parent.parent / "config" / "candidate_profile.example.yaml"
    if not repo_example.exists():
        pytest.skip("Repository candidate_profile.example.yaml not found")

    renamed_path = tmp_path / "my_custom_secret_profile.yaml"
    renamed_path.write_bytes(repo_example.read_bytes())

    with pytest.raises(RealProofError, match="matches repository example file"):
        validate_profile_path(renamed_path)


def test_validate_job_requires_greenhouse_source_binding() -> None:
    company = CompanyModel(id=uuid.uuid4(), normalized_name="OpenSesame")
    desc = "A" * 150
    desc_sha = hashlib.sha256(desc.encode("utf-8")).hexdigest()
    job = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        company=company,
        normalized_title="AI Automation Engineer",
        description_text=desc,
        sources=[],
    )

    questions = ["What is your notice period?", "What is your target compensation?"]
    with pytest.raises(RealProofError, match="must contain at least one public source record"):
        validate_job(job, questions=questions)

    # Add source without GREENHOUSE provider
    non_gh_source = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job.id,
        provider="MANUAL",
        source_url="https://boards.greenhouse.io/opensesame/jobs/7967740",
    )
    job.sources = [non_gh_source]
    with pytest.raises(RealProofError, match="does not have an imported GREENHOUSE source record"):
        validate_job(job, questions=questions)

    # Add GREENHOUSE source with invalid source_kind
    gh_source = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job.id,
        provider="GREENHOUSE",
        source_job_id="7967740",
        source_url="https://boards.greenhouse.io/opensesame/jobs/7967740",
        source_payload_json={
            "source_kind": "invalid",
            "api_url": "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740",
            "content_sha256": desc_sha,
            "question_list_sha256": compute_questions_sha256(questions),
        },
    )
    job.sources = [gh_source]
    with pytest.raises(RealProofError, match="invalid or missing source_kind"):
        validate_job(job, questions=questions)

    # Invalid api_url
    gh_source.source_payload_json["source_kind"] = "greenhouse_public_job_board_api"
    gh_source.source_payload_json["api_url"] = "https://example.com/api"
    with pytest.raises(RealProofError, match="invalid api_url"):
        validate_job(job, questions=questions)

    # Mismatched description hash
    gh_source.source_payload_json["api_url"] = "https://boards-api.greenhouse.io/v1/boards/opensesame/jobs/7967740"
    gh_source.source_payload_json["content_sha256"] = "0" * 64
    with pytest.raises(RealProofError, match="Greenhouse description hash mismatch"):
        validate_job(job, questions=questions)

    # Mismatched question list hash
    gh_source.source_payload_json["content_sha256"] = desc_sha
    gh_source.source_payload_json["question_list_sha256"] = "0" * 64
    with pytest.raises(RealProofError, match="Question list SHA-256 mismatch"):
        validate_job(job, questions=questions)

    # Valid complete attestation
    gh_source.source_payload_json["question_list_sha256"] = compute_questions_sha256(questions)
    validate_job(job, questions=questions)

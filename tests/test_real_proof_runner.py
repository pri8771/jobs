"""Tests for the V1.4 real-proof runner input validation and binding checks."""

from __future__ import annotations

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
    company = CompanyModel(id=uuid.uuid4(), normalized_name="Acme Inc")
    job = JobModel(
        id=uuid.uuid4(),
        company_id=company.id,
        company=company,
        normalized_title="AI Engineer",
        description_text="A" * 150,
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
        source_url="https://boards.greenhouse.io/acme/jobs/12345",
    )
    job.sources = [non_gh_source]
    with pytest.raises(RealProofError, match="does not have an imported GREENHOUSE source record"):
        validate_job(job, questions=questions)

    # Add GREENHOUSE source with mismatched questions hash
    gh_source = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job.id,
        provider="GREENHOUSE",
        source_url="https://boards.greenhouse.io/acme/jobs/12345",
        source_payload_json={"question_list_sha256": "0" * 64},
    )
    job.sources = [gh_source]
    with pytest.raises(RealProofError, match="Question list SHA-256 mismatch"):
        validate_job(job, questions=questions)

    # Match questions hash
    correct_sha = compute_questions_sha256(questions)
    gh_source.source_payload_json = {"question_list_sha256": correct_sha}
    # Should pass without error
    validate_job(job, questions=questions)

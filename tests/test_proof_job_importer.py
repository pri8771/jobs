"""Tests for the live Greenhouse V1.4 proof-job importer helpers."""

from __future__ import annotations

from typing import Any

import pytest

from scripts.import_v14_proof_job import (
    DEFAULT_EXPECTED_TITLE,
    ProofJobImportError,
    _extract_screening_questions,
    _html_to_text,
    _validated_job_fields,
)


def test_html_to_text_strips_markup() -> None:
    assert _html_to_text("<p>Hello <strong>world</strong></p>") == "Hello\nworld"


def test_extract_screening_questions_filters_standard_fields() -> None:
    payload = {
        "questions": [
            {"label": "First Name*"},
            {"label": "Email*"},
            {"label": "Are you legally authorized to work in the United States?*"},
            {"label": "Describe a reusable automation system you built.*"},
        ]
    }
    questions = _extract_screening_questions(payload)
    assert questions == [
        "Are you legally authorized to work in the United States?",
        "Describe a reusable automation system you built.",
    ]


def test_extract_screening_questions_deduplicates_labels() -> None:
    payload = {
        "questions": [
            {"label": "Question A*"},
            {"label": "question a"},
            {"label": "Question B*"},
        ]
    }
    assert _extract_screening_questions(payload) == ["Question A", "Question B"]


def test_extract_screening_questions_requires_real_question_data() -> None:
    payload = {"questions": [{"label": "First Name*"}, {"label": "Email*"}]}
    try:
        _extract_screening_questions(payload)
    except ProofJobImportError:
        pass
    else:
        raise AssertionError("Expected ProofJobImportError")


def _payload(
    job_id: int = 8110413, title: str = "Forward Deployed Engineer - Supply Chain Solutions"
) -> dict[str, Any]:
    return {
        "id": job_id,
        "title": title,
        "location": {"name": "San Francisco, California, United States"},
        "content": "<p>" + ("Real public posting content. " * 30) + "</p>",
    }


def test_validated_job_fields_accepts_operator_selected_title_case_insensitively() -> None:
    title, location, content = _validated_job_fields(
        _payload(),
        job_id="8110413",
        expected_title="forward deployed engineer - supply chain solutions",
    )
    assert title == "Forward Deployed Engineer - Supply Chain Solutions"
    assert location == "San Francisco, California, United States"
    assert len(content) >= 500


def test_validated_job_fields_rejects_a_different_title() -> None:
    with pytest.raises(ProofJobImportError, match="Unexpected proof-job title"):
        _validated_job_fields(_payload(), job_id="8110413", expected_title=DEFAULT_EXPECTED_TITLE)


def test_validated_job_fields_rejects_id_mismatch_and_blank_expectation() -> None:
    with pytest.raises(ProofJobImportError, match="expected '8110414'"):
        _validated_job_fields(_payload(), job_id="8110414", expected_title=_payload()["title"])
    with pytest.raises(ProofJobImportError, match="expected proof-job title is required"):
        _validated_job_fields(_payload(), job_id="8110413", expected_title="   ")


def test_validated_job_fields_rejects_short_content() -> None:
    payload = _payload()
    payload["content"] = "<p>too short</p>"
    with pytest.raises(ProofJobImportError, match="unexpectedly short"):
        _validated_job_fields(payload, job_id="8110413", expected_title=payload["title"])


def test_default_expectation_preserves_the_original_proof_job() -> None:
    title, _, _ = _validated_job_fields(
        _payload(7967740, "AI Automation Engineer"),
        job_id="7967740",
        expected_title=DEFAULT_EXPECTED_TITLE,
    )
    assert title == "AI Automation Engineer"

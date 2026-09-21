"""Tests for the live Greenhouse V1.4 proof-job importer helpers."""

from __future__ import annotations

from scripts.import_v14_proof_job import (
    ProofJobImportError,
    _extract_screening_questions,
    _html_to_text,
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

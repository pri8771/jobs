"""Tests for the production-safe deterministic model gateway."""

from __future__ import annotations

import pytest

from jobs_automation.adapters.models import DeterministicModelGateway


def test_deterministic_gateway_cover_letter_requests_canonical_renderer() -> None:
    gateway = DeterministicModelGateway()
    result = gateway.complete(task="cover_letter", prompt="real prompt content")
    assert result["content"] == ""
    assert result["origin"] == "deterministic"
    assert result["model"] == "deterministic-canonical-renderer"


def test_deterministic_gateway_questions_fail_safe_unresolved() -> None:
    gateway = DeterministicModelGateway()
    result = gateway.complete(
        task="question_answering",
        prompt="Describe an unsupported candidate fact.",
    )
    assert result["resolved"] is False
    assert result["answer"] is None
    assert result["origin"] == "deterministic"


def test_deterministic_gateway_does_not_synthesize_unsupported_semantic_tasks() -> None:
    gateway = DeterministicModelGateway()
    with pytest.raises(ValueError, match="requires a configured semantic model provider"):
        gateway.complete(task="resume_tailoring", prompt="Invent nothing")

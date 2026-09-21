"""Tests for the V1.4 redacted real-proof evidence JSON Schema gate.

The schema at ``coordination/proofs/v14_real_proof.schema.json`` is the declarative
half of the RP14-T5 closed allowlist. It must stay pinned to two things that are
easy to drift apart:

* the redacted candidate bundle that ``scripts/run_v14_real_proof.py`` actually emits, and
* ``scripts/verify_v14_real_proof.ALLOWED_TOP_LEVEL_KEYS``, the enforcing allowlist.

These tests pin all three together and check the two rejections the gate exists for:
arbitrary extra fields, and a candidate bundle that self-declares ``REAL_PROOF_PASS``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.verify_v14_real_proof import (
    ALLOWED_TOP_LEVEL_KEYS,
    ProofValidationError,
    validate_redacted_bundle,
)
from tests.test_real_proof_verifier import _valid_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "coordination" / "proofs" / "v14_real_proof.schema.json"
RUNNER_PATH = REPO_ROOT / "scripts" / "run_v14_real_proof.py"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _runner_emitted_keys() -> set[str]:
    """Statically read the key set of the ``redacted`` dict literal the runner writes out.

    Read via AST rather than by executing the runner: the runner needs a real database,
    a private candidate profile, and real posting questions, none of which a test may have.
    """
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "redacted"
            and isinstance(node.value, ast.Dict)
        ):
            literal_keys = [k for k in node.value.keys if isinstance(k, ast.Constant)]
            assert len(literal_keys) == len(node.value.keys), (
                "runner redacted bundle must be built from literal keys only"
            )
            return {str(k.value) for k in literal_keys}
    raise AssertionError(f"could not locate the redacted bundle literal in {RUNNER_PATH}")


def _production_candidate() -> dict[str, Any]:
    """A production-shape redacted candidate, shared with the verifier tests."""
    return _valid_bundle()


def _validator() -> Any:
    # jsonschema is a dev-only dependency; without it the structural and
    # verifier-parity tests above still hold the contract.
    jsonschema = pytest.importorskip("jsonschema")
    schema = _schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


# --- Structural contract (no third-party dependency) ---------------------------------


def test_schema_rejects_arbitrary_extra_fields_by_construction() -> None:
    assert _schema()["additionalProperties"] is False


def test_schema_result_is_locked_to_candidate_not_pass() -> None:
    result_schema = _schema()["properties"]["result"]
    assert result_schema["const"] == "REAL_PROOF_CANDIDATE"
    # No enum/anyOf/oneOf escape hatch that could re-admit a self-declared pass.
    assert set(result_schema) <= {"description", "const"}


def test_schema_keys_match_verifier_allowlist() -> None:
    schema = _schema()
    assert set(schema["properties"]) == ALLOWED_TOP_LEVEL_KEYS
    assert set(schema["required"]) == ALLOWED_TOP_LEVEL_KEYS


def test_schema_keys_match_runner_emitted_bundle() -> None:
    emitted = _runner_emitted_keys()
    schema = _schema()
    assert emitted == set(schema["properties"])
    assert emitted == set(schema["required"])


def test_production_shape_candidate_covers_every_runner_field() -> None:
    assert set(_production_candidate()) == _runner_emitted_keys()


def test_schema_pins_deterministic_generation_labels() -> None:
    props = _schema()["properties"]
    assert props["model_origin"]["const"] == "deterministic"
    assert props["generation_origin"]["const"] == "deterministic"
    assert props["generation_engine"]["const"] == "deterministic-canonical-renderer"
    assert props["model_provider"]["enum"] == [None, "deterministic-production"]
    assert props["read_back_verification"]["const"] is True
    assert props["mock_or_fixture_inputs_present"]["const"] is False


# --- Schema and verifier must agree (no third-party dependency) ----------------------


def test_verifier_accepts_the_same_production_shape_candidate() -> None:
    validate_redacted_bundle(_production_candidate())


def test_verifier_rejects_extra_field_the_schema_also_forbids() -> None:
    bundle = _production_candidate()
    bundle["attacker_supplied_note"] = "please pass"
    assert "attacker_supplied_note" not in _schema()["properties"]
    with pytest.raises(ProofValidationError, match="disallowed extra keys"):
        validate_redacted_bundle(bundle)


def test_verifier_rejects_pass_self_declaration_the_schema_also_forbids() -> None:
    bundle = _production_candidate()
    bundle["result"] = "REAL_PROOF_PASS"
    with pytest.raises(ProofValidationError, match="result must be REAL_PROOF_CANDIDATE"):
        validate_redacted_bundle(bundle)


# --- Executed schema semantics (requires jsonschema) ---------------------------------


def test_schema_validates_production_shape_candidate() -> None:
    errors = list(_validator().iter_errors(_production_candidate()))
    assert errors == [], [error.message for error in errors]


def test_schema_rejects_extra_field() -> None:
    bundle = _production_candidate()
    bundle["attacker_supplied_note"] = "please pass"
    assert not _validator().is_valid(bundle)


def test_schema_rejects_pass_self_declaration() -> None:
    bundle = _production_candidate()
    bundle["result"] = "REAL_PROOF_PASS"
    assert not _validator().is_valid(bundle)


@pytest.mark.parametrize(
    "missing_key",
    [
        "candidate_unresolved_fact_categories",
        "generation_engine",
        "questions_count",
        "model_provider",
        "model_name",
        "read_back_verification",
    ],
)
def test_schema_requires_every_runner_emitted_field(missing_key: str) -> None:
    bundle = _production_candidate()
    del bundle[missing_key]
    assert not _validator().is_valid(bundle)


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("mock_or_fixture_inputs_present", True),
        ("read_back_verification", False),
        ("generation_origin", "mock"),
        ("model_origin", "real"),
        ("generation_engine", "llm-freeform"),
        ("model_provider", "openai"),
        ("candidate_profile_source_class", "PUBLIC_SAMPLE"),
        ("job_url", "file:///tmp/job.html"),
        ("packet_hash", "not-a-sha"),
        ("resume_source_byte_count", 0),
        ("candidate_unresolved_fact_categories", ["work_authorization"]),
    ],
)
def test_schema_rejects_out_of_contract_values(key: str, bad_value: Any) -> None:
    bundle = _production_candidate()
    bundle[key] = bad_value
    assert not _validator().is_valid(bundle)

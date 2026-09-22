#!/usr/bin/env python3
"""Validate a redacted V1.4 real-proof evidence bundle and generate a verification receipt.

This verifies evidence structure (executed JSON Schema plus semantic allowlists), the
anti-mock/anti-fixture invariants, and, when the private full bundle is provided, the
complete cross-binding of local artifacts, the parsed canonical candidate profile, the
selected resume mapping, and the persisted database rows the proof claims to describe.

Trust boundaries:

* The redacted bundle and the private bundle are untrusted inputs. Nothing in them
  chooses which database the verifier connects to: the private bundle carries only a
  database *identity* and the verifier connects to the trusted runtime database
  (``DATABASE_URL`` via ``AppSettings``) after proving that identity matches.
* Rejection reasons written into the committed receipt are sanitized: URL credentials
  and absolute filesystem paths are never copied into evidence.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import jsonschema
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.config import AppSettings, ConfigLoader
from jobs_automation.db.models import (
    ApplicationPacketModel,
    ArtifactModel,
    JobModel,
    ResumeVariantModel,
)
from jobs_automation.db.session import get_engine, get_sessionmaker
from jobs_automation.preparation.packet_builder import compute_canonical_packet_hash
from jobs_automation.preparation.tailoring import ResumeVariantSelector
from jobs_automation.proof.database_identity import (
    ProofDatabaseIdentityError,
    database_identity,
    resolve_runtime_database,
)
from jobs_automation.proof.profile_fingerprint import candidate_profile_fingerprint

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_SCHEMA_PATH = REPO_ROOT / "coordination" / "proofs" / "v14_real_proof.schema.json"

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
UUID_TEXT = re.compile(r"^[0-9a-fA-F-]{36}$")
FORBIDDEN_TOKENS = (
    "mock",
    "fixture",
    "synthetic",
    "example.yaml",
    "candidate_profile.example",
    "tmp_path",
    "test_resume",
    "hallucinatingmodelgateway",
    "mockmodelgateway",
    "adversarial_mock",
)
PRIVATE_KEYS = {
    "candidate_email",
    "candidate_phone",
    "candidate_address",
    "resume_text",
    "cover_letter_text",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
}

# RP14-T5: Strict allowlist of top-level keys
ALLOWED_TOP_LEVEL_KEYS = {
    "result",
    "proof_run_id",
    "run_timestamp_utc",
    "code_commit_sha",
    "job_url",
    "job_title",
    "company",
    "job_snapshot_sha256",
    "candidate_profile_source_class",
    "candidate_profile_version",
    "candidate_unresolved_fact_categories",
    "resume_family",
    "resume_variant",
    "resume_version",
    "resume_source_sha256",
    "resume_source_byte_count",
    "model_provider",
    "model_name",
    "model_origin",
    "generation_origin",
    "generation_engine",
    "packet_id",
    "packet_hash",
    "resume_artifact_sha256",
    "cover_letter_artifact_sha256",
    "manifest_sha256",
    "is_live_ready",
    "resolved_answers_count",
    "unresolved_questions",
    "questions_count",
    "read_back_verification",
    "mock_or_fixture_inputs_present",
}


class ProofValidationError(Exception):
    """Raised when a real-proof evidence invariant fails."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    sha = result.stdout.strip()
    return sha if len(sha) >= 7 else "unknown"


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ProofValidationError(f"missing required field: {key}")
    return data[key]


def _require_sha(data: dict[str, Any], key: str) -> str:
    value = str(_require(data, key))
    if not HEX64.fullmatch(value):
        raise ProofValidationError(f"{key} must be a 64-character SHA-256 hex digest")
    return value.lower()


def _require_uuid_text(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value or not UUID_TEXT.fullmatch(value):
        raise ProofValidationError(f"local bundle missing mandatory valid UUID {key}")
    return value


def _walk_forbidden_private_keys(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            current = f"{path}.{key}" if path else str(key)
            if key_lower in PRIVATE_KEYS:
                raise ProofValidationError(f"private field must not be committed: {current}")
            _walk_forbidden_private_keys(child, current)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _walk_forbidden_private_keys(child, f"{path}[{i}]")


def _assert_allowlisted_keys(data: dict[str, Any]) -> None:
    extra = set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if extra:
        raise ProofValidationError(
            f"disallowed extra keys in redacted evidence bundle: {sorted(extra)}"
        )


def _assert_no_fixture_markers(data: dict[str, Any]) -> None:
    """Reject mock/fixture markers in evidence values, not schema/key names."""

    def scan(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                current = f"{path}.{key}" if path else str(key)
                scan(child, current)
            return
        if isinstance(value, list):
            for i, child in enumerate(value):
                scan(child, f"{path}[{i}]")
            return
        if isinstance(value, str):
            lowered = value.lower()
            for token in FORBIDDEN_TOKENS:
                if token in lowered:
                    raise ProofValidationError(
                        f"forbidden mock/fixture marker present in {path}: {token}"
                    )

    scan(data)


def validate_redacted_bundle(data: dict[str, Any]) -> None:
    _assert_allowlisted_keys(data)
    _walk_forbidden_private_keys(data)

    result = str(_require(data, "result"))
    if result != "REAL_PROOF_CANDIDATE":
        raise ProofValidationError(f"result must be REAL_PROOF_CANDIDATE, got {result!r}")

    if _require(data, "mock_or_fixture_inputs_present") is not False:
        raise ProofValidationError("mock_or_fixture_inputs_present must be false")

    source_class = str(_require(data, "candidate_profile_source_class")).upper()
    if source_class not in {"PRIVATE_LOCAL", "PRIVATE_CONNECTED_SOURCE"}:
        raise ProofValidationError(
            "candidate_profile_source_class must identify a real private source"
        )

    job_url = str(_require(data, "job_url"))
    if not job_url.startswith(("https://", "http://")):
        raise ProofValidationError("job_url must be an HTTP(S) public source")
    if "example." in job_url.lower() or "localhost" in job_url.lower():
        raise ProofValidationError("job_url appears non-real/test-local")

    # RP14-T6: Deterministic generation labeling enforced by verifier
    generation_origin = str(_require(data, "generation_origin")).lower()
    if generation_origin != "deterministic":
        raise ProofValidationError(
            f"generation_origin must be 'deterministic' for V1.4 proof, got {generation_origin!r}"
        )

    model_origin = str(_require(data, "model_origin")).lower()
    if model_origin != "deterministic":
        raise ProofValidationError(
            f"model_origin must be 'deterministic' for V1.4 proof, got {model_origin!r}"
        )

    generation_engine = str(_require(data, "generation_engine")).lower()
    if generation_engine != "deterministic-canonical-renderer":
        raise ProofValidationError(
            f"generation_engine must be 'deterministic-canonical-renderer', got {generation_engine!r}"
        )

    model_provider = data.get("model_provider")
    if model_provider is not None and model_provider != "deterministic-production":
        raise ProofValidationError(
            f"model_provider must be null or 'deterministic-production', got {model_provider!r}"
        )

    for key in (
        "job_snapshot_sha256",
        "resume_source_sha256",
        "packet_hash",
        "resume_artifact_sha256",
        "cover_letter_artifact_sha256",
        "manifest_sha256",
    ):
        _require_sha(data, key)

    resume_bytes = int(_require(data, "resume_source_byte_count"))
    if resume_bytes <= 0:
        raise ProofValidationError("resume_source_byte_count must be > 0")

    read_back = _require(data, "read_back_verification")
    if read_back is not True:
        raise ProofValidationError("read_back_verification must be true")

    variant = str(_require(data, "resume_variant"))
    family = str(_require(data, "resume_family"))
    if not variant or not family:
        raise ProofValidationError("resume_variant and resume_family must be non-empty")

    code_sha = str(_require(data, "code_commit_sha"))
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", code_sha):
        raise ProofValidationError("code_commit_sha must be a Git SHA")

    _assert_no_fixture_markers(data)


# ---------------------------------------------------------------------------
# F145-01: executed evidence schema validation (Draft 2020-12 with format checks)
# ---------------------------------------------------------------------------


def load_evidence_schema(schema_path: Path = EVIDENCE_SCHEMA_PATH) -> dict[str, Any]:
    if not schema_path.is_file():
        raise ProofValidationError(
            "evidence schema file is missing; the redacted bundle cannot be validated"
        )
    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofValidationError(
            f"evidence schema could not be read ({type(exc).__name__})"
        ) from None
    if not isinstance(data, dict):
        raise ProofValidationError("evidence schema must be a JSON object")
    return data


def _collect_schema_formats(node: Any) -> set[str]:
    formats: set[str] = set()
    if isinstance(node, dict):
        declared = node.get("format")
        if isinstance(declared, str):
            formats.add(declared)
        for child in node.values():
            formats |= _collect_schema_formats(child)
    elif isinstance(node, list):
        for child in node:
            formats |= _collect_schema_formats(child)
    return formats


def _describe_schema_error(error: Any) -> str:
    """Describe a schema violation by location and constraint, never by instance value.

    The location is a JSON pointer in ``#/a/b`` fragment form; the ``#`` prefix keeps it
    distinct from a filesystem path for the reason sanitizer.
    """
    pointer = "#/" + "/".join(str(part) for part in error.absolute_path)
    keyword = str(error.validator)
    instance = error.instance if isinstance(error.instance, dict) else {}
    if keyword == "required":
        required = error.validator_value if isinstance(error.validator_value, list) else []
        missing = sorted(str(key) for key in required if key not in instance)
        return f"schema violation at {pointer}: missing required field(s) {missing}"
    if keyword == "additionalProperties":
        properties = error.schema.get("properties", {}) if isinstance(error.schema, dict) else {}
        extra = sorted(str(key) for key in instance if key not in properties)
        return f"schema violation at {pointer}: disallowed extra field(s) {extra}"
    if keyword in {
        "type",
        "format",
        "const",
        "enum",
        "pattern",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
    }:
        expected = json.dumps(error.validator_value, sort_keys=True, default=str)
        return f"schema violation at {pointer}: {keyword} constraint failed (expected {expected})"
    return f"schema violation at {pointer}: {keyword} constraint failed"


def validate_redacted_bundle_schema(
    data: dict[str, Any], schema_path: Path = EVIDENCE_SCHEMA_PATH
) -> str:
    """Validate the redacted bundle against the closed evidence schema.

    Format assertions (``date-time``, ``uri``) must actually execute: if the installed
    format checker cannot check a format the schema declares, validation fails closed
    instead of silently skipping the assertion. Returns the SHA-256 of the schema file
    so the receipt is bound to the exact schema that was enforced.
    """
    schema = load_evidence_schema(schema_path)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        raise ProofValidationError(
            f"evidence schema is itself invalid ({type(exc).__name__})"
        ) from None

    format_checker = jsonschema.FormatChecker()
    unavailable = sorted(_collect_schema_formats(schema) - set(format_checker.checkers))
    if unavailable:
        raise ProofValidationError(
            f"evidence schema format checker unavailable for {unavailable}; install the "
            "verifier runtime dependencies (rfc3339-validator, rfc3986-validator)"
        )

    validator = jsonschema.Draft202012Validator(schema, format_checker=format_checker)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: ([str(part) for part in error.absolute_path], str(error.validator)),
    )
    if errors:
        raise ProofValidationError(_describe_schema_error(errors[0]))
    return sha256_file(schema_path)


# ---------------------------------------------------------------------------
# F145-05: sanitized rejection reasons and receipt naming
# ---------------------------------------------------------------------------

_URL_CREDENTIALS = re.compile(r"(?P<scheme>[A-Za-z][A-Za-z0-9+.\-]*://)[^/@\s]+@")
# Local-file URLs carry an absolute path right after the scheme (sqlite:////home/x.db).
_LOCAL_FILE_URL_PATH = re.compile(
    r"(?P<scheme>(?:sqlite|file)(?:\+[A-Za-z0-9_]+)?://)(?P<path>/[^\s'\"`,()\[\]{}<>]+)"
)
# Two or more slash-delimited segments not preceded by a word/URL character, another
# slash (HTTP URL paths), or the "#" that marks a JSON pointer.
_ABSOLUTE_PATH = re.compile(r"(?<![\w\-.:#/])(?:/[^\s/'\"`:;,()\[\]{}<>]+){2,}")
_SAFE_RECEIPT_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]{0,63}$")
MAX_REASON_LENGTH = 400


def sanitize_reason(text: str) -> str:
    """Strip credentials and absolute private paths from a reason before it is recorded."""
    text = _URL_CREDENTIALS.sub(lambda match: f"{match.group('scheme')}***@", text)
    text = _LOCAL_FILE_URL_PATH.sub(
        lambda match: f"{match.group('scheme')}<path:{Path(match.group('path')).name}>", text
    )
    text = _ABSOLUTE_PATH.sub(lambda match: f"<path:{Path(match.group(0)).name}>", text)
    text = " ".join(text.split())
    if len(text) > MAX_REASON_LENGTH:
        text = text[: MAX_REASON_LENGTH - 3] + "..."
    return text


def receipt_filename(proof_run_id: str, candidate_bundle_sha: str) -> str:
    """Never build a receipt path from an untrusted proof_run_id."""
    if _SAFE_RECEIPT_COMPONENT.fullmatch(proof_run_id) and ".." not in proof_run_id:
        return f"v14_real_proof_receipt_{proof_run_id}.json"
    return f"v14_real_proof_receipt_unbound_{candidate_bundle_sha[:16]}.json"


def compute_questions_sha256(questions: list[str]) -> str:
    """Compute canonical SHA-256 hash of application questions list."""
    serialized = json.dumps(questions, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def parse_utc(value: str | None) -> datetime.datetime | None:
    if not value or value.strip().lower() == "null":
        return None
    try:
        return datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(
            datetime.UTC
        )
    except ValueError:
        return None


def verify_local_artifact(path: Path, expected_sha: str) -> None:
    if not path.exists() or not path.is_file():
        raise ProofValidationError(f"local artifact missing: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected_sha.lower():
        raise ProofValidationError(
            f"local artifact hash mismatch for {path.name}: {actual} != {expected_sha}"
        )


def load_canonical_profile(path: Path) -> CandidateProfileConfig:
    """Parse the private profile with the production loader; never echo its contents."""
    try:
        profile, _ = ConfigLoader(REPO_ROOT / "config").load_candidate_profile(path)
    except Exception as exc:  # YAML, pydantic and OS errors carry private content
        raise ProofValidationError(
            "candidate profile on disk does not parse as a canonical candidate profile "
            f"({type(exc).__name__})"
        ) from None
    return profile


def _resolved(path_value: Any) -> Path:
    return Path(str(path_value)).expanduser().resolve()


def validate_local_bundle(
    local_data: dict[str, Any],
    redacted_data: dict[str, Any],
    candidate_bundle_sha: str | None = None,
) -> None:
    """RP14-T2/T3/T4/T7 and F145-02..04: cross-bind every claim to independent evidence."""
    local_proof_id = local_data.get("proof_run_id")
    redacted_proof_id = redacted_data.get("proof_run_id")
    if not local_proof_id or local_proof_id != redacted_proof_id:
        raise ProofValidationError(
            f"proof_run_id mismatch between local bundle ({local_proof_id}) "
            f"and redacted evidence ({redacted_proof_id})"
        )

    # RP14-T2: Mandatory candidate-bundle SHA binding
    if "candidate_bundle_sha256" not in local_data:
        raise ProofValidationError("local bundle missing mandatory candidate_bundle_sha256")
    if (
        candidate_bundle_sha
        and str(local_data["candidate_bundle_sha256"]).lower() != candidate_bundle_sha.lower()
    ):
        raise ProofValidationError(
            f"candidate_bundle_sha256 in local bundle does not match computed candidate SHA: "
            f"{local_data['candidate_bundle_sha256']} != {candidate_bundle_sha}"
        )

    # RP14-T4: Candidate profile path on disk, SHA check & example file rejection
    _require_sha(local_data, "candidate_profile_sha256")
    cand_profile_path_raw = local_data.get("candidate_profile_path")
    if not cand_profile_path_raw:
        raise ProofValidationError("local bundle missing mandatory candidate_profile_path")
    cand_profile_path = Path(str(cand_profile_path_raw)).expanduser()
    if not cand_profile_path.exists() or not cand_profile_path.is_file():
        raise ProofValidationError(
            f"candidate_profile_path file not found on disk: {cand_profile_path}"
        )

    actual_profile_sha = sha256_file(cand_profile_path).lower()
    expected_profile_sha = str(local_data["candidate_profile_sha256"]).lower()
    if actual_profile_sha != expected_profile_sha:
        raise ProofValidationError(
            f"candidate profile file on disk hash mismatch: {actual_profile_sha} != {expected_profile_sha}"
        )

    cand_lower = str(cand_profile_path.name).lower()
    if (
        "example" in cand_lower
        or cand_lower.endswith(".example.yaml")
        or cand_lower == "candidate_profile.example.yaml"
    ):
        raise ProofValidationError(
            f"candidate profile file name indicates test/example fixture: {cand_profile_path.name}"
        )

    example_files = list(REPO_ROOT.glob("config/*example*")) + list(
        REPO_ROOT.glob("tests/fixtures/*example*")
    )
    for eg in example_files:
        if eg.is_file() and sha256_file(eg).lower() == actual_profile_sha:
            raise ProofValidationError(
                f"candidate_profile_sha256 matches repository example file ({eg.name}); "
                "real private profile is required for REAL_PROOF"
            )

    if local_data.get("candidate_profile_source_class") != "PRIVATE_LOCAL":
        raise ProofValidationError(
            f"candidate_profile_source_class in local bundle must be 'PRIVATE_LOCAL', got {local_data.get('candidate_profile_source_class')!r}"
        )
    if redacted_data.get("candidate_profile_source_class") != "PRIVATE_LOCAL":
        raise ProofValidationError(
            f"candidate_profile_source_class in redacted bundle must be 'PRIVATE_LOCAL', got {redacted_data.get('candidate_profile_source_class')!r}"
        )

    # F145-04: the profile must parse as a canonical profile and bind by normalized
    # fingerprint and version, not merely by the existence of a file plus a digest.
    profile = load_canonical_profile(cand_profile_path)
    profile_fingerprint = candidate_profile_fingerprint(profile)
    attested_fingerprint = _require_sha(local_data, "candidate_profile_fingerprint_sha256")
    if attested_fingerprint != profile_fingerprint:
        raise ProofValidationError(
            "candidate_profile_fingerprint_sha256 in local bundle does not match the "
            "fingerprint of the parsed canonical profile on disk"
        )
    if str(local_data.get("candidate_profile_version")) != str(profile.version):
        raise ProofValidationError(
            f"local bundle candidate_profile_version ({local_data.get('candidate_profile_version')!r}) "
            f"does not match the parsed candidate profile version ({profile.version})"
        )
    if str(redacted_data.get("candidate_profile_version")) != str(profile.version):
        raise ProofValidationError(
            f"redacted candidate_profile_version ({redacted_data.get('candidate_profile_version')!r}) "
            f"does not match the parsed candidate profile version ({profile.version})"
        )
    expected_unresolved_categories = {
        key: len(values) for key, values in profile.check_unresolved_facts().items() if values
    }
    if redacted_data.get("candidate_unresolved_fact_categories") != expected_unresolved_categories:
        raise ProofValidationError(
            "redacted candidate_unresolved_fact_categories do not match the unresolved-fact "
            "categories derived from the parsed candidate profile"
        )

    # RP14-T3: Source attestation validation
    source_attestation = local_data.get("source_attestation")
    if not isinstance(source_attestation, dict):
        raise ProofValidationError("local bundle missing mandatory source_attestation object")
    if str(source_attestation.get("provider")) != "GREENHOUSE":
        raise ProofValidationError("source_attestation provider must be GREENHOUSE")
    if str(source_attestation.get("source_kind")) != "greenhouse_public_job_board_api":
        raise ProofValidationError(
            "source_attestation source_kind must be greenhouse_public_job_board_api"
        )
    public_job_id = str(source_attestation.get("public_job_id", "")).strip()
    if not public_job_id:
        raise ProofValidationError("source_attestation missing public_job_id")

    fetched_at_raw = source_attestation.get("fetched_at_utc")
    if not fetched_at_raw or parse_utc(str(fetched_at_raw)) is None:
        raise ProofValidationError(
            "source_attestation has missing or invalid fetched_at_utc ISO timestamp"
        )

    api_url = str(source_attestation.get("api_url", "")).strip()
    if not api_url.startswith("https://boards-api.greenhouse.io/"):
        raise ProofValidationError(f"source_attestation has invalid api_url: {api_url}")
    if public_job_id not in api_url:
        raise ProofValidationError(
            f"source_attestation public_job_id {public_job_id} not found in api_url: {api_url}"
        )

    canonical_url = str(source_attestation.get("canonical_apply_url", "")).strip()
    if not canonical_url.startswith(("https://", "http://")):
        raise ProofValidationError(
            f"source_attestation has invalid canonical_apply_url: {canonical_url}"
        )
    if public_job_id not in canonical_url:
        raise ProofValidationError(
            f"source_attestation public_job_id {public_job_id} not found in canonical_apply_url: {canonical_url}"
        )

    redacted_job_url = str(redacted_data.get("job_url", "")).strip()
    if redacted_job_url != canonical_url:
        raise ProofValidationError(
            f"redacted job_url ({redacted_job_url}) does not match source_attestation canonical_apply_url ({canonical_url})"
        )

    _require_sha(source_attestation, "description_sha256")
    _require_sha(source_attestation, "question_list_sha256")

    # Independent question list verification from questions_json_path file on disk
    questions_path_raw = local_data.get("questions_json_path")
    if not questions_path_raw:
        raise ProofValidationError("local bundle missing mandatory questions_json_path")
    questions_path = Path(str(questions_path_raw)).expanduser()
    if not questions_path.exists() or not questions_path.is_file():
        raise ProofValidationError(f"questions_json_path file not found on disk: {questions_path}")
    try:
        questions_data = json.loads(questions_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofValidationError(
            f"could not parse questions JSON from {questions_path}: {type(exc).__name__}"
        ) from None
    if not isinstance(questions_data, list) or not all(isinstance(q, str) for q in questions_data):
        raise ProofValidationError(f"questions JSON in {questions_path} must be a list of strings")

    recomputed_questions_sha = compute_questions_sha256(questions_data)
    if recomputed_questions_sha.lower() != str(source_attestation["question_list_sha256"]).lower():
        raise ProofValidationError(
            f"questions JSON on disk hash mismatch against source attestation: "
            f"{recomputed_questions_sha} != {source_attestation['question_list_sha256']}"
        )
    if len(questions_data) != int(redacted_data.get("questions_count", 0)):
        raise ProofValidationError(
            f"questions count in questions JSON ({len(questions_data)}) "
            f"does not match redacted evidence questions_count ({redacted_data.get('questions_count')})"
        )

    # Artifact map verification
    artifacts = local_data.get("local_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ProofValidationError("local full bundle requires non-empty local_artifacts")

    artifact_map: dict[str, dict[str, Any]] = {}
    for item in artifacts:
        if not isinstance(item, dict):
            raise ProofValidationError("each local_artifacts entry must be an object")
        art_type = str(_require(item, "type"))
        path = Path(str(_require(item, "path"))).expanduser()
        expected = str(_require(item, "sha256"))
        if not HEX64.fullmatch(expected):
            raise ProofValidationError(f"local artifact sha256 for {art_type} must be 64 hex chars")
        verify_local_artifact(path, expected)
        artifact_map[art_type] = {"path": path, "sha256": expected.lower()}

    # Cross-bind local hashes against redacted bundle fields (RP14-T2)
    expected_bindings = {
        "resume_source": "resume_source_sha256",
        "resume_artifact": "resume_artifact_sha256",
        "cover_letter_artifact": "cover_letter_artifact_sha256",
        "manifest": "manifest_sha256",
    }
    for art_type, redacted_key in expected_bindings.items():
        if art_type not in artifact_map:
            raise ProofValidationError(
                f"local full bundle is missing required artifact: {art_type}"
            )
        local_sha = artifact_map[art_type]["sha256"]
        redacted_sha = str(redacted_data.get(redacted_key, "")).lower()
        if local_sha != redacted_sha:
            raise ProofValidationError(
                f"cross-binding hash mismatch for {art_type}: "
                f"local {local_sha} != redacted {redacted_sha}"
            )

    # In deterministic V1.4 packet builder, resume_source is copied directly to resume_artifact
    if (
        redacted_data["resume_source_sha256"].lower()
        != redacted_data["resume_artifact_sha256"].lower()
    ):
        raise ProofValidationError(
            "resume_source_sha256 does not match resume_artifact_sha256 for copied deterministic packet"
        )

    # F145-04: the selected variant must be the one the profile maps to the verified
    # resume bytes, with the exact byte count and the family the profile derives.
    selected_variant = str(local_data.get("selected_resume_variant") or "").strip()
    if not selected_variant:
        raise ProofValidationError("local bundle missing mandatory selected_resume_variant")
    if selected_variant != str(redacted_data.get("resume_variant")):
        raise ProofValidationError(
            f"local bundle selected_resume_variant ({selected_variant}) does not match "
            f"redacted resume_variant ({redacted_data.get('resume_variant')})"
        )
    mapped_source_raw = profile.resume.resolve_source_path(selected_variant)
    if not mapped_source_raw:
        raise ProofValidationError(
            f"candidate profile does not map the selected resume variant {selected_variant} "
            "to any resume source"
        )
    mapped_source = _resolved(mapped_source_raw)
    resume_source_entry = artifact_map["resume_source"]
    if _resolved(resume_source_entry["path"]) != mapped_source:
        raise ProofValidationError(
            "resume_source artifact does not match the resume file the candidate profile maps "
            f"to the selected variant {selected_variant}"
        )
    if _resolved(local_data.get("resume_source_path", "")) != mapped_source:
        raise ProofValidationError(
            "local bundle resume_source_path does not match the resume file the candidate "
            f"profile maps to the selected variant {selected_variant}"
        )
    if str(local_data.get("resume_source_sha256", "")).lower() != resume_source_entry["sha256"]:
        raise ProofValidationError(
            "local bundle resume_source_sha256 does not match the verified resume_source artifact"
        )
    mapped_byte_count = mapped_source.stat().st_size
    if int(redacted_data.get("resume_source_byte_count", -1)) != mapped_byte_count:
        raise ProofValidationError(
            f"redacted resume_source_byte_count ({redacted_data.get('resume_source_byte_count')}) "
            f"does not match the byte count of the mapped resume file ({mapped_byte_count})"
        )
    if int(local_data.get("resume_source_byte_count", -1)) != mapped_byte_count:
        raise ProofValidationError(
            f"local bundle resume_source_byte_count ({local_data.get('resume_source_byte_count')}) "
            f"does not match the byte count of the mapped resume file ({mapped_byte_count})"
        )
    expected_family = ResumeVariantSelector.get_resume_family(selected_variant, profile)
    if str(redacted_data.get("resume_family")) != expected_family:
        raise ProofValidationError(
            f"redacted resume_family ({redacted_data.get('resume_family')!r}) does not match the "
            f"family the candidate profile derives for {selected_variant} ({expected_family!r})"
        )

    # Manifest content, local JobModel link, and canonical packet hash recomputation (RP14-T7)
    manifest_info = artifact_map.get("manifest")
    if not manifest_info:
        raise ProofValidationError("manifest artifact missing from local artifacts")

    manifest_path: Path = manifest_info["path"]
    try:
        manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofValidationError(f"could not read manifest JSON ({type(exc).__name__})") from None
    if not isinstance(manifest_json, dict):
        raise ProofValidationError("manifest JSON must be an object")

    # Mandatory job_id
    local_job_id = _require_uuid_text(local_data, "job_id")
    if str(manifest_json.get("job_id")) != local_job_id:
        raise ProofValidationError(
            f"manifest job_id ({manifest_json.get('job_id')}) does not match local job_id ({local_job_id})"
        )

    # Mandatory packet_id, resume_variant_id, and artifact IDs
    local_packet_id = _require_uuid_text(local_data, "packet_id")
    if local_packet_id != str(redacted_data.get("packet_id")) or local_packet_id != str(
        manifest_json.get("packet_id")
    ):
        raise ProofValidationError(
            "packet_id mismatch across local bundle, redacted bundle, and manifest"
        )

    local_resume_variant_id = _require_uuid_text(local_data, "resume_variant_id")
    if local_resume_variant_id != str(manifest_json.get("resume_variant_id")):
        raise ProofValidationError("resume_variant_id mismatch between local bundle and manifest")

    _require_uuid_text(local_data, "resume_artifact_id")
    _require_uuid_text(local_data, "cover_letter_artifact_id")

    if str(manifest_json.get("resume_family")) != str(redacted_data.get("resume_family")):
        raise ProofValidationError("manifest resume_family does not match redacted resume_family")
    if str(manifest_json.get("resume_variant_name")) != str(redacted_data.get("resume_variant")):
        raise ProofValidationError(
            "manifest resume_variant_name does not match redacted resume_variant"
        )
    if (
        str(manifest_json.get("resume_artifact_sha256")).lower()
        != str(redacted_data.get("resume_artifact_sha256")).lower()
    ):
        raise ProofValidationError(
            "manifest resume_artifact_sha256 does not match redacted resume_artifact_sha256"
        )
    if (
        str(manifest_json.get("cover_letter_artifact_sha256")).lower()
        != str(redacted_data.get("cover_letter_artifact_sha256")).lower()
    ):
        raise ProofValidationError(
            "manifest cover_letter_artifact_sha256 does not match redacted cover_letter_artifact_sha256"
        )
    if (
        str(manifest_json.get("generation_origin")).lower()
        != str(redacted_data.get("generation_origin")).lower()
    ):
        raise ProofValidationError(
            "manifest generation_origin does not match redacted generation_origin"
        )
    if manifest_json.get("is_live_ready") != redacted_data.get("is_live_ready"):
        raise ProofValidationError("manifest is_live_ready does not match redacted is_live_ready")

    # F145-03/04: manifest identity fields bind to the parsed profile and the resume mapping.
    manifest_fingerprint = str(
        manifest_json.get("candidate_profile_fingerprint_sha256") or ""
    ).lower()
    if not manifest_fingerprint:
        raise ProofValidationError(
            "manifest is missing candidate_profile_fingerprint_sha256; regenerate the packet "
            "with the current packet builder"
        )
    if manifest_fingerprint != profile_fingerprint:
        raise ProofValidationError(
            "manifest candidate_profile_fingerprint_sha256 does not match the fingerprint of "
            "the parsed candidate profile on disk"
        )
    if str(manifest_json.get("candidate_profile_version")) != str(profile.version):
        raise ProofValidationError(
            f"manifest candidate_profile_version ({manifest_json.get('candidate_profile_version')!r}) "
            f"does not match the parsed candidate profile version ({profile.version})"
        )
    manifest_source_reference = manifest_json.get("resume_source_reference")
    if not manifest_source_reference or _resolved(manifest_source_reference) != mapped_source:
        raise ProofValidationError(
            "manifest resume_source_reference does not match the resume file the candidate "
            f"profile maps to the selected variant {selected_variant}"
        )
    manifest_answers = manifest_json.get("answers")
    manifest_provenance = manifest_json.get("answer_provenance")
    manifest_unresolved = manifest_json.get("unresolved_questions")
    if (
        not isinstance(manifest_answers, dict)
        or not isinstance(manifest_provenance, dict)
        or not isinstance(manifest_unresolved, list)
    ):
        raise ProofValidationError(
            "manifest answers, answer_provenance and unresolved_questions must all be present"
        )
    if manifest_unresolved != list(redacted_data.get("unresolved_questions", [])):
        raise ProofValidationError(
            "manifest unresolved_questions do not match redacted unresolved_questions"
        )
    if len(manifest_answers) != int(redacted_data.get("resolved_answers_count", -1)):
        raise ProofValidationError(
            f"redacted resolved_answers_count ({redacted_data.get('resolved_answers_count')}) does "
            f"not match the number of manifest answers ({len(manifest_answers)})"
        )
    if len(manifest_answers) + len(manifest_unresolved) != len(questions_data):
        raise ProofValidationError(
            f"manifest answers ({len(manifest_answers)}) plus unresolved questions "
            f"({len(manifest_unresolved)}) do not account for the {len(questions_data)} "
            "attested questions"
        )
    attested_questions = {question.strip() for question in questions_data}
    if not set(manifest_answers) <= attested_questions:
        raise ProofValidationError(
            "manifest answers include a question that is not in the attested question list"
        )
    if set(manifest_provenance) != set(manifest_answers):
        raise ProofValidationError(
            "manifest answer_provenance keys do not match the manifest answers"
        )

    # Recompute canonical packet hash from manifest components
    canonical_payload = {
        "job_id": str(manifest_json.get("job_id")),
        "profile_version": manifest_json.get("candidate_profile_version"),
        "resume_variant_id": str(manifest_json.get("resume_variant_id")),
        "resume_sha": str(manifest_json.get("resume_artifact_sha256")),
        "cover_letter_sha": str(manifest_json.get("cover_letter_artifact_sha256")),
        "answers": manifest_answers,
        "answer_provenance": manifest_provenance,
    }
    recomputed_packet_hash = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    if recomputed_packet_hash.lower() != str(redacted_data.get("packet_hash")).lower():
        raise ProofValidationError(
            f"canonical packet hash recomputation mismatch: "
            f"{recomputed_packet_hash} != {redacted_data.get('packet_hash')}"
        )
    if str(manifest_json.get("packet_hash")).lower() != recomputed_packet_hash.lower():
        raise ProofValidationError(
            f"manifest packet_hash does not match recomputed canonical hash: "
            f"{manifest_json.get('packet_hash')} != {recomputed_packet_hash}"
        )

    # RP14-T7/RP14-T8 and F145-02/03/04: persisted DB rows, artifact rows, the independent
    # Greenhouse source binding, and the profile/variant binding are mandatory for PASS.
    verify_database_linkage(
        local_data,
        redacted_data,
        questions=questions_data,
        artifact_map=artifact_map,
        manifest=manifest_json,
        profile=profile,
        profile_fingerprint=profile_fingerprint,
        mapped_resume_source=mapped_source,
    )


SQLITE_FILE_MAGIC = b"SQLite format 3\x00"

# Leading scheme of a SQLAlchemy URL, e.g. "sqlite", "postgresql+psycopg".
DB_URL_SCHEME = re.compile(r"^(?P<backend>[A-Za-z][A-Za-z0-9]*)(?:\+(?P<driver>[A-Za-z0-9_]+))?://")
POSTGRES_BACKENDS = frozenset({"postgresql", "postgres"})
# Synchronous DBAPI drivers the verifier can actually open a blocking session with.
# psycopg is the driver AppSettings uses by default (postgresql+psycopg://).
SUPPORTED_POSTGRES_DRIVERS = frozenset({"", "psycopg", "psycopg2", "psycopg2cffi", "pg8000"})
SUPPORTED_SQLITE_DRIVERS = frozenset({"", "pysqlite"})


def _redact_db_url(db_url: str) -> str:
    """Strip any embedded credentials before a DB target reaches logs or receipts."""
    scheme, separator, remainder = db_url.partition("://")
    if not separator or "@" not in remainder:
        return db_url
    _, _, host_part = remainder.rpartition("@")
    return f"{scheme}://***@{host_part}"


def _require_readable_sqlite_file(db_path: Path) -> None:
    """Reject absent, non-file, or non-openable SQLite proof-database evidence."""
    if not db_path.exists() or not db_path.is_file():
        raise ProofValidationError(f"proof database file not found on disk: {db_path}")
    try:
        with db_path.open("rb") as handle:
            header = handle.read(len(SQLITE_FILE_MAGIC))
    except OSError as exc:
        raise ProofValidationError(
            f"proof database file could not be opened for reading: {db_path} ({type(exc).__name__})"
        ) from None
    if header != SQLITE_FILE_MAGIC:
        raise ProofValidationError(
            f"proof database file is not an openable SQLite database: {db_path}"
        )


def _split_db_url_scheme(db_str: str) -> tuple[str, str] | None:
    """Return ``(backend, driver)`` for a SQLAlchemy URL, or None for a bare filesystem path."""
    match = DB_URL_SCHEME.match(db_str)
    if match is None:
        return None
    return str(match.group("backend")).lower(), str(match.group("driver") or "").lower()


def _require_usable_postgres_target(db_str: str, driver: str) -> None:
    """Reject PostgreSQL targets this verifier cannot read persisted proof rows from."""
    safe = _redact_db_url(db_str)
    if driver not in SUPPORTED_POSTGRES_DRIVERS:
        raise ProofValidationError(
            f"unsupported PostgreSQL driver {driver!r} for synchronous proof verification: {safe}"
        )
    remainder = db_str.split("://", 1)[1]
    _, separator, database = remainder.partition("/")
    database = database.split("?", 1)[0].strip()
    if not separator or not database:
        raise ProofValidationError(
            f"PostgreSQL proof database URL must name the database holding the proof rows: {safe}"
        )


def _require_persisted_sqlite_target(db_str: str, driver: str) -> None:
    """Reject SQLite targets that are not a readable on-disk proof database."""
    if driver not in SUPPORTED_SQLITE_DRIVERS:
        raise ProofValidationError(
            f"unsupported SQLite driver {driver!r} for synchronous proof verification: {db_str}"
        )
    _, separator, tail = db_str.partition(":///")
    if not separator:
        raise ProofValidationError(f"unsupported SQLite proof database URL: {db_str}")
    raw_path = tail.split("?", 1)[0]
    if not raw_path or raw_path == ":memory:":
        raise ProofValidationError("in-memory SQLite is not acceptable persisted proof evidence")
    _require_readable_sqlite_file(Path(raw_path).expanduser())


def resolve_proof_db_url(db_target: str | Path) -> str:
    """Normalize a legacy declared proof-database target, failing closed on unusable evidence.

    Accepts the SQLAlchemy URL forms the application itself produces, including the
    driver-qualified ``postgresql+psycopg://`` URL that ``AppSettings.database_url``
    defaults to. Also accepts a persisted SQLite URL or a bare SQLite file path.

    Everything else is a rejection, never a silent pass: async drivers the verifier
    cannot open a blocking session with, non-PostgreSQL/non-SQLite backends,
    PostgreSQL URLs that name no database, in-memory SQLite, and SQLite files that
    are absent, unreadable, or not real SQLite databases.

    The returned string is a *target description* only. The verifier never connects
    to it directly: it is reduced to a database identity and reconciled with the
    trusted runtime configuration by ``resolve_verification_database``.
    """
    db_str = str(db_target).strip()
    if not db_str:
        raise ProofValidationError("proof database target is empty")

    scheme = _split_db_url_scheme(db_str)
    if scheme is None:
        # No URL scheme at all: the target is a SQLite proof database path on disk.
        db_path = Path(db_str).expanduser().resolve()
        _require_readable_sqlite_file(db_path)
        return f"sqlite:///{db_path}"

    backend, driver = scheme
    if backend in POSTGRES_BACKENDS:
        _require_usable_postgres_target(db_str, driver)
        if backend == "postgres":
            # SQLAlchemy 2.x dropped the legacy "postgres" dialect alias.
            suffix = db_str.split("://", 1)[1]
            return f"postgresql+{driver}://{suffix}" if driver else f"postgresql://{suffix}"
        return db_str

    if backend == "sqlite":
        _require_persisted_sqlite_target(db_str, driver)
        return db_str

    raise ProofValidationError(
        f"unsupported proof database backend {backend!r}: only PostgreSQL and persisted "
        f"SQLite proof databases can be verified ({_redact_db_url(db_str)})"
    )


def resolve_verification_database(
    local_data: dict[str, Any], runtime_url: str | URL | None = None
) -> URL:
    """F145-02: connect only to the trusted runtime database, after proving identity.

    The private bundle declares the database *identity* the runner persisted into
    (``proof_database``). Credentials come exclusively from trusted runtime
    configuration (``AppSettings.database_url``, i.e. ``DATABASE_URL``); the identity
    must match that runtime target exactly or verification fails. A legacy
    ``database_url``/``db_path`` string is reduced to an identity the same way, and a
    password-masked legacy URL is rejected rather than reconstructed.
    """
    reference = local_data.get("proof_database")
    legacy_target = local_data.get("database_url") or local_data.get("db_path")
    if reference is None and (legacy_target is None or not str(legacy_target).strip()):
        raise ProofValidationError(
            "local full bundle must explicitly configure a proof database target "
            "(proof_database identity, or legacy database_url/db_path); REAL_PROOF_PASS "
            "requires persisted DB evidence"
        )

    if reference is not None:
        if not isinstance(reference, dict):
            raise ProofValidationError(
                "proof_database must be a database identity object, not a connection string"
            )
    else:
        resolved_legacy = resolve_proof_db_url(str(legacy_target))
        try:
            reference = database_identity(resolved_legacy)
        except ProofDatabaseIdentityError as exc:
            raise ProofValidationError(
                f"legacy proof database target rejected: {exc}; regenerate the private bundle "
                "with the current runner"
            ) from None

    if runtime_url is None:
        try:
            runtime_url = AppSettings().database_url
        except Exception as exc:
            raise ProofValidationError(
                f"trusted runtime database configuration could not be loaded ({type(exc).__name__})"
            ) from None

    try:
        url = resolve_runtime_database(reference, runtime_url)
    except ProofDatabaseIdentityError as exc:
        raise ProofValidationError(
            "proof database identity could not be reconciled with the trusted runtime "
            f"database (DATABASE_URL): {exc}"
        ) from None

    if url.drivername.startswith("sqlite"):
        _require_readable_sqlite_file(Path(str(url.database)).expanduser())
    return url


def verify_source_attestation_against_db(
    job: Any,
    source_rows: list[Any],
    attestation: dict[str, Any],
    redacted_data: dict[str, Any],
    questions: list[str] | None,
) -> None:
    """RP14-T8: bind source_attestation to persisted Greenhouse JobSource/Job evidence.

    The local attestation is untrusted input. Every attested field must be
    independently corroborated by the persisted ``job_source`` row (its own
    columns and its captured Greenhouse payload) and by the linked ``job`` row,
    so a self-consistent forged attestation cannot reach REAL_PROOF_PASS.
    """
    public_job_id = str(attestation.get("public_job_id", "")).strip()

    greenhouse_rows = [
        row for row in source_rows if str(getattr(row, "provider", "")).upper() == "GREENHOUSE"
    ]
    if not greenhouse_rows:
        raise ProofValidationError(
            f"no persisted GREENHOUSE JobSource row is linked to job {job.id}; "
            "source_attestation is not independently corroborated"
        )
    matching = [
        row for row in greenhouse_rows if str(row.source_job_id or "").strip() == public_job_id
    ]
    if len(matching) != 1:
        raise ProofValidationError(
            f"expected exactly one persisted GREENHOUSE JobSource with source_job_id "
            f"{public_job_id!r} for job {job.id}, found {len(matching)}"
        )
    source = matching[0]
    if source.job_id != job.id:
        raise ProofValidationError(
            f"persisted GREENHOUSE JobSource job_id ({source.job_id}) is not linked to "
            f"proof job {job.id}"
        )
    persisted_requisition = str(getattr(source, "requisition_id", "") or "").strip()
    if persisted_requisition and persisted_requisition != public_job_id:
        raise ProofValidationError(
            f"persisted GREENHOUSE JobSource.requisition_id ({persisted_requisition!r}) does not "
            f"match attested public_job_id ({public_job_id!r})"
        )

    payload = source.source_payload_json
    if not isinstance(payload, dict) or not payload:
        raise ProofValidationError(
            "persisted GREENHOUSE JobSource.source_payload_json is missing or not an object; "
            "source_attestation cannot be independently verified"
        )

    # Exact-match provenance fields captured at fetch time.
    for att_key, payload_key, label in (
        ("provider", "provider", "provider"),
        ("source_kind", "source_kind", "source kind"),
        ("public_job_id", "public_job_id", "public job id"),
        ("api_url", "api_url", "API URL"),
    ):
        persisted = str(payload.get(payload_key, "")).strip()
        attested = str(attestation.get(att_key, "")).strip()
        if not persisted:
            raise ProofValidationError(
                f"persisted Greenhouse source payload is missing {payload_key}; "
                f"attested {label} is uncorroborated"
            )
        if persisted != attested:
            raise ProofValidationError(
                f"source_attestation {label} ({attested!r}) does not match persisted "
                f"Greenhouse evidence ({persisted!r})"
            )

    if str(payload.get("provider", "")).strip().upper() != "GREENHOUSE":
        raise ProofValidationError(
            f"persisted Greenhouse source payload provider must be GREENHOUSE, "
            f"got {payload.get('provider')!r}"
        )
    if str(payload.get("source_kind", "")).strip() != "greenhouse_public_job_board_api":
        raise ProofValidationError(
            f"persisted Greenhouse source payload source_kind must be "
            f"greenhouse_public_job_board_api, got {payload.get('source_kind')!r}"
        )
    if str(payload.get("public_job_id", "")).strip() != str(source.source_job_id or "").strip():
        raise ProofValidationError(
            f"persisted Greenhouse payload public_job_id ({payload.get('public_job_id')!r}) "
            f"does not match JobSource.source_job_id ({source.source_job_id!r})"
        )

    # fetched_at_utc must exist in the persisted record and denote the same instant.
    persisted_fetched = parse_utc(str(payload.get("fetched_at_utc", "")))
    if persisted_fetched is None:
        raise ProofValidationError(
            "persisted Greenhouse source payload has missing or invalid fetched_at_utc; "
            "attested fetch time is uncorroborated"
        )
    attested_fetched = parse_utc(str(attestation.get("fetched_at_utc", "")))
    if attested_fetched is None or attested_fetched != persisted_fetched:
        raise ProofValidationError(
            f"source_attestation fetched_at_utc ({attestation.get('fetched_at_utc')!r}) does not "
            f"match persisted Greenhouse fetched_at_utc ({payload.get('fetched_at_utc')!r})"
        )

    # Canonical apply URL must agree across attestation, JobSource column, and redacted evidence.
    attested_canonical = str(attestation.get("canonical_apply_url", "")).strip()
    persisted_canonical = str(source.canonical_apply_url or "").strip()
    if not persisted_canonical:
        raise ProofValidationError(
            f"persisted GREENHOUSE JobSource for job {job.id} has no canonical_apply_url"
        )
    if persisted_canonical != attested_canonical:
        raise ProofValidationError(
            f"source_attestation canonical_apply_url ({attested_canonical}) does not match "
            f"persisted JobSource.canonical_apply_url ({persisted_canonical})"
        )
    redacted_job_url = str(redacted_data.get("job_url", "")).strip()
    if persisted_canonical != redacted_job_url:
        raise ProofValidationError(
            f"persisted JobSource.canonical_apply_url ({persisted_canonical}) does not match "
            f"redacted job_url ({redacted_job_url})"
        )
    if str(job.apply_url or "").strip() != redacted_job_url:
        raise ProofValidationError(
            f"persisted JobModel apply URL ({job.apply_url}) does not match "
            f"redacted job_url ({redacted_job_url})"
        )

    # Description/content SHA must be recomputable from the persisted job description.
    description_text = job.description_text
    if not description_text or not str(description_text).strip():
        raise ProofValidationError(
            f"persisted JobModel {job.id} has no description_text; attested "
            "description_sha256 is uncorroborated"
        )
    recomputed_description_sha = sha256_bytes(str(description_text).encode("utf-8"))
    attested_description_sha = str(attestation.get("description_sha256", "")).strip().lower()
    if attested_description_sha != recomputed_description_sha:
        raise ProofValidationError(
            f"source_attestation description_sha256 ({attested_description_sha}) does not match "
            f"SHA-256 of the persisted job description ({recomputed_description_sha})"
        )
    persisted_description_sha = str(payload.get("content_sha256", "")).strip().lower()
    if not persisted_description_sha:
        raise ProofValidationError(
            "persisted Greenhouse source payload is missing content_sha256; "
            "attested description SHA is uncorroborated"
        )
    if persisted_description_sha != recomputed_description_sha:
        raise ProofValidationError(
            f"persisted Greenhouse payload content_sha256 ({persisted_description_sha}) does not "
            f"match SHA-256 of the persisted job description ({recomputed_description_sha})"
        )
    persisted_description_hash = str(job.description_hash or "").strip().lower()
    if persisted_description_hash != recomputed_description_sha:
        raise ProofValidationError(
            f"persisted JobModel.description_hash ({persisted_description_hash}) does not match "
            f"SHA-256 of its own description_text ({recomputed_description_sha})"
        )

    # Question-list SHA must match the persisted capture, not just the local file.
    persisted_question_sha = str(payload.get("question_list_sha256", "")).strip().lower()
    if not persisted_question_sha:
        raise ProofValidationError(
            "persisted Greenhouse source payload is missing question_list_sha256; "
            "attested question-list SHA is uncorroborated"
        )
    attested_question_sha = str(attestation.get("question_list_sha256", "")).strip().lower()
    if persisted_question_sha != attested_question_sha:
        raise ProofValidationError(
            f"source_attestation question_list_sha256 ({attested_question_sha}) does not match "
            f"persisted Greenhouse question_list_sha256 ({persisted_question_sha})"
        )
    if questions is not None:
        recomputed_question_sha = compute_questions_sha256(questions).lower()
        if recomputed_question_sha != persisted_question_sha:
            raise ProofValidationError(
                f"questions JSON on disk hashes to {recomputed_question_sha}, which does not match "
                f"persisted Greenhouse question_list_sha256 ({persisted_question_sha})"
            )
        persisted_count = payload.get("screening_question_count")
        if persisted_count is None:
            raise ProofValidationError(
                "persisted Greenhouse source payload is missing screening_question_count"
            )
        if int(persisted_count) != len(questions):
            raise ProofValidationError(
                f"persisted Greenhouse screening_question_count ({persisted_count}) does not "
                f"match the {len(questions)} questions on disk"
            )


def compute_job_snapshot_sha256(job: Any) -> str:
    """Recompute the runner's job-snapshot digest from persisted JobModel/JobSource rows.

    This mirrors ``scripts/run_v14_real_proof.py::job_snapshot`` field-for-field so the
    redacted ``job_snapshot_sha256`` is re-derived from database truth instead of being
    trusted from the candidate bundle. ``tests/test_real_proof_verifier.py`` pins the two
    implementations to the same digest.
    """
    snapshot = {
        "company": job.company.normalized_name if job.company else None,
        "title": job.normalized_title,
        "location": job.location_text,
        "remote_type": job.remote_type,
        "employment_type": job.employment_type,
        "compensation_min": str(job.compensation_min) if job.compensation_min is not None else None,
        "compensation_max": str(job.compensation_max) if job.compensation_max is not None else None,
        "compensation_currency": job.compensation_currency,
        "description_sha256": sha256_bytes((job.description_text or "").encode("utf-8")),
        "sources": [
            {
                "provider": source.provider,
                "source_job_id": source.source_job_id,
                "source_url": source.source_url,
                "canonical_apply_url": source.canonical_apply_url,
                "requisition_id": source.requisition_id,
            }
            for source in sorted(job.sources, key=lambda s: str(s.id))
        ],
    }
    serialized = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(serialized.encode("utf-8"))


def verify_persisted_job_identity(job: Any, redacted_data: dict[str, Any]) -> None:
    """Bind the redacted job identity to the persisted JobModel, not to the bundle's own claims.

    ``job_title``, ``company`` and ``job_snapshot_sha256`` in the candidate bundle are
    runtime outputs of the runner; a REAL_PROOF_PASS requires each of them to be
    re-derivable from the persisted job row the proof claims to be about.
    """
    persisted_title = str(job.normalized_title or "")
    attested_title = str(redacted_data.get("job_title") or "")
    if persisted_title != attested_title:
        raise ProofValidationError(
            f"redacted job_title ({attested_title!r}) does not match persisted "
            f"JobModel.normalized_title ({persisted_title!r})"
        )

    persisted_company = job.company.normalized_name if job.company else "Unknown"
    attested_company = str(redacted_data.get("company") or "")
    if str(persisted_company) != attested_company:
        raise ProofValidationError(
            f"redacted company ({attested_company!r}) does not match persisted "
            f"CompanyModel.normalized_name ({persisted_company!r})"
        )

    recomputed_snapshot = compute_job_snapshot_sha256(job)
    attested_snapshot = str(redacted_data.get("job_snapshot_sha256") or "").lower()
    if recomputed_snapshot != attested_snapshot:
        raise ProofValidationError(
            f"redacted job_snapshot_sha256 ({attested_snapshot}) does not match the snapshot "
            f"recomputed from persisted JobModel/JobSource rows ({recomputed_snapshot})"
        )


def verify_persisted_packet_components(
    packet: Any,
    resume_art: Any,
    cl_art: Any,
    manifest: dict[str, Any],
    redacted_data: dict[str, Any],
    questions: list[str],
) -> None:
    """F145-03: re-derive packet identity from persisted answers/provenance, not stored hashes.

    The stored ``packet_hash`` is only a claim. The packet identity is recomputed from
    the persisted answers, answer provenance, unresolved list, profile version, variant
    id and artifact hashes, and every component is compared with the manifest and the
    redacted evidence.
    """
    db_answers = packet.answers_json
    db_provenance = packet.answer_provenance_json
    db_unresolved = packet.unresolved_questions_json
    if (
        not isinstance(db_answers, dict)
        or not isinstance(db_provenance, dict)
        or not isinstance(db_unresolved, list)
    ):
        raise ProofValidationError(
            "DB ApplicationPacketModel answers_json, answer_provenance_json and "
            "unresolved_questions_json must all be present"
        )

    recomputed = compute_canonical_packet_hash(
        job_id=packet.job_id,
        profile_version=packet.candidate_profile_version,
        resume_variant_id=packet.resume_variant_id,
        resume_sha=str(resume_art.sha256),
        cover_letter_sha=str(cl_art.sha256),
        answers=db_answers,
        answer_provenance=db_provenance,
    ).lower()
    if recomputed != str(packet.packet_hash or "").lower():
        raise ProofValidationError(
            "packet hash recomputed from persisted DB components (answers, provenance, artifact "
            f"hashes, profile version, variant id) is {recomputed}, which does not match the "
            f"stored ApplicationPacketModel.packet_hash ({packet.packet_hash})"
        )
    if recomputed != str(redacted_data.get("packet_hash", "")).lower():
        raise ProofValidationError(
            f"packet hash recomputed from persisted DB components ({recomputed}) does not match "
            f"redacted packet_hash ({redacted_data.get('packet_hash')})"
        )
    if db_answers != manifest.get("answers"):
        raise ProofValidationError(
            "DB ApplicationPacketModel answers_json does not match the manifest answers"
        )
    if db_provenance != manifest.get("answer_provenance"):
        raise ProofValidationError(
            "DB ApplicationPacketModel answer_provenance_json does not match the manifest "
            "answer_provenance"
        )
    if list(db_unresolved) != list(manifest.get("unresolved_questions", [])):
        raise ProofValidationError(
            "DB ApplicationPacketModel unresolved_questions_json does not match the manifest "
            "unresolved_questions"
        )
    if list(db_unresolved) != list(redacted_data.get("unresolved_questions", [])):
        raise ProofValidationError(
            "DB ApplicationPacketModel unresolved_questions_json does not match redacted "
            "unresolved_questions"
        )
    if len(db_answers) != int(redacted_data.get("resolved_answers_count", -1)):
        raise ProofValidationError(
            f"redacted resolved_answers_count ({redacted_data.get('resolved_answers_count')}) does "
            f"not match the number of persisted answers ({len(db_answers)})"
        )
    if len(db_answers) + len(db_unresolved) != len(questions):
        raise ProofValidationError(
            f"persisted answers ({len(db_answers)}) plus unresolved questions "
            f"({len(db_unresolved)}) do not account for the {len(questions)} attested questions"
        )
    attested_questions = {question.strip() for question in questions}
    if not set(db_answers) <= attested_questions:
        raise ProofValidationError(
            "persisted answers include a question that is not in the attested question list"
        )
    if set(db_provenance) != set(db_answers):
        raise ProofValidationError(
            "persisted answer_provenance keys do not match the persisted answers"
        )
    for record in db_provenance.values():
        method = str(record.get("method", "")).lower() if isinstance(record, dict) else ""
        if method != "deterministic":
            raise ProofValidationError(
                f"persisted answer provenance method must be deterministic, got {method!r}"
            )
    if db_unresolved and bool(packet.is_live_ready):
        raise ProofValidationError(
            "DB ApplicationPacketModel is marked live-ready despite persisted unresolved questions"
        )


def verify_persisted_profile_and_variant_binding(
    job: Any,
    packet: Any,
    resume_variant: Any,
    resume_art: Any,
    cl_art: Any,
    local_data: dict[str, Any],
    redacted_data: dict[str, Any],
    profile: CandidateProfileConfig,
    profile_fingerprint: str,
    mapped_resume_source: Path,
) -> None:
    """F145-04: bind the parsed profile and selected genuine resume mapping to the DB rows."""
    generation_metadata = packet.generation_metadata_json
    persisted_fingerprint = str(
        generation_metadata.get("candidate_profile_fingerprint_sha256") or ""
    ).lower()
    if not persisted_fingerprint:
        raise ProofValidationError(
            "DB ApplicationPacketModel generation_metadata_json is missing the production "
            "candidate_profile_fingerprint_sha256 key"
        )
    if persisted_fingerprint != profile_fingerprint:
        raise ProofValidationError(
            "persisted candidate_profile_fingerprint_sha256 does not match the fingerprint of "
            "the parsed candidate profile on disk"
        )
    if int(packet.candidate_profile_version) != int(profile.version):
        raise ProofValidationError(
            f"DB ApplicationPacketModel candidate_profile_version ({packet.candidate_profile_version}) "
            f"does not match the parsed candidate profile version ({profile.version})"
        )

    expected_variant = ResumeVariantSelector.select_variant(job)
    if str(resume_variant.name) != expected_variant:
        raise ProofValidationError(
            f"persisted ResumeVariantModel.name ({resume_variant.name!r}) is not the variant the "
            f"production selector derives for the persisted job ({expected_variant!r})"
        )
    if str(local_data.get("selected_resume_variant")) != expected_variant:
        raise ProofValidationError(
            f"local bundle selected_resume_variant ({local_data.get('selected_resume_variant')!r}) "
            f"is not the variant the production selector derives ({expected_variant!r})"
        )
    expected_family = ResumeVariantSelector.get_resume_family(expected_variant, profile)
    if str(resume_variant.resume_family) != expected_family:
        raise ProofValidationError(
            f"persisted ResumeVariantModel.resume_family ({resume_variant.resume_family!r}) does "
            f"not match the family derived from the candidate profile ({expected_family!r})"
        )
    if int(resume_variant.version) != int(redacted_data.get("resume_version", -1)):
        raise ProofValidationError(
            f"persisted ResumeVariantModel.version ({resume_variant.version}) does not match "
            f"redacted resume_version ({redacted_data.get('resume_version')})"
        )
    if int(local_data.get("resume_variant_version", -1)) != int(resume_variant.version):
        raise ProofValidationError(
            f"local bundle resume_variant_version ({local_data.get('resume_variant_version')}) "
            f"does not match persisted ResumeVariantModel.version ({resume_variant.version})"
        )
    source_reference = resume_variant.source_reference
    if not source_reference or _resolved(source_reference) != mapped_resume_source:
        raise ProofValidationError(
            "persisted ResumeVariantModel.source_reference does not point at the resume file "
            "the candidate profile maps to the selected variant"
        )

    if str(resume_art.type) != "resume":
        raise ProofValidationError(
            f"persisted resume ArtifactModel.type is {resume_art.type!r}, expected 'resume'"
        )
    if str(cl_art.type) != "cover_letter":
        raise ProofValidationError(
            f"persisted cover letter ArtifactModel.type is {cl_art.type!r}, expected 'cover_letter'"
        )
    artifact_metadata = resume_art.metadata_json
    if not isinstance(artifact_metadata, dict):
        raise ProofValidationError("persisted resume ArtifactModel.metadata_json is missing")
    if str(artifact_metadata.get("variant")) != expected_variant:
        raise ProofValidationError(
            f"persisted resume artifact metadata variant ({artifact_metadata.get('variant')!r}) "
            f"does not match the selected variant ({expected_variant!r})"
        )
    size_bytes = artifact_metadata.get("size_bytes")
    expected_size = int(redacted_data.get("resume_source_byte_count", -1))
    if size_bytes is None or int(size_bytes) != expected_size:
        raise ProofValidationError(
            f"persisted resume artifact size_bytes ({size_bytes}) does not match redacted "
            f"resume_source_byte_count ({expected_size})"
        )
    artifact_source_path = artifact_metadata.get("source_path")
    if not artifact_source_path or _resolved(artifact_source_path) != mapped_resume_source:
        raise ProofValidationError(
            "persisted resume artifact metadata source_path does not match the resume file the "
            "candidate profile maps to the selected variant"
        )


def _resolve_storage_path(uri: str) -> Path | None:
    value = uri.strip()
    if not value:
        return None
    if value.startswith("file://"):
        value = value[len("file://") :]
    return Path(value).expanduser().resolve()


def verify_database_linkage(
    local_data: dict[str, Any],
    redacted_data: dict[str, Any],
    *,
    questions: list[str],
    artifact_map: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    profile: CandidateProfileConfig,
    profile_fingerprint: str,
    mapped_resume_source: Path,
    runtime_url: str | URL | None = None,
) -> None:
    """RP14-T7: Verify persisted DB records against local bundle and redacted proof.

    Fails closed: REAL_PROOF_PASS requires the trusted runtime database to carry the
    identity the private bundle declares and to hold packet/resume/artifact rows whose
    recomputed identity matches the manifest and the redacted evidence. Missing,
    unopenable, unrelated, or tampered DB evidence is a rejection, never a silent skip.
    """
    url = resolve_verification_database(local_data, runtime_url=runtime_url)

    try:
        engine = get_engine(url)
    except (SQLAlchemyError, ImportError, ValueError) as exc:
        raise ProofValidationError(
            "proof database target could not be opened as a SQLAlchemy engine "
            f"({type(exc).__name__})"
        ) from None
    session_factory = get_sessionmaker(engine)
    try:
        with session_factory() as session:
            job_id = uuid.UUID(str(local_data["job_id"]))
            packet_id = uuid.UUID(str(local_data["packet_id"]))
            resume_variant_id = uuid.UUID(str(local_data["resume_variant_id"]))
            resume_artifact_id = uuid.UUID(str(local_data["resume_artifact_id"]))
            cl_artifact_id = uuid.UUID(str(local_data["cover_letter_artifact_id"]))

            if resume_artifact_id == cl_artifact_id:
                raise ProofValidationError(
                    "resume_artifact_id and cover_letter_artifact_id must be distinct rows"
                )

            job = session.get(JobModel, job_id)
            if job is None:
                raise ProofValidationError(f"JobModel not found in DB with id {job_id}")
            if job.apply_url != redacted_data.get("job_url"):
                raise ProofValidationError(
                    f"DB JobModel apply_url ({job.apply_url}) mismatch vs redacted job_url ({redacted_data.get('job_url')})"
                )

            packet = session.get(ApplicationPacketModel, packet_id)
            if packet is None:
                raise ProofValidationError(
                    f"ApplicationPacketModel not found in DB with id {packet_id}"
                )
            if packet.job_id != job_id:
                raise ProofValidationError(
                    f"DB ApplicationPacketModel job_id ({packet.job_id}) does not match {job_id}"
                )
            if packet.resume_variant_id != resume_variant_id:
                raise ProofValidationError(
                    f"DB ApplicationPacketModel resume_variant_id ({packet.resume_variant_id}) does not match {resume_variant_id}"
                )
            if packet.resume_artifact_id != resume_artifact_id:
                raise ProofValidationError(
                    f"DB ApplicationPacketModel resume_artifact_id mismatch: {packet.resume_artifact_id} != {resume_artifact_id}"
                )
            if packet.cover_letter_artifact_id != cl_artifact_id:
                raise ProofValidationError(
                    f"DB ApplicationPacketModel cover_letter_artifact_id mismatch: {packet.cover_letter_artifact_id} != {cl_artifact_id}"
                )
            if (
                str(packet.packet_hash or "").lower()
                != str(redacted_data.get("packet_hash")).lower()
            ):
                raise ProofValidationError(
                    f"DB ApplicationPacketModel packet_hash mismatch: {packet.packet_hash} != {redacted_data.get('packet_hash')}"
                )
            if str(packet.candidate_profile_version) != str(
                redacted_data.get("candidate_profile_version")
            ):
                raise ProofValidationError(
                    f"DB ApplicationPacketModel candidate_profile_version ({packet.candidate_profile_version}) "
                    f"does not match redacted candidate_profile_version ({redacted_data.get('candidate_profile_version')})"
                )
            if bool(packet.is_live_ready) != bool(redacted_data.get("is_live_ready")):
                raise ProofValidationError(
                    f"DB ApplicationPacketModel is_live_ready ({packet.is_live_ready}) does not match "
                    f"redacted is_live_ready ({redacted_data.get('is_live_ready')})"
                )
            generation_metadata = packet.generation_metadata_json
            if not isinstance(generation_metadata, dict):
                raise ProofValidationError(
                    "DB ApplicationPacketModel generation_metadata_json is missing or not an object"
                )
            # The production packet builder persists the origin under the
            # "generation_origin" key (src/jobs_automation/preparation/packet_builder.py).
            # No production writer has ever emitted a bare "origin" key, so accepting
            # one would only add an unverified acceptance route for the proof gate.
            if "generation_origin" not in generation_metadata:
                raise ProofValidationError(
                    "DB ApplicationPacketModel generation_metadata_json is missing the "
                    "production generation_origin key; got keys "
                    f"{sorted(str(key) for key in generation_metadata)}"
                )
            packet_origin = generation_metadata["generation_origin"]
            if str(packet_origin).lower() != "deterministic":
                raise ProofValidationError(
                    f"DB ApplicationPacketModel generation origin in metadata must be deterministic, got {packet_origin!r}"
                )

            resume_variant = session.get(ResumeVariantModel, resume_variant_id)
            if resume_variant is None:
                raise ProofValidationError(
                    f"ResumeVariantModel not found in DB with id {resume_variant_id}"
                )
            if packet.resume_variant is None or packet.resume_variant.id != resume_variant_id:
                raise ProofValidationError(
                    "DB ApplicationPacketModel is not related to the declared ResumeVariantModel row"
                )
            if resume_variant.resume_family != redacted_data.get("resume_family"):
                raise ProofValidationError(
                    f"DB ResumeVariantModel resume_family mismatch: {resume_variant.resume_family} != {redacted_data.get('resume_family')}"
                )
            if resume_variant.name != redacted_data.get("resume_variant"):
                raise ProofValidationError(
                    f"DB ResumeVariantModel name mismatch: {resume_variant.name} != {redacted_data.get('resume_variant')}"
                )
            if (
                str(resume_variant.content_hash or "").lower()
                != str(redacted_data.get("resume_artifact_sha256", "")).lower()
            ):
                raise ProofValidationError(
                    f"DB ResumeVariantModel content_hash ({resume_variant.content_hash}) does not match "
                    f"redacted resume_artifact_sha256 ({redacted_data.get('resume_artifact_sha256')})"
                )
            if resume_variant.target_job_id is not None and resume_variant.target_job_id != job_id:
                raise ProofValidationError(
                    f"DB ResumeVariantModel target_job_id ({resume_variant.target_job_id}) is not the proof job {job_id}"
                )

            resume_art = session.get(ArtifactModel, resume_artifact_id)
            if resume_art is None:
                raise ProofValidationError(
                    f"ArtifactModel row for resume_artifact_id {resume_artifact_id} not found in DB"
                )
            if (
                str(resume_art.sha256 or "").lower()
                != str(redacted_data.get("resume_artifact_sha256")).lower()
            ):
                raise ProofValidationError(
                    f"DB resume ArtifactModel sha256 mismatch: {resume_art.sha256} != {redacted_data.get('resume_artifact_sha256')}"
                )

            cl_art = session.get(ArtifactModel, cl_artifact_id)
            if cl_art is None:
                raise ProofValidationError(
                    f"ArtifactModel row for cover_letter_artifact_id {cl_artifact_id} not found in DB"
                )
            if (
                str(cl_art.sha256 or "").lower()
                != str(redacted_data.get("cover_letter_artifact_sha256")).lower()
            ):
                raise ProofValidationError(
                    f"DB cover letter ArtifactModel sha256 mismatch: {cl_art.sha256} != {redacted_data.get('cover_letter_artifact_sha256')}"
                )

            # Bind persisted artifact rows to the hash-verified bytes on disk.
            for art_type, artifact_row in (
                ("resume_artifact", resume_art),
                ("cover_letter_artifact", cl_art),
            ):
                local_entry = artifact_map.get(art_type)
                if not local_entry:
                    raise ProofValidationError(f"local artifact map is missing {art_type}")
                stored = _resolve_storage_path(str(artifact_row.storage_uri or ""))
                if stored is None:
                    raise ProofValidationError(
                        f"DB {art_type} ArtifactModel storage_uri is empty; "
                        "persisted artifact bytes are unbound"
                    )
                local_path = Path(local_entry["path"]).expanduser().resolve()
                if stored != local_path:
                    raise ProofValidationError(
                        f"DB {art_type} ArtifactModel storage_uri ({stored}) does not point at "
                        f"the verified local artifact ({local_path})"
                    )

            # F145-03: packet identity recomputed from persisted components.
            verify_persisted_packet_components(
                packet=packet,
                resume_art=resume_art,
                cl_art=cl_art,
                manifest=manifest,
                redacted_data=redacted_data,
                questions=questions,
            )

            # F145-04: parsed profile, selector and genuine resume mapping bound to rows.
            verify_persisted_profile_and_variant_binding(
                job=job,
                packet=packet,
                resume_variant=resume_variant,
                resume_art=resume_art,
                cl_art=cl_art,
                local_data=local_data,
                redacted_data=redacted_data,
                profile=profile,
                profile_fingerprint=profile_fingerprint,
                mapped_resume_source=mapped_resume_source,
            )

            # RP14-T8: source_attestation must be corroborated by persisted evidence.
            attestation = local_data.get("source_attestation")
            if not isinstance(attestation, dict):
                raise ProofValidationError(
                    "local bundle missing mandatory source_attestation object"
                )
            verify_source_attestation_against_db(
                job=job,
                source_rows=list(job.sources),
                attestation=attestation,
                redacted_data=redacted_data,
                questions=questions,
            )

            # Job identity (title/company/snapshot digest) must be re-derivable from
            # the persisted rows, not accepted from the candidate bundle.
            verify_persisted_job_identity(job, redacted_data)
    except SQLAlchemyError as exc:
        raise ProofValidationError(
            "proof database evidence could not be read from the configured runtime database "
            f"({type(exc).__name__})"
        ) from None
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Receipt generation and entry point
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class VerificationOutcome:
    candidate_bundle_sha: str = "unknown"
    proof_run_id: str = "unknown"
    passed: bool = False
    structural_only: bool = False
    local_verified: bool = False
    schema_validated: bool = False
    database_evidence_verified: bool = False
    evidence_schema_sha256: str = "unknown"
    reasons: list[str] = dataclasses.field(default_factory=list)


def generate_receipt(
    candidate_bundle_sha: str,
    proof_run_id: str,
    passed: bool,
    local_verified: bool,
    reasons: list[str] | None = None,
    *,
    evidence_schema_sha256: str = "unknown",
    schema_validated: bool = False,
    database_evidence_verified: bool = False,
) -> dict[str, Any]:
    return {
        "receipt_schema_version": 2,
        "proof_run_id": proof_run_id[:128],
        "candidate_bundle_sha256": candidate_bundle_sha,
        "verifier_code_commit_sha": get_git_sha(),
        "verification_timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "result": "REAL_PROOF_PASS" if passed else "REAL_PROOF_FAIL",
        "evidence_schema_sha256": evidence_schema_sha256,
        "schema_validated": schema_validated,
        "local_full_bundle_verified": local_verified,
        "database_evidence_verified": database_evidence_verified,
        "rejection_reasons": [sanitize_reason(reason) for reason in (reasons or [])],
    }


def run_verification(redacted_bundle: Path, local_full_bundle: Path | None) -> VerificationOutcome:
    """Run every gate and return a bound outcome; malformed inputs never escape as tracebacks."""
    outcome = VerificationOutcome()
    try:
        raw_bundle_bytes = redacted_bundle.read_bytes()
        outcome.candidate_bundle_sha = sha256_bytes(raw_bundle_bytes)
        redacted = json.loads(raw_bundle_bytes.decode("utf-8"))
        if not isinstance(redacted, dict):
            raise ProofValidationError("redacted bundle must be a JSON object")

        proof_run_id = redacted.get("proof_run_id")
        if isinstance(proof_run_id, str) and proof_run_id:
            outcome.proof_run_id = proof_run_id

        # F145-01: executed schema (types, required fields, formats) before semantics.
        outcome.evidence_schema_sha256 = validate_redacted_bundle_schema(redacted)
        outcome.schema_validated = True
        validate_redacted_bundle(redacted)

        # RP14-T1 & RP14-T2: PASS requires local full bundle verification
        if local_full_bundle is None:
            outcome.structural_only = True
            outcome.reasons.append(
                "local full bundle required for REAL_PROOF_PASS; structural check only"
            )
            return outcome

        local_data = json.loads(local_full_bundle.read_text(encoding="utf-8"))
        if not isinstance(local_data, dict):
            raise ProofValidationError("local full bundle must be a JSON object")
        validate_local_bundle(
            local_data,
            redacted,
            candidate_bundle_sha=outcome.candidate_bundle_sha,
        )
        outcome.local_verified = True
        outcome.database_evidence_verified = True
        outcome.passed = True
    except (
        OSError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
        ProofValidationError,
    ) as exc:
        outcome.reasons.append(sanitize_reason(str(exc)))
    except Exception as exc:  # defensive: a malformed input must fail closed, not crash
        outcome.reasons.append(f"internal verifier error: {type(exc).__name__}")
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("redacted_bundle", type=Path)
    parser.add_argument(
        "--local-full-bundle",
        type=Path,
        default=None,
        help="Private bundle containing local artifact paths for hash and manifest cross-check (MANDATORY for PASS).",
    )
    parser.add_argument(
        "--receipt-output",
        type=Path,
        default=None,
        help="Path to write the verification receipt JSON. Defaults to v14_real_proof_receipt_<proof_run_id>.json next to the redacted bundle.",
    )
    args = parser.parse_args()

    outcome = run_verification(args.redacted_bundle, args.local_full_bundle)

    receipt = generate_receipt(
        candidate_bundle_sha=outcome.candidate_bundle_sha,
        proof_run_id=outcome.proof_run_id,
        passed=outcome.passed,
        local_verified=outcome.local_verified,
        reasons=outcome.reasons,
        evidence_schema_sha256=outcome.evidence_schema_sha256,
        schema_validated=outcome.schema_validated,
        database_evidence_verified=outcome.database_evidence_verified,
    )
    receipt_path = args.receipt_output
    if receipt_path is None:
        receipt_path = args.redacted_bundle.parent / receipt_filename(
            outcome.proof_run_id, outcome.candidate_bundle_sha
        )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if outcome.passed:
        print("REAL_PROOF_VALIDATION_PASS")
        print(f"receipt_output={receipt_path}")
        print(f"candidate_bundle_sha256={outcome.candidate_bundle_sha}")
        print(f"local_full_bundle_verified={outcome.local_verified}")
        return 0

    if outcome.structural_only:
        print(
            "REAL_PROOF_VALIDATION_STRUCTURAL_ONLY: PASS requires --local-full-bundle",
            file=sys.stderr,
        )
        print(f"receipt_output={receipt_path}")
        print(f"candidate_bundle_sha256={outcome.candidate_bundle_sha}")
        print("local_full_bundle_verified=False")
        return 1

    for reason in receipt["rejection_reasons"]:
        print(f"REAL_PROOF_VALIDATION_FAIL: {reason}", file=sys.stderr)
    print(f"receipt_output={receipt_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

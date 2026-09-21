#!/usr/bin/env python3
"""Validate a redacted V1.4 real-proof evidence bundle and generate verification receipt.

This verifies evidence structure, strict allowlists, and anti-mock/anti-fixture invariants.
When a local full bundle is provided, it cross-binds local artifacts, hashes, and manifest content.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
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


def validate_local_bundle(
    local_data: dict[str, Any],
    redacted_data: dict[str, Any],
    candidate_bundle_sha: str | None = None,
) -> None:
    """RP14-T2, RP14-T3, RP14-T4 & RP14-T7: Validate local artifacts, Greenhouse source attestation, and cross-bind."""
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
        and local_data["candidate_bundle_sha256"].lower() != candidate_bundle_sha.lower()
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

    repo_root = Path(__file__).resolve().parent.parent
    example_files = list(repo_root.glob("config/*example*")) + list(
        repo_root.glob("tests/fixtures/*example*")
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
            f"could not parse questions JSON from {questions_path}: {exc}"
        ) from exc
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

    # Manifest content, local JobModel link, and canonical packet hash recomputation (RP14-T7)
    manifest_info = artifact_map.get("manifest")
    if not manifest_info:
        raise ProofValidationError("manifest artifact missing from local artifacts")

    manifest_path: Path = manifest_info["path"]
    try:
        manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofValidationError(f"could not read manifest JSON: {exc}") from exc

    # Mandatory job_id
    local_job_id = str(local_data.get("job_id", "")).strip()
    if not local_job_id or not re.fullmatch(r"^[0-9a-fA-F-]{36}$", local_job_id):
        raise ProofValidationError("local bundle missing mandatory valid UUID job_id")
    if str(manifest_json.get("job_id")) != local_job_id:
        raise ProofValidationError(
            f"manifest job_id ({manifest_json.get('job_id')}) does not match local job_id ({local_job_id})"
        )

    # Mandatory packet_id, resume_variant_id, and artifact IDs
    local_packet_id = str(local_data.get("packet_id", "")).strip()
    if not local_packet_id or not re.fullmatch(r"^[0-9a-fA-F-]{36}$", local_packet_id):
        raise ProofValidationError("local bundle missing mandatory valid UUID packet_id")
    if local_packet_id != str(redacted_data.get("packet_id")) or local_packet_id != str(
        manifest_json.get("packet_id")
    ):
        raise ProofValidationError(
            "packet_id mismatch across local bundle, redacted bundle, and manifest"
        )

    local_resume_variant_id = str(local_data.get("resume_variant_id", "")).strip()
    if not local_resume_variant_id or not re.fullmatch(
        r"^[0-9a-fA-F-]{36}$", local_resume_variant_id
    ):
        raise ProofValidationError("local bundle missing mandatory valid UUID resume_variant_id")
    if local_resume_variant_id != str(manifest_json.get("resume_variant_id")):
        raise ProofValidationError("resume_variant_id mismatch between local bundle and manifest")

    local_resume_artifact_id = str(local_data.get("resume_artifact_id", "")).strip()
    if not local_resume_artifact_id or not re.fullmatch(
        r"^[0-9a-fA-F-]{36}$", local_resume_artifact_id
    ):
        raise ProofValidationError("local bundle missing mandatory valid UUID resume_artifact_id")

    local_cl_artifact_id = str(local_data.get("cover_letter_artifact_id", "")).strip()
    if not local_cl_artifact_id or not re.fullmatch(r"^[0-9a-fA-F-]{36}$", local_cl_artifact_id):
        raise ProofValidationError(
            "local bundle missing mandatory valid UUID cover_letter_artifact_id"
        )

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

    # Recompute canonical packet hash from manifest components
    canonical_payload = {
        "job_id": str(manifest_json.get("job_id")),
        "profile_version": manifest_json.get("candidate_profile_version"),
        "resume_variant_id": str(manifest_json.get("resume_variant_id")),
        "resume_sha": str(manifest_json.get("resume_artifact_sha256")),
        "cover_letter_sha": str(manifest_json.get("cover_letter_artifact_sha256")),
        "answers": manifest_json.get("answers", {}),
        "answer_provenance": manifest_json.get("answer_provenance", {}),
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

    # RP14-T7/RP14-T8: persisted DB rows, artifact rows, and the independent
    # Greenhouse source binding are mandatory for REAL_PROOF_PASS.
    verify_database_linkage(
        local_data,
        redacted_data,
        questions=questions_data,
        artifact_map=artifact_map,
    )


SQLITE_FILE_MAGIC = b"SQLite format 3\x00"

# Leading scheme of a SQLAlchemy URL, e.g. "sqlite", "postgresql+psycopg".
DB_URL_SCHEME = re.compile(
    r"^(?P<backend>[A-Za-z][A-Za-z0-9]*)(?:\+(?P<driver>[A-Za-z0-9_]+))?://"
)
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
            f"proof database file could not be opened for reading: {db_path}: {exc}"
        ) from exc
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
    """Normalize a declared proof-database target, failing closed on unusable evidence.

    Accepts the SQLAlchemy URL forms the application itself produces, including the
    driver-qualified ``postgresql+psycopg://`` URL that ``AppSettings.database_url``
    defaults to and that ``scripts/run_v14_real_proof.py`` records as ``database_url``.
    Also accepts a persisted SQLite URL or a bare SQLite file path.

    Everything else is a rejection, never a silent pass: async drivers the verifier
    cannot open a blocking session with, non-PostgreSQL/non-SQLite backends,
    PostgreSQL URLs that name no database, in-memory SQLite, and SQLite files that
    are absent, unreadable, or not real SQLite databases.
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


def verify_database_linkage(
    local_data: dict[str, Any],
    redacted_data: dict[str, Any],
    db_target: str | Path | None = None,
    questions: list[str] | None = None,
    artifact_map: dict[str, dict[str, Any]] | None = None,
) -> None:
    """RP14-T7: Verify persisted DB records against local bundle and redacted proof.

    Fails closed: REAL_PROOF_PASS requires an explicitly configured proof database
    target that opens and validates the persisted packet/resume/artifact rows and
    their relationships. Missing, unopenable, unrelated, or tampered DB evidence
    is a rejection, never a silent skip.
    """
    if db_target is None:
        db_target = local_data.get("database_url") or local_data.get("db_path")
    if not db_target or not str(db_target).strip():
        raise ProofValidationError(
            "local full bundle must explicitly configure a proof database target "
            "(database_url or db_path); REAL_PROOF_PASS requires persisted DB evidence"
        )

    import uuid

    try:
        from sqlalchemy.exc import SQLAlchemyError

        from jobs_automation.db.models import (
            ApplicationPacketModel,
            ArtifactModel,
            JobModel,
            ResumeVariantModel,
        )
        from jobs_automation.db.session import get_engine, get_sessionmaker
    except ImportError as exc:  # pragma: no cover - environment defect, not proof defect
        raise ProofValidationError(
            f"proof database evidence cannot be verified: {exc}"
        ) from exc

    db_url = resolve_proof_db_url(db_target)
    safe_db_url = _redact_db_url(db_url)

    try:
        engine = get_engine(db_url)
    except (SQLAlchemyError, ImportError) as exc:
        raise ProofValidationError(
            f"proof database target could not be opened as a SQLAlchemy engine "
            f"({safe_db_url}): {exc}"
        ) from exc
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
            if str(packet.packet_hash or "").lower() != str(redacted_data.get("packet_hash")).lower():
                raise ProofValidationError(
                    f"DB ApplicationPacketModel packet_hash mismatch: {packet.packet_hash} != {redacted_data.get('packet_hash')}"
                )
            if packet.candidate_profile_version != redacted_data.get("candidate_profile_version"):
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
            if artifact_map:
                for art_type, artifact_row in (
                    ("resume_artifact", resume_art),
                    ("cover_letter_artifact", cl_art),
                ):
                    local_entry = artifact_map.get(art_type)
                    if not local_entry:
                        continue
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
    except SQLAlchemyError as exc:
        raise ProofValidationError(
            f"proof database evidence could not be read from {safe_db_url}: {exc}"
        ) from exc
    finally:
        engine.dispose()


def _resolve_storage_path(uri: str) -> Path | None:
    value = uri.strip()
    if not value:
        return None
    if value.startswith("file://"):
        value = value[len("file://") :]
    return Path(value).expanduser().resolve()


def generate_receipt(
    candidate_bundle_sha: str,
    proof_run_id: str,
    passed: bool,
    local_verified: bool,
    reasons: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "receipt_schema_version": 1,
        "proof_run_id": proof_run_id,
        "candidate_bundle_sha256": candidate_bundle_sha,
        "verifier_code_commit_sha": get_git_sha(),
        "verification_timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "result": "REAL_PROOF_PASS" if passed else "REAL_PROOF_FAIL",
        "local_full_bundle_verified": local_verified,
        "rejection_reasons": reasons or [],
    }


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
        help="Path to write the verification receipt JSON. Defaults to v14_real_proof_receipt_<proof_run_id>.json.",
    )
    args = parser.parse_args()

    rejection_reasons: list[str] = []
    candidate_bundle_sha = "unknown"
    proof_run_id = "unknown"
    local_verified = False

    try:
        raw_bundle_bytes = args.redacted_bundle.read_bytes()
        candidate_bundle_sha = sha256_bytes(raw_bundle_bytes)
        redacted = json.loads(raw_bundle_bytes.decode("utf-8"))
        if not isinstance(redacted, dict):
            raise ProofValidationError("redacted bundle must be a JSON object")

        proof_run_id = str(redacted.get("proof_run_id", "unknown"))
        validate_redacted_bundle(redacted)

        # RP14-T1 & RP14-T2: PASS requires local full bundle verification
        if args.local_full_bundle is None:
            rejection_reasons.append(
                "local full bundle required for REAL_PROOF_PASS; structural check only"
            )
            receipt = generate_receipt(
                candidate_bundle_sha=candidate_bundle_sha,
                proof_run_id=proof_run_id,
                passed=False,
                local_verified=False,
                reasons=rejection_reasons,
            )
            receipt_path = args.receipt_output
            if receipt_path is None:
                receipt_path = (
                    args.redacted_bundle.parent / f"v14_real_proof_receipt_{proof_run_id}.json"
                )
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(
                "REAL_PROOF_VALIDATION_STRUCTURAL_ONLY: PASS requires --local-full-bundle",
                file=sys.stderr,
            )
            print(f"receipt_output={receipt_path}")
            print(f"candidate_bundle_sha256={candidate_bundle_sha}")
            print("local_full_bundle_verified=False")
            return 1

        local_data = json.loads(args.local_full_bundle.read_text(encoding="utf-8"))
        if not isinstance(local_data, dict):
            raise ProofValidationError("local full bundle must be a JSON object")
        validate_local_bundle(
            local_data,
            redacted,
            candidate_bundle_sha=candidate_bundle_sha,
        )
        local_verified = True

        receipt = generate_receipt(
            candidate_bundle_sha=candidate_bundle_sha,
            proof_run_id=proof_run_id,
            passed=True,
            local_verified=True,
        )

        receipt_path = args.receipt_output
        if receipt_path is None:
            receipt_path = (
                args.redacted_bundle.parent / f"v14_real_proof_receipt_{proof_run_id}.json"
            )

        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        print("REAL_PROOF_VALIDATION_PASS")
        print(f"receipt_output={receipt_path}")
        print(f"candidate_bundle_sha256={candidate_bundle_sha}")
        print(f"local_full_bundle_verified={local_verified}")
        return 0

    except (OSError, json.JSONDecodeError, ValueError, ProofValidationError) as exc:
        rejection_reasons.append(str(exc))
        receipt = generate_receipt(
            candidate_bundle_sha=candidate_bundle_sha,
            proof_run_id=proof_run_id,
            passed=False,
            local_verified=local_verified,
            reasons=rejection_reasons,
        )
        receipt_path = args.receipt_output
        if receipt_path is None:
            receipt_path = (
                args.redacted_bundle.parent / f"v14_real_proof_receipt_{proof_run_id}.json"
            )
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"REAL_PROOF_VALIDATION_FAIL: {exc}", file=sys.stderr)
        print(f"receipt_output={receipt_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

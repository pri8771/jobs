#!/usr/bin/env python3
"""Validate a redacted V1.4 real-proof evidence bundle.

This verifies evidence structure and anti-mock/anti-fixture invariants.
It does not itself prove that private local files exist unless a local full bundle is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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


class ProofValidationError(Exception):
    """Raised when a real-proof evidence invariant fails."""


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


def _assert_no_fixture_markers(data: dict[str, Any]) -> None:
    searchable = json.dumps(data, sort_keys=True).lower()
    for token in FORBIDDEN_TOKENS:
        if token in searchable:
            raise ProofValidationError(f"forbidden mock/fixture marker present: {token}")


def validate_redacted_bundle(data: dict[str, Any]) -> None:
    _walk_forbidden_private_keys(data)

    result = str(_require(data, "result"))
    if result != "REAL_PROOF_PASS":
        raise ProofValidationError(f"result must be REAL_PROOF_PASS, got {result}")

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

    generation_origin = str(_require(data, "generation_origin")).lower()
    if generation_origin in {"mock", "test", "adversarial_mock"}:
        raise ProofValidationError("generation_origin is mock/test")
    if not generation_origin:
        raise ProofValidationError("generation_origin is empty")

    model_origin = str(_require(data, "model_origin")).lower()
    if model_origin in {"mock", "test", "adversarial_mock"}:
        raise ProofValidationError("model_origin is mock/test")
    if not model_origin:
        raise ProofValidationError("model_origin is empty")

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


def verify_local_artifact(path: Path, expected_sha: str) -> None:
    if not path.exists() or not path.is_file():
        raise ProofValidationError(f"local artifact missing: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual.lower() != expected_sha.lower():
        raise ProofValidationError(
            f"local artifact hash mismatch for {path.name}: {actual} != {expected_sha}"
        )


def validate_local_bundle(data: dict[str, Any]) -> None:
    artifacts = data.get("local_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ProofValidationError("local full bundle requires non-empty local_artifacts")

    for item in artifacts:
        if not isinstance(item, dict):
            raise ProofValidationError("each local_artifacts entry must be an object")
        path = Path(str(_require(item, "path"))).expanduser()
        expected = str(_require(item, "sha256"))
        if not HEX64.fullmatch(expected):
            raise ProofValidationError("local artifact sha256 must be 64 hex chars")
        verify_local_artifact(path, expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("redacted_bundle", type=Path)
    parser.add_argument(
        "--local-full-bundle",
        type=Path,
        default=None,
        help="Optional ignored private bundle containing local artifact paths for hash re-check.",
    )
    args = parser.parse_args()

    try:
        redacted = json.loads(args.redacted_bundle.read_text(encoding="utf-8"))
        if not isinstance(redacted, dict):
            raise ProofValidationError("redacted bundle must be a JSON object")
        validate_redacted_bundle(redacted)

        if args.local_full_bundle is not None:
            local_data = json.loads(args.local_full_bundle.read_text(encoding="utf-8"))
            if not isinstance(local_data, dict):
                raise ProofValidationError("local full bundle must be a JSON object")
            validate_local_bundle(local_data)

        print("REAL_PROOF_VALIDATION_PASS")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, ProofValidationError) as exc:
        print(f"REAL_PROOF_VALIDATION_FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

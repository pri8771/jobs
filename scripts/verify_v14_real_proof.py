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
    if result not in {"REAL_PROOF_CANDIDATE", "REAL_PROOF_PASS"}:
        raise ProofValidationError(
            f"result must be REAL_PROOF_CANDIDATE or REAL_PROOF_PASS, got {result}"
        )

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
    """RP14-T2 & RP14-T7: Validate local artifacts and cross-bind to redacted candidate evidence."""
    local_proof_id = local_data.get("proof_run_id")
    redacted_proof_id = redacted_data.get("proof_run_id")
    if not local_proof_id or local_proof_id != redacted_proof_id:
        raise ProofValidationError(
            f"proof_run_id mismatch between local bundle ({local_proof_id}) "
            f"and redacted evidence ({redacted_proof_id})"
        )

    if candidate_bundle_sha and "candidate_bundle_sha256" in local_data:
        if local_data["candidate_bundle_sha256"].lower() != candidate_bundle_sha.lower():
            raise ProofValidationError(
                f"candidate_bundle_sha256 in local bundle does not match computed candidate SHA: "
                f"{local_data['candidate_bundle_sha256']} != {candidate_bundle_sha}"
            )

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
            raise ProofValidationError(f"local full bundle is missing required artifact: {art_type}")
        local_sha = artifact_map[art_type]["sha256"]
        redacted_sha = str(redacted_data.get(redacted_key, "")).lower()
        if local_sha != redacted_sha:
            raise ProofValidationError(
                f"cross-binding hash mismatch for {art_type}: "
                f"local {local_sha} != redacted {redacted_sha}"
            )

    # In deterministic V1.4 packet builder, resume_source is copied directly to resume_artifact
    if redacted_data["resume_source_sha256"].lower() != redacted_data["resume_artifact_sha256"].lower():
        raise ProofValidationError(
            "resume_source_sha256 does not match resume_artifact_sha256 for copied deterministic packet"
        )

    # Manifest content and cross-link validation (RP14-T7)
    manifest_info = artifact_map.get("manifest")
    if manifest_info:
        manifest_path: Path = manifest_info["path"]
        try:
            manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProofValidationError(f"could not read manifest JSON: {exc}") from exc

        if str(manifest_json.get("packet_id")) != str(redacted_data.get("packet_id")):
            raise ProofValidationError("manifest packet_id does not match redacted packet_id")
        if str(manifest_json.get("packet_hash")).lower() != str(redacted_data.get("packet_hash")).lower():
            raise ProofValidationError("manifest packet_hash does not match redacted packet_hash")
        if str(manifest_json.get("resume_artifact_sha256")).lower() != str(redacted_data.get("resume_artifact_sha256")).lower():
            raise ProofValidationError("manifest resume_artifact_sha256 does not match redacted resume_artifact_sha256")
        if str(manifest_json.get("cover_letter_artifact_sha256")).lower() != str(redacted_data.get("cover_letter_artifact_sha256")).lower():
            raise ProofValidationError("manifest cover_letter_artifact_sha256 does not match redacted cover_letter_artifact_sha256")


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
        help="Optional private bundle containing local artifact paths for hash and manifest cross-check.",
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

        if args.local_full_bundle is not None:
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
            local_verified=local_verified,
        )

        receipt_path = args.receipt_output
        if receipt_path is None:
            receipt_path = args.redacted_bundle.parent / f"v14_real_proof_receipt_{proof_run_id}.json"

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
        if args.receipt_output is not None:
            args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
            args.receipt_output.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(f"REAL_PROOF_VALIDATION_FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

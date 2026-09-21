#!/usr/bin/env python3
"""Run the V1.4 real-data packet proof against the configured Jobs database.

This command does NOT open a browser or submit an application.
It requires:
- an existing real JobModel in the configured database,
- a private real candidate-profile YAML path,
- a JSON file containing real application questions from the public posting.

Private artifacts are written under .local/proofs/ (gitignored).
A redacted evidence candidate bundle is written under coordination/proofs/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from jobs_automation.adapters.models import DeterministicModelGateway
from jobs_automation.core.config import ConfigLoader
from jobs_automation.db.models import ArtifactModel, JobModel
from jobs_automation.db.session import get_sessionmaker
from jobs_automation.preparation.packet_builder import (
    ApplicationPacketBuilder,
    compute_questions_sha256,
)
from jobs_automation.preparation.tailoring import ResumeVariantSelector
from jobs_automation.storage.artifact_store import ArtifactStore


class RealProofError(Exception):
    """Raised when the real-proof command detects a non-real or unsafe input."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def resolve_storage_path(uri: str) -> Path:
    return Path(uri[7:] if uri.startswith("file://") else uri)


def get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RealProofError(f"Could not resolve current Git commit SHA: {exc}") from exc
    sha = result.stdout.strip()
    if len(sha) < 7:
        raise RealProofError("Git commit SHA is unexpectedly empty")
    return sha


def load_real_questions(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        raise RealProofError(f"Questions file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data or not all(isinstance(v, str) for v in data):
        raise RealProofError("Questions JSON must be a non-empty array of strings")
    return [str(v).strip() for v in data if str(v).strip()]


def validate_profile_path(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise RealProofError(f"Candidate profile not found: {path}")

    # Content-level check: compare sha256 against known example candidate profiles (RP14-T4)
    repo_root = Path(__file__).resolve().parent.parent
    example_files = list((repo_root / "config").glob("*example*.yaml"))
    target_sha = sha256_file(path)
    for eg in example_files:
        if eg.is_file() and sha256_file(eg) == target_sha:
            raise RealProofError(
                f"Candidate profile content matches repository example file ({eg.name}); "
                "real private profile is required for REAL_PROOF"
            )

    lowered = str(path).lower()
    if "candidate_profile.example" in lowered or path.name.endswith(".example.yaml"):
        raise RealProofError("Example candidate profile is forbidden for REAL_PROOF")
    if "pytest" in lowered or "tmp" in path.parts:
        raise RealProofError("Temporary/test candidate profile path is forbidden for REAL_PROOF")


def validate_job(job: JobModel, questions: list[str] | None = None) -> None:
    if not job.company or not job.company.normalized_name or job.company.normalized_name == "Unknown":
        raise RealProofError("Job must have a real company")
    if not job.normalized_title:
        raise RealProofError("Job must have a real title")
    if not job.description_text or len(job.description_text.strip()) < 100:
        raise RealProofError("Job must contain a real non-trivial description")
    if not job.sources:
        raise RealProofError("Job must contain at least one public source record")
    url = job.apply_url
    if not url or not url.startswith(("https://", "http://")):
        raise RealProofError("Job must have a public HTTP(S) apply/source URL")
    lowered = url.lower()
    if "localhost" in lowered or "example." in lowered:
        raise RealProofError("Job source URL appears synthetic/local")

    # Check source attestation and question binding (RP14-T3)
    if questions is not None:
        expected_questions_sha = compute_questions_sha256(questions)
        greenhouse_sources = [s for s in job.sources if s.provider == "GREENHOUSE"]
        if not greenhouse_sources:
            raise RealProofError("Job does not have an imported GREENHOUSE source record")
        
        gh_source = greenhouse_sources[0]
        payload = gh_source.source_payload_json or {}
        source_questions_sha = payload.get("question_list_sha256")
        if not source_questions_sha:
            raise RealProofError(
                "Greenhouse source payload missing question_list_sha256 attestation"
            )
        if source_questions_sha.lower() != expected_questions_sha.lower():
            raise RealProofError(
                f"Question list SHA-256 mismatch against Greenhouse source attestation: "
                f"{expected_questions_sha} != {source_questions_sha}"
            )


def job_snapshot(job: JobModel) -> dict[str, Any]:
    return {
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


def get_artifact(session: Session, artifact_id: uuid.UUID | None, label: str) -> ArtifactModel:
    if artifact_id is None:
        raise RealProofError(f"Packet has no {label} artifact ID")
    artifact = session.get(ArtifactModel, artifact_id)
    if artifact is None:
        raise RealProofError(f"{label} artifact row not found: {artifact_id}")
    path = resolve_storage_path(artifact.storage_uri)
    if not path.exists():
        raise RealProofError(f"{label} artifact bytes not found: {path}")
    if sha256_file(path) != artifact.sha256:
        raise RealProofError(f"{label} artifact read-back SHA mismatch")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True, help="Existing real JobModel UUID")
    parser.add_argument(
        "--candidate-profile",
        required=True,
        type=Path,
        help="Private real candidate profile YAML path. Example YAML is rejected.",
    )
    parser.add_argument(
        "--questions-json",
        required=True,
        type=Path,
        help="JSON array of real application questions captured from the public posting.",
    )
    parser.add_argument(
        "--redacted-output-dir",
        type=Path,
        default=Path("coordination/proofs"),
    )
    parser.add_argument(
        "--private-output-dir",
        type=Path,
        default=Path(".local/proofs"),
    )
    args = parser.parse_args()

    try:
        validate_profile_path(args.candidate_profile)
        questions = load_real_questions(args.questions_json)

        loader = ConfigLoader("config")
        profile, loaded_profile_path = loader.load_candidate_profile(args.candidate_profile)
        if loaded_profile_path.resolve() != args.candidate_profile.resolve():
            raise RealProofError("Loaded candidate profile path does not match requested private path")

        session_factory = get_sessionmaker()
        with session_factory() as session:
            try:
                job_uuid = uuid.UUID(args.job_id)
            except ValueError as exc:
                raise RealProofError("--job-id must be a valid UUID") from exc

            job = session.get(JobModel, job_uuid)
            if job is None:
                raise RealProofError(f"Job not found in configured database: {job_uuid}")
            validate_job(job, questions=questions)

            variant_name = ResumeVariantSelector.select_variant(job)
            source_path_raw = profile.resume.resolve_source_path(variant_name)
            if not source_path_raw:
                raise RealProofError(
                    f"Real profile cannot resolve resume source for selected variant {variant_name}"
                )
            source_path = Path(source_path_raw).expanduser().resolve()
            source_lower = str(source_path).lower()
            if not source_path.exists() or not source_path.is_file():
                raise RealProofError(f"Real resume source not found: {source_path}")
            if "test_resume" in source_lower or "pytest" in source_lower:
                raise RealProofError("Test/fixture resume source is forbidden for REAL_PROOF")

            resume_source_sha = sha256_file(source_path)
            resume_source_byte_count = source_path.stat().st_size

            proof_run_id = str(uuid.uuid4())
            artifact_root = args.private_output_dir / "artifacts" / proof_run_id
            artifact_store = ArtifactStore(artifact_root)
            gateway = DeterministicModelGateway()

            builder = ApplicationPacketBuilder(
                session=session,
                candidate_profile=profile,
                model_gateway=gateway,
                artifact_store=artifact_store,
            )
            packet, result = builder.build_packet(job=job, questions=questions)
            session.commit()

            if result.generation_origin.lower() in {"mock", "test", "adversarial_mock"}:
                raise RealProofError(
                    f"Packet generation origin is not real/deterministic: {result.generation_origin}"
                )

            resume_artifact = get_artifact(session, packet.resume_artifact_id, "resume")
            cover_letter_artifact = get_artifact(
                session, packet.cover_letter_artifact_id, "cover-letter"
            )
            manifest_path = resolve_storage_path(result.manifest_artifact_uri)
            if not manifest_path.exists():
                raise RealProofError("Packet manifest bytes are missing")
            manifest_sha = sha256_file(manifest_path)

            snapshot = job_snapshot(job)
            snapshot_json = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
            job_snapshot_sha = sha256_bytes(snapshot_json.encode("utf-8"))

            code_sha = get_git_sha()
            unresolved = list(result.unresolved_questions)

            # RP14-T1: Runner outputs REAL_PROOF_CANDIDATE.
            # RP14-T6: Unambiguous deterministic generation labeling.
            redacted: dict[str, Any] = {
                "result": "REAL_PROOF_CANDIDATE",
                "proof_run_id": proof_run_id,
                "run_timestamp_utc": packet.created_at.isoformat(),
                "code_commit_sha": code_sha,
                "job_url": job.apply_url,
                "job_title": job.normalized_title,
                "company": job.company.normalized_name if job.company else "Unknown",
                "job_snapshot_sha256": job_snapshot_sha,
                "candidate_profile_source_class": "PRIVATE_LOCAL",
                "candidate_profile_version": profile.version,
                "candidate_unresolved_fact_categories": {
                    key: len(values)
                    for key, values in profile.check_unresolved_facts().items()
                    if values
                },
                "resume_family": result.resume_family,
                "resume_variant": result.resume_variant_name,
                "resume_version": (
                    packet.resume_variant.version if packet.resume_variant is not None else 1
                ),
                "resume_source_sha256": resume_source_sha,
                "resume_source_byte_count": resume_source_byte_count,
                "model_provider": None,
                "model_name": "DeterministicModelGateway",
                "model_origin": "deterministic",
                "generation_origin": result.generation_origin,
                "generation_engine": "deterministic-canonical-renderer",
                "packet_id": str(packet.id),
                "packet_hash": packet.packet_hash,
                "resume_artifact_sha256": resume_artifact.sha256,
                "cover_letter_artifact_sha256": cover_letter_artifact.sha256,
                "manifest_sha256": manifest_sha,
                "is_live_ready": packet.is_live_ready,
                "resolved_answers_count": result.resolved_answers_count,
                "unresolved_questions": unresolved,
                "questions_count": len(questions),
                "read_back_verification": True,
                "mock_or_fixture_inputs_present": False,
            }

            args.private_output_dir.mkdir(parents=True, exist_ok=True)
            args.redacted_output_dir.mkdir(parents=True, exist_ok=True)

            redacted_content = json.dumps(redacted, indent=2, sort_keys=True) + "\n"
            candidate_bundle_sha = sha256_bytes(redacted_content.encode("utf-8"))

            private_bundle = {
                "proof_run_id": proof_run_id,
                "candidate_bundle_sha256": candidate_bundle_sha,
                "candidate_profile_sha256": sha256_file(args.candidate_profile),
                "candidate_profile_path": str(args.candidate_profile.resolve()),
                "resume_source_path": str(source_path),
                "questions_json_path": str(args.questions_json.resolve()),
                "local_artifacts": [
                    {
                        "type": "resume_source",
                        "path": str(source_path),
                        "sha256": resume_source_sha,
                    },
                    {
                        "type": "resume_artifact",
                        "path": str(resolve_storage_path(resume_artifact.storage_uri)),
                        "sha256": resume_artifact.sha256,
                    },
                    {
                        "type": "cover_letter_artifact",
                        "path": str(resolve_storage_path(cover_letter_artifact.storage_uri)),
                        "sha256": cover_letter_artifact.sha256,
                    },
                    {
                        "type": "manifest",
                        "path": str(manifest_path),
                        "sha256": manifest_sha,
                    },
                ],
            }

            redacted_path = args.redacted_output_dir / f"v14_real_proof_{proof_run_id}.json"
            private_path = args.private_output_dir / f"v14_real_proof_{proof_run_id}_private.json"

            redacted_path.write_text(redacted_content, encoding="utf-8")
            private_path.write_text(
                json.dumps(private_bundle, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            print("REAL_PROOF_RUN_COMPLETE")
            print(f"candidate_bundle={redacted_path}")
            print(f"candidate_bundle_sha256={candidate_bundle_sha}")
            print(f"private_bundle={private_path}")
            print(f"packet_id={packet.id}")
            print(f"packet_hash={packet.packet_hash}")
            print(f"generation_origin={result.generation_origin}")
            print(f"is_live_ready={packet.is_live_ready}")
            print(f"resolved_answers_count={result.resolved_answers_count}")
            print(f"unresolved_questions_count={len(unresolved)}")

        return 0
    except (OSError, json.JSONDecodeError, RealProofError) as exc:
        print(f"REAL_PROOF_RUN_FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Application packet builder creating reproducible, versioned application packets with exact attribution."""

from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jobs_automation.core.job_search import JobSearchConfig

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import CandidateProfileConfig
from jobs_automation.db.models import (
    ApplicationPacketModel,
    ArtifactModel,
    JobModel,
    ResumeVariantModel,
    TaskModel,
)
from jobs_automation.preparation.tailoring import (
    CoverLetterDrafter,
    ResumeVariantSelector,
    ScreeningQuestionAnsweringService,
)
from jobs_automation.proof.profile_fingerprint import candidate_profile_fingerprint
from jobs_automation.storage.artifact_store import ArtifactStore


def compute_canonical_packet_hash(
    job_id: str | uuid.UUID,
    profile_version: int | str,
    resume_variant_id: str | uuid.UUID | None,
    resume_sha: str,
    cover_letter_sha: str | None,
    answers: dict[str, Any] | None,
    answer_provenance: dict[str, Any] | None,
) -> str:
    """Compute the deterministic SHA-256 identity of an application packet payload.

    The payload shape is the canonical packet-hash contract shared by packet
    preparation, the assisted-browser pre-write revalidation and the real-proof
    verifier. For fully populated inputs the digest is byte-identical to the original
    inline formula; ``None`` inputs are normalized (``""`` variant, ``{}`` maps) instead
    of hashing the literal string ``"None"``.
    """
    payload = {
        "job_id": str(job_id),
        "profile_version": profile_version,
        "resume_variant_id": str(resume_variant_id) if resume_variant_id else "",
        "resume_sha": resume_sha,
        "cover_letter_sha": cover_letter_sha,
        "answers": answers or {},
        "answer_provenance": answer_provenance or {},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def compute_questions_sha256(questions: list[str]) -> str:
    """Compute canonical SHA-256 hash of application questions list."""
    serialized = json.dumps(questions, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class PacketBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    job_id: str
    packet_hash: str
    resume_variant_id: str
    resume_variant_name: str
    resume_variant: str = ""
    resume_family: str = ""
    resume_artifact_uri: str
    resume_artifact_sha256: str
    cover_letter_artifact_uri: str
    cover_letter_artifact_sha256: str
    manifest_artifact_uri: str
    is_live_ready: bool = False
    generation_origin: str = "mock"
    has_unresolved_questions: bool
    unresolved_questions: list[str] = Field(default_factory=list)
    resolved_answers_count: int = 0
    answer_provenance: dict[str, Any] = Field(default_factory=dict)


class ApplicationPacketBuilder:
    """Assembles reproducible, immutable application packets with exact resume attribution."""

    def __init__(
        self,
        session: Session,
        candidate_profile: CandidateProfileConfig,
        model_gateway: ModelGateway,
        artifact_store: ArtifactStore | None = None,
        config: JobSearchConfig | None = None,
    ) -> None:
        self.session = session
        self.profile = candidate_profile
        self.gateway = model_gateway
        self.artifact_store = artifact_store or ArtifactStore("artifacts")
        self.cover_letter_drafter = CoverLetterDrafter(model_gateway)
        self.question_service = ScreeningQuestionAnsweringService(model_gateway)
        self.config = config

    def build_packet(
        self,
        job: JobModel,
        questions: list[str] | None = None,
        matched_role_family: str | None = None,
    ) -> tuple[ApplicationPacketModel, PacketBuildResult]:
        """Build a complete versioned packet for a shortlisted job.

        Fails closed:
        - If the exact selected resume variant cannot be resolved to a source file, raises FileNotFoundError.
        - Never synthesizes stub resumes.
        - Materializes and verifies SHA-256 for all stored artifacts.
        """
        # 1. Select targeted resume variant and resolve exact source path (J14-01, J14-02)
        variant_name = ResumeVariantSelector.select_variant(job, matched_role_family, session=self.session, config=self.config)
        source_path = self.profile.resume.resolve_source_path(variant_name)

        if not source_path:
            raise FileNotFoundError(
                f"Selected resume variant '{variant_name}' cannot be resolved to any configured source in candidate profile. "
                f"Operational packet building fails closed."
            )

        path_obj = Path(source_path)
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(
                f"Configured resume source file for variant '{variant_name}' does not exist on disk: '{source_path}'"
            )

        resume_content = path_obj.read_text(encoding="utf-8")

        # 2. Materialize Resume Artifact & Verify Read-back Hash (J14-05)
        resume_filename = f"{variant_name}_{job.id}.md"
        resume_uri, resume_sha, resume_size = self.artifact_store.store(
            content=resume_content,
            artifact_type="resumes",
            filename=resume_filename,
        )

        resume_artifact = ArtifactModel(
            type="resume",
            storage_uri=resume_uri,
            sha256=resume_sha,
            metadata_json={
                "variant": variant_name,
                "job_id": str(job.id),
                "source_path": str(source_path),
                "size_bytes": resume_size,
            },
        )
        self.session.add(resume_artifact)
        self.session.flush()

        # 3. Create Immutable ResumeVariant Record with Exact Family Attribution (R14-02)
        resume_family = ResumeVariantSelector.get_resume_family(variant_name, self.profile)
        resume_variant = ResumeVariantModel(
            resume_family=resume_family,
            name=variant_name,
            version=1,
            source_reference=str(source_path),
            target_job_id=job.id,
            target_role_family=matched_role_family,
            tailoring_method="base",
            content_hash=resume_sha,
        )
        self.session.add(resume_variant)
        self.session.flush()

        # 4. Draft and Materialize Cover Letter (J14-05, J14-06)
        cover_letter_text, cl_metadata = self.cover_letter_drafter.draft_with_metadata(
            job, self.profile
        )
        cl_filename = f"{job.id}.txt"
        cl_uri, cl_sha, cl_size = self.artifact_store.store(
            content=cover_letter_text,
            artifact_type="cover_letters",
            filename=cl_filename,
        )

        cl_artifact = ArtifactModel(
            type="cover_letter",
            storage_uri=cl_uri,
            sha256=cl_sha,
            metadata_json={
                "job_id": str(job.id),
                "company": job.company.normalized_name if job.company else None,
                "size_bytes": cl_size,
            },
        )
        self.session.add(cl_artifact)
        self.session.flush()

        # 5. Resolve Questions with Provenance (J14-08, J14-09, R14-04)
        answers: dict[str, str] = {}
        answer_provenance: dict[str, Any] = {}
        unresolved: list[str] = []
        if questions:
            answers, answer_provenance, unresolved = self.question_service.resolve_questions(
                questions, self.profile
            )

        # 6. Determine Generation Origin and Live-Readiness Gate (R14-03)
        # Check origins across model gateway, cover letter drafter, and question answering
        is_mock_gateway = type(self.gateway).__name__ in ("MockModelGateway", "HallucinatingModelGateway")
        cl_origin = cl_metadata.get("origin", "mock" if is_mock_gateway else "real")

        mock_answer_found = any(
            str(p.get("model_origin", "")).lower() in ("mock", "test", "adversarial_mock")
            for p in answer_provenance.values()
        )

        if is_mock_gateway or cl_origin in ("mock", "test", "adversarial_mock") or mock_answer_found:
            generation_origin = "mock"
        elif cl_origin == "real" or any(p.get("method") == "model_assisted" for p in answer_provenance.values()):
            generation_origin = "real"
        else:
            generation_origin = "deterministic"

        # Explicit mock/test generation origin may NEVER create a live-ready packet.
        # Live readiness requires non-mock generation origin AND zero unresolved questions.
        is_live_ready = bool(
            generation_origin not in ("mock", "test", "adversarial_mock")
            and not unresolved
        )

        # 7. Deterministic Packet Hash
        packet_hash = compute_canonical_packet_hash(
            job_id=str(job.id),
            profile_version=self.profile.version,
            resume_variant_id=str(resume_variant.id),
            resume_sha=resume_sha,
            cover_letter_sha=cl_sha,
            answers=answers,
            answer_provenance=answer_provenance,
        )

        # The parsed-profile fingerprint binds this packet to the exact candidate
        # facts it was generated from; the real-proof verifier recomputes it from the
        # profile file and compares it with this persisted value.
        profile_fingerprint = candidate_profile_fingerprint(self.profile)

        # 8. Persist ApplicationPacketModel with ResumeVariant Linkage and Readiness
        packet = ApplicationPacketModel(
            job_id=job.id,
            candidate_profile_version=self.profile.version,
            resume_variant_id=resume_variant.id,
            resume_artifact_id=resume_artifact.id,
            cover_letter_artifact_id=cl_artifact.id,
            answers_json=answers,
            answer_provenance_json=answer_provenance,
            unresolved_questions_json=unresolved,
            packet_hash=packet_hash,
            is_live_ready=is_live_ready,
            generation_metadata_json={
                "generation_origin": generation_origin,
                "cover_letter_origin": cl_origin,
                "cover_letter_model": cl_metadata.get("model"),
                "candidate_profile_fingerprint_sha256": profile_fingerprint,
            },
        )
        self.session.add(packet)
        self.session.flush()

        # 9. Materialize Machine-Readable Packet Manifest (J14-10, R14-02, R14-03)
        manifest_data = {
            "packet_id": str(packet.id),
            "job_id": str(job.id),
            "company": job.company.normalized_name if job.company else "Unknown",
            "title": job.normalized_title,
            "candidate_profile_version": self.profile.version,
            "candidate_profile_fingerprint_sha256": profile_fingerprint,
            "resume_family": resume_family,
            "resume_variant_id": str(resume_variant.id),
            "resume_variant_name": variant_name,
            "resume_source_reference": str(source_path),
            "resume_artifact_uri": resume_uri,
            "resume_artifact_sha256": resume_sha,
            "cover_letter_artifact_uri": cl_uri,
            "cover_letter_artifact_sha256": cl_sha,
            "answers": answers,
            "answer_provenance": answer_provenance,
            "unresolved_questions": unresolved,
            "generation_origin": generation_origin,
            "is_live_ready": is_live_ready,
            "packet_hash": packet_hash,
            "created_at": packet.created_at.isoformat(),
        }
        manifest_uri, _, _ = self.artifact_store.store(
            content=json.dumps(manifest_data, indent=2),
            artifact_type="packets",
            filename=f"manifest_{packet.id}.json",
        )

        # 10. Check unresolved questions and route to task if needed
        if unresolved:
            task = TaskModel(
                task_type="NEEDS_REVIEW",
                status="pending",
                payload_json={
                    "reason": f"Packet has {len(unresolved)} unresolved question(s)",
                    "job_id": str(job.id),
                    "packet_id": str(packet.id),
                    "unresolved_questions": unresolved,
                },
            )
            self.session.add(task)
            job.status = "packet_prepared_review_needed"
        else:
            job.status = "packet_prepared"

        self.session.flush()

        result = PacketBuildResult(
            packet_id=str(packet.id),
            job_id=str(job.id),
            packet_hash=packet_hash,
            resume_variant_id=str(resume_variant.id),
            resume_variant_name=variant_name,
            resume_variant=variant_name,
            resume_family=resume_family,
            resume_artifact_uri=resume_uri,
            resume_artifact_sha256=resume_sha,
            cover_letter_artifact_uri=cl_uri,
            cover_letter_artifact_sha256=cl_sha,
            manifest_artifact_uri=manifest_uri,
            is_live_ready=is_live_ready,
            generation_origin=generation_origin,
            has_unresolved_questions=bool(unresolved),
            unresolved_questions=unresolved,
            resolved_answers_count=len(answers),
            answer_provenance=answer_provenance,
        )

        return packet, result

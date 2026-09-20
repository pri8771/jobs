"""Application packet builder creating reproducible, versioned application packets."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import CandidateProfileConfig
from jobs_automation.db.models import ApplicationPacketModel, ArtifactModel, JobModel, TaskModel
from jobs_automation.preparation.tailoring import (
    CoverLetterDrafter,
    ResumeVariantSelector,
    ScreeningQuestionAnsweringService,
)


class PacketBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    job_id: str
    packet_hash: str
    resume_variant: str
    has_unresolved_questions: bool
    unresolved_questions: list[str] = Field(default_factory=list)
    resolved_answers_count: int = 0


class ApplicationPacketBuilder:
    """Assembles reproducible application packets (resume, cover letter, question answers)."""

    def __init__(
        self,
        session: Session,
        candidate_profile: CandidateProfileConfig,
        model_gateway: ModelGateway,
    ) -> None:
        self.session = session
        self.profile = candidate_profile
        self.gateway = model_gateway
        self.cover_letter_drafter = CoverLetterDrafter(model_gateway)
        self.question_service = ScreeningQuestionAnsweringService(model_gateway)

    def build_packet(
        self,
        job: JobModel,
        questions: list[str] | None = None,
        matched_role_family: str | None = None,
    ) -> tuple[ApplicationPacketModel, PacketBuildResult]:
        """Build a complete versioned packet for a shortlisted job."""
        # 1. Select targeted resume variant
        variant_name = ResumeVariantSelector.select_variant(job, matched_role_family)
        resume_content: str | None = None
        from pathlib import Path
        for rpath in self.profile.resume.base_resume_paths:
            p = Path(rpath)
            if p.exists() and p.is_file():
                resume_content = p.read_text(encoding="utf-8")
                break

        if not resume_content:
            resume_content = f"# Resume Variant: {variant_name}\nCandidate: {self.profile.identity.full_name}\nTarget: {job.normalized_title}\n"

        resume_sha = hashlib.sha256(resume_content.encode("utf-8")).hexdigest()

        resume_artifact = ArtifactModel(
            type="resume",
            storage_uri=f"file:///artifacts/resumes/{variant_name}_{job.id}.md",
            sha256=resume_sha,
            metadata_json={"variant": variant_name, "job_id": str(job.id)},
        )
        self.session.add(resume_artifact)
        self.session.flush()

        # 2. Draft Cover Letter
        cover_letter_text = self.cover_letter_drafter.draft(job, self.profile)
        cl_sha = hashlib.sha256(cover_letter_text.encode("utf-8")).hexdigest()

        cl_artifact = ArtifactModel(
            type="cover_letter",
            storage_uri=f"file:///artifacts/cover_letters/{job.id}.txt",
            sha256=cl_sha,
            metadata_json={
                "job_id": str(job.id),
                "company": job.company.normalized_name if job.company else None,
            },
        )
        self.session.add(cl_artifact)
        self.session.flush()

        # 3. Resolve Questions
        answers: dict[str, str] = {}
        unresolved: list[str] = []
        if questions:
            answers, unresolved = self.question_service.resolve_questions(questions, self.profile)

        # 4. Deterministic Packet Hash
        packet_payload = {
            "job_id": str(job.id),
            "profile_version": self.profile.version,
            "resume_sha": resume_sha,
            "cover_letter_sha": cl_sha,
            "answers": answers,
        }
        packet_hash = hashlib.sha256(
            json.dumps(packet_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # 5. Persist ApplicationPacketModel
        packet = ApplicationPacketModel(
            job_id=job.id,
            candidate_profile_version=self.profile.version,
            resume_artifact_id=resume_artifact.id,
            cover_letter_artifact_id=cl_artifact.id,
            answers_json=answers,
            unresolved_questions_json=unresolved,
            packet_hash=packet_hash,
        )
        self.session.add(packet)
        self.session.flush()

        # 6. Check unresolved questions
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
            resume_variant=variant_name,
            has_unresolved_questions=bool(unresolved),
            unresolved_questions=unresolved,
            resolved_answers_count=len(answers),
        )

        return packet, result

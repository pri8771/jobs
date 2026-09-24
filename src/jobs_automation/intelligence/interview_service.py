"""InterviewIntelligenceService — Interview briefs, story maps, and follow-up packages (V23-II-03..05)."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    MessageLinkModel,
)
from jobs_automation.evaluation.scorer import SemanticScorer
from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.intelligence.candidate_evidence import CandidateEvidenceService
from jobs_automation.intelligence.interview import (
    CandidateStoryMap,
    FollowupPackage,
    InterviewBrief,
    PersonRef,
    RequirementRef,
    StalenessReport,
    StoryMapEntry,
)
from jobs_automation.core.untrusted_text import detect_prompt_injection_signals


class InterviewIntelligenceService:
    """Service for composing interview briefs, candidate story maps, and follow-up packages."""

    def __init__(
        self,
        session: Session,
        evidence_service: CandidateEvidenceService | None = None,
        scorer: SemanticScorer | None = None,
    ) -> None:
        self.session = session
        self.evidence_service = evidence_service
        self.scorer = scorer

    def build_brief(
        self,
        application_id: uuid.UUID | str,
        as_of: datetime.datetime | None = None,
    ) -> InterviewBrief:
        """Build a comprehensive, evidence-backed InterviewBrief for an application."""
        app_uuid = uuid.UUID(str(application_id))
        app = self.session.get(ApplicationModel, app_uuid)
        if not app:
            raise LookupError(f"Application not found: {application_id}")

        job = app.job
        if not job:
            raise LookupError(f"Job not found for application: {application_id}")

        company = job.company

        # 1. Fetch latest interview record if present
        latest_interview = self.session.scalars(
            select(InterviewModel)
            .where(InterviewModel.application_id == app.id)
            .order_by(InterviewModel.scheduled_start.desc())
        ).first()

        interview_stage = (
            latest_interview.status
            if latest_interview and latest_interview.status in ("scheduled", "rescheduling_needed", "cancelled")
            else app.status
        )

        scheduled_start = latest_interview.scheduled_start if latest_interview else None
        scheduled_end = latest_interview.scheduled_end if latest_interview else None
        tz = latest_interview.timezone if latest_interview else None
        interview_id_str = str(latest_interview.id) if latest_interview else None

        # 2. Extract people (contacts linked via MessageLinkModel to this application)
        msg_links = list(
            self.session.scalars(
                select(MessageLinkModel).where(
                    MessageLinkModel.application_id == app.id,
                    MessageLinkModel.contact_id.isnot(None),
                )
            ).all()
        )
        people: list[PersonRef] = []
        seen_contacts: set[uuid.UUID] = set()
        for ml in msg_links:
            if ml.contact_id and ml.contact_id not in seen_contacts:
                seen_contacts.add(ml.contact_id)
                contact = self.session.get(ContactModel, ml.contact_id)
                if contact:
                    people.append(
                        PersonRef(
                            name=contact.name,
                            email_fingerprint=contact.email,
                            role=contact.role,
                            evidence_refs=[
                                EvidenceRef(ref_type="contact", ref_id=str(contact.id)),
                                EvidenceRef(ref_type="message_link", ref_id=str(ml.id)),
                            ],
                        )
                    )

        # 3. Role summary & requirements
        role_summary = f"{job.normalized_title} at {company.normalized_name if company else 'Unknown'}"
        req_refs: list[RequirementRef] = []
        if self.scorer:
            extracted = self.scorer.extract_requirements(job)
            source_ref = EvidenceRef(
                ref_type="job",
                ref_id=str(job.id),
                note=f"sha256:{job.description_hash}" if job.description_hash else None,
            )
            for phrase, skills in extracted:
                req_refs.append(
                    RequirementRef(
                        text=phrase,
                        source_ref=source_ref,
                        matched_skills=skills,
                    )
                )

        # 4. Candidate Story Map
        story_map = self.build_story_map(req_refs) if req_refs else None

        # 5. Staleness report
        staleness = StalenessReport()
        if app.packet_id:
            packet = self.session.get(ApplicationPacketModel, app.packet_id)
            if packet and packet.generation_metadata_json:
                gen_hash = packet.generation_metadata_json.get("job_description_hash")
                if gen_hash and job.description_hash and gen_hash != job.description_hash:
                    staleness.is_stale = True
                    staleness.reasons.append("Job description hash changed since packet preparation")

        # 6. Conflicts & review items
        conflicts: list[str] = []
        all_interviews = list(
            self.session.scalars(
                select(InterviewModel).where(InterviewModel.application_id == app.id)
            ).all()
        )
        if len([i for i in all_interviews if i.status == "scheduled"]) > 1:
            conflicts.append("Multiple active scheduled interviews exist for this application")
        if latest_interview and latest_interview.status == "rescheduling_needed":
            conflicts.append("Interview requires rescheduling")

        # 7. Security signals (prompt injection in job description or message bodies)
        security_signals: list[str] = []
        if job.description_text:
            signals = detect_prompt_injection_signals(job.description_text, context="job_description")
            for s in signals:
                security_signals.append(f"Prompt injection signal in JD [{s.pattern_id}]: {s.excerpt}")

        source_refs = [
            EvidenceRef(ref_type="application", ref_id=str(app.id)),
            EvidenceRef(ref_type="job", ref_id=str(job.id)),
        ]
        if company:
            source_refs.append(EvidenceRef(ref_type="company", ref_id=str(company.id)))

        return InterviewBrief(
            artifact_type="interview_brief",
            generated_at=utc_now(),
            generator="InterviewIntelligenceService",
            generator_version="2.3",
            source_refs=source_refs,
            application_id=str(app.id),
            job_id=str(job.id),
            company_id=str(company.id) if company else "",
            interview_id=interview_id_str,
            interview_stage=interview_stage,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            timezone=tz,
            people=people,
            role_summary=role_summary,
            key_requirements=req_refs,
            candidate_evidence_map=story_map,
            staleness=staleness,
            conflicts=conflicts,
            security_signals=security_signals,
            confidence="HIGH" if req_refs else "MEDIUM",
        )

    def build_story_map(self, requirements: list[RequirementRef]) -> CandidateStoryMap:
        """Build CandidateStoryMap linking requirements to candidate evidence claims."""
        entries: list[StoryMapEntry] = []

        for req in requirements:
            allowed_claims: list[str] = []
            unsupported_claims: list[str] = []
            confidence: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
            evidence_refs = []

            if self.evidence_service:
                result = self.evidence_service.evidence_for_requirement(req.text)
                evidence_refs = result.evidence_refs
                if result.has_evidence and result.evidence_claims:
                    allowed_claims = result.evidence_claims
                    confidence = "HIGH"
                else:
                    unsupported_claims = [req.text]
            else:
                unsupported_claims = [req.text]

            entries.append(
                StoryMapEntry(
                    requirement=req,
                    evidence_refs=evidence_refs,
                    allowed_claims=allowed_claims,
                    unsupported_claims_to_avoid=unsupported_claims,
                    confidence=confidence,
                )
            )

        return CandidateStoryMap(
            artifact_type="candidate_story_map",
            generated_at=utc_now(),
            generator="InterviewIntelligenceService",
            generator_version="2.3",
            source_refs=[],
            entries=entries,
        )

    def build_followup(
        self,
        application_id: uuid.UUID | str,
        contact_id: uuid.UUID | str | None = None,
    ) -> FollowupPackage:
        """Build a FollowupPackage for an application."""
        app_uuid = uuid.UUID(str(application_id))
        app = self.session.get(ApplicationModel, app_uuid)
        if not app:
            raise LookupError(f"Application not found: {application_id}")

        contact_refs: list[EvidenceRef] = []
        if contact_id:
            contact_refs.append(EvidenceRef(ref_type="contact", ref_id=str(contact_id)))

        latest_interview = self.session.scalars(
            select(InterviewModel)
            .where(InterviewModel.application_id == app.id)
            .order_by(InterviewModel.scheduled_start.desc())
        ).first()

        facts: list[dict[str, Any]] = [
            {"fact": f"Application status is {app.status}", "evidence_ref": f"application:{app.id}"}
        ]
        unresolved: list[str] = []

        if latest_interview:
            facts.append({
                "fact": f"Interview scheduled for {latest_interview.scheduled_start}",
                "evidence_ref": f"interview:{latest_interview.id}",
            })
        else:
            unresolved.append("No specific interview schedule evidence found")

        draft_inputs = {
            "application_id": str(app.id),
            "stage": app.status,
            "topics_discussed": "unknown",
        }

        return FollowupPackage(
            artifact_type="followup_package",
            generated_at=utc_now(),
            generator="InterviewIntelligenceService",
            generator_version="2.3",
            source_refs=[EvidenceRef(ref_type="application", ref_id=str(app.id))],
            application_id=str(app.id),
            contact_refs=contact_refs,
            stage_context=f"Follow-up for {app.status} stage",
            facts=facts,
            draft_inputs=draft_inputs,
            unresolved_facts=unresolved,
            send_performed=False,
        )

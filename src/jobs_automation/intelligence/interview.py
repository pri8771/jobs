"""V23 Interview Intelligence typed data models (V23-II-01)."""

from __future__ import annotations

import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from jobs_automation.intelligence.envelope import DerivedArtifactEnvelope, EvidenceRef
from jobs_automation.intelligence.candidate_evidence import CandidateEvidenceRef


class PersonRef(BaseModel):
    name: str
    email_fingerprint: str | None = None
    role: str | None = None
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class RequirementRef(BaseModel):
    text: str
    source_ref: EvidenceRef
    matched_skills: list[str] = Field(default_factory=list)


class StoryMapEntry(BaseModel):
    requirement: RequirementRef
    evidence_refs: list[CandidateEvidenceRef] = Field(default_factory=list)
    allowed_claims: list[str] = Field(default_factory=list)
    unsupported_claims_to_avoid: list[str] = Field(default_factory=list)
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"


class CandidateStoryMap(DerivedArtifactEnvelope):
    artifact_type: Literal["candidate_story_map"] = "candidate_story_map"
    entries: list[StoryMapEntry] = Field(default_factory=list)


class StalenessReport(BaseModel):
    is_stale: bool = False
    reasons: list[str] = Field(default_factory=list)


class InterviewBrief(DerivedArtifactEnvelope):
    artifact_type: Literal["interview_brief"] = "interview_brief"
    application_id: str
    job_id: str
    company_id: str
    interview_id: str | None = None
    interview_stage: str
    scheduled_start: datetime.datetime | None = None
    scheduled_end: datetime.datetime | None = None
    timezone: str | None = None
    people: list[PersonRef] = Field(default_factory=list)
    role_summary: str = ""
    key_requirements: list[RequirementRef] = Field(default_factory=list)
    candidate_evidence_map: CandidateStoryMap | None = None
    likely_question_areas: list[str] = Field(default_factory=list)
    risk_gap_areas: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    staleness: StalenessReport = Field(default_factory=StalenessReport)
    conflicts: list[str] = Field(default_factory=list)
    security_signals: list[str] = Field(default_factory=list)


class FollowupPackage(DerivedArtifactEnvelope):
    artifact_type: Literal["followup_package"] = "followup_package"
    application_id: str
    contact_refs: list[EvidenceRef] = Field(default_factory=list)
    stage_context: str = ""
    facts: list[dict[str, Any]] = Field(default_factory=list)
    draft_inputs: dict[str, str] = Field(default_factory=dict)
    unresolved_facts: list[str] = Field(default_factory=list)
    send_performed: Literal[False] = False

    @field_validator("send_performed")
    @classmethod
    def validate_send_performed(cls, val: bool) -> bool:
        if val is not False:
            raise ValueError("send_performed must always be False")
        return False

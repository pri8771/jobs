"""V23 Career Briefing typed data models and JSON schema export (V23-CB-01)."""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Literal
from pydantic import BaseModel, Field

from jobs_automation.intelligence.envelope import DerivedArtifactEnvelope, EvidenceRef, RateWithN
from jobs_automation.intelligence.target_companies import RelationshipSignal


class DataFreshness(BaseModel):
    last_ingestion_at: datetime.datetime | None = None
    last_worker_run_at: datetime.datetime | None = None
    gmail_mode: Literal["REAL", "UNAVAILABLE", "MOCK"] = "REAL"
    last_watch_run_at: datetime.datetime | None = None


class ResumeRecommendation(BaseModel):
    variant_id: str | None = None
    family: str = "general"
    basis: Literal["selector", "strategy"] = "selector"
    rates: list[RateWithN] = Field(default_factory=list)
    action: str = "GATHER_MORE_DATA"


class OpportunityCard(BaseModel):
    job_ref: EvidenceRef
    company_ref: EvidenceRef
    title: str
    company_name: str
    score: float | None = None
    decision: str | None = None
    reasons: list[dict[str, Any]] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    relationship_signal: RelationshipSignal | None = None
    recommended_resume: ResumeRecommendation | None = None
    next_action: Literal[
        "EVALUATE",
        "PREPARE_PACKET",
        "RESOLVE_UNRESOLVED",
        "APPLY_MANUAL",
        "ASSISTED_PREFILL",
        "AWAIT_APPROVAL",
        "FOLLOW_UP",
        "NONE",
    ] = "EVALUATE"
    policy_decision: str = "MANUAL_ONLY"
    posting_age_days: int | None = None
    stale: bool = False


class CareerBriefing(DerivedArtifactEnvelope):
    artifact_type: Literal["career_briefing"] = "career_briefing"
    profile_version: int = 1
    data_freshness: DataFreshness = Field(default_factory=DataFreshness)
    top_opportunities: list[OpportunityCard] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    interviews_upcoming: list[dict[str, Any]] = Field(default_factory=list)
    followups_due: list[dict[str, Any]] = Field(default_factory=list)
    review_queue_summary: dict[str, Any] = Field(default_factory=dict)
    strategy: list[dict[str, Any]] = Field(default_factory=list)
    watch_highlights: list[dict[str, Any]] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


def export_briefing_schema(output_path: str = "docs/schemas/career_briefing.schema.json") -> str:
    """Generate and write the JSON Schema for CareerBriefing."""
    schema = CareerBriefing.model_json_schema()
    schema_json = json.dumps(schema, indent=2)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(schema_json + "\n")
    return schema_json

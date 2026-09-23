from datetime import datetime, timezone
from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator
import json
import hashlib

ConfidenceLabel = Literal["LOW", "MEDIUM", "HIGH"]

class EvidenceRef(BaseModel):
    ref_type: Literal[
        "job", "job_source", "application", "application_event", "message",
        "message_link", "contact", "company", "interview", "task",
        "artifact", "packet", "resume_variant", "evaluation", "edge",
        "observation", "experiment", "audit", "public_source", "candidate_field"
    ]
    ref_id: str
    note: str | None = None

class DerivedArtifactEnvelope(BaseModel):
    artifact_type: str
    generated_at: datetime
    generator: str
    generator_version: str
    code_sha: str | None = None
    source_refs: list[EvidenceRef]
    confidence: ConfidenceLabel | None = None
    warnings: list[str] = Field(default_factory=list)
    review_items: list[str] = Field(default_factory=list)
    valid_until: datetime | None = None
    supersedes: str | None = None
    stale: bool = False
    simulated: bool = False

class RateWithN(BaseModel):
    numerator: int
    denominator: int
    rate: float | None = None
    n: int = 0
    min_n: int = 0
    low_n: bool = False
    window_days: int | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    evidence_class: Literal["DESCRIPTIVE", "EXPERIMENTAL"] = "DESCRIPTIVE"

    @model_validator(mode="after")
    def validate_and_compute(self) -> 'RateWithN':
        if self.numerator > self.denominator:
            raise ValueError("Numerator cannot be greater than denominator")
        self.n = self.denominator
        self.low_n = self.n < self.min_n
        if self.denominator == 0:
            self.rate = None
        else:
            self.rate = round(self.numerator / self.denominator, 4)
        return self

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def canonical_json_hash(obj: Any) -> str:
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

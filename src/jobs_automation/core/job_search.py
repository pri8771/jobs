"""Job search configuration models and validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GlobalSearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    freshness_days: int = Field(gt=0, default=7)
    max_jobs_per_source_email: int = Field(gt=0, default=100)
    require_compensation: bool = False
    target_compensation_usd_min: int = Field(ge=0, default=150000)
    compensation_basis: str = Field(default="confirm_base_vs_total_comp")


class LocationCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include: list[str] = Field(default_factory=list)
    include_radius_miles: list[int] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)


class EmploymentTypeCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)


class HardRejectCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title_keywords: list[str] = Field(default_factory=list)
    company_names: list[str] = Field(default_factory=list)
    clearance_requirements: list[str] = Field(default_factory=list)
    max_travel_percent: int | None = None


class RoleFamilyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    priority: int
    enabled: bool = True
    include_titles: list[str] = Field(default_factory=list)
    include_skills: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class ScoringWeightsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title_match: int = 25
    must_have_skills: int = 25
    preferred_skills: int = 15
    compensation: int = 15
    location: int = 10
    seniority: int = 5
    freshness: int = 5

    @model_validator(mode="after")
    def verify_sum_to_100(self) -> ScoringWeightsConfig:
        total = (
            self.title_match
            + self.must_have_skills
            + self.preferred_skills
            + self.compensation
            + self.location
            + self.seniority
            + self.freshness
        )
        if total != 100:
            raise ValueError(f"Scoring weights must sum to 100, current sum is {total}")
        return self


class ScoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    threshold_shortlist: int = Field(ge=0, le=100, default=70)
    threshold_review: int = Field(ge=0, le=100, default=55)
    weights: ScoringWeightsConfig = Field(default_factory=ScoringWeightsConfig)

    @model_validator(mode="after")
    def verify_thresholds(self) -> ScoringConfig:
        if self.threshold_shortlist < self.threshold_review:
            raise ValueError(
                f"threshold_shortlist ({self.threshold_shortlist}) cannot be less than threshold_review ({self.threshold_review})"
            )
        return self



from pydantic import model_validator
from typing import Literal

class StrategyGuardrails(BaseModel):
    min_n_descriptive: int = 5
    min_n_comparison: int = 10
    min_n_per_arm: int = 5
    default_window_days: int = 90
    stale_after_days: int = 180
    
    @model_validator(mode='after')
    def validate_positive(self) -> 'StrategyGuardrails':
        if self.min_n_descriptive < 0 or self.min_n_comparison < 0 or self.min_n_per_arm < 0 or self.default_window_days < 0 or self.stale_after_days < 0:
            raise ValueError("Guardrail values cannot be negative")
        return self


class TailoringStrategyConfig(BaseModel):
    resume_strategy: Literal['highest_conversion', 'explore'] = 'highest_conversion'

class JobSearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    global_config: GlobalSearchConfig = Field(alias="global")
    locations: LocationCriteria = Field(default_factory=LocationCriteria)
    employment_types: EmploymentTypeCriteria = Field(default_factory=EmploymentTypeCriteria)
    hard_reject: HardRejectCriteria = Field(default_factory=HardRejectCriteria)
    role_families: list[RoleFamilyConfig] = Field(default_factory=list)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    strategy_guardrails: StrategyGuardrails = Field(default_factory=StrategyGuardrails)
    tailoring: TailoringStrategyConfig = Field(default_factory=TailoringStrategyConfig)

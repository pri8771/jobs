"""Policy registry configuration models and validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyDecision(StrEnum):
    MANUAL_ONLY = "manual_only"
    ASSISTED = "assisted"
    AUTO_ALLOWED = "auto_allowed"
    BLOCKED = "blocked"


class DefaultPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = "submit_application"
    decision: PolicyDecision = PolicyDecision.BLOCKED
    reason: str = "deny_by_default"

    @model_validator(mode="after")
    def verify_default_deny(self) -> DefaultPolicyConfig:
        if self.decision != PolicyDecision.BLOCKED:
            raise ValueError(
                f"Default policy decision must be 'blocked' (deny-by-default), found '{self.decision}'."
            )
        return self


class PolicyEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    domain_pattern: str
    capability: str = "submit_application"
    decision: PolicyDecision
    reviewed_at: str
    review_due_at: str | None = None
    evidence: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PolicyRegistryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    default: DefaultPolicyConfig = Field(default_factory=DefaultPolicyConfig)
    entries: list[PolicyEntryConfig] = Field(default_factory=list)

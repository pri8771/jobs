"""Model routing and gateway configuration models and validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ModelTaskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    sensitivity: str = "normal"
    fallback_models: list[str] = Field(default_factory=list)


class DefaultsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=60, gt=0)
    max_retries: int = Field(default=2, ge=0)


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_external_models_for_candidate_data: bool = True
    redact_unrelated_email_content: bool = True
    local_only_tasks: list[str] = Field(default_factory=list)


class ModelRoutingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    gateway: str = "litellm_compatible"
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    tasks: dict[str, ModelTaskConfig] = Field(default_factory=dict)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)

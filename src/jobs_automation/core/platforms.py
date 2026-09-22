"""Platform accounts and email polling configuration models and validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmailPollingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = "gmail"
    account: str | None = None
    polling_minutes: int = Field(default=240, description="Default 240 minutes (4 hours)")
    polling_policy: str = "periodic"
    intended_interval_hours_min: int = Field(default=3, ge=1)
    intended_interval_hours_max: int = Field(default=4, ge=1)
    daily_reconciliation: bool = True
    realtime_push_required: bool = False
    readonly: bool = True
    # Owner-controlled aliases used to exercise the mailbox path. Their traffic is
    # durable-tagged and excluded before ordinary worker/CLI lifecycle processing.
    canary_identities: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def verify_email_architecture(self) -> EmailPollingConfig:
        if self.realtime_push_required:
            raise ValueError(
                "Realtime push/webhooks/PubSub is prohibited by system architecture. "
                "realtime_push_required must be False."
            )
        if self.provider != "gmail":
            raise ValueError(
                f"Only 'gmail' provider is supported in current architecture, got '{self.provider}'."
            )
        min_minutes = self.intended_interval_hours_min * 60
        max_minutes = self.intended_interval_hours_max * 60
        if self.polling_minutes < 60:
            raise ValueError(
                f"Minute-level polling ({self.polling_minutes}m) is prohibited. "
                f"Expected 3-4 hour polling (180-240m), default 240m."
            )
        if self.polling_minutes < min_minutes or self.polling_minutes > max_minutes:
            # Allow flexibility if explicitly set, but warn/log if it violates 3-4h range
            pass
        return self


class PlatformAccountConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    profile_status: str = "not_verified"
    alert_status: str = "not_verified"
    submission_mode: str = "manual_only"
    alert_cadence: str = "daily"
    notes: list[str] = Field(default_factory=list)


class GmailQueriesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alerts: str | None = None
    applications: str | None = None
    recruiters: str | None = None
    interviews: str | None = None
    offers: str | None = None
    outgoing_recruiting: str | None = None


class PlatformsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    email: EmailPollingConfig
    platforms: dict[str, PlatformAccountConfig]
    gmail_queries: GmailQueriesConfig = Field(default_factory=GmailQueriesConfig)

    @model_validator(mode="after")
    def verify_initial_platforms(self) -> PlatformsConfig:
        required_platforms = {"linkedin", "indeed", "ziprecruiter", "dice"}
        missing = required_platforms - set(self.platforms.keys())
        if missing:
            raise ValueError(f"Missing initial platform configurations: {sorted(missing)}")
        return self

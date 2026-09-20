"""Candidate profile configuration models and validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IdentityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    preferred_name: str | None = None
    email: str | None = None
    phone: str | None = None
    city: str
    state: str
    country: str = "US"


class LinksConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    personal_site: str | None = None


class TargetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_headline: str
    alternate_headlines: list[str] = Field(default_factory=list)
    target_role_families: list[str] = Field(default_factory=list)
    target_compensation_usd_min: int = Field(ge=0, default=150000)
    compensation_basis: str = Field(default="confirm_base_vs_total_comp")
    remote_preference: str | None = None
    relocation: bool | None = None
    travel_percent_max: int | None = None


class PositioningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    differentiators: list[str] = Field(default_factory=list)
    avoid_positioning_as: list[str] = Field(default_factory=list)


class WorkAuthorizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorized_to_work_in_us: bool | None = None
    requires_sponsorship_now: bool | None = None
    requires_sponsorship_future: bool | None = None
    notes: str | None = None


class ExperienceRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    role: str
    start: str | None = None
    end: str | None = None


class CurrentRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    role: str
    start: str | None = None


class ExperienceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_role: CurrentRole | None = None
    roles: list[ExperienceRole] = Field(default_factory=list)


class EducationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school: str
    credential: str


class SkillsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class ResumeVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    priority: int
    emphasize: list[str] = Field(default_factory=list)


class ResumeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str = "maintain_targeted_versions"
    recommended_versions: list[ResumeVersion] = Field(default_factory=list)
    base_resume_paths: list[str] = Field(default_factory=list)
    default_resume_id: str


class ApplicationAnswersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    willing_to_relocate: bool | None = None
    willing_to_travel: bool | None = None
    notice_period_days: int | None = None
    earliest_start_date: str | None = None
    salary_expectation_text: str | None = None


class DemographicAnswersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: str = "do_not_guess"
    values: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def verify_no_guessing_policy(self) -> DemographicAnswersConfig:
        if self.policy != "do_not_guess":
            raise ValueError(f"Demographic policy must be 'do_not_guess', found '{self.policy}'.")
        return self


class CandidateProfileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    identity: IdentityConfig
    links: LinksConfig = Field(default_factory=LinksConfig)
    target: TargetConfig
    positioning: PositioningConfig
    work_authorization: WorkAuthorizationConfig = Field(default_factory=WorkAuthorizationConfig)
    experience: ExperienceConfig
    education: list[EducationItem] = Field(default_factory=list)
    skills: SkillsConfig
    resume: ResumeConfig
    application_answers: ApplicationAnswersConfig = Field(default_factory=ApplicationAnswersConfig)
    demographic_answers: DemographicAnswersConfig = Field(default_factory=DemographicAnswersConfig)
    notes: list[str] = Field(default_factory=list)

    def check_unresolved_facts(self) -> dict[str, list[str]]:
        """Identify fields that are currently unresolved (null / unknown).

        Guarantees that agents and execution engines do not silently invent facts.
        """
        missing_identity: list[str] = []
        if self.identity.email is None:
            missing_identity.append("email")
        if self.identity.phone is None:
            missing_identity.append("phone")

        unresolved_auth: list[str] = []
        if self.work_authorization.authorized_to_work_in_us is None:
            unresolved_auth.append("authorized_to_work_in_us")
        if self.work_authorization.requires_sponsorship_now is None:
            unresolved_auth.append("requires_sponsorship_now")
        if self.work_authorization.requires_sponsorship_future is None:
            unresolved_auth.append("requires_sponsorship_future")

        unresolved_target: list[str] = []
        if self.target.compensation_basis == "confirm_base_vs_total_comp":
            unresolved_target.append("compensation_basis_unconfirmed")
        if self.target.remote_preference is None:
            unresolved_target.append("remote_preference")
        if self.target.relocation is None:
            unresolved_target.append("relocation")
        if self.target.travel_percent_max is None:
            unresolved_target.append("travel_percent_max")

        unresolved_roles: list[str] = []
        for r in self.experience.roles:
            if r.start is None or r.end is None:
                unresolved_roles.append(f"{r.company} ({r.role}): dates unresolved")

        return {
            "identity": missing_identity,
            "work_authorization": unresolved_auth,
            "target": unresolved_target,
            "experience_dates": unresolved_roles,
        }

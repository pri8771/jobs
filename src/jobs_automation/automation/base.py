"""Base abstractions and types for ATS automatic application adapters."""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.db.models import ApplicationPacketModel


class ValidationResult(BaseModel):
    """Validation outcome prior to ATS submission."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    missing_fields: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    unknown_question_stop: bool = False
    message: str = "Validation passed"


class SubmissionResult(BaseModel):
    """Atomic receipt and outcome of an ATS submission."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    status: str  # SUBMITTED, STOPPED_UNKNOWN_QUESTION, RATE_LIMITED, RETRYABLE_ERROR, FATAL_ERROR, KILL_SWITCH_ACTIVE
    receipt_id: str | None = None
    confirmation_url: str | None = None
    response_payload: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime.datetime
    retry_count: int = 0
    message: str


class ATSAdapter(ABC):
    """Abstract adapter for structured direct submission to an allowlisted ATS platform."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the ATS platform (e.g. greenhouse, lever)."""
        pass

    @abstractmethod
    def can_handle(self, destination_domain: str) -> bool:
        """Returns True if this adapter can submit to the given domain."""
        pass

    @abstractmethod
    def validate_packet(
        self,
        packet: ApplicationPacketModel,
        candidate_profile: CandidateProfileConfig,
        form_schema: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validates all required fields exist and no required unknown questions are unaddressed."""
        pass

    @abstractmethod
    def submit_application(
        self,
        packet: ApplicationPacketModel,
        target_url: str,
        candidate_profile: CandidateProfileConfig,
        mock_mode: bool = False,
    ) -> SubmissionResult:
        """Executes idempotent submission and returns atomic receipt."""
        pass

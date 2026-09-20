"""Data models for raw emails, classified messages, and extracted jobs."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EmailClassification(StrEnum):
    JOB_ALERT = "JOB_ALERT"
    APPLICATION_CONFIRMATION = "APPLICATION_CONFIRMATION"
    RECRUITER_OUTREACH = "RECRUITER_OUTREACH"
    RECRUITER_FOLLOW_UP = "RECRUITER_FOLLOW_UP"
    CANDIDATE_REPLY = "CANDIDATE_REPLY"
    SCREENING_REQUEST = "SCREENING_REQUEST"
    ASSESSMENT_REQUEST = "ASSESSMENT_REQUEST"
    INTERVIEW_REQUEST = "INTERVIEW_REQUEST"
    INTERVIEW_CONFIRMATION = "INTERVIEW_CONFIRMATION"
    INTERVIEW_RESCHEDULE = "INTERVIEW_RESCHEDULE"
    INTERVIEW_CANCELLED = "INTERVIEW_CANCELLED"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    BACKGROUND_CHECK = "BACKGROUND_CHECK"
    ONBOARDING = "ONBOARDING"
    GENERAL_COMPANY_COMMUNICATION = "GENERAL_COMPANY_COMMUNICATION"
    UNKNOWN_REVIEW_REQUIRED = "UNKNOWN_REVIEW_REQUIRED"


class RawEmailMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_message_id: str
    provider_thread_id: str | None = None
    received_at: datetime.datetime
    sender: str
    recipients: list[str] = Field(default_factory=list)
    direction: str = "inbound"  # "inbound" | "outbound"
    subject: str
    headers: dict[str, Any] = Field(default_factory=dict)
    body_text: str = ""
    body_html: str | None = None
    raw_reference: str | None = None


class ExtractedJobPosting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company: str
    location: str | None = None
    remote_type: str | None = None  # "remote" | "hybrid" | "on_site"
    compensation_min: float | None = None
    compensation_max: float | None = None
    compensation_currency: str = "USD"
    job_url: str | None = None
    source_url: str | None = None
    source_job_id: str | None = None
    requisition_id: str | None = None
    source_provider: str  # "linkedin" | "indeed" | "ziprecruiter" | "dice" | "generic"
    description_snippet: str | None = None


class EmailClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: EmailClassification
    confidence: float = Field(ge=0.0, le=1.0)
    direction: str = "inbound"
    company_hint: str | None = None
    job_title_hint: str | None = None
    needs_review: bool = False
    review_reason: str | None = None

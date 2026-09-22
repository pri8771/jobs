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
    WITHDRAWAL = "WITHDRAWAL"
    GENERAL_COMPANY_COMMUNICATION = "GENERAL_COMPANY_COMMUNICATION"
    UNKNOWN_REVIEW_REQUIRED = "UNKNOWN_REVIEW_REQUIRED"


class RawEmailMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_message_id: str
    provider_thread_id: str | None = None
    # Provider-observed time (Gmail internalDate). Never the sender-claimed Date header.
    received_at: datetime.datetime
    sender: str
    recipients: list[str] = Field(default_factory=list)
    direction: str = "inbound"  # "inbound" | "outbound"
    subject: str
    headers: dict[str, Any] = Field(default_factory=dict)
    body_text: str = ""
    body_html: str | None = None
    raw_reference: str | None = None
    # Non-secret provider facts kept separate from the claimed headers: label ids,
    # internal date, claimed Date header, how direction was derived, sender address.
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class PollReport(BaseModel):
    """Completeness accounting for one adapter poll (V17-M01).

    A poll is complete only when every listed message was fetched and the result was not
    truncated by the caller's cap. An incomplete poll must never let a checkpoint advance
    past evidence that was listed but not ingested.
    """

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    since_timestamp: str | None = None
    max_results: int
    pages_fetched: int = 0
    listed_count: int = 0
    fetched_count: int = 0
    missing_message_ids: list[str] = Field(default_factory=list)
    truncated_by_cap: bool = False
    complete: bool = True
    adapter: str = "unknown"
    synthetic: bool = False


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

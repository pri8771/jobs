"""Foundational database models matching docs/DATA_MODEL.md."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from jobs_automation.db.base import Base, UTCDateTime, generate_uuid, utc_now

# Use portable JSON type that falls back to JSONB on PostgreSQL
JSONType = JSON().with_variant(JSONB, "postgresql")


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profile"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    structured_profile_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    superseded_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)


class SourceAccountModel(Base):
    __tablename__ = "source_account"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_account_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile_status: Mapped[str] = mapped_column(String(64), default="not_verified", nullable=False)
    alert_status: Mapped[str] = mapped_column(String(64), default="not_verified", nullable=False)
    last_verified_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)

    alerts: Mapped[list[SourceAlertModel]] = relationship(back_populates="account")


class SourceAlertModel(Base):
    __tablename__ = "source_alert"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_account.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    query_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    cadence: Mapped[str] = mapped_column(String(32), default="daily", nullable=False)
    email_match_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    account: Mapped[SourceAccountModel] = relationship(back_populates="alerts")


class InboundMessageModel(Base):
    __tablename__ = "inbound_message"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    provider_message_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    provider_thread_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    received_at: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipients_json: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    direction: Mapped[str] = mapped_column(
        String(16), default="inbound", nullable=False
    )  # inbound | outbound
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    headers_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    body_html_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )

    links: Mapped[list[MessageLinkModel]] = relationship(back_populates="message")


class CompanyModel(Base):
    __tablename__ = "company"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    aliases_json: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    jobs: Mapped[list[JobModel]] = relationship(back_populates="company")
    contacts: Mapped[list[ContactModel]] = relationship(back_populates="company")


class JobModel(Base):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("company.id"), nullable=True)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compensation_min: Mapped[int | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_max: Mapped[int | None] = mapped_column(Numeric(12, 2), nullable=True)
    compensation_currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    posted_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    status: Mapped[str] = mapped_column(String(64), default="discovered", nullable=False)

    company: Mapped[CompanyModel | None] = relationship(back_populates="jobs")
    sources: Mapped[list[JobSourceModel]] = relationship(back_populates="job")
    evaluations: Mapped[list[JobEvaluationModel]] = relationship(back_populates="job")
    applications: Mapped[list[ApplicationModel]] = relationship(back_populates="job")

    @property
    def apply_url(self) -> str | None:
        for s in self.sources:
            if s.canonical_apply_url:
                return s.canonical_apply_url
            if s.source_url:
                return s.source_url
        return None

    @property
    def title(self) -> str:
        return self.normalized_title

    @property
    def company_name(self) -> str:
        return self.company.normalized_name if self.company else "Unknown"


class JobSourceModel(Base):
    __tablename__ = "job_source"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_job_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    canonical_apply_url: Mapped[str | None] = mapped_column(String(1024), index=True, nullable=True)
    requisition_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    source_payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )

    job: Mapped[JobModel] = relationship(back_populates="sources")


class JobEvaluationModel(Base):
    __tablename__ = "job_evaluation"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason_codes_json: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )

    job: Mapped[JobModel] = relationship(back_populates="evaluations")


class ArtifactModel(Base):
    __tablename__ = "artifact"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )


class ApplicationPacketModel(Base):
    __tablename__ = "application_packet"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), nullable=False)
    candidate_profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    resume_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("artifact.id"), nullable=True
    )
    cover_letter_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("artifact.id"), nullable=True
    )
    answers_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    unresolved_questions_json: Mapped[list[str]] = mapped_column(
        JSONType, default=list, nullable=False
    )
    packet_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )


class ApplicationModel(Base):
    __tablename__ = "application"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="DISCOVERED", nullable=False)
    application_mode: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    destination_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_decision: Mapped[str] = mapped_column(String(32), default="blocked", nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    packet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("application_packet.id"), nullable=True
    )
    applied_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    closed_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)

    job: Mapped[JobModel] = relationship(back_populates="applications")
    events: Mapped[list[ApplicationEventModel]] = relationship(back_populates="application")
    interviews: Mapped[list[InterviewModel]] = relationship(back_populates="application")


class ApplicationEventModel(Base):
    __tablename__ = "application_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("application.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    actor: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )

    application: Mapped[ApplicationModel] = relationship(back_populates="events")


class MessageLinkModel(Base):
    __tablename__ = "message_link"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    inbound_message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inbound_message.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job.id"), nullable=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("application.id"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("company.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )

    message: Mapped[InboundMessageModel] = relationship(back_populates="links")


class ContactModel(Base):
    __tablename__ = "contact"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("company.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_contact_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_contact_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)

    company: Mapped[CompanyModel | None] = relationship(back_populates="contacts")


class InterviewModel(Base):
    __tablename__ = "interview"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("application.id"), nullable=False)
    round_type: Mapped[str] = mapped_column(String(64), nullable=False)
    scheduled_start: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
    scheduled_end: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    location_or_link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="scheduled", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[ApplicationModel] = relationship(back_populates="interviews")


class TaskModel(Base):
    __tablename__ = "task"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("application.id"), nullable=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    due_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)


class PolicyRegistryModel(Base):
    __tablename__ = "policy_registry"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    domain_pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), default="blocked", nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    reviewed_at: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
    review_due_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    actor: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, default=utc_now, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

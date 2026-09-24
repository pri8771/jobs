"""V23 Agent Tool Envelope Types (V23-TL-01).

Defines transport-neutral tool invocation requests, results, permission contexts,
and action classifications.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from jobs_automation.db.base import utc_now
from jobs_automation.intelligence.envelope import EvidenceRef


class ActionClass(StrEnum):
    P0_READ = "P0_READ"
    P1_LOCAL_WRITE = "P1_LOCAL_WRITE"
    P2_EXTERNAL_PREP = "P2_EXTERNAL_PREP"
    P3_USER_APPROVED_EXTERNAL = "P3_USER_APPROVED_EXTERNAL"
    P4_BLOCKED = "P4_BLOCKED"

    def rank(self) -> int:
        _ranks = {
            ActionClass.P0_READ: 0,
            ActionClass.P1_LOCAL_WRITE: 1,
            ActionClass.P2_EXTERNAL_PREP: 2,
            ActionClass.P3_USER_APPROVED_EXTERNAL: 3,
            ActionClass.P4_BLOCKED: 4,
        }
        return _ranks[self]


class ToolStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PARTIAL = "PARTIAL"


class ErrorCategory(StrEnum):
    PERMISSION_DENIED = "PERMISSION_DENIED"
    MISSING_FACT = "MISSING_FACT"
    UNRESOLVED_REVIEW = "UNRESOLVED_REVIEW"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    STALE_ENTITY = "STALE_ENTITY"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class PermissionContext(BaseModel):
    actor: str
    actor_kind: Literal["USER", "SERVICE", "AGENT"]
    caller_ceiling: ActionClass = ActionClass.P1_LOCAL_WRITE
    approval_id: uuid.UUID | None = None
    allow_external_prep: bool = False
    task_id: str | None = None
    agent_id: str | None = None
    agent_version: str | None = None


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of a payload dictionary."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class ToolRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    tool_version: str = "1.0"
    action_class: ActionClass
    target_refs: list[EvidenceRef] = Field(default_factory=list)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    input_hash: str = ""
    permission_context: PermissionContext
    idempotency_key: str | None = None
    created_at: datetime.datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def compute_hash_if_missing(self) -> ToolRequest:
        if not self.input_hash:
            self.input_hash = compute_payload_hash(self.input_payload)
        return self


class PermissionDecisionRecord(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    permission_class: ActionClass
    decision: Literal["ALLOW", "DENY", "REQUIRE_APPROVAL"]
    policy_refs: list[str] = Field(default_factory=list)
    approval_ref: str | None = None
    reason_code: str
    evaluated_at: datetime.datetime = Field(default_factory=utc_now)


class ToolResult(BaseModel):
    request_id: str
    tool_name: str
    tool_version: str = "1.0"
    status: ToolStatus
    entity_refs: list[EvidenceRef] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    review_needs: list[str] = Field(default_factory=list)
    audit_ref: str | None = None
    external_reference: str | None = None
    error_category: ErrorCategory | None = None
    error_message_safe: str | None = None
    result_payload: dict[str, Any] = Field(default_factory=dict)
    result_hash: str = ""
    simulated: bool = False
    completed_at: datetime.datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_partial_warnings_and_hash(self) -> ToolResult:
        if self.status == ToolStatus.PARTIAL and not self.warnings:
            raise ValueError("ToolResult with PARTIAL status must have non-empty warnings")
        if not self.result_hash and self.result_payload:
            self.result_hash = compute_payload_hash(self.result_payload)
        return self

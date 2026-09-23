import datetime
import uuid
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class AgentTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_type: str
    requested_by: str
    assigned_agent: str | None = None
    input_artifact_refs: list[str] = Field(default_factory=list)
    goal: str | None = None
    constraints: list[str] = Field(default_factory=list)
    permission_scope: str
    status: Literal["READY", "RUNNING", "NEEDS_REVIEW", "BLOCKED", "SUCCEEDED", "FAILED", "CANCELLED"] = "READY"
    attempt: int = 0
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    output_artifact_refs: list[str] = Field(default_factory=list)
    error_reason: str | None = None

class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_id: str
    memory_key: str
    memory_value: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_id: uuid.UUID | None = None
    event_type: str
    event_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

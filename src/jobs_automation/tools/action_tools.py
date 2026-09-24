"""V23 Action Tool Contracts for P2 and P3 External Operations (V23-TL-09)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.tools.envelope import ActionClass, PermissionContext, ToolStatus
from jobs_automation.tools.registry import ToolHandlerResult, ToolRegistry, ToolSpec


class AssistedApplicationInput(BaseModel):
    job_id: str
    packet_id: str
    destination_domain: str
    mock_browser: bool = False


class AssistedApplicationOutput(BaseModel):
    job_id: str
    packet_id: str
    status: str
    simulated: bool = False


class SubmitApplicationInput(BaseModel):
    job_id: str
    packet_id: str
    approval_id: str


class SubmitApplicationOutput(BaseModel):
    job_id: str
    packet_id: str
    status: str
    message: str


class SendMessageInput(BaseModel):
    recipient_email: str
    subject: str
    body: str


class SendMessageOutput(BaseModel):
    status: str = "NOT_IMPLEMENTED"


class UpdateCalendarInput(BaseModel):
    title: str
    start_iso: str
    end_iso: str


class UpdateCalendarOutput(BaseModel):
    status: str = "NOT_IMPLEMENTED"


def handle_assisted_application(session: Session, input_model: AssistedApplicationInput, context: PermissionContext) -> ToolHandlerResult:
    out = AssistedApplicationOutput(
        job_id=input_model.job_id,
        packet_id=input_model.packet_id,
        status="PREFILL_PREPARED",
        simulated=input_model.mock_browser,
    )
    return ToolHandlerResult(
        payload_model=out,
        status=ToolStatus.SUCCEEDED,
        simulated=input_model.mock_browser,
        entity_refs=[EvidenceRef(ref_type="job", ref_id=input_model.job_id)],
    )


def handle_submit_application(session: Session, input_model: SubmitApplicationInput, context: PermissionContext) -> ToolHandlerResult:
    # Safe contract: returns BLOCKED / NOT_IMPLEMENTED until live submit transport lands
    out = SubmitApplicationOutput(
        job_id=input_model.job_id,
        packet_id=input_model.packet_id,
        status="NOT_IMPLEMENTED",
        message="Live external submit transport is not implemented in current engineering gate.",
    )
    return ToolHandlerResult(
        payload_model=out,
        status=ToolStatus.BLOCKED,
        entity_refs=[EvidenceRef(ref_type="job", ref_id=input_model.job_id)],
    )


def handle_send_message(session: Session, input_model: SendMessageInput, context: PermissionContext) -> ToolHandlerResult:
    return ToolHandlerResult(payload_model=SendMessageOutput(), status=ToolStatus.BLOCKED)


def handle_update_calendar(session: Session, input_model: UpdateCalendarInput, context: PermissionContext) -> ToolHandlerResult:
    return ToolHandlerResult(payload_model=UpdateCalendarOutput(), status=ToolStatus.BLOCKED)


def register_action_tools(registry: ToolRegistry) -> None:
    """Register P2 and P3 action tools into the provided ToolRegistry."""
    registry.register(ToolSpec(
        name="open_assisted_application", version="1.0", action_class=ActionClass.P2_EXTERNAL_PREP,
        capability="assisted_prefill", input_model=AssistedApplicationInput, output_model=AssistedApplicationOutput,
        handler=handle_assisted_application, requires_destination=True,
    ))
    registry.register(ToolSpec(
        name="submit_application", version="1.0", action_class=ActionClass.P3_USER_APPROVED_EXTERNAL,
        capability="submit_application", input_model=SubmitApplicationInput, output_model=SubmitApplicationOutput,
        handler=handle_submit_application, requires_destination=True,
    ))
    registry.register(ToolSpec(
        name="send_message", version="1.0", action_class=ActionClass.P3_USER_APPROVED_EXTERNAL,
        capability="send_message", input_model=SendMessageInput, output_model=SendMessageOutput,
        handler=handle_send_message, requires_destination=False,
    ))
    registry.register(ToolSpec(
        name="update_external_calendar", version="1.0", action_class=ActionClass.P3_USER_APPROVED_EXTERNAL,
        capability="update_calendar", input_model=UpdateCalendarInput, output_model=UpdateCalendarOutput,
        handler=handle_update_calendar, requires_destination=False,
    ))

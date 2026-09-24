"""V23 Tool Audit Persistence and Replay Lookup (V23-TL-04)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.models import AuditLogModel
from jobs_automation.tools.envelope import (
    PermissionDecisionRecord,
    ToolRequest,
    ToolResult,
)

logger = logging.getLogger(__name__)


def record_invocation(
    session: Session,
    request: ToolRequest,
    result: ToolResult,
    decision: PermissionDecisionRecord | None = None,
) -> uuid.UUID:
    """Record a tool invocation in the AuditLogModel evidence store."""
    entity_ref_ids = [str(r.ref_id) for r in result.entity_refs]
    evidence_ref_ids = [str(r.ref_id) for r in result.evidence_refs]

    audit_row = AuditLogModel(
        action_type="tool_invocation",
        entity_type="tool_request",
        external_reference=request.request_id,
        input_hash=request.input_hash,
        actor=request.permission_context.actor,
        result=result.status.value,
        metadata_json={
            "tool": request.tool_name,
            "version": request.tool_version,
            "action_class": request.action_class.value,
            "idempotency_key": request.idempotency_key,
            "result_hash": result.result_hash,
            "simulated": result.simulated,
            "error_category": result.error_category.value if result.error_category else None,
            "entity_refs": entity_ref_ids,
            "evidence_refs": evidence_ref_ids,
            "task_id": request.permission_context.task_id,
            "agent_id": request.permission_context.agent_id,
            "agent_version": request.permission_context.agent_version,
            "decision_id": decision.decision_id if decision else None,
        },
    )
    session.add(audit_row)
    session.flush()
    return audit_row.id


def find_replay(session: Session, idempotency_key: str) -> tuple[str, str] | None:
    """Find a prior successful or partial invocation by idempotency key.

    Returns tuple of (input_hash, result_hash) if found, else None.
    """
    if not idempotency_key:
        return None

    # Query audit logs for matching idempotency_key
    rows = list(
        session.scalars(
            select(AuditLogModel)
            .where(
                AuditLogModel.action_type == "tool_invocation",
                AuditLogModel.result.in_(["SUCCEEDED", "PARTIAL"]),
            )
            .order_by(AuditLogModel.occurred_at.desc())
        ).all()
    )

    for r in rows:
        meta = r.metadata_json or {}
        if meta.get("idempotency_key") == idempotency_key:
            input_hash = r.input_hash or ""
            result_hash = meta.get("result_hash", "")
            return input_hash, result_hash

    return None

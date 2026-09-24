"""V23 Agent Tool Runtime Pipeline (V23-TL-05).

Executes tool requests through validation, idempotency checks, permission gate,
handler execution, exception mapping, and audit persistence.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.tools.audit import find_replay, record_invocation
from jobs_automation.tools.envelope import (
    ActionClass,
    ErrorCategory,
    PermissionContext,
    ToolRequest,
    ToolResult,
    ToolStatus,
    compute_payload_hash,
)
from jobs_automation.tools.permission_gate import PermissionGate
from jobs_automation.tools.registry import ToolRegistry, ToolSpec
from jobs_automation.worker import sanitize_error_message

logger = logging.getLogger(__name__)


class ToolContractError(Exception):
    """Raised when a tool handler violates runtime contract rules."""
    pass


class ToolRuntime:
    """Central invocation runtime for typed agent tools."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        registry: ToolRegistry | None = None,
        gate: PermissionGate | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.registry = registry or ToolRegistry()
        self.gate = gate

    def invoke(
        self,
        tool_name: str,
        payload: dict[str, Any],
        context: PermissionContext,
        idempotency_key: str | None = None,
        version: str = "1.0",
    ) -> ToolResult:
        """Invoke a tool through validation, gate, handler execution, and audit."""
        req_id = str(uuid.uuid4())
        now = utc_now()

        # 1. Lookup ToolSpec
        spec = self.registry.get(tool_name, version)
        if not spec:
            return ToolResult(
                request_id=req_id,
                tool_name=tool_name,
                tool_version=version,
                status=ToolStatus.FAILED,
                error_category=ErrorCategory.NOT_FOUND,
                error_message_safe=f"Tool not found: {tool_name} (v{version})",
                completed_at=now,
            )

        # 2. Input Validation
        try:
            input_model_inst = spec.input_model.model_validate(payload)
        except ValidationError as val_err:
            return ToolResult(
                request_id=req_id,
                tool_name=tool_name,
                tool_version=version,
                status=ToolStatus.FAILED,
                error_category=ErrorCategory.INVALID_INPUT,
                error_message_safe=f"Input validation failed: {sanitize_error_message(val_err)}",
                completed_at=now,
            )

        # 3. Build ToolRequest
        request = ToolRequest(
            request_id=req_id,
            tool_name=tool_name,
            tool_version=version,
            action_class=spec.action_class,
            permission_context=context,
            input_payload=payload,
            idempotency_key=idempotency_key,
            created_at=now,
        )

        # 4. Idempotency Check
        if idempotency_key:
            with self.session_factory() as session:
                replay = find_replay(session, idempotency_key)
                if replay:
                    prior_input_hash, prior_result_hash = replay
                    if prior_input_hash == request.input_hash:
                        # Write tools return replayed result
                        if spec.action_class != ActionClass.P0_READ:
                            return ToolResult(
                                request_id=req_id,
                                tool_name=tool_name,
                                tool_version=version,
                                status=ToolStatus.SUCCEEDED,
                                warnings=["REPLAYED"],
                                result_hash=prior_result_hash,
                                completed_at=now,
                            )
                    else:
                        return ToolResult(
                            request_id=req_id,
                            tool_name=tool_name,
                            tool_version=version,
                            status=ToolStatus.FAILED,
                            error_category=ErrorCategory.DUPLICATE_REQUEST,
                            error_message_safe="Idempotency key reused with different input payload",
                            completed_at=now,
                        )

        # 5. Permission Gate Check
        with self.session_factory() as session:
            gate = self.gate or PermissionGate(session)
            decision = gate.decide(spec, request)

            if decision.decision == "DENY":
                category = ErrorCategory.PERMISSION_DENIED
                if decision.reason_code == "POLICY_BLOCKED":
                    category = ErrorCategory.POLICY_BLOCKED
                return ToolResult(
                    request_id=req_id,
                    tool_name=tool_name,
                    tool_version=version,
                    status=ToolStatus.BLOCKED,
                    error_category=category,
                    error_message_safe=f"Tool execution blocked: {decision.reason_code}",
                    completed_at=now,
                )
            elif decision.decision == "REQUIRE_APPROVAL":
                return ToolResult(
                    request_id=req_id,
                    tool_name=tool_name,
                    tool_version=version,
                    status=ToolStatus.NEEDS_REVIEW,
                    error_category=ErrorCategory.UNRESOLVED_REVIEW,
                    review_needs=[decision.reason_code],
                    error_message_safe=f"User approval required: {decision.reason_code}",
                    completed_at=now,
                )

        # 6. Execute Handler
        with self.session_factory() as session:
            try:
                handler_res = spec.handler(session, input_model_inst, context)
                session.commit()

                res_payload = handler_res.payload_model.model_dump(mode="json")

                # Mock contract enforcement check
                if res_payload.get("origin") == "mock" and not handler_res.simulated:
                    raise ToolContractError("Mock payload returned but handler result did not set simulated=True")

                result = ToolResult(
                    request_id=req_id,
                    tool_name=tool_name,
                    tool_version=version,
                    status=handler_res.status,
                    entity_refs=handler_res.entity_refs,
                    evidence_refs=handler_res.evidence_refs,
                    warnings=handler_res.warnings,
                    review_needs=handler_res.review_needs,
                    external_reference=handler_res.external_reference,
                    result_payload=res_payload,
                    simulated=handler_res.simulated,
                    completed_at=utc_now(),
                )

            except LookupError as exc:
                session.rollback()
                result = ToolResult(
                    request_id=req_id, tool_name=tool_name, tool_version=version,
                    status=ToolStatus.FAILED, error_category=ErrorCategory.NOT_FOUND,
                    error_message_safe=sanitize_error_message(exc), completed_at=utc_now(),
                )
            except PermissionError as exc:
                session.rollback()
                result = ToolResult(
                    request_id=req_id, tool_name=tool_name, tool_version=version,
                    status=ToolStatus.BLOCKED, error_category=ErrorCategory.PERMISSION_DENIED,
                    error_message_safe=sanitize_error_message(exc), completed_at=utc_now(),
                )
            except FileNotFoundError as exc:
                session.rollback()
                result = ToolResult(
                    request_id=req_id, tool_name=tool_name, tool_version=version,
                    status=ToolStatus.FAILED, error_category=ErrorCategory.MISSING_FACT,
                    error_message_safe=sanitize_error_message(exc), completed_at=utc_now(),
                )
            except (ConnectionError, TimeoutError) as exc:
                session.rollback()
                result = ToolResult(
                    request_id=req_id, tool_name=tool_name, tool_version=version,
                    status=ToolStatus.FAILED, error_category=ErrorCategory.PROVIDER_UNAVAILABLE,
                    error_message_safe=sanitize_error_message(exc), completed_at=utc_now(),
                )
            except Exception as exc:
                session.rollback()
                result = ToolResult(
                    request_id=req_id, tool_name=tool_name, tool_version=version,
                    status=ToolStatus.FAILED, error_category=ErrorCategory.INTERNAL_ERROR,
                    error_message_safe=f"Internal handler error: {sanitize_error_message(exc)}", completed_at=utc_now(),
                )

        # 7. Persist Invocation Audit
        with self.session_factory() as audit_session:
            try:
                record_invocation(audit_session, request, result, decision)
                audit_session.commit()
            except Exception as audit_exc:
                logger.warning("Failed to record tool invocation audit: %s", audit_exc)

        return result

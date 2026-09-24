"""V23 Deterministic PermissionGate (V23-TL-03).

Enforces tool authorization ceilings, platform policies, kill-switches,
and user approval verification for P2 and P3 operations.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.db.base import utc_now
from jobs_automation.db.models import AuditLogModel
from jobs_automation.tools.envelope import (
    ActionClass,
    PermissionDecisionRecord,
    ToolRequest,
)
from jobs_automation.tools.registry import ToolSpec

logger = logging.getLogger(__name__)


class PermissionGate:
    """Evaluates tool invocation permissions and logs decisions."""

    def __init__(
        self,
        session: Session,
        policy_evaluator: PolicyEvaluator | None = None,
        kill_switch: KillSwitchManager | None = None,
        approval_lookup: Callable[[Any], Any] | None = None,
    ) -> None:
        self.session = session
        self.policy_evaluator = policy_evaluator or PolicyEvaluator(session)
        self.kill_switch = kill_switch or KillSwitchManager()
        self.approval_lookup = approval_lookup

    def decide(self, spec: ToolSpec, request: ToolRequest) -> PermissionDecisionRecord:
        """Evaluate authorization and policy rules for a ToolRequest."""
        context = request.permission_context
        requested_class = spec.action_class
        ceiling_class = context.caller_ceiling

        try:
            # 1. P4_BLOCKED → DENY POLICY_BLOCKED
            if requested_class == ActionClass.P4_BLOCKED:
                return self._create_record(
                    request, requested_class, "DENY", "POLICY_BLOCKED", ["policy:p4_blocked"]
                )

            # 2. Ceiling check: rank(requested_class) > rank(caller_ceiling) → DENY PERMISSION_DENIED
            if requested_class.rank() > ceiling_class.rank():
                return self._create_record(
                    request, requested_class, "DENY", "PERMISSION_DENIED", ["context:caller_ceiling_exceeded"]
                )

            # 3. P0_READ & P1_LOCAL_WRITE → ALLOW
            if requested_class in (ActionClass.P0_READ, ActionClass.P1_LOCAL_WRITE):
                return self._create_record(
                    request, requested_class, "ALLOW", "ALLOW_LOCAL_ONLY", []
                )

            # 4. P2_EXTERNAL_PREP
            if requested_class == ActionClass.P2_EXTERNAL_PREP:
                if not context.allow_external_prep:
                    return self._create_record(
                        request, requested_class, "REQUIRE_APPROVAL", "EXTERNAL_PREP_NOT_ENABLED", []
                    )

                if spec.requires_destination:
                    domain = request.input_payload.get("destination_domain") or request.input_payload.get("domain") or ""
                    capability = spec.capability or "assisted_prefill"
                    pol_eval = self.policy_evaluator.evaluate(domain, capability=capability)
                    is_killed, kill_reason = self.kill_switch.is_global_active()

                    if is_killed:
                        return self._create_record(
                            request, requested_class, "DENY", "KILL_SWITCH_ACTIVE", [f"kill_switch:{kill_reason}"]
                        )

                    if pol_eval.decision in ("ASSISTED", "AUTO_ALLOWED"):
                        return self._create_record(
                            request, requested_class, "ALLOW", "ALLOW_EXTERNAL_PREP", [f"policy:{pol_eval.decision}"]
                        )
                    else:
                        return self._create_record(
                            request, requested_class, "DENY", "POLICY_BLOCKED", [f"policy:{pol_eval.decision}"]
                        )

                return self._create_record(
                    request, requested_class, "ALLOW", "ALLOW_EXTERNAL_PREP", []
                )

            # 5. P3_USER_APPROVED_EXTERNAL
            if requested_class == ActionClass.P3_USER_APPROVED_EXTERNAL:
                if self.approval_lookup is None:
                    return self._create_record(
                        request, requested_class, "REQUIRE_APPROVAL", "APPROVAL_STORE_UNAVAILABLE", []
                    )

                if not context.approval_id:
                    return self._create_record(
                        request, requested_class, "REQUIRE_APPROVAL", "APPROVAL_REQUIRED", []
                    )

                approval = self.approval_lookup(context.approval_id)
                if not approval:
                    return self._create_record(
                        request, requested_class, "REQUIRE_APPROVAL", "APPROVAL_REQUIRED", []
                    )

                # Validate approval fields
                if getattr(approval, "status", None) != "ACTIVE":
                    return self._create_record(
                        request, requested_class, "DENY", "APPROVAL_CONSUMED" if getattr(approval, "status", None) == "CONSUMED" else "APPROVAL_EXPIRED", []
                    )

                # Check expiration
                expires_at = getattr(approval, "expires_at", None)
                if expires_at and expires_at < utc_now():
                    return self._create_record(
                        request, requested_class, "DENY", "APPROVAL_EXPIRED", []
                    )

                # Check hash mismatch if present
                app_hash = getattr(approval, "packet_hash", None) or getattr(approval, "input_hash", None)
                req_hash = request.input_payload.get("packet_hash") or request.input_hash
                if app_hash and app_hash != req_hash:
                    return self._create_record(
                        request, requested_class, "DENY", "APPROVAL_HASH_MISMATCH", []
                    )

                # Kill switch check
                is_killed, kill_reason = self.kill_switch.is_global_active()
                if is_killed:
                    return self._create_record(
                        request, requested_class, "DENY", "KILL_SWITCH_ACTIVE", [f"kill_switch:{kill_reason}"]
                    )

                return self._create_record(
                    request, requested_class, "ALLOW", "ALLOW_USER_APPROVED", [f"approval:{context.approval_id}"]
                )

            return self._create_record(
                request, requested_class, "DENY", "PERMISSION_DENIED", ["unknown_action_class"]
            )

        except Exception as exc:
            logger.error("Error evaluating PermissionGate decision: %s", exc, exc_info=True)
            return self._create_record(
                request, requested_class, "DENY", "INTERNAL_ERROR", [f"error:{exc}"]
            )

    def _create_record(
        self,
        request: ToolRequest,
        permission_class: ActionClass,
        decision: str,
        reason_code: str,
        policy_refs: list[str],
        approval_ref: str | None = None,
    ) -> PermissionDecisionRecord:
        record = PermissionDecisionRecord(
            request_id=request.request_id,
            permission_class=permission_class,
            decision=decision,
            policy_refs=policy_refs,
            approval_ref=approval_ref or (str(request.permission_context.approval_id) if request.permission_context.approval_id else None),
            reason_code=reason_code,
            evaluated_at=utc_now(),
        )

        # Audit log for P2 & P3 decisions
        if permission_class in (ActionClass.P2_EXTERNAL_PREP, ActionClass.P3_USER_APPROVED_EXTERNAL):
            try:
                audit_row = AuditLogModel(
                    action_type="permission_decision",
                    entity_type="tool_request",
                    external_reference=request.request_id,
                    input_hash=request.input_hash,
                    result=decision,
                    metadata_json={
                        "tool": request.tool_name,
                        "action_class": permission_class.value,
                        "reason_code": reason_code,
                        "policy_refs": policy_refs,
                        "approval_ref": record.approval_ref,
                    },
                )
                self.session.add(audit_row)
                self.session.flush()
            except Exception as audit_exc:
                logger.warning("Failed to persist audit log for permission decision: %s", audit_exc)

        return record

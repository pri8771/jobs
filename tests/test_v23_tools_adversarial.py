"""Adversarial and contract unit tests for V2.3 Agent Tools (V23-TL-11)."""

import ast
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.tools import (
    ActionClass,
    ErrorCategory,
    PermissionContext,
    ToolResult,
    ToolRuntime,
    ToolStatus,
    get_default_tool_registry,
)
from jobs_automation.tools.envelope import ToolRequest, compute_payload_hash


@pytest.fixture
def db_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    try:
        yield SessionLocal
    finally:
        Base.metadata.drop_all(engine)


def test_ceiling_check_blocks_higher_action_class(db_session_factory) -> None:
    """Contract rule TL-03: Ceiling P0_READ denies P1_LOCAL_WRITE tool invocation."""
    runtime = ToolRuntime(db_session_factory, get_default_tool_registry())
    context = PermissionContext(actor="agent_1", actor_kind="AGENT", caller_ceiling=ActionClass.P0_READ)

    # evaluate_job is P1_LOCAL_WRITE
    res = runtime.invoke("evaluate_job", {"job_id": "00000000-0000-0000-0000-000000000000"}, context)

    assert res.status == ToolStatus.BLOCKED
    assert res.error_category == ErrorCategory.PERMISSION_DENIED


def test_stale_entity_id_returns_not_found(db_session_factory) -> None:
    """Contract rule TL-05: Nonexistent entity ID returns FAILED NOT_FOUND."""
    runtime = ToolRuntime(db_session_factory, get_default_tool_registry())
    context = PermissionContext(actor="user_1", actor_kind="USER", caller_ceiling=ActionClass.P0_READ)

    res = runtime.invoke("get_job", {"job_id": "00000000-0000-0000-0000-000000000000"}, context)

    assert res.status == ToolStatus.FAILED
    assert res.error_category == ErrorCategory.NOT_FOUND


def test_idempotency_replay_same_payload(db_session_factory) -> None:
    """Contract rule TL-05: Same key + same payload returns replayed result with warning."""
    runtime = ToolRuntime(db_session_factory, get_default_tool_registry())
    context = PermissionContext(actor="user_1", actor_kind="USER", caller_ceiling=ActionClass.P1_LOCAL_WRITE)

    payload = {"task_type": "TARGET_COMPANY_NEW_ROLE", "reason": "test idempotency"}
    idempotency_key = "idemp_key_123"

    res1 = runtime.invoke("create_review_task", payload, context, idempotency_key=idempotency_key)
    assert res1.status == ToolStatus.SUCCEEDED

    # Second invocation with same payload & key
    res2 = runtime.invoke("create_review_task", payload, context, idempotency_key=idempotency_key)
    assert res2.status == ToolStatus.SUCCEEDED
    assert "REPLAYED" in res2.warnings


def test_idempotency_duplicate_mismatch_fails(db_session_factory) -> None:
    """Contract rule TL-05: Same key + different payload returns DUPLICATE_REQUEST failure."""
    runtime = ToolRuntime(db_session_factory, get_default_tool_registry())
    context = PermissionContext(actor="user_1", actor_kind="USER", caller_ceiling=ActionClass.P1_LOCAL_WRITE)

    idempotency_key = "idemp_key_456"

    res1 = runtime.invoke("create_review_task", {"task_type": "T1", "reason": "r1"}, context, idempotency_key=idempotency_key)
    assert res1.status == ToolStatus.SUCCEEDED

    res2 = runtime.invoke("create_review_task", {"task_type": "T1", "reason": "DIFFERENT"}, context, idempotency_key=idempotency_key)
    assert res2.status == ToolStatus.FAILED
    assert res2.error_category == ErrorCategory.DUPLICATE_REQUEST


def test_partial_status_requires_warnings() -> None:
    """Contract rule TL-01: PARTIAL status with empty warnings raises ValueError."""
    with pytest.raises(ValueError, match="PARTIAL status must have non-empty warnings"):
        ToolResult(
            request_id="req-1",
            tool_name="test",
            tool_version="1.0",
            status=ToolStatus.PARTIAL,
            warnings=[],  # Invalid! Must have warnings
        )


def test_no_third_party_agent_framework_imports() -> None:
    """Contract rule TL-11: Assert no third-party agent framework imports under src/jobs_automation/tools/."""
    tools_dir = os.path.abspath("src/jobs_automation/tools")
    forbidden = {"langchain", "llama_index", "autogen", "crewai", "semantic_kernel"}

    for root, _, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=path)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert alias.name not in forbidden, f"Forbidden import {alias.name} in {path}"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            mod = node.module.split(".")[0]
                            assert mod not in forbidden, f"Forbidden import {mod} in {path}"

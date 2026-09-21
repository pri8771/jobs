# V3 Runtime Data Contracts

Artifacts:
- A-V30-PERMISSION-MODEL
- A-V30-SHARED-MEMORY
- A-V30-AGENT-RUNTIME
- A-V30-AGENT-EVALUATION

Purpose:
Prevent the future V3 worker from inventing incompatible task, permission, memory and tool envelopes while implementing orchestration.

## AgentDefinition

Fields:
- agent_id
- version
- purpose
- allowed_tool_names
- maximum_permission_class
- model_policy_id
- memory_scope
- input_artifact_types
- output_artifact_types
- max_retry_policy
- enabled

Agent definitions are configuration/registry, not authority to bypass tool policy.

## AgentTask

Fields:
- task_id
- parent_task_id nullable
- root_goal_id
- task_type
- requested_by
- assigned_agent_id nullable
- goal
- constraints
- input_artifact_refs
- expected_output_types
- permission_ceiling
- model_policy_id
- max_cost nullable
- status
- attempt
- lease_owner nullable
- lease_expires_at nullable
- checkpoint_ref nullable
- created_at
- started_at nullable
- completed_at nullable
- error_category nullable
- review_reason nullable
- output_artifact_refs

Statuses:
READY | RUNNING | NEEDS_REVIEW | BLOCKED | SUCCEEDED | FAILED | CANCELLED

Invariant:
SUCCEEDED requires valid output artifact/evidence, not just a model statement.

## ToolRequest

Fields:
- request_id
- task_id
- agent_id/version
- tool_name/version
- action_class
- target_refs
- input_hash
- permission_context
- idempotency_key nullable
- created_at

## PermissionDecision

Fields:
- decision_id
- request_id
- permission_class
- decision: ALLOW | DENY | REQUIRE_APPROVAL
- policy refs
- approval ref nullable
- reason_code
- evaluated_at

Prompt/model text is never a policy source.

## ScopedApproval

Fields:
- approval_id
- actor/user
- action_class
- exact target refs
- exact artifact/version/hash refs when relevant
- method/transport
- issued_at
- expires_at
- one_time
- consumed_at nullable
- revoked_at nullable
- policy_version

## ToolResult

Fields:
- request_id
- status: SUCCEEDED | FAILED | BLOCKED | NEEDS_REVIEW | PARTIAL
- entity/artifact refs
- evidence refs
- audit_ref
- external_reference nullable
- warnings
- error_category nullable
- result_hash
- completed_at

A PARTIAL/BLOCKED result may not be normalized to SUCCEEDED by the agent.

## MemoryEntry

Fields:
- memory_id
- memory_class: M0 | M1 | M2 | M3 | M4
- entity/task scope
- source_refs
- payload
- confidence nullable
- sensitivity_class
- allowed_agent_scopes
- created_at
- updated_at
- review_at/valid_until nullable
- supersedes nullable
- superseded_by nullable
- invalidated_at nullable

See `docs/V3_SHARED_MEMORY_CONTRACT.md`.

## AgentCheckpoint

Fields:
- checkpoint_id
- task_id
- attempt
- completed_step_ids
- pending_step_ids
- output_artifact_refs
- outstanding_approval_refs
- external_action_state
- created_at

External-action state must make replay safety explicit:
- NOT_STARTED
- PREPARED
- REQUEST_DISPATCHED_UNCONFIRMED
- CONFIRMED

## TraceEvent

Fields:
- trace_id
- root_goal_id
- task_id
- agent/version
- event_type
- model/provider nullable
- tool request/result refs
- permission decision ref
- input/output artifact refs
- cost/tokens nullable
- latency nullable
- timestamp
- safe error category/details

Never log secrets/raw OAuth tokens.

## GoalPlan

Fields:
- root_goal_id
- original goal
- assumptions
- task DAG
- dependency edges
- approval boundaries
- stop conditions
- created_by planner/version
- created_at

The plan is mutable through audited revisions; individual agents cannot silently broaden root scope.

## Restart semantics

After process restart:
- RUNNING tasks with expired leases become recoverable,
- confirmed external actions are not replayed,
- unconfirmed dispatched actions route to reconciliation,
- completed artifacts are reused,
- pending approvals remain pending,
- bounded retry counts persist.

## Acceptance

Data model must support:
- multi-agent handoff,
- durable restart,
- permission interception,
- idempotent tool invocation,
- scoped memory,
- trace/evaluation,
- no hidden success without evidence.

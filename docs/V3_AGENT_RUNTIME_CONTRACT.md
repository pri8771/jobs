# V3 Agent Runtime Contract

Artifact: A-V30-AGENT-RUNTIME

## Purpose

Coordinate specialist career agents through bounded tasks and artifact handoffs while deterministic runtime code owns durable state and permissions.

## AgentTask

Minimum:
- id
- task_type
- requested_by
- assigned_agent
- input_artifact_refs
- goal
- constraints
- permission_scope
- max_cost / model policy
- status
- attempt
- created_at / started_at / completed_at
- output_artifact_refs
- error / review reason

Statuses:
- READY
- RUNNING
- NEEDS_REVIEW
- BLOCKED
- SUCCEEDED
- FAILED
- CANCELLED

## Runtime responsibilities

- choose eligible specialist agent
- enforce permissions before tool calls
- pass artifact references, not giant unbounded chat history
- bound retries
- time/cost limits
- cancellation
- persist outputs/errors
- prevent duplicate consequential work
- emit trace/metrics
- hand off to another agent when contract allows

## Agent responsibilities

- operate only inside assigned scope
- produce artifact-backed output
- cite/source factual conclusions
- escalate missing facts/permissions
- not silently broaden the task

## Framework neutrality

Core task/artifact/permission model should work without LangGraph/CrewAI/etc.

A framework may orchestrate execution if it materially helps, but the domain runtime remains portable.

## Self-improvement boundary

Agents may propose:
- prompt changes
- routing changes
- new tests
- new tools
- code changes

They do not deploy self-modifying production behavior without the normal review/acceptance path.

## Acceptance

- two specialist agents can hand off via artifacts.
- restart does not lose task state.
- permission denial stops external action.
- retry is bounded and traceable.
- failed agent cannot mark task success.
- user can inspect why/what each agent did.

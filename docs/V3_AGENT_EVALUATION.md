# V3 Agent Evaluation & Observability Contract

Artifact: A-V30-AGENT-EVALUATION

## Purpose

Measure whether specialist agents are useful, truthful, efficient, and safe.

## Trace per agent task

Capture:
- task ID / artifact IDs
- agent role/version
- model/provider
- tool calls
- permission decisions
- source references
- output artifacts
- tokens/cost when available
- latency
- retries
- review escalations
- final status

Do not log secrets/raw OAuth tokens.

## Evaluation dimensions

- factual grounding
- task completion
- artifact validity
- policy compliance
- unnecessary user interruptions
- unnecessary tool calls
- cost efficiency
- latency
- handoff quality
- duplicate-work avoidance

## Golden scenarios

Maintain deterministic evaluation cases for:
- job matching
- packet selection
- recruiter timeline
- interview brief
- follow-up draft
- networking suggestion
- policy refusal/approval handling
- ambiguous evidence escalation

## Production outcome metrics

For applicable agents:
- accepted recommendation rate
- correction/rework rate
- recruiter/interview/offer outcome contribution
- false-positive/false-negative rate
- user override rate

Do not optimize agents directly for applications/messages sent; quality and outcome matter more than volume.

## Acceptance

- every agent task is traceable.
- failures are visible.
- model swaps can be compared on same eval set.
- unsafe behavior is measurable as a regression.
- no hidden success claim without artifact/evidence.


## Integration acceptance scenarios

Use:
- `docs/V3_INTEGRATION_ACCEPTANCE_SCENARIOS.md`
- `docs/V3_SPECIALIST_AGENT_SPECS.md`

Evaluation must include multi-agent handoffs, interruption/restart, prompt injection, permission escalation attempts, duplicate application races, missing facts, and provider failure.

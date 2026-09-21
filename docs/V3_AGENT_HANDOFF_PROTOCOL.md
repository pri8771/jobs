# V3 Agent Handoff Protocol

Artifacts:
- A-V30-AGENT-RUNTIME
- A-V30-SHARED-MEMORY
- specialist agent artifacts

## Principle

Agents hand off through typed artifacts/tasks, not by forwarding an unbounded chat transcript.

## Handoff envelope

Minimum:
- handoff_id
- source_task_id
- source_agent/version
- destination_agent or eligible capability
- goal/subgoal
- input_artifact_refs
- source/evidence refs
- constraints
- permission ceiling
- outstanding review/approval refs
- freshness/staleness metadata
- expected output types
- created_at

## Rules

1. Permission may only stay the same or become more restrictive.
2. Derived summary never replaces canonical evidence refs.
3. Missing candidate fact remains missing across handoff.
4. NEEDS_REVIEW cannot be converted to resolved by another model without new evidence/user confirmation.
5. External-action state is explicit and replay-safe.
6. A destination agent may reject/escalate an incompatible handoff.
7. Agent identity/version is auditable.
8. Handoff loops are bounded/detected.

## Examples

### Scout → Matcher
Pass:
job/source refs, observations, candidate strategy ref.
Do not pass:
permission to apply.

### Matcher → Resume Strategist
Pass:
job requirements, match rationale, candidate evidence refs.
Do not pass:
unsupported inferred candidate skill as truth.

### Resume Strategist → Application Operator
Pass:
approved/recommended resume variant, packet prep inputs.
External submit authority remains separate.

### CRM Agent → Interview Agent
Pass:
application/contact/interview refs and source messages.
No send/calendar authority.

### Analytics Agent → Market Scout
Pass:
strategy recommendation/hypothesis and evidence.
Scout may change search focus but not mutate historical outcomes.

## Loop protection

Runtime should track:
- handoff count,
- repeated task signature,
- same-agent bounce,
- unchanged NEEDS_REVIEW state.

When threshold exceeded:
- stop and request review rather than continuing model-to-model chatter.

## Acceptance tests

- permission cannot increase through handoff,
- missing fact stays unresolved,
- source refs survive multi-hop handoff,
- stale artifact warning propagates,
- one agent failure can route to alternate eligible agent without losing state,
- handoff cycle detected,
- restart preserves pending handoff.

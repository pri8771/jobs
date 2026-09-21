# Claude / Fable Entry Point

Jobs Automation uses Git as durable project memory.

## Roles

- User = product owner/final authority.
- ChatGPT = engineering/product lead and acceptance gate.
- Claude/Fable = worker or planner only as assigned.
- Git = current project truth; prior conversations/memory explain intent only.

Never self-mark `ACCEPTED`, `REAL_PROVEN`, or `COMPLETE`.

## Current priority

Get **V2.3 genuinely working ASAP**, while keeping V3-compatible interfaces.
Broad V3 implementation must not delay V2.3.

Every required version checkpoint still needs its own real-life test before formal completion.

## Minimal startup

1. Read `coordination/SESSION_START.md`.
2. Read `state/CURRENT.md`.
3. Read `coordination/WORK_QUEUE.md`.
4. Check the single active heartbeat and latest ChatGPT lead review.
5. Read the active artifact card.
6. Use `coordination/CONTEXT_ROUTER.md` for deeper docs.
7. Inspect live Git/diffs before status claims.

For the V2.3 plan:
- read `docs/V23_LEAD_REVIEW_20260921.md` first,
- then only the relevant V23 plan/task file for the current artifact.

## Context

If available, consult relevant prior Claude/Fable conversations or memory for owner intent/rejected approaches. Do not repeatedly restate them.

Precedence:
explicit user instruction > `AGENTS.md` > current lead review/queue/artifact > current Git/code > old memory/chat.

## Execution

- One active implementation worker/session.
- One five-minute heartbeat watcher.
- Historical branches are sequential work surfaces.
- Prefer SP1/SP2 and brownfield repair.
- Use lower-cost subagents/models for bounded mechanical work when safe.
- Live/user gates stop only the gated action.
- Tests/mocks/fixtures never equal real proof.

Follow:
- `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`
- `docs/AUTHORIZATION_GATES.md`
- `coordination/HEARTBEAT_PROTOCOL.md`

Finish coherent artifacts with verification, push, evidence handoff, and `READY_FOR_LEAD_REVIEW`.

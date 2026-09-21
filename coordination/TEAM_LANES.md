# Historical Work Surfaces / Single Active Session

Authoritative operating model:
**one Antigravity implementation session is active at a time.**

The historical lane branches remain useful because they preserve code ownership, PR history, and bounded work surfaces. They are not three simultaneous active worker sessions.

ChatGPT is engineering/product lead and acceptance gate.
`worker-pc` may provide independent bounded audit/support; it is not an implementation session.

Canonical execution program:
- `docs/ANTIGRAVITY_V1_4_TO_V1_7_EXECUTION.md`

## Current sequential order

1. Lane 1 work surface — V1.4 real-proof critical path
2. Lane 2 work surface — V1.5 assisted application, then V1.6 when authorized
3. Lane 3 work surface — V1.7 recruiting operations
4. later V2.0/V2.3/V3.0 work per canonical roadmap/prep plan

Only one of these work surfaces is active in Antigravity at a time.

## Lane 1 work surface — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`

Lane file:
- `coordination/lanes/LANE_1.md`

Owns:
- RP14 proof-tool integrity
- after P0A acceptance, genuine V1.4 real proof
- later candidate provenance/Gmail-readiness work when assigned

Priority:
- P0 until V1.4 proof gate is cleared

## Lane 2 work surface — V1.5 / V1.6 Application Execution

Branch:
- `worker/v15-assisted-application`

Lane file:
- `coordination/lanes/LANE_2.md`

Current scope:
- preserve accepted A-R15-01..05
- finish/verify A-R15-06..09
- V1.6 starts only after V1.5 acceptance or explicit lead authorization

No live submission authority is implied.

## Lane 3 work surface — V1.7 Recruiting Operations

Branch:
- `worker/recruiting-ops`

Lane file:
- `coordination/lanes/LANE_3.md`

Owns when this becomes the active work surface:
- audit/close remaining A-V17-CRM-EVIDENCE gaps
- audit/close remaining A-V17-INTERVIEW-FOLLOWUP gaps
- bounded V2.0 recruiting/reliability support later

Substantial Lane 3 work is already accepted/merged; audit before rebuilding anything.

## Paused historical branches

Old Lane D / `worker/v23-foundations`:
- paused as an implementation session.

Old Scout / `scout/qa-prep`:
- paused as an active session.

Old Lane C / `worker/live-data-foundations`:
- superseded by the current work-surface structure.

## Heartbeat

One active Antigravity session = exactly one heartbeat watcher.

When changing work surfaces:
- stop old watcher,
- switch/sync branch,
- start one watcher for the new active work surface.

See:
- `coordination/HEARTBEAT_PROTOCOL.md`

## Shared-file rule

Antigravity does not edit lead-owned project truth unless explicitly assigned:
- `coordination/ARTIFACT_INDEX.md`
- `coordination/WORK_QUEUE.md`
- `coordination/CONTEXT.md`
- `coordination/AI_SYNC.md`
- `coordination/HEARTBEAT_DASHBOARD.md`
- `state/CURRENT.md`
- `docs/ROADMAP_1_TO_3.md`

## Review model

1. Antigravity works the current historical lane branch,
2. the single heartbeat watcher proves session liveness,
3. worker pushes a coherent tested batch,
4. ChatGPT reviews actual diff/tests/CI,
5. worker-pc may provide bounded independent audit,
6. only ChatGPT updates acceptance/integration truth.

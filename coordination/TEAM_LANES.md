# Active Team Lanes

Authoritative operating model: **3 implementation lanes**.

ChatGPT is engineering/product lead and acceptance gate.
`worker-pc` is an independent review/support resource when available; it is not a project lane.

## Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`

Lane file:
- `coordination/lanes/LANE_1.md`

Owns:
- RP14-T1..T7 proof-tool integrity
- after P0A acceptance, RP14-C1..C3 real input readiness
- first genuine V1.4 real-proof execution when real inputs are present
- then candidate provenance / Gmail-readiness work previously assigned to old Lane C

Primary paths:
- proof scripts/schema/tests
- later provenance/Gmail paths

Priority:
- P0

## Lane 2 — V1.5 Application Safety

Branch:
- `worker/v15-assisted-application`

Lane file:
- `coordination/lanes/LANE_2.md`

Owns:
- preserve accepted A-R15-01..05
- A-R15-06..09
- real-proof execution only if Lane 1 is P0A-accepted and this machine has genuine selected resume bytes
- V1.6 remains blocked

Primary paths:
- `src/jobs_automation/browser/`
- application execution tests

## Lane 3 — V1.7 / V2.0 Recruiting & Reliability

Branch:
- `worker/recruiting-ops`

Lane file:
- `coordination/lanes/LANE_3.md`

Owns:
- preserve accepted B-R17-03 / B-R20-07 / B-R20-08
- B-R20-05 / J20-14 repair
- B-R20-01 / B-R20-02 headline funnel repair
- later J20G-04 after Gmail readiness exists

Primary paths:
- lifecycle / worker / health / analytics / dashboard tests

## Paused lanes

Old Lane D / `worker/v23-foundations`:
- PAUSED.
- V2.3 work is intentionally deferred until V1.4 is complete and V2.0 is materially closer to engineering acceptance.

Old Scout / `scout/qa-prep`:
- PAUSED as an active session.
- Independent review is performed by ChatGPT plus `worker-pc` when useful.
- Scout branch/history remains available as audit evidence.

Old Lane C / `worker/live-data-foundations`:
- SUPERSEDED by clean Lane 1 branch `worker/v14-real-proof`.
- It had no worker production code ahead of main.

## Shared-file rule

Workers do not edit lead-owned project truth unless explicitly assigned:
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md
- coordination/CONTEXT.md
- coordination/AI_SYNC.md
- coordination/HEARTBEAT_DASHBOARD.md
- state/CURRENT.md
- docs/ROADMAP_1_TO_3.md

## Review model

1. worker implements on its lane branch,
2. heartbeat/progress feed proves liveness,
3. worker pushes coherent tested batch,
4. ChatGPT reviews actual diff/tests/CI,
5. worker-pc may perform independent bounded audit,
6. only ChatGPT updates acceptance state / merges accepted work.

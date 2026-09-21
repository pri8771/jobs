# Team Lanes

Authoritative operating model: **exactly three active implementation lanes**.

ChatGPT is engineering/product lead and the acceptance/integration gate.
`worker-pc` in `pri8771/remote-workers` is infrastructure for bounded independent support only; it is not a fourth implementation lane.

| Lane | Branch | Lane file | PR | Current scope |
|---|---|---|---|---|
| Lane 1 | `worker/v14-real-proof` | `coordination/lanes/LANE_1.md` | draft #8 | P0 RP14-T1..T7 proof-tool integrity → genuine V1.4 real proof → candidate provenance/Gmail readiness when assigned |
| Lane 2 | `worker/v15-assisted-application` | `coordination/lanes/LANE_2.md` | draft #2 | Preserve A-R15-01..05; finish/verify A-R15-06..09; no V1.6 until gates pass |
| Lane 3 | `worker/recruiting-ops` | `coordination/lanes/LANE_3.md` | #3 merged; create a new draft PR only when new worker commits are ahead of main | Preserve accepted B-R17-03/B-R20-07/B-R20-08 and B-R20-05/J20-14 + B-R20-01/B-R20-02; verify integrated baseline and repair only evidence-backed regressions |

## Lane 1 — V1.4 real-proof critical path

Priority: P0.

The lane owns:
- RP14-T1..T7 proof-tool integrity,
- after P0A lead acceptance, real private-input readiness and the genuine V1.4 packet proof,
- later candidate provenance/Gmail-readiness work only when explicitly assigned.

No private candidate/resume proof run before ChatGPT accepts P0A.
No browser application submission authority is implied.

## Lane 2 — V1.5 assisted application

Preserve accepted A-R15-01..05.
Current bounded work is A-R15-06..09.
Do not expand into V1.6 until the V1.5 gate passes or the owner/lead explicitly authorizes it.

Lane 2 may execute the V1.4 packet proof only after P0A and only if that machine genuinely has the exact selected private resume mapping. It may not synthesize, relabel, copy, or silently substitute another resume.

## Lane 3 — recruiting/reliability

PR #3's B repair batch was reviewed, accepted, and merged to main.
Accepted work includes:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- B-R20-05 / J20-14,
- B-R20-01,
- B-R20-02.

These task IDs remain the owner-named Lane 3 work surface, but accepted behavior must not be rebuilt merely to create activity. Lane 3 first synchronizes to current main and verifies the integrated baseline. Repair only a real regression or a newly evidenced acceptance gap.

## Paused / superseded workers

Not active:
- old Lane C / `worker/live-data-foundations`,
- old Lane D / `worker/v23-foundations`,
- old Scout / `scout/qa-prep`.

Do not reopen them just to keep workers busy. Reopen another lane only for a concrete critical-path or integration bottleneck with lead authorization.

## Heartbeat

All three active lanes use:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- interval 5 minutes,
- exactly one watcher per lane,
- no proving/watch/hourly transitions.

If a lane still runs DAYWATCH or another historical watcher, stop it once, sync the lane to latest main, and start exactly one current-epoch watcher.

Canonical protocol:
- `coordination/HEARTBEAT_PROTOCOL.md`

## Shared-file discipline

Workers do not edit lead-owned project truth unless explicitly assigned:
- `coordination/ARTIFACT_INDEX.md`
- `coordination/WORK_QUEUE.md`
- `coordination/TEAM_LANES.md`
- `coordination/CONTEXT.md`
- `coordination/AI_SYNC.md`
- `coordination/HEARTBEAT_DASHBOARD.md`
- `state/CURRENT.md`

## Review model

1. Lane worker implements a bounded assignment on its branch.
2. Lane heartbeat provides durable liveness/progress evidence.
3. Worker pushes a coherent tested batch and marks `READY_FOR_LEAD_REVIEW`.
4. ChatGPT reviews actual diff, tests, branch CI, and artifact evidence.
5. `worker-pc` may provide bounded independent audit/support when useful.
6. Only ChatGPT marks milestone-relevant work accepted and integrates it.
7. After integration, ChatGPT writes the next bounded assignment into that lane file.

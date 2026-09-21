# Heartbeat Protocol

Purpose:
Provide durable liveness/progress evidence for the single active Antigravity implementation session.

## Authoritative owner mode

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes while active
- active implementation sessions: exactly 1
- heartbeat watchers for that active session: exactly 1
- cadence transitions: none

All DAYWATCH / PROVING_5M / WATCH_15M_24H / STEADY_HOURLY instructions are historical and superseded.

## One session, one heartbeat

The active Antigravity session works one historical lane branch at a time.

Historical work surfaces:
- Lane 1 — `worker/v14-real-proof`
- Lane 2 — `worker/v15-assisted-application`
- Lane 3 — `worker/recruiting-ops`

Only the currently active work surface gets a watcher.

If the same Antigravity session changes branches:
1. finish/push a coherent batch,
2. stop the old watcher,
3. switch/sync the next branch,
4. start exactly one watcher for the new active branch.

Never leave two heartbeat watcher processes running.

## Heartbeat files

Use the existing lane-specific heartbeat file for whichever historical branch is currently active:
- `coordination/heartbeats/LANE_1.md`
- `coordination/heartbeats/LANE_2.md`
- `coordination/heartbeats/LANE_3.md`

The inactive branch heartbeat files are historical status, not evidence that another worker session is active.

## Watcher

For the currently active historical lane only:

```bash
python scripts/worker_heartbeat_watch.py --lane <1|2|3> --epoch FIVE_MIN_2026_09_21 --detach
```

Start it once.
Do not restart it unless it died or the active session is intentionally switching branches.
Before restarting, ensure the prior process is stopped.

## Heartbeat content

A normal heartbeat may be minimal:

`Still working on <artifact/task>; no blocker.`

No code push is required at every heartbeat.

At a meaningful milestone/blocker/review boundary, include:
- current artifact/task,
- progress/evidence,
- blocker if any,
- branch/head,
- review state,
- lead action requested.

Valid review states:
- `WORKING`
- `READY_FOR_LEAD_REVIEW`
- `BLOCKED`

Valid lead actions:
- `NONE`
- `REVIEW`
- `DECOMPOSE`
- `ARCHITECTURE_DECISION`
- `USER_ACTION`

## Verification

Actual Git/file timestamps outrank worker self-claims.

Heartbeat is liveness/progress evidence only.
It never substitutes for:
- tests,
- CI,
- code review,
- artifact acceptance,
- real proof.

## Human-visible feed

Heartbeat pushes for the active numeric lane are mirrored to GitHub issue #7:
`Jobs Automation — Live Progress`.

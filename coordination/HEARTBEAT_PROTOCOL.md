# Heartbeat Protocol

Purpose: durable liveness/progress evidence for the **single active implementation session**.

## Authoritative owner standard

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes
- active implementation sessions: exactly 1
- active heartbeat watchers: exactly 1
- cadence transitions: none

There is no proving phase, 24-hour watch, or hourly transition.

All `DAYWATCH_2026_09_21`, `PROVING_5M`, `WATCH_15M_24H`, and `STEADY_HOURLY` instructions are historical and superseded.

## Historical lane files

Historical work surfaces may still use:
- Lane 1 / `worker/v14-real-proof` / `coordination/heartbeats/LANE_1.md`
- Lane 2 / `worker/v15-assisted-application` / `coordination/heartbeats/LANE_2.md`
- Lane 3 / `worker/recruiting-ops` / `coordination/heartbeats/LANE_3.md`

These files do **not** mean three workers should run.

Only the branch/work surface currently owned by the one active implementation session has a live watcher.

Inactive historical heartbeat files are audit history.

## Start / branch switch

Before starting a watcher:
1. check whether the active implementation session already has one,
2. never start a duplicate.

When the implementation session intentionally switches branch/work surface:
1. finish/push the coherent batch,
2. stop the old watcher,
3. verify the old watcher stopped,
4. switch/sync branch,
5. start exactly one watcher for the new active work surface,
6. verify current epoch/mode/interval.

Example commands when that historical work surface is active:

Lane 1:
```bash
python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --detach
```

Lane 2:
```bash
python scripts/worker_heartbeat_watch.py --lane 2 --epoch FIVE_MIN_2026_09_21 --detach
```

Lane 3:
```bash
python scripts/worker_heartbeat_watch.py --lane 3 --epoch FIVE_MIN_2026_09_21 --detach
```

Run **only one** of these for the active implementation session.

## Planning sessions

A Fable/Claude planning-only session is not a second implementation worker.

If an implementation watcher is already active:
- inspect it,
- do not start another watcher merely because planning is happening.

## Required heartbeat metadata

Active heartbeat should expose:
- lane/work surface
- branch
- heartbeat_epoch
- mode
- interval_minutes
- heartbeat_count
- last_check_in_utc
- current artifact/task
- progress_note
- review_state
- lead_action_requested

Expected:
- `heartbeat_epoch: FIVE_MIN_2026_09_21`
- `mode: ACTIVE_5M`
- `interval_minutes: 5`

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

A normal heartbeat may be:
`Still working on <artifact/task>; no blocker.`

No code push is required every heartbeat.

## Verification

Actual branch commits and heartbeat-file timestamps outrank worker self-claims.

Heartbeat proves liveness/progress only. It never establishes:
- correctness,
- CI acceptance,
- artifact acceptance,
- `REAL_PROVEN`,
- milestone `COMPLETE`.

## Human-visible feed

The active heartbeat should be mirrored to GitHub issue #7 when Actions infrastructure is available.

If heartbeat commits continue but issue comments stop:
- first check Actions runner/account state,
- do not rewrite working heartbeat logic solely to create activity,
- record infrastructure blockage truthfully.

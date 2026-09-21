# Heartbeat Protocol

Purpose: durable liveness/progress evidence for the **single active implementation session**.

## Authoritative owner standard

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes
- active implementation sessions: exactly 1
- active watchers: exactly 1
- cadence transitions: none

Historical proving/15-minute/24-hour/hourly modes are superseded.

## Historical heartbeat files

Historical branches may use:
- `coordination/heartbeats/LANE_1.md`
- `coordination/heartbeats/LANE_2.md`
- `coordination/heartbeats/LANE_3.md`

These files are audit history. They do not authorize three simultaneous workers.

Only the currently active implementation work surface has a live watcher.

## Start/restart/switch

Before starting:
1. determine the current active implementation branch,
2. verify no watcher is already running,
3. start exactly one watcher.

When switching work surfaces:
1. finish/push the current coherent batch,
2. stop the old watcher,
3. verify it stopped,
4. switch/sync branch,
5. start exactly one watcher for the new work surface.

Example commands for historical work surfaces:

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

Run only the command for the one active work surface.

Planning-only sessions do not launch a second watcher.

## Metadata

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

Review states:
- `WORKING`
- `READY_FOR_LEAD_REVIEW`
- `BLOCKED`

Lead actions:
- `NONE`
- `REVIEW`
- `DECOMPOSE`
- `ARCHITECTURE_DECISION`
- `USER_ACTION`

A heartbeat may simply say:
`Still working on <artifact/task>; no blocker.`

No code push is required every heartbeat.

## Interpretation

Actual branch/file timestamps outrank self-claims.

Heartbeat proves liveness only. It never establishes:
- correctness,
- CI acceptance,
- artifact acceptance,
- `REAL_PROVEN`,
- `COMPLETE`.

## Issue #7

Mirror the active heartbeat to issue #7 when Actions infrastructure works.

If heartbeat commits continue but comments stop:
- inspect Actions account/runner state first,
- do not rewrite working heartbeat logic just to manufacture visible activity.

If no implementation worker is currently active, stale historical heartbeat files are not themselves an error.

# Heartbeat Protocol

Purpose: provide durable liveness/progress evidence for all three active implementation lanes.

## Authoritative owner standard

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes
- active implementation lanes: exactly 3
- watchers: exactly one watcher per active lane
- cadence transitions: none

There is no proving phase, 24-hour watch, or hourly transition.
All `DAYWATCH_2026_09_21`, `PROVING_5M`, `WATCH_15M_24H`, and `STEADY_HOURLY` instructions are historical and superseded.

## Active lanes

- Lane 1 — `worker/v14-real-proof` — `coordination/heartbeats/LANE_1.md`
- Lane 2 — `worker/v15-assisted-application` — `coordination/heartbeats/LANE_2.md`
- Lane 3 — `worker/recruiting-ops` — `coordination/heartbeats/LANE_3.md`

Each lane should have one current-epoch watcher while its worker session is active.
Do not use one lane's watcher as evidence for another lane.
Do not launch duplicate watchers in the same lane.

## Migration from an old watcher

If a lane still shows an old epoch/mode:
1. stop the old watcher once,
2. pull/rebase latest main as required by the lane file,
3. start exactly one current watcher,
4. verify the lane file shows `FIVE_MIN_2026_09_21` / `ACTIVE_5M` / `interval_minutes: 5`,
5. verify issue #7 receives the corresponding heartbeat comment.

## Watcher commands

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

Start each lane watcher once. Restart only if it died or the lane intentionally stopped/restarted its session; before restart, ensure the prior watcher is stopped.

## Required heartbeat metadata

Current heartbeat files should expose at least:
- `lane`
- `branch`
- `heartbeat_epoch`
- `mode`
- `interval_minutes`
- `heartbeat_count`
- `last_check_in_utc`
- `current_task`
- `progress_note`
- `review_state`
- `lead_action_requested`

Expected fixed values:
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

A normal heartbeat may be minimal:
`Still working on <artifact/task>; no blocker.`

At a meaningful milestone/blocker/review boundary, include the evidence/blocker and correct review/lead-action state.

## Verification

Actual branch commit timestamps and heartbeat-file contents outrank worker self-claims.
A worker cannot declare itself current if the actual timestamp stream disagrees.

Heartbeat is liveness/progress evidence only. It never establishes:
- code correctness,
- CI acceptance,
- artifact acceptance,
- `REAL_PROVEN`,
- version `COMPLETE`.

## Human-visible progress

Every active-lane heartbeat push should be mirrored automatically to GitHub issue #7, `Jobs Automation — Live Progress`, by `.github/workflows/heartbeat-progress.yml`.

At each ChatGPT lead run:
- inspect actual Lane 1/2/3 heartbeat timestamps,
- inspect the matching issue #7 comments,
- if heartbeat commits continue but comments stop, diagnose/repair the workflow,
- post one concise ChatGPT lead comment to issue #7 regardless of whether code changed.

# Heartbeat Protocol

Purpose: provide durable liveness/progress evidence for the **exactly three active implementation lanes** authorized by the owner and `AGENTS.md`.

## Authoritative owner standard

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes
- active implementation lanes: exactly 3
- watchers: exactly one watcher per active lane
- cadence transitions: none

There is no proving phase, 24-hour watch, or hourly transition. Any `DAYWATCH_2026_09_21`, `PROVING_5M`, `WATCH_15M_24H`, or `STEADY_HOURLY` instruction is historical and superseded.

## Active lanes

- Lane 1 — `worker/v14-real-proof` — `coordination/heartbeats/LANE_1.md`
- Lane 2 — `worker/v15-assisted-application` — `coordination/heartbeats/LANE_2.md`
- Lane 3 — `worker/recruiting-ops` — `coordination/heartbeats/LANE_3.md`

Each active lane owns one current-epoch watcher while its worker session is active. One lane's heartbeat is never evidence for another lane. Do not launch duplicate watchers in a lane.

## Migration from an old watcher

If an active lane still shows an old epoch/mode:
1. stop that old watcher once,
2. confirm it stopped,
3. pull/rebase latest main as required by the lane file,
4. start exactly one current watcher for that lane,
5. verify the heartbeat file shows `FIVE_MIN_2026_09_21` / `ACTIVE_5M` / `interval_minutes: 5`.

If a current-epoch watcher has stopped, verify no old process remains before restarting exactly one watcher.

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

## Required heartbeat metadata

Each current heartbeat should expose at least:
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

A normal heartbeat may be minimal: `Still working on <artifact/task>; no blocker.`

## Verification

Actual branch commit timestamps and heartbeat-file contents outrank worker self-claims. A worker cannot declare itself current if the actual timestamp stream disagrees.

Heartbeat is liveness/progress evidence only. It never establishes code correctness, CI acceptance, artifact acceptance, `REAL_PROVEN`, or version `COMPLETE`.

## Human-visible progress

Every active-lane heartbeat push should be mirrored automatically to GitHub issue #7, `Jobs Automation — Live Progress`, by `.github/workflows/heartbeat-progress.yml` when GitHub Actions runners are available.

At each ChatGPT lead run:
- inspect actual Lane 1/2/3 heartbeat timestamps,
- inspect matching issue #7 comments,
- if heartbeat commits continue but comments stop, diagnose runner/workflow state before changing heartbeat logic,
- post one concise ChatGPT lead comment to issue #7 regardless of whether code changed.

## Scope boundary

Planning-only sessions do not replace or collapse the three active implementation lanes. Old Lane C, old Lane D, and old Scout remain paused/superseded. `worker-pc` is bounded support infrastructure, not a fourth Jobs implementation lane.
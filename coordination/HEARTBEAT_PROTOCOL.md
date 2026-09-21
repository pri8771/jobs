# Heartbeat Protocol

Purpose:
Provide durable worker liveness and concise progress evidence through Git.

## Current authoritative epoch

- `DAYWATCH_2026_09_21`

Exactly three active lanes:
- Lane 1 — `worker/v14-real-proof`
- Lane 2 — `worker/v15-assisted-application`
- Lane 3 — `worker/recruiting-ops`

Historical A/B/C/D/Scout files and any other epoch do not count for this exercise.

## Required cadence

### Phase 1 — `PROVING_5M`

A fresh/current-epoch worker must produce 3 consecutive worker-authored heartbeats with gaps of **4–7 minutes**.

- first valid check-in: 1/3
- next 4–7 minutes later: 2/3
- next 4–7 minutes later: 3/3
- any gap outside 4–7 minutes resets the proving streak to 1 on the newest check-in

After verified 3/3, enter `WATCH_15M_24H`.

### Phase 2 — `WATCH_15M_24H`

Publish approximately every 15 minutes for a clean 24-hour window.

- any gap **>20 minutes** increments `missed_intervals`
- that miss restarts the clean 24-hour window from the newest check-in
- historical misses remain visible; the current clean-window start is `watch_started_utc`
- after a clean 24 hours, switch to `STEADY_HOURLY`

### Phase 3 — `STEADY_HOURLY`

After the clean 24-hour watch completes, publish approximately hourly.

## Active heartbeat files

- Lane 1: `coordination/heartbeats/LANE_1.md`
- Lane 2: `coordination/heartbeats/LANE_2.md`
- Lane 3: `coordination/heartbeats/LANE_3.md`

Required top-level metadata:

```yaml
lane: 1
branch: worker/v14-real-proof
heartbeat_epoch: DAYWATCH_2026_09_21
mode: PROVING_5M
interval_minutes: 5
consecutive_on_time: 1
last_check_in_utc: 2026-09-21T16:00:00Z
watch_started_utc: null
watch_until_utc: null
watch_checkins: 0
missed_intervals: 0
watch_completed_utc: null
current_task: assigned lane task
progress_note: still working on assigned task
review_state: WORKING
lead_action_requested: NONE
```

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

## Detached watcher

Launch one watcher per active worker session:

```bash
python scripts/worker_heartbeat_watch.py --lane <1|2|3> --epoch DAYWATCH_2026_09_21 --detach
```

Do not run a watcher from another epoch at the same time. If a superseded `FIVE_MIN_2026_09_21` watcher is running, stop it before launching/continuing DAYWATCH.

## Verification rules

ChatGPT lead verifies actual Git commit/file timestamps. Worker self-claims do not override timestamps.

Heartbeat proves liveness/progress only. It never substitutes for code review, tests, CI, artifact acceptance, or real proof.

## Human-visible feed

Every active numeric-lane heartbeat push triggers `.github/workflows/heartbeat-progress.yml` and posts to GitHub issue #7, `Jobs Automation — Live Progress`.

The scheduled ChatGPT lead check remains hourly due platform limits and must also post one concise lead comment to issue #7 on every run.

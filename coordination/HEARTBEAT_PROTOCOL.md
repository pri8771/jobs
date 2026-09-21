# Heartbeat Protocol

Purpose:
Provide durable worker liveness evidence through Git without relying on a chat session remembering to check in.

## Current liveness exercise

Heartbeat epoch:
- `DAYWATCH_2026_09_21`

For fresh sessions started during this exercise:

### Stage 1 — PROVING_5M

Each active lane must produce **3 consecutive worker-authored heartbeats** approximately five minutes apart.

Mode:
- `PROVING_5M`
- `interval_minutes: 5`

Valid proving gap:
- 4 to 7 minutes between worker-authored check-ins.

Rules:
- first heartbeat establishes 1/3,
- an on-time next heartbeat advances the streak,
- any gap outside 4–7 minutes resets the streak to 1,
- historical heartbeats from prior epochs do not count.

After 3/3, automatically switch to:

- `mode: WATCH_15M_24H`
- `interval_minutes: 15`

### Stage 2 — WATCH_15M_24H

For the next full 24 hours:

- heartbeat every 15 minutes,
- a gap greater than 20 minutes counts as a missed interval,
- any missed interval restarts the clean 24-hour watch window,
- preserve all history and increment `missed_intervals`,
- after a clean full 24-hour watch, automatically switch to `STEADY_HOURLY`.

Expected clean watch:
- approximately 96 fifteen-minute heartbeat pushes.

### Stage 3 — STEADY_HOURLY

After the 24-hour watch completes with zero missed intervals:

- `mode: STEADY_HOURLY`
- `interval_minutes: 60`

Continue hourly while the worker remains active, plus immediate heartbeat on blockers or review-ready events.

## Detached watcher

Fresh sessions should launch:

```bash
python scripts/worker_heartbeat_watch.py --lane <A|B|C|D|SCOUT> --epoch DAYWATCH_2026_09_21 --detach
```

The watcher:
- runs independently of the implementation agent,
- uses a separate lightweight clone under `.local/heartbeat-watch/`,
- pushes only the lane heartbeat file,
- does not modify the implementation working tree,
- performs 5-minute proving automatically,
- then performs the 15-minute 24-hour watch automatically,
- switches to hourly after a clean 24-hour watch.

The implementation session may continue normal work after the watcher starts.

## Active worker heartbeat files

- Lane 1: `coordination/heartbeats/LANE_1.md`
- Lane 2: `coordination/heartbeats/LANE_2.md`
- Lane 3: `coordination/heartbeats/LANE_3.md`

Historical A/B/C/D/Scout heartbeat files are preserved but are not active for the current operating model.

Only the lane/watcher edits its heartbeat file on the lane branch.

## Required top-level metadata

```yaml
lane: 1
branch: worker/v14-real-proof
heartbeat_epoch: DAYWATCH_2026_09_21
mode: PROVING_5M
interval_minutes: 5
consecutive_on_time: 1
last_check_in_utc: 2026-09-21T14:45:00Z
watch_started_utc: null
watch_until_utc: null
watch_checkins: 0
missed_intervals: 0
watch_completed_utc: null
review_state: WORKING
lead_action_requested: NONE
```

Valid modes:
- PROVING_5M
- WATCH_15M_24H
- STEADY_HOURLY

Valid review states:
- WORKING
- READY_FOR_LEAD_REVIEW
- BLOCKED

Valid lead actions:
- NONE
- REVIEW
- DECOMPOSE
- ARCHITECTURE_DECISION
- USER_ACTION

## Immediate event heartbeat

Regardless of scheduled cadence, push an immediate heartbeat when:
- a coherent implementation batch is READY_FOR_LEAD_REVIEW,
- the lane becomes BLOCKED,
- USER_ACTION is required,
- a safety/architecture decision is required.

Event heartbeats do not by themselves advance a cadence streak if they fall outside the cadence window.

## Lead verification

ChatGPT lead verifies:
- branch commit timestamps,
- heartbeat metadata,
- epoch,
- proving gaps,
- 24-hour watch gaps,
- CI/PR state,
- review/blocker requests.

A worker may not self-declare the cadence successful when timestamps disagree.

## Important scheduler limitation

ChatGPT scheduled lead automation remains hourly; the platform does not support a 5-minute or 15-minute scheduled ChatGPT poll.

Therefore:
- worker watcher generates 5m/15m evidence,
- GitHub records it immediately,
- ChatGPT audits the accumulated evidence hourly and on user-requested status checks.

## Shared-file discipline

Workers do not edit shared lead-owned truth unless explicitly assigned:
- `coordination/WORK_QUEUE.md`
- `coordination/ARTIFACT_INDEX.md`
- `coordination/CONTEXT.md`
- `coordination/AI_SYNC.md`
- `state/CURRENT.md`
- `coordination/HEARTBEAT_DASHBOARD.md`


## Human-visible progress feed

Each active Lane 1/2/3 heartbeat push triggers `.github/workflows/heartbeat-progress.yml`.

The workflow posts a concise comment to GitHub issue #7 containing:
- lane,
- current task,
- progress note,
- heartbeat stage/streak/watch count,
- blocker/review state,
- branch and commit.

The default watcher progress note is `still working on assigned task`. A worker may update its lane heartbeat `progress_note` when a more useful concise status is available.

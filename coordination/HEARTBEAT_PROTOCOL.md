# Heartbeat Protocol

Purpose:
Provide durable worker liveness and concise progress evidence through Git.

## Active standard

There is one heartbeat cadence for every active lane:

**every 5 minutes while the lane session is active.**

There are no proving, 15-minute, 24-hour, or hourly transitions.

Current epoch:
- `FIVE_MIN_2026_09_21`

Active lanes:
- Lane 1 — `worker/v14-real-proof`
- Lane 2 — `worker/v15-assisted-application`
- Lane 3 — `worker/recruiting-ops`

Historical cadence/heartbeat entries are preserved only as audit history.

## Detached watcher

Launch exactly one watcher per active lane:

```bash
python scripts/worker_heartbeat_watch.py --lane <1|2|3> --epoch FIVE_MIN_2026_09_21 --detach
```

The watcher:
- uses a separate lightweight clone,
- never dirties the implementation working tree,
- emits at most one heartbeat inside a 4-minute minimum gap,
- continues every 5 minutes until the process/session stops,
- tolerates accidental duplicate watcher processes by suppressing too-soon duplicate writes,
- never changes cadence.

Do not restart the watcher merely because a new chat/session message arrives.

## Active heartbeat files

- Lane 1: `coordination/heartbeats/LANE_1.md`
- Lane 2: `coordination/heartbeats/LANE_2.md`
- Lane 3: `coordination/heartbeats/LANE_3.md`

## Required metadata

```yaml
lane: 1
branch: worker/v14-real-proof
heartbeat_epoch: FIVE_MIN_2026_09_21
mode: ACTIVE_5M
interval_minutes: 5
heartbeat_count: 1
last_check_in_utc: 2026-09-21T16:45:00Z
current_task: V1.4 real-proof tooling RP14-T1..T7
progress_note: still working on assigned task
review_state: WORKING
lead_action_requested: NONE
```

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

## Progress content

Every heartbeat must contain a useful concise update. It may be as small as:
- `still working on assigned task`
- `implementing verifier receipt binding; no blocker`
- `tests running; no blocker`

Code does not need to be pushed every heartbeat.

Workers should update `progress_note` whenever a more specific short status is available.

## Immediate events

Do not wait for the next five-minute tick when:
- BLOCKED
- READY_FOR_LEAD_REVIEW
- USER_ACTION required
- architecture/safety decision required

Update the heartbeat immediately, then resume normal five-minute cadence.

## Human-visible feed

Each Lane 1/2/3 heartbeat push triggers `.github/workflows/heartbeat-progress.yml` and posts to GitHub issue #7:
`Jobs Automation — Live Progress`.

## Lead-side limitation

ChatGPT's scheduled lead automation remains hourly. GitHub receives worker heartbeat evidence every five minutes; ChatGPT audits it hourly and whenever the user explicitly asks for status.

Heartbeat proves liveness/progress only. It never substitutes for code review, tests, CI, artifact acceptance, or real proof.

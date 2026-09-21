# Heartbeat Dashboard

Current operating model:
- exactly 3 active implementation lanes
- historical A/B/C/D/Scout heartbeat streams are CLOSED and do not count
- heartbeat epoch: `DAYWATCH_2026_09_21`
- human-visible feed: GitHub issue #7 `Jobs Automation — Live Progress`

## Required cadence

Stage 1:
- PROVING_5M
- 3 consecutive worker-authored heartbeats
- valid gap: 4–7 minutes

Stage 2:
- WATCH_15M_24H
- heartbeat every 15 minutes
- gap >20 minutes counts as a miss and restarts the clean 24-hour window

Stage 3:
- STEADY_HOURLY after clean 24-hour watch

## Current verified state

| Lane | Branch | Assignment | Proving | Watch | State |
|---|---|---|---:|---:|---|
| 1 | worker/v14-real-proof | RP14-T1..T7 real-proof tooling | 0/3 | not started | waiting for first worker heartbeat |
| 2 | worker/v15-assisted-application | A-R15-06..09 V1.5 safety | 2/3 | not started | ACTIVE; 15:58:58Z then 16:04:00Z is a valid ~5m interval |
| 3 | worker/recruiting-ops | B-R20-05 + B-R20-01/02 | 0/3 | not started | waiting for first worker heartbeat |

## Closed historical streams

These remain in Git only as audit history and are no longer active:
- LANE_A
- LANE_B
- LANE_C
- LANE_D
- SCOUT

No historical heartbeat contributes to Lane 1/2/3 cadence or acceptance.

## Visible progress

GitHub issue #7 is receiving active-lane heartbeat comments.

Verified:
- Lane 2 1/3 comment posted for 2026-09-21T15:58:58Z
- Lane 2 2/3 comment posted for 2026-09-21T16:04:00Z

The progress workflow may also post a setup/state comment when the heartbeat file changes without advancing the timestamp. Only timestamped worker heartbeat entries count toward cadence.

## Acceptance

Heartbeat proves liveness/progress only. It never substitutes for code review, tests, CI, artifact acceptance, or real-proof evidence.

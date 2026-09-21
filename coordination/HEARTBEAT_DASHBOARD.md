# Heartbeat Dashboard

Current operating model:
- exactly 3 active implementation lanes
- historical A/B/C/D/Scout streams are CLOSED
- epoch: `DAYWATCH_2026_09_21`
- visible feed: GitHub issue #7

## Required cadence

1. PROVING_5M — 3 consecutive worker-authored heartbeats, each 4–7 minutes apart
2. WATCH_15M_24H — every 15 minutes for a clean 24 hours; >20m gap restarts watch
3. STEADY_HOURLY after clean 24-hour watch

## Current verified state

| Lane | Branch | Assignment | Verified liveness | Lead state |
|---|---|---|---|---|
| 1 | worker/v14-real-proof | RP14-T1..T7 V1.4 proof tooling | 1/3 at 16:27:55Z | ACTIVE; first valid proving heartbeat |
| 2 | worker/v15-assisted-application | A-R15-06..09 | prior 3/3 + one 15m watch heartbeat existed, but watcher was restarted at 16:28:04Z; current stream is 1/3 at 16:28:06Z | ACTIVE but reset; previous successful watch was interrupted by duplicate restart |
| 3 | worker/recruiting-ops | B-R20-05 + B-R20-01/02 | 1/3 at 16:18:20Z; no 2nd heartbeat within 4–7m window | STALE / proving streak broken; next valid heartbeat must restart at 1/3 |

## Lane 1 evidence

- watcher reset: 16:27:53Z
- proving heartbeat 1/3: 16:27:55Z
- next heartbeat must land 4–7 minutes later to advance.

## Lane 2 evidence

Earlier valid sequence:
- 15:58:58Z -> 1/3
- 16:04:00Z -> 2/3
- 16:09:02Z -> 3/3
- 16:24:04Z -> first valid 15-minute watch heartbeat

Then a second watcher/session reset the same epoch:
- reset: 16:28:04Z
- new proving heartbeat: 16:28:06Z -> 1/3

Therefore current authoritative liveness is the newer stream at 1/3. Do not launch another watcher for Lane 2 while this one is running.

## Lane 3 evidence

- 16:18:20Z -> 1/3 and READY_FOR_LEAD_REVIEW
- no subsequent heartbeat in the required 4–7 minute proving window

Therefore the proving streak is broken. When Lane 3 resumes heartbeat proving, restart at 1/3.

## Visible progress

GitHub issue #7 is functioning and receiving active-lane heartbeat comments.

Heartbeat is liveness/progress evidence only. It never substitutes for code review, tests, CI, artifact acceptance, or real proof.

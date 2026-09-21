# Heartbeat Dashboard

Current operating model:
- exactly 3 active implementation lanes
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

## Current fresh-session state

| Lane | Branch | Current assignment | 5m proving | 24h watch | State |
|---|---|---|---:|---:|---|
| 1 | worker/v14-real-proof | RP14-T1..T7 real-proof tooling | 0/3 | not started | WAITING FOR FRESH SESSION |
| 2 | worker/v15-assisted-application | A-R15-06..09 V1.5 safety | 0/3 | not started | WAITING FOR FRESH SESSION |
| 3 | worker/recruiting-ops | B-R20-05 + B-R20-01/02 | 0/3 | not started | WAITING FOR FRESH SESSION |

Historical A/B/C/D/Scout heartbeats remain available for audit but do not count toward this operating model.

## Visible progress

Every Lane 1/2/3 heartbeat push should create a comment in GitHub issue #7 via:
- `.github/workflows/heartbeat-progress.yml`

Each comment includes:
- task,
- progress note,
- heartbeat stage,
- review/blocker state,
- branch + commit.

ChatGPT Jobs Lead Sync also posts one concise lead update hourly.

## Acceptance

Heartbeat proves liveness/progress only.
It never substitutes for:
- code review,
- tests,
- CI,
- artifact acceptance,
- real-proof evidence.

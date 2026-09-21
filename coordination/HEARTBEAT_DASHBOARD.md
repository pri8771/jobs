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

## Current verified state

| Lane | Branch | Current assignment | 5m proving | 24h watch | Lead-verified state |
|---|---|---|---:|---:|---|
| 1 | worker/v14-real-proof | RP14-T1..T7 real-proof tooling | 0/3 | not started | Branch identical to main; active `LANE_1.md` heartbeat still null; no worker implementation commit |
| 2 | worker/v15-assisted-application | A-R15-06..09 V1.5 safety | 0/3 | not started | PR #2 head `552da79`; CI green, but worker is still committing historical `LANE_A.md`; active `LANE_2.md` remains null and heartbeat validation fails on the obsolete file |
| 3 | worker/recruiting-ops | B-R20-05 + B-R20-01/02 | 0/3 | not started | PR #3 head `68595d1`; CI green, but branch is far behind main and still uses historical `LANE_B.md`; active `LANE_3.md` is not yet present on the branch |

Historical A/B/C/D/Scout heartbeats remain available for audit but do not count toward this operating model or epoch.

## Visible progress verification

`.github/workflows/heartbeat-progress.yml` is functioning for the active Lane 1/2/3 paths: GitHub Actions has posted issue #7 comments for active heartbeat-file pushes.

Current problem is worker migration, not feed delivery:
- Lane 2 continued committing the historical `LANE_A.md`, which the active progress-feed workflow intentionally ignores.
- Lane 3 has not rebased far enough to acquire/use `LANE_3.md`.
- Seed comments with `last_check_in_utc: null` are setup noise and do not count as worker-authored heartbeats.

Fresh worker sessions must rebase latest main and launch the numeric lane watcher so subsequent commits land in `LANE_1.md`, `LANE_2.md`, or `LANE_3.md` and automatically appear in issue #7.

## Acceptance

Heartbeat proves liveness/progress only.
It never substitutes for:
- code review,
- tests,
- CI,
- artifact acceptance,
- real-proof evidence.

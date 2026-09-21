# Heartbeat Dashboard

Authoritative epoch:
- `DAYWATCH_2026_09_21`

Cadence:
1. `PROVING_5M` — 3 consecutive worker-authored check-ins with 4–7 minute gaps.
2. `WATCH_15M_24H` — approximately every 15 minutes for a clean 24 hours; gap >20 minutes increments misses and restarts the clean window.
3. `STEADY_HOURLY` — only after a clean 24-hour watch.

Actual Git timestamps/file timestamps override worker self-claims.

## Lead verification — 2026-09-21 16:55Z

### Lane 1 — `worker/v14-real-proof`

- proving sequence: 16:27:55 → 16:32:56 → 16:37:59 UTC: **valid 3/3**
- mode: `WATCH_15M_24H`
- clean-window start: 16:37:59 UTC
- verified watch check-in: 16:53:01 UTC, 15.0-minute gap
- misses: 0
- current task: RP14-T1..T7 P0A rework
- code: PR #8 / commit `8f8c21f`; CI #401 green; lead review found four blocking proof-integrity defects

### Lane 2 — `worker/v15-assisted-application`

- proving sequence: 16:28:06 → 16:33:07 → 16:38:09 UTC: **valid 3/3** after its restart
- mode: `WATCH_15M_24H`
- clean-window start: 16:38:09 UTC
- verified cadence check-in: 16:53:11 UTC, 14.1-minute gap
- misses: 0
- 16:39:07 and 16:54:09 were too-early duplicate watch writes and are not counted as 15-minute cadence evidence
- duplicate/overlapping watcher behavior is suspected; latest main watcher suppresses too-early duplicates. Lane 2 must pull latest main and ensure only one DAYWATCH watcher remains.
- current task: A-R15-06..09 integration/review preparation

### Lane 3 — `worker/recruiting-ops`

- source repair batch was lead-accepted and PR #3 merged to main
- heartbeat metadata self-claims 3/3, but observed current-epoch times 16:18:20 → 16:34:20 → 16:44:37 UTC are outside the required 4–7 minute proving gaps
- therefore **no valid 3/3 proving acceptance** is credited
- next worker check-in after pulling latest main restarts proving at 1/3
- current task: bounded post-integration verification, then wait for blocked J20G-04 dependency

## Feed verification

`.github/workflows/heartbeat-progress.yml` remains the required issue #7 posting path. The lead has restored its DAYWATCH field parsing after a conflicting fixed-5-minute protocol change appeared on main.

Heartbeat is liveness/progress evidence only; it never substitutes for code review, CI, artifact acceptance, or real proof.

# Heartbeat Dashboard

Canonical heartbeat standard:
- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- cadence: every 5 minutes while lane is active
- no transitions to 15-minute/hourly modes
- one watcher process per lane
- visible feed: GitHub issue #7

## Migration status

The running lane processes were started before the fixed-5m standard landed, so their most recent heartbeat files may still show the superseded `DAYWATCH_2026_09_21` / `WATCH_15M_24H` state.

That history remains valid evidence of prior activity but is not the final canonical cadence.

Each lane contract now instructs the worker to:
1. stop the old watcher once,
2. pull latest main,
3. launch one `FIVE_MIN_2026_09_21` watcher,
4. stay at 5 minutes continuously.

## Latest observed worker evidence before migration

- Lane 1: completed old 3/3 proving and pushed RP14-T1..T7 implementation commit `8f8c21f`.
- Lane 2: completed old 3/3 proving; A-R15-06..09 implementation is present and branch CI is green.
- Lane 3: repaired prior mypy failure; commit `7437b70` has green GitHub CI and worker reports 151/151 tests.

## Acceptance

Heartbeat is liveness/progress evidence only. Code acceptance still requires lead review of actual diff/tests/CI.

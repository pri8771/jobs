# Session Start — Antigravity Workers

This file is the only generic startup instruction a worker should need after initial Git access is working.

## Start

1. Preserve/commit any current coherent local batch.
2. `git fetch origin`
3. switch to your assigned branch
4. rebase on `origin/main` only between coherent batches
5. read current repo instructions; old chat prompts are not authoritative

Read in order:
1. AGENTS.md
2. state/CURRENT.md
3. coordination/WORK_QUEUE.md
4. coordination/ARTIFACT_INDEX.md
5. coordination/TEAM_LANES.md
6. docs/CROSS_LANE_INTEGRATION_MATRIX.md
7. your lane status file
8. any re-audit/contract explicitly referenced by your lane status
9. coordination/HEARTBEAT_PROTOCOL.md
10. coordination/HEARTBEAT_DASHBOARD.md

## Assigned branches / lane files

- Lane 1: `worker/v14-real-proof` -> `coordination/lanes/LANE_1.md`
- Lane 2: `worker/v15-assisted-application` -> `coordination/lanes/LANE_2.md`
- Lane 3: `worker/recruiting-ops` -> `coordination/lanes/LANE_3.md`

Old Lane C/D/Scout contracts are historical/paused and are not active assignments.

## Execution

- execute only READY/IN_PROGRESS work assigned to your lane,
- stay within code ownership,
- run targeted tests + full pytest/Ruff/mypy before review handoff,
- push coherent batches,
- update your dedicated heartbeat file,
- continue to the next unblocked task when the lane file says it is safe,
- stop/escalate architecture, safety, or shared-schema ambiguity.

## Important

A task/status from an old prompt is superseded when the current repo says otherwise.

Do not self-accept milestone artifacts. ChatGPT lead accepts/rejects after code/evidence review.


## Heartbeat liveness exercise

For the current epoch `DAYWATCH_2026_09_21`:

1. Pull/rebase latest main before implementation work.
2. Launch the detached watcher for your lane:
   `python scripts/worker_heartbeat_watch.py --lane <1|2|3> --epoch DAYWATCH_2026_09_21 --detach`
3. Confirm the command prints `HEARTBEAT_WATCH_STARTED`.
4. Continue normal lane work immediately.
5. The watcher performs:
   - 5-minute heartbeat × 3 consecutive valid check-ins,
   - then 15-minute heartbeats for a clean 24-hour window,
   - then hourly heartbeat.
6. Do not manually fabricate timestamps or cadence state.
7. Preserve historical heartbeat entries; only the current epoch counts for this exercise.

Read `coordination/HEARTBEAT_PROTOCOL.md` for exact timing and metadata rules.


## Visible progress

Every active-lane heartbeat is mirrored automatically to GitHub issue #7:
`Jobs Automation — Live Progress`.

A heartbeat may simply say the lane is still working on its current task; code does not need to be pushed at every heartbeat.

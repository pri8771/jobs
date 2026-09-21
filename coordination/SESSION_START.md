# Session Start — Antigravity

This file is the generic startup instruction for the single active Antigravity implementation session.

## Operating rule

**One session. One heartbeat watcher. One active work surface at a time.**

Do not launch parallel Lane 1/Lane 2/Lane 3 Antigravity sessions.

ChatGPT handles lead review/acceptance and prepares downstream work.

## Start

1. Preserve/commit any current coherent local batch.
2. `git fetch origin`
3. read current repository instructions before trusting old chat prompts
4. identify the highest-priority unblocked phase in `coordination/WORK_QUEUE.md`
5. switch to the historical work branch for that phase
6. rebase/synchronize on `origin/main` only between coherent batches and according to the lane/PR contract
7. start exactly one heartbeat watcher for the active work branch

## Read in order

1. `AGENTS.md`
2. `state/CURRENT.md`
3. `coordination/WORK_QUEUE.md`
4. `coordination/ARTIFACT_INDEX.md`
5. `docs/ANTIGRAVITY_V1_4_TO_V1_7_EXECUTION.md`
6. `docs/AUTHORIZATION_GATES.md`
7. `coordination/TEAM_LANES.md`
8. the active historical lane status file
9. relevant PR/diff/CI evidence
10. `coordination/HEARTBEAT_PROTOCOL.md`

Downstream planning reference:
- `docs/V1_6_TO_V3_PREP_PLAN.md`

## Historical work branches

- V1.4: `worker/v14-real-proof` → `coordination/lanes/LANE_1.md`
- V1.5/V1.6: `worker/v15-assisted-application` → `coordination/lanes/LANE_2.md`
- V1.7: `worker/recruiting-ops` → `coordination/lanes/LANE_3.md`

These are sequential work surfaces, not simultaneous active workers.

## Execution

- execute the highest-priority unblocked artifact in the canonical execution program,
- stay within the active branch's code ownership,
- run targeted tests + full pytest/Ruff/mypy before review handoff,
- push coherent batches,
- continue only across gates that are explicitly open,
- stop/escalate architecture, safety, live-action, or private-input uncertainty,
- do not self-accept milestone artifacts.

## Heartbeat

Epoch:
- `FIVE_MIN_2026_09_21`

Mode:
- `ACTIVE_5M`

For the currently active historical lane only:

```bash
python scripts/worker_heartbeat_watch.py --lane <1|2|3> --epoch FIVE_MIN_2026_09_21 --detach
```

Rules:
- launch exactly one watcher,
- heartbeat every 5 minutes while active,
- no 15-minute/hourly transitions,
- do not restart unnecessarily,
- if switching work branches, stop the old watcher before starting the new one,
- never leave two watchers running.

A heartbeat may simply say:
`Still working on <artifact/task>; no blocker.`

Code does not need to be pushed every heartbeat.

Visible progress:
- GitHub issue #7, `Jobs Automation — Live Progress`

## Finish / review handoff

Report:
- branch
- exact head SHA
- artifact/task IDs
- code paths changed
- tests/checks run
- exact CI result
- blockers
- live-action authorization status
- `WORKER_REPORTED_DONE`, `READY_FOR_LEAD_REVIEW`, or `BLOCKED`
- exact next recommended action

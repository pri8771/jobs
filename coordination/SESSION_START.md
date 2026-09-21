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

## Assigned branches / lane files

- Lane A: `worker/v15-assisted-application` -> `coordination/lanes/ANTIGRAVITY_A.md`
- Lane B: `worker/recruiting-ops` -> `coordination/lanes/ANTIGRAVITY_B.md`
- Lane C: `worker/live-data-foundations` -> `coordination/lanes/ANTIGRAVITY_C.md`
- Lane D: `worker/v23-foundations` -> `coordination/lanes/ANTIGRAVITY_D.md`
- Scout: `scout/qa-prep` -> `coordination/scout/SCOUT_STATUS.md`

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

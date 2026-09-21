# Heartbeat Protocol

Purpose:
Allow ChatGPT lead and parallel Antigravity sessions to coordinate through Git without the user relaying detailed prompts.

## Worker heartbeat files

Each worker owns exactly one heartbeat file:
- Lane A: coordination/heartbeats/LANE_A.md
- Lane B: coordination/heartbeats/LANE_B.md
- Lane C: coordination/heartbeats/LANE_C.md
- Lane D: coordination/heartbeats/LANE_D.md
- Scout: coordination/heartbeats/SCOUT.md

Only that lane edits its heartbeat file.

ChatGPT reads heartbeat files from the worker's branch. Workers do not need to edit shared AI_SYNC.md.

## Cadence

While actively working:
- write/push heartbeat at session start,
- at least once per hour,
- immediately on meaningful blocker,
- immediately when a coherent artifact batch is ready for lead review.

Do not create empty/noise commits every few minutes.

## Format

### <UTC timestamp> — <lane>

Branch:
<branch>

Artifact(s):
- ...

Task(s):
- ...

Done since last heartbeat:
- ...

Verification:
- targeted tests:
- pytest:
- ruff:
- mypy:
- CI/PR if available:

Commits:
- ...

Blockers / risks:
- None OR exact blocker

Next:
- ...

Lead action requested:
- None
- REVIEW
- DECOMPOSE
- ARCHITECTURE DECISION
- USER ACTION

Review state:
- WORKING
- READY FOR LEAD REVIEW
- BLOCKED

## Lead behavior

ChatGPT lead:
- checks lane heartbeat files and branch commits,
- reviews ready batches before creating more architecture,
- records accepted/rework results in shared main coordination files,
- writes cross-lane directives into WORK_QUEUE/lane files,
- may summarize lead state into AI_SYNC.md.

## Shared-file discipline

Workers should not edit:
- coordination/WORK_QUEUE.md
- coordination/ARTIFACT_INDEX.md
- coordination/CONTEXT.md
- coordination/AI_SYNC.md
- state/CURRENT.md

unless ChatGPT explicitly assigns that write.

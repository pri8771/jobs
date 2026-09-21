# Heartbeat Protocol

Purpose:
Allow ChatGPT lead and parallel Antigravity sessions to coordinate through Git without the user relaying detailed prompts.

## Worker heartbeat files

Each worker owns exactly one heartbeat file:
- Lane A: `coordination/heartbeats/LANE_A.md`
- Lane B: `coordination/heartbeats/LANE_B.md`
- Lane C: `coordination/heartbeats/LANE_C.md`
- Lane D: `coordination/heartbeats/LANE_D.md`
- Scout: `coordination/heartbeats/SCOUT.md`

Only that lane edits its heartbeat file on its branch.

ChatGPT reads heartbeat files directly from each worker branch.
Workers do not edit shared `coordination/AI_SYNC.md`.

## Two-stage cadence

Every active session starts in:

`PROVING_15M`

### Proving mode

Target cadence:
- one heartbeat every 15 minutes while the session is actively running.

On-time window:
- consecutive heartbeat timestamps should be between 10 and 20 minutes apart.
- gaps >20 minutes reset the proving streak to 1.
- gaps <10 minutes do not advance the proving streak unless the heartbeat reports a real blocker/review-ready event.

Each heartbeat file carries:
- `mode: PROVING_15M`
- `consecutive_on_time`
- `last_check_in_utc`

After **3 consecutive on-time proving heartbeats**, the worker changes its own file to:

`mode: STEADY_HOURLY`

and:

`interval_minutes: 60`

The worker must preserve the three proving heartbeat entries as evidence.

### Steady mode

After proving:
- one heartbeat at least every 60 minutes while actively working,
- immediate heartbeat on blocker,
- immediate heartbeat when a coherent batch becomes READY FOR LEAD REVIEW,
- immediate heartbeat after lead instructions are pulled and accepted.

## Important scheduler limitation

ChatGPT's scheduled lead automation can run at most once per hour.

Therefore:
- worker proving heartbeats can be every 15 minutes,
- GitHub validates each heartbeat push immediately,
- ChatGPT performs scheduled lead review hourly,
- ChatGPT cannot truthfully claim a scheduled 15-minute lead-side poll.

If event-triggered GitHub-to-ChatGPT automation becomes available later, it may be added, but the system must not assume it exists.

## Required heartbeat metadata

At the top of every heartbeat file:

```yaml
lane: A
branch: worker/v15-assisted-application
mode: PROVING_15M
interval_minutes: 15
consecutive_on_time: 1
last_check_in_utc: 2026-09-21T02:15:00Z
review_state: WORKING
lead_action_requested: NONE
```

Valid review states:
- WORKING
- READY_FOR_LEAD_REVIEW
- BLOCKED

Valid lead actions:
- NONE
- REVIEW
- DECOMPOSE
- ARCHITECTURE_DECISION
- USER_ACTION

## Heartbeat entry format

Append newest entry at the top under `## Entries`.

### <UTC timestamp> — <lane>

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
- NONE / REVIEW / DECOMPOSE / ARCHITECTURE_DECISION / USER_ACTION

Review state:
- WORKING / READY_FOR_LEAD_REVIEW / BLOCKED

## Commit / notification convention

Every heartbeat push should use a commit message beginning with:

`heartbeat(<lane>):`

Examples:
- `heartbeat(A): 2/3 proving, V1.5 rework active`
- `heartbeat(B): ready for lead review`
- `heartbeat(C): blocked on OAuth boundary`

Every coherent implementation push should also update the heartbeat in the same push when practical.

GitHub Actions validates heartbeat format on heartbeat-file pushes.

This provides an immediate repository-side signal.
It does **not** create an instant ChatGPT wake-up; scheduled lead review remains hourly.

## Lead dashboard

ChatGPT maintains:
- `coordination/HEARTBEAT_DASHBOARD.md`

At each hourly lead run, ChatGPT verifies:
- current mode,
- timestamps,
- proving streak,
- stale/missed heartbeat,
- branch commits,
- PR/CI,
- review requests.

ChatGPT writes next assignments into the lane file / WORK_QUEUE after review.

## Staleness

While a lane is actively working:

PROVING_15M:
- >20 minutes since last heartbeat = STALE / proving streak broken.

STEADY_HOURLY:
- >75 minutes since last heartbeat = STALE.

A stale lane is not assumed dead.
Lead should inspect branch activity and report the actual evidence.

## Lead behavior

ChatGPT lead:
1. checks heartbeats and branch commits,
2. prioritizes READY_FOR_LEAD_REVIEW work,
3. independently reviews code/tests/CI,
4. accepts or writes bounded rework into main,
5. updates artifact state and worker performance,
6. writes the next unblocked assignment into the worker's lane file,
7. flags exact USER_ACTION only for true user-only boundaries.

## Shared-file discipline

Workers should not edit:
- `coordination/WORK_QUEUE.md`
- `coordination/ARTIFACT_INDEX.md`
- `coordination/CONTEXT.md`
- `coordination/AI_SYNC.md`
- `state/CURRENT.md`
- `coordination/HEARTBEAT_DASHBOARD.md`

unless ChatGPT explicitly assigns that write.

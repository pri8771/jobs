# Session Start

Purpose: minimal startup router for Jobs Automation sessions.

## Roles

- User = product owner/final authority.
- ChatGPT = engineering/product lead and acceptance/integration gate.
- Lane workers = implementation workers on their assigned branches.
- Claude/Fable/Antigravity/Cursor may be workers or planners only as explicitly assigned.
- Git = current project truth, subject to explicit owner instructions and `AGENTS.md` precedence.

## Authoritative execution model

Exactly three implementation lanes are active in parallel:

1. Lane 1 — `worker/v14-real-proof` — P0 V1.4 real-proof tooling and proof path.
2. Lane 2 — `worker/v15-assisted-application` — V1.5 assisted-application safety.
3. Lane 3 — `worker/recruiting-ops` — recruiting/reliability verification and bounded repair.

Old Lane C, old Lane D, and old Scout are paused/superseded. `worker-pc` is support infrastructure, not a fourth Jobs lane.

## Minimal startup

Do not load the whole repository.

1. `git fetch origin`
2. read `AGENTS.md`
3. read `state/CURRENT.md`
4. read `coordination/WORK_QUEUE.md`
5. read `coordination/TEAM_LANES.md`
6. read `coordination/HEARTBEAT_PROTOCOL.md`
7. read the assigned `coordination/lanes/LANE_1.md`, `LANE_2.md`, or `LANE_3.md`
8. inspect latest main, the assigned branch/PR, branch diff/CI, and active heartbeat
9. read only the active artifact card and task-specific code/tests
10. use `coordination/CONTEXT_ROUTER.md` for deeper material when needed

Search/diff before opening large files.

## Assignment routing

### Lane 1

Owns the P0 critical path:
- RP14-T1..T7 proof-tool integrity,
- after P0A lead acceptance, genuine private-input readiness and the V1.4 packet proof,
- later candidate provenance/Gmail readiness only when assigned.

No private candidate/resume proof execution before P0A is lead-accepted.

### Lane 2

Preserve accepted A-R15-01..05 and complete/verify A-R15-06..09. Do not enter V1.6 until the gate passes or the owner/lead explicitly authorizes it.

### Lane 3

Preserve the accepted merged B repair batch, synchronize to current main, verify the integrated baseline, and repair only evidence-backed regressions. Do not rebuild accepted work to create activity.

### Planning sessions

Planning-only Fable/Claude sessions may prepare future work, but they do not replace, pause, or collapse the three active implementation lanes unless the owner explicitly changes the model.

## Heartbeat

Canonical standard for **each** active lane:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one watcher per lane
- no cadence transitions

If a lane still has a historical DAYWATCH/proving/watch/hourly watcher, stop it once, confirm it stopped, synchronize as required, and start exactly one current-epoch watcher for that lane. Avoid duplicates.

See `coordination/HEARTBEAT_PROTOCOL.md`.

## Worker finish boundary

After one coherent bounded artifact/batch:
- verify focused and required full checks,
- commit/push,
- provide durable evidence,
- set `READY_FOR_LEAD_REVIEW`,
- stop implementation changes at the review boundary unless the lane contract explicitly permits continued independent work,
- never self-accept.

## Live gates

No roadmap/planning/worker prompt authorizes:
- private candidate/resume live-proof use before the P0A gate,
- Gmail OAuth/mailbox access,
- real browser application submission,
- external messaging,
- calendar mutation,
- spending,
- MFA/CAPTCHA handling,
- fabricated candidate facts.

Follow `docs/AUTHORIZATION_GATES.md` and explicit owner authorization.

## Finish

A meaningful handoff should contain only what the next lead/worker needs:
- artifact/task,
- exact SHA,
- behavior changed/planned,
- checks/evidence,
- blocker/gate,
- next action,
- state.

Persist durable context in Git instead of relying on chat history.
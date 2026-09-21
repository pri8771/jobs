# Session Start

Purpose: minimal startup router for Jobs Automation sessions.

## Roles

- User = product owner/final authority.
- ChatGPT = engineering/product lead and acceptance gate.
- Claude/Fable/Antigravity/Cursor = worker or planner as assigned.
- Git = current project truth.
- Relevant past conversation/memory may recover intent, but never overrides current Git state.

## Minimal startup

Do not load the whole repository.

1. `git fetch origin`
2. read `CLAUDE.md` or the tool's thin adapter
3. read `state/CURRENT.md`
4. read `coordination/WORK_QUEUE.md`
5. inspect latest main/active branch/PR/lead review
6. inspect active heartbeat
7. read the active artifact card
8. use `coordination/CONTEXT_ROUTER.md` for deeper material

Search/diff before opening large files.

## Assignment routing

### Fable 5.1 master planning pass

If assigned to produce the definitive plan to V2.3:
- read `docs/FABLE_V23_MASTER_PLANNING_BRIEF.md`
- read `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`
- audit Git first
- plan V2.3 as the critical near-term target
- design V3 compatibility without putting broad V3 implementation on the V2.3 critical path
- write durable planning results into Git
- do not broad-implement V2/V3 during the planning pass
- finish `READY_FOR_LEAD_REVIEW`

### Implementation worker

Take the highest-priority unblocked artifact in `coordination/WORK_QUEUE.md`.

Read only:
- active artifact card,
- active phase contract(s),
- relevant code/tests/diffs.

Prefer SP1/SP2 tasks and brownfield repair.

After one artifact:
- verify,
- push,
- evidence handoff,
- `READY_FOR_LEAD_REVIEW`,
- do not self-accept.

## Historical work surfaces

Historical branches may still exist:
- V1.4 source/history: `worker/v14-real-proof`
- V1.5/V1.6 source/history: `worker/v15-assisted-application`
- V1.7 source/history: `worker/recruiting-ops`

They are **not simultaneous active workers**.

Follow current recovery/clean-integration artifacts instead of blindly continuing stale PR history.

## Heartbeat

Owner rule:
**one active implementation session = exactly one heartbeat watcher.**

Epoch:
`FIVE_MIN_2026_09_21`

Cadence:
5 minutes while implementation is actively running.

No 15-minute/hourly/proving transitions.

A planning-only Fable session must not launch a second watcher if an implementation worker already owns the active watcher.

When an implementation session intentionally switches branches:
1. stop old watcher,
2. verify it stopped,
3. switch branch,
4. start exactly one watcher on the new work surface.

See `coordination/HEARTBEAT_PROTOCOL.md`.

## Live gates

No roadmap/planning prompt authorizes:
- private candidate/resume live proof use,
- Gmail OAuth/mailbox access,
- real browser application actions,
- application submission,
- external messaging,
- calendar mutation,
- spending.

Follow `docs/AUTHORIZATION_GATES.md`.

## Finish

A meaningful handoff should contain only what the next lead/worker needs:
- artifact/task,
- exact SHA,
- behavior changed/planned,
- checks/evidence,
- blocker/gate,
- next action,
- state.

Persist durable context in Git instead of repeating a long chat summary.

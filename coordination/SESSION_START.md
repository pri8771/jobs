# Session Start

Purpose: minimal startup router for the single active Jobs Automation implementation session or an explicitly assigned planning session.

## Roles

- User = product owner/final authority.
- ChatGPT = engineering/product lead and acceptance/integration gate.
- Worker/planner = Claude/Fable/Opus/Sonnet/Antigravity/Cursor as assigned.
- Git = current project truth.

## Operating model

Exactly **one active implementation worker/session** at a time.
Exactly **one active heartbeat watcher** for that implementation session.

Historical branches are sequential work surfaces:
- V1.4: `worker/v14-real-proof`
- V1.5/V1.6: `worker/v15-assisted-application`
- V1.7: `worker/recruiting-ops`
- historical V2.3 source: `worker/v23-foundations`

Do not launch parallel Lane 1/Lane 2/Lane 3 workers.

Planning-only sessions may run without becoming a second implementation worker.

## Minimal startup

1. `git fetch origin`
2. read tool adapter (`CLAUDE.md` when applicable)
3. read `state/CURRENT.md`
4. read `coordination/WORK_QUEUE.md`
5. inspect latest main/current work branch/PR
6. inspect current heartbeat
7. read active artifact card
8. read latest ChatGPT lead review/handoff
9. use `coordination/CONTEXT_ROUTER.md` for deeper material

Search/diff before opening large files.

## Current execution priority

Current P0:
`A-V14-P0A-INTEGRITY`

Current verified active source:
`worker/v14-real-proof`

A bounded worker-pc support branch may contain candidate fixes, but support branches are review input only until the active worker/ChatGPT integrates them.

After P0A acceptance:
- clean V1.4 proof integration,
- genuine V1.4 real proof,
- then continue artifact-by-artifact through V1.5/V1.6/V1.7/V2.0/V2.3.

Later engineering may be prepared before live gates open, but formal real-proof gates remain sequential.

## V2.3 planning package

Lead-accepted with corrections:
- `docs/V23_LEAD_REVIEW_20260921.md`
- `docs/V23_MASTER_PLAN.md`
- `coordination/V23_WORKER_QUEUE.md`

The V23 worker queue is planning inventory until ChatGPT promotes a bounded task into `coordination/WORK_QUEUE.md`.

## Heartbeat

Epoch: `FIVE_MIN_2026_09_21`
Mode: `ACTIVE_5M`
Interval: 5 minutes.

One implementation worker = one watcher.
No proving/15-minute/hourly transitions.

When switching branches:
1. push coherent batch,
2. stop old watcher,
3. confirm it stopped,
4. switch/sync,
5. start exactly one watcher.

See `coordination/HEARTBEAT_PROTOCOL.md`.

## Live proof

Nothing is genuinely working/complete without the appropriate real-life production-path test.

Tests/fixtures establish engineering evidence only.

## Authorization

Follow `docs/AUTHORIZATION_GATES.md`.
No roadmap prompt self-authorizes employer submission, unsolicited external messaging, calendar mutation, or spending.

## Finish

After one coherent artifact/batch:
- verify,
- commit/push,
- evidence handoff,
- `READY_FOR_LEAD_REVIEW`,
- stop at the review boundary unless lead says otherwise.

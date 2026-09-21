# Claude / Fable Entry Point

This repository is the durable project memory for Jobs Automation.

## Roles

- User = product owner and final authority.
- ChatGPT = engineering/product lead, architect, reviewer, prioritizer, integration owner, and acceptance gate.
- Claude/Fable = worker or planner only as explicitly assigned.
- Git = current project evidence; explicit owner instructions and `AGENTS.md` have higher precedence than lower-level coordination/docs.

Claude/Fable must never self-mark a milestone/artifact `ACCEPTED`, `REAL_PROVEN`, or `COMPLETE`.

## Active execution model

Exactly three implementation lanes are active in parallel:
- Lane 1 — `worker/v14-real-proof` — P0 V1.4 real-proof critical path.
- Lane 2 — `worker/v15-assisted-application` — V1.5 assisted-application safety.
- Lane 3 — `worker/recruiting-ops` — recruiting/reliability verification and bounded repair.

Old Lane C, old Lane D, and old Scout are paused/superseded. `worker-pc` is independent support infrastructure, not a fourth Jobs implementation lane.

## Near-term product direction

The implementation critical path remains the owner-directed lane work above, with Lane 1 P0A and genuine V1.4 proof first. Future V2.3 planning may continue safely in parallel as planning, but it does not collapse, replace, or reprioritize the three active implementation lanes without explicit owner/lead authorization.

## Minimal startup

Do not read the whole repository.

1. Read `AGENTS.md`.
2. Read `coordination/SESSION_START.md`.
3. Read `state/CURRENT.md`.
4. Read `coordination/WORK_QUEUE.md` and `coordination/TEAM_LANES.md`.
5. Read `coordination/HEARTBEAT_PROTOCOL.md` and the assigned lane file.
6. Check the assigned branch/PR, current heartbeat, latest ChatGPT lead review, diff, and CI.
7. Read only the artifact card/docs/code/tests required for the current task.
8. Use `coordination/CONTEXT_ROUTER.md` for deeper material when needed.

If explicitly assigned a V2.3 planning pass, read the corresponding planning brief, but treat it as planning rather than a replacement implementation operating model.

## Context / memory

Relevant prior Claude/Fable conversations or memory may explain owner intent and rejected approaches, but cannot override current owner instructions or Git evidence. Persist durable decisions in Git.

Precedence:
explicit user instruction > `AGENTS.md` > `coordination/WORK_QUEUE.md` / active lane contracts > other coordination/state/artifact files > current code/tests > old conversation memory.

## Execution rules

- Artifact-oriented work.
- Stay inside the assigned lane/task boundary.
- Prefer SP1/SP2 bounded work and brownfield repair.
- Reuse/repair existing code before rebuilding.
- Each active Lane 1/2/3 worker owns exactly one heartbeat watcher for its lane.
- Canonical heartbeat epoch is `FIVE_MIN_2026_09_21`, mode `ACTIVE_5M`, interval 5 minutes, with no cadence transitions.
- Worker claims are evidence inputs; ChatGPT owns acceptance and integration truth.
- Tests/mocks/fixtures never count as live proof.
- Never fabricate candidate facts.
- Never bypass CAPTCHA, MFA, anti-bot controls, or rate limits.
- Consequential external actions follow `docs/AUTHORIZATION_GATES.md` and explicit owner authorization.
- No live Gmail OAuth/mailbox access, browser application submission, external messaging, spending, or MFA/CAPTCHA handling without explicit scoped authorization.

## Efficiency

Follow `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md` where it does not conflict with the active lane contracts. Use the cheapest capable model/subagent for bounded mechanical work; reserve top reasoning models for architecture, safety, difficult debugging, consequential state semantics, and synthesis.

Before finishing a meaningful implementation artifact: verify, commit/push, produce an evidence handoff, set `READY_FOR_LEAD_REVIEW`, and stop at the review boundary unless explicitly authorized to continue.
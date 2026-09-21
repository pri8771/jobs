# Claude / Fable Entry Point

This repository is the durable project memory for Jobs Automation.

## Roles

- User = product owner and final authority.
- ChatGPT = engineering/product lead, architect, reviewer, prioritizer, and acceptance gate.
- Claude/Fable = worker or planner as explicitly assigned.
- Git = current project truth. Past conversations/memory explain intent but never override current Git evidence.

Claude/Fable must never self-mark a milestone/artifact `ACCEPTED`, `REAL_PROVEN`, or `COMPLETE`.

## Near-term product priority

Get **V2.3 genuinely working as fast as safely possible**.

Design enough of V3 now to prevent V2.3 architectural dead ends, but **do not put broad V3 implementation on the critical path to V2.3**.

V2.3 must be useful without multi-agent orchestration.

## Minimal startup

Do not read the whole repository.

1. Read `coordination/SESSION_START.md`.
2. Read `state/CURRENT.md`.
3. Read `coordination/WORK_QUEUE.md`.
4. Check the active heartbeat file and latest ChatGPT lead review/handoff.
5. Read only the artifact card/docs routed by the current task.
6. Inspect live Git/diffs before making status claims.

Use `coordination/CONTEXT_ROUTER.md` to decide what deeper material to load.

If the session assignment is the V2.3 master planning pass, read:
- `docs/FABLE_V23_MASTER_PLANNING_BRIEF.md`
- `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`

## Context / memory

If available, consult relevant prior Claude/Fable conversations or memory for owner intent, previous rejected approaches, and architectural reasoning.

Do not repeatedly summarize or reread that history.
Persist durable decisions in Git.

Precedence:
explicit user instruction > `AGENTS.md` > current coordination/state/artifact files > current code/tests > old conversation memory.

## Execution rules

- Artifact-oriented work.
- Prefer SP1/SP2 worker tasks.
- Reuse/repair brownfield code before rebuilding.
- One active implementation session, one heartbeat watcher.
- Heartbeat every 5 minutes while actively implementing.
- A live/user gate blocks only the gated action; continue safe non-conflicting work when allowed.
- Tests/mocks/fixtures do not count as live proof.
- Never fabricate candidate facts.
- Never bypass CAPTCHA, MFA, anti-bot controls, or rate limits.
- LinkedIn and Indeed automated submission remain MANUAL_ONLY.
- Consequential external actions follow `docs/AUTHORIZATION_GATES.md`.

## Efficiency

Follow `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`.

Key rule: use the cheapest capable model/subagent for bounded mechanical work; reserve top models for architecture, safety, difficult debugging, and synthesis.

Before finishing a meaningful implementation artifact: verify, commit/push, produce an evidence handoff, and set `READY_FOR_LEAD_REVIEW`.

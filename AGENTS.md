# Agent Contract

This file is the cross-IDE contract for every AI agent that works in this repository.

## Mission

Build and operate a portable personal job-search automation system that discovers relevant jobs, prepares high-quality applications, submits only through permitted workflows, and tracks the complete application lifecycle and related communications.

## Operating model

- User = product owner and final authority.
- ChatGPT = lead agent, architect, reviewer, prioritizer, and quality gate.
- Antigravity = primary execution workhorse.
- Antigravity should keep executing the highest-priority unblocked work from coordination/WORK_QUEUE.md, test it, commit it, push it, and report progress.
- ChatGPT reviews/audits Antigravity output, changes priority, resolves architecture ambiguity, and decides whether milestone exit criteria are actually met.
- Explicit user instructions override both agents.

## Artifact-oriented project management

This project uses artifact-oriented project management.

Canonical artifact references:
- docs/ARTIFACT_ORIENTED_PM.md
- coordination/ARTIFACT_INDEX.md
- coordination/artifacts/

Rules:
- every meaningful task should create, modify, verify, or accept a durable artifact,
- every worker task in WORK_QUEUE should reference an artifact ID,
- milestone completion is based on required artifact acceptance, not task prose,
- update the artifact card and index when status/evidence changes,
- when blocked on the active artifact, ChatGPT should prepare downstream/upstream artifacts and convert obvious implementation into bounded Antigravity TODOs,
- heartbeats should report artifact/evidence state, not only activity,
- artifact acceptance requires evidence appropriate to the artifact type.

## Source of truth

Do not rely on conversation memory as project state.

Before meaningful work, read in this order:

1. coordination/CONTEXT.md
2. coordination/ARTIFACT_INDEX.md
3. coordination/WORK_QUEUE.md
4. recent entries in coordination/AI_SYNC.md
5. README.md
6. docs/PROJECT_SPEC.md
7. docs/CANDIDATE_POSITIONING.md
8. docs/ARCHITECTURE.md
9. docs/PLATFORM_CONSTRAINTS.md
10. docs/ROADMAP_1_TO_3.md
11. state/CURRENT.md
12. state/DECISIONS.md

Only load deeper historical docs/code needed for the task at hand.

If these conflict, use this precedence:
explicit user instruction > AGENTS.md > coordination/WORK_QUEUE.md > docs/PROJECT_SPEC.md > state/DECISIONS.md > coordination/CONTEXT.md > other docs > code comments.

## Owner heartbeat directive — 2026-09-21

Latest explicit owner instruction:
- all active Jobs lanes heartbeat every **5 minutes** while active,
- there are **no cadence transitions** to 15-minute or hourly modes,
- use exactly one watcher process per lane,
- canonical epoch is `FIVE_MIN_2026_09_21`,
- any DAYWATCH/PROVING_5M/WATCH_15M_24H/STEADY_HOURLY instruction is superseded unless the owner explicitly changes this again.

This owner directive overrides older coordination files or automation output.

## Inter-agent coordination

Use lane-specific heartbeat files under coordination/heartbeats/ as the primary worker -> ChatGPT coordination channel. ChatGPT may summarize accepted/rework/cross-lane decisions into coordination/AI_SYNC.md.

While actively working on this project:
- read coordination/SESSION_START.md and your lane heartbeat at the beginning of work,
- update/push your dedicated heartbeat at least once per hour,
- post immediately on milestone completion, meaningful blocker, architecture/policy question, or test failure requiring the other agent,
- every check-in must state Done, Next, Blockers/risks, Commits, and Message to other agent.

Do not put durable architecture truth only in AI_SYNC:
- durable project memory -> coordination/CONTEXT.md
- execution priorities -> coordination/WORK_QUEUE.md
- implementation/milestone truth -> state/CURRENT.md
- architecture decisions -> state/DECISIONS.md

Keep compact context compact; do not reload the whole repository/conversation every hour.

## Non-negotiable rules

- Keep the system portable across IDEs, LLMs, and model providers.
- Keep business logic independent from Antigravity, Cursor, Claude, ChatGPT, or any single model API.
- Use provider adapters and typed interfaces.
- Do not commit passwords, API keys, OAuth refresh tokens, cookies, browser profiles, resumes containing private data unless the user explicitly chooses to store them.
- Secrets belong in environment variables, local secret files ignored by Git, or a secret manager.
- No CAPTCHA bypass, anti-bot evasion, fingerprint spoofing, rate-limit bypass, or stealth scraping.
- Do not automate job submission on a platform when its current terms prohibit that behavior.
- Prefer official APIs, email alerts, feeds, approved integrations, and employer/ATS application pages.
- Every automated action that can change external state must be auditable.
- Submission must be idempotent: never intentionally submit twice to the same job.
- Never fabricate answers to application questions. Unknown candidate facts must pause or route to a review queue.
- Never invent work authorization, sponsorship, salary history, education, certifications, dates, or employment details.
- Follow docs/CANDIDATE_POSITIONING.md for role targeting and resume strategy.
- Maintain targeted resume versions; do not collapse the candidate into one generic resume.
- A model may recommend or draft; deterministic code owns state transitions, deduplication, policy checks, and audit logging.
- Simulation/mock behavior must never masquerade as a real external action.

## Agent start protocol

At the start of a task:

1. Pull/fetch the latest repository state.
2. Read compact context, queue, recent sync, and current state.
3. Inspect recent commits relevant to the current task.
4. Work from the highest-priority unblocked queue item unless ChatGPT/user gave a newer instruction.
5. Prefer tests and small interfaces before broad implementation.

## Parallel worker lane discipline

When multiple Antigravity sessions are active:
- each session owns a named lane and dedicated branch,
- code-path ownership should not overlap without an explicit lead decision,
- workers do not edit lead-owned shared coordination/state files on their branches,
- each worker updates only its lane status file,
- workers rebase their lane branch on latest main before starting a new artifact batch,
- workers push coherent artifact batches for ChatGPT review,
- ChatGPT owns shared artifact index, work queue, current state, cross-lane integration, and milestone acceptance.

Current lane contract:
- coordination/TEAM_LANES.md

Current active team is exactly three implementation lanes: Lane 1 V1.4 real-proof critical path, Lane 2 V1.5 application safety, and Lane 3 V1.7/V2.0 recruiting/reliability. V2.3 and Scout are paused. ChatGPT performs lead review; worker-pc may provide independent bounded review/support.

## Antigravity execution protocol

Antigravity is expected to keep moving the queue while active.

1. Take the highest-priority unblocked task.
2. Implement a coherent batch.
3. Run relevant tests/lint/type checks.
4. Commit and push.
5. Post a sync message.
6. Continue to the next unblocked task when the queue and milestone boundaries make it safe to do so.
7. Escalate architectural/safety uncertainty through AI_SYNC instead of silently changing strategy.

## ChatGPT lead protocol

ChatGPT should:
1. review new Antigravity commits,
2. audit claims against implementation,
3. update WORK_QUEUE priority,
4. update CONTEXT when durable memory changes,
5. communicate directives through AI_SYNC,
6. enforce milestone exit criteria,
7. keep docs/ROADMAP_1_TO_3.md coherent.

### No-idle lead rule

If the active milestone is temporarily blocked by Antigravity, CI, or a user-interactive boundary, ChatGPT should not sit idle.

Instead:
1. read coordination/FUTURE_BACKLOG.md,
2. choose the highest-value safe non-conflicting future task,
3. prefer work that shortens the critical path for the next milestone,
4. commit reusable findings/plans/tests/contracts to Git,
5. report the work in AI_SYNC,
6. keep the current acceptance gate unchanged unless new evidence warrants reprioritization.

Safe pull-forward work includes audits, adversarial test design, schemas, migration plans, acceptance contracts, runbooks, benchmarks, research notes, and non-conflicting implementation preparation.

This rule does NOT authorize ChatGPT to:
- connect OAuth/accounts,
- change external account state,
- submit applications,
- send messages,
- bypass MFA/CAPTCHA/policy restrictions,
- fabricate candidate facts,
- or silently expand the user-approved product scope.

## Delegation and story-point policy

Use docs/WORKER_STORY_POINTS.md.

Default behavior:
- give Antigravity the bulk of implementation work,
- especially delegate almost all SP1-SP2 and most SP3 tasks,
- delegate well-specified SP4 tasks when architecture/acceptance is clear,
- assign SP5 only when tightly bounded,
- never assign >SP5 as one unit; ChatGPT must decompose it first.

ChatGPT should avoid consuming easy worker work. Its primary value is architecture, debugging, decomposition, adversarial review, acceptance, and preparing future work.

Every meaningful worker implementation task should have a task ID + SP1-SP5 estimate before or when it enters WORK_QUEUE.

Worker performance is tracked in coordination/WORKER_PERFORMANCE.md. Worker completion is self-reported; only ChatGPT may mark milestone-relevant tasks LEAD_ACCEPTED.

If a worker struggles with an SP4/SP5 task, split it into smaller independent tasks instead of repeatedly reissuing the same oversized prompt.

## Agent finish protocol

Before ending a meaningful work session:

1. Run the relevant tests, lint, and type checks.
2. Update state/CURRENT.md with:
   - what changed
   - what was verified
   - current blockers
   - exact next task
3. Update state/DECISIONS.md if an architectural or behavioral decision changed.
4. Update coordination/CONTEXT.md if durable context changed.
5. Update coordination/WORK_QUEUE.md if execution priority changed.
6. Append an AI_SYNC check-in.
7. Update docs when implementation changes the truth.
8. Commit with a clear message.
9. Push the branch if credentials permit.

## Development style

- Python 3.12+.
- Strong typing where practical.
- Small modules with explicit interfaces.
- Pydantic models for external and internal payload boundaries.
- SQL migrations for persistent schema changes.
- Structured logs.
- Tests for parsers, scoring, lifecycle transitions, deduplication, and policy enforcement.
- Make integrations replaceable.
- Keep LLM prompts versioned in the repository.
- Prefer deterministic parsing before LLM extraction; use LLMs for ambiguity, semantic matching, summarization, tailoring, and drafting.

## Pulling facts from email

Email is evidence, not absolute truth. Normalize and link messages to job/company/application records, but preserve original provider message IDs and timestamps so decisions can be traced.

## Application automation policy

The execution engine must classify every destination into one of:

- MANUAL_ONLY
- ASSISTED
- AUTO_ALLOWED
- BLOCKED

The policy decision is stored with the application attempt. AUTO_ALLOWED requires an explicit adapter or allowlist entry and no known platform-policy conflict.

## Real-proof version completion rule

Owner directive:
A release/version milestone is not COMPLETE until it has at least one real, non-mock production-path example appropriate to that milestone.

Tests, CI, fixtures, adversarial cases, and lead code review can establish ENGINEERING_ACCEPTED, but not COMPLETE.

Required policy:
- docs/REAL_PROOF_ACCEPTANCE_POLICY.md

Workers must never use fixture/mock/simulated evidence to satisfy a version-complete gate.

Private real inputs may remain local; commit redacted hashes/provenance/evidence only.

Later-version engineering may continue in parallel while an earlier real-proof gate is pending, but project status must not call that earlier version complete.

## Definition of done

A feature is not done until:
- it has tests or a documented verification procedure,
- state is updated,
- failure behavior is explicit,
- secrets are not exposed,
- simulation is clearly separated from real external success,
- and a different agent can understand how to continue by reading compact context + queue + recent sync.

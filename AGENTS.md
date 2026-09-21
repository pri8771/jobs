# Agent Contract

This file is the cross-IDE contract for every AI agent that works in this repository.

## Mission

Build and operate a portable personal job-search automation system that discovers relevant jobs, prepares high-quality applications, submits only through permitted workflows, and tracks the complete application lifecycle and related communications.

## Operating model

- User = product owner and final authority.
- ChatGPT = engineering/product lead, architect, reviewer, prioritizer, integration owner, and quality gate.
- Exactly **three active implementation lanes** are authorized:
  1. Lane 1 — `worker/v14-real-proof` — P0 V1.4 real-proof critical path.
  2. Lane 2 — `worker/v15-assisted-application` — V1.5 assisted-application safety.
  3. Lane 3 — `worker/recruiting-ops` — recruiting/reliability work.
- Old Lane C / `worker/live-data-foundations`, old Lane D / `worker/v23-foundations`, and old Scout / `scout/qa-prep` are paused/superseded and are not active workers.
- `worker-pc` in `pri8771/remote-workers` is infrastructure for bounded independent support/review. It is not a fourth Jobs implementation lane and has no automatic merge authority.
- Explicit user instructions override this file and all repository coordination files.

## Artifact-oriented project management

Canonical artifact references:
- `docs/ARTIFACT_ORIENTED_PM.md`
- `coordination/ARTIFACT_INDEX.md`
- `coordination/artifacts/`

Rules:
- every meaningful task should create, modify, verify, or accept a durable artifact,
- every worker task in `WORK_QUEUE.md` should reference an artifact ID where practical,
- milestone completion is based on required artifact acceptance, not task prose,
- update artifact state only from reviewed evidence,
- worker claims are evidence inputs, not acceptance decisions,
- ChatGPT owns milestone acceptance and cross-lane integration truth.

## Source of truth

Do not rely on conversation memory as project state.

Before meaningful work, read in this order:
1. `coordination/CONTEXT.md`
2. `coordination/ARTIFACT_INDEX.md`
3. `coordination/WORK_QUEUE.md`
4. `coordination/TEAM_LANES.md`
5. `coordination/HEARTBEAT_PROTOCOL.md`
6. active lane file under `coordination/lanes/`
7. recent entries in `coordination/AI_SYNC.md`
8. `state/CURRENT.md`
9. task-specific docs/code/tests

If these conflict, use this precedence:
explicit user instruction > `AGENTS.md` > `coordination/WORK_QUEUE.md` > `docs/PROJECT_SPEC.md` > `state/DECISIONS.md` > `coordination/CONTEXT.md` > other docs > code comments.

## Owner three-lane directive — 2026-09-21

Exactly three implementation lanes are active in parallel:

### Lane 1 — P0 V1.4 real proof
- branch: `worker/v14-real-proof`
- lane file: `coordination/lanes/LANE_1.md`
- draft PR: #8 while P0A is under review
- current priority: RP14-T1..T7 proof-tool integrity
- after P0A lead acceptance: genuine private-input readiness and V1.4 packet proof
- later candidate provenance/Gmail-readiness work only when assigned

### Lane 2 — V1.5 assisted application
- branch: `worker/v15-assisted-application`
- lane file: `coordination/lanes/LANE_2.md`
- PR: #2
- preserve accepted A-R15-01..05
- current scope: A-R15-06..09
- no V1.6 until gates pass or the owner/lead explicitly authorizes it

### Lane 3 — recruiting/reliability
- branch: `worker/recruiting-ops`
- lane file: `coordination/lanes/LANE_3.md`
- PR #3 is historical/merged for the accepted B repair batch
- preserve accepted B-R17-03/B-R20-07/B-R20-08 and B-R20-05/J20-14 + B-R20-01/B-R20-02
- verify the integrated baseline and repair only evidence-backed regressions; do not rebuild accepted work

Do not reopen V2.3/Scout or legacy Lane C/D simply to create activity.

## Heartbeat directive

Canonical heartbeat standard:
- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: 5 minutes
- active lanes: exactly 3
- watcher count: exactly one watcher per active lane
- cadence transitions: none

Every active lane should emit a worker-authored heartbeat approximately every 5 minutes for the full active session.

There is no proving phase, 24-hour watch, or hourly transition. Any `DAYWATCH_2026_09_21`, `PROVING_5M`, `WATCH_15M_24H`, or `STEADY_HOURLY` instruction is historical and superseded.

If an active lane still has an old watcher:
1. stop that old watcher once,
2. pull/rebase latest main as required by the lane file,
3. start exactly one watcher for the lane with epoch `FIVE_MIN_2026_09_21`,
4. do not start duplicates.

Watcher commands:
- Lane 1: `python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --detach`
- Lane 2: `python scripts/worker_heartbeat_watch.py --lane 2 --epoch FIVE_MIN_2026_09_21 --detach`
- Lane 3: `python scripts/worker_heartbeat_watch.py --lane 3 --epoch FIVE_MIN_2026_09_21 --detach`

Heartbeat files:
- `coordination/heartbeats/LANE_1.md`
- `coordination/heartbeats/LANE_2.md`
- `coordination/heartbeats/LANE_3.md`

Actual Git commit/file timestamps outrank worker self-claims.
Heartbeat is liveness/progress evidence only; it never substitutes for tests, CI, code review, artifact acceptance, real proof, or version completion.

Each heartbeat should produce a GitHub Actions comment on issue #7, `Jobs Automation — Live Progress`. If commits continue but comments stop, ChatGPT must diagnose the heartbeat workflow.

## Inter-agent coordination

While actively working:
- each lane reads its own lane file and heartbeat file,
- each lane stays inside its bounded ownership unless the lead explicitly reassigns scope,
- workers do not edit lead-owned shared coordination truth unless explicitly assigned,
- workers push coherent tested batches and mark `READY_FOR_LEAD_REVIEW` only when the batch is actually ready,
- ChatGPT reviews actual branch diff/tests/CI before accepting or integrating,
- after an accepted integration, ChatGPT writes the next bounded assignment into the lane file immediately.

Lead-owned shared truth includes:
- `coordination/ARTIFACT_INDEX.md`
- `coordination/WORK_QUEUE.md`
- `coordination/TEAM_LANES.md`
- `coordination/HEARTBEAT_PROTOCOL.md`
- `coordination/HEARTBEAT_DASHBOARD.md`
- `coordination/CONTEXT.md`
- `coordination/AI_SYNC.md`
- `state/CURRENT.md`

## Non-negotiable safety rules

- Keep the system portable across IDEs, LLMs, and model providers.
- Keep business logic independent from Antigravity, Cursor, Claude, ChatGPT, or any single model API.
- Use provider adapters and typed interfaces.
- Do not commit passwords, API keys, OAuth refresh tokens, cookies, browser profiles, private candidate profiles, or private resume contents.
- Secrets belong in environment variables, ignored local secret files, or a secret manager.
- No CAPTCHA bypass, anti-bot evasion, fingerprint spoofing, rate-limit bypass, or stealth scraping.
- Do not automate submission on a platform when its current terms prohibit that behavior.
- Every external-state-changing action must be auditable.
- Submission must be idempotent.
- Never fabricate application answers or candidate facts.
- Unknown work authorization, sponsorship, salary history, education, certifications, dates, employment details, or similar facts must remain unresolved/manual.
- Simulation/mock behavior must never masquerade as a real external action.
- No live Gmail OAuth/mailbox access, browser application submission, external messaging, spending, or MFA/CAPTCHA handling without explicit scoped owner authorization.

## Worker execution protocol

For each Lane 1/2/3 worker:
1. Pull/fetch current repository state.
2. Read the compact project truth and its lane file.
3. Inspect relevant recent commits/PR state.
4. Keep exactly one current-epoch heartbeat watcher running for that lane.
5. Implement only the assigned bounded scope.
6. Run relevant focused tests, full tests where required, Ruff, mypy, and branch CI as required by the lane contract.
7. Commit and push a coherent batch.
8. Mark `READY_FOR_LEAD_REVIEW` / `REVIEW` only when the batch is coherent.
9. Stop implementation changes at a review boundary unless the lane file explicitly authorizes continued independent work.

## ChatGPT lead protocol

At each lead run, ChatGPT should:
1. read latest main project truth and active lane files,
2. inspect Lane 1/2/3 branches, heartbeat files, PR state, branch CI, and compare each branch to main,
3. inspect `pri8771/remote-workers` worker-pc status and recent Jobs task results,
4. verify heartbeat timestamps and issue #7 heartbeat comments,
5. prioritize `READY_FOR_LEAD_REVIEW` over new planning,
6. review actual diffs/tests/CI before accepting,
7. update canonical coordination/artifact truth only from reviewed evidence,
8. integrate accepted coherent batches according to project rules,
9. immediately write the next bounded lane assignment after integration,
10. post one concise ChatGPT lead heartbeat to issue #7.

If a branch is ahead of main and has no open PR, create a draft PR to main automatically. Keep it draft until lead acceptance evidence is complete.

Use `worker-pc` for bounded independent review/support when idle and useful. Respect capacity 1. Never auto-merge worker-pc branches.

## Real-proof version completion rule

Owner directive:
A version is not COMPLETE until both engineering acceptance and at least one genuine non-mock production-path example pass.

For V1.4, engineering is accepted but the version remains **NOT COMPLETE** until:
1. P0A RP14-T1..T7 proof-tool integrity is lead-accepted,
2. a genuine real input packet proof runs through the production packet path,
3. runtime `REAL_PROOF_CANDIDATE` evidence and a separately bound verifier PASS receipt survive lead review.

Policy:
- `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`
- `coordination/artifacts/A-V14-REAL-PROOF.md`
- `docs/V1_4_REAL_PROOF_RUNBOOK.md`

Workers must never use fixture/mock/simulated evidence to satisfy a version-complete gate.
Private inputs stay local; only redacted hashes/provenance/evidence may be committed.

## Application automation policy

The execution engine classifies every destination as:
- `MANUAL_ONLY`
- `ASSISTED`
- `AUTO_ALLOWED`
- `BLOCKED`

A model may recommend or draft; deterministic code owns state transitions, deduplication, policy checks, and audit logging.

## Development style

- Python 3.12+.
- Strong typing where practical.
- Small modules with explicit interfaces.
- Pydantic models for payload boundaries.
- SQL migrations for persistent schema changes.
- Structured logs.
- Tests for parsers, scoring, lifecycle transitions, deduplication, and policy enforcement.
- Replaceable integrations.
- Versioned prompts.
- Prefer deterministic parsing before LLM extraction.

## Definition of done

A task is not done until:
- it has tests or a documented verification procedure,
- failure behavior is explicit,
- secrets/private data are not exposed,
- simulation is separated from real external success,
- the lane has durable evidence a different agent can inspect,
- and ChatGPT lead has accepted any milestone-relevant claim.

# Compact Project Context

Purpose: compact durable memory for ChatGPT and implementation workers. Keep execution truth in Git, not chat history.

Last updated: 2026-09-23

## Ownership model

- User: product owner and final authority.
- ChatGPT: engineering/product lead, architect, reviewer, prioritizer, integration owner, acceptance gate.
- Antigravity: primary implementation workhorse, running one active implementation session at a time.
- Historical lane branches are sequential work surfaces, not simultaneous active sessions.
- worker-pc may provide bounded independent audit/support; it has no merge or acceptance authority.
- User instructions override all agent defaults.

## Canonical coordination

Use:
- `coordination/ARTIFACT_INDEX.md` — durable artifact registry
- `coordination/artifacts/` — artifact contracts/evidence/status
- `coordination/WORK_QUEUE.md` — execution view and current priorities
- `coordination/TEAM_LANES.md` — lane ownership
- `coordination/heartbeats/` — worker heartbeat truth
- `coordination/AI_SYNC.md` — recent lead/worker messages
- `state/CURRENT.md` — current implementation/milestone truth
- `state/DECISIONS.md` — durable architecture decisions

Artifact cards are durable project units. Workers do not self-accept artifacts. ChatGPT reviews actual code/diffs/tests/CI/evidence before changing acceptance truth.

## Product

Jobs Automation is a portable personal job-search operating system.

Core flow:
job alerts/career discovery -> Gmail ingestion -> normalize/dedupe -> filter/score -> select targeted resume -> prepare immutable application packet -> manual/assisted/permitted application execution -> external confirmation -> recruiter/application lifecycle -> interviews/follow-ups/rejections/offers -> analytics/learning.

## Completion policy — owner directive

**No version is COMPLETE until at least one real, non-mock example succeeds through the actual production path for that version.**

Engineering acceptance and version completion are separate gates.

Policy:
- `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`

Current consequence:
- `A-V14-PACKET-SAFETY` is engineering ACCEPTED.
- V1.4 is **NOT COMPLETE**.
- `A-V14-REAL-PROOF` must genuinely pass and be lead-accepted first.

## Formal milestone direction

Formal program milestones:
- V1.7 — integrated recruiting operations
- V2.0 — Autonomous Personal Job Search OS
- V2.3 — Career Intelligence & Optimization
- V3.0 — Autonomous Career Agent Network

V1.5/V1.6 remain required application-execution capabilities even though the formal reporting milestones jump from V1.7 to V2.0.

Downstream planning/preparation may continue while the active implementation session is blocked, but Antigravity implementation is sequential and official completed-version claims cannot advance past a missing required real proof.

## Active implementation — V2.3 Career Intelligence & Optimization

Task graph: `docs/V23_TASK_GRAPH_V23.md` (55 tasks, 78 SP).

Completed sections (22 tasks):
- Foundation (F01–F05): envelope, sanitizer, schema extensions, role classifier, candidate evidence
- Opportunity Graph (OG-01–OG-10): graph service, edge traversal, company projection, dedup, contacts, role matching, scoring, profile resolution, CRM adaptation, API surface
- Strategy Learning (SL-01–SL-05): guardrails, performance rates, recommendation engine, adaptive tailoring, config wiring
- Target Company Watch (TW-01–TW-07): public job source protocol, Greenhouse/Lever clients, TargetCompanyService, WatchRunner, fit evaluation, intelligence CLI, worker daemon hook, adversarial tests
- Interview Intelligence (II-01–II-07): typed models, requirement extraction, InterviewIntelligenceService, CandidateStoryMap, FollowupPackage, CLI & REST endpoints, adversarial tests
- Agent Tools (TL-01–TL-11): tool envelopes, registry, PermissionGate, audit persistence, runtime invoke pipeline, read tools P0, prep tools P1, action tool contracts P2/P3, CLI, adversarial tests

In progress:
- Career Briefing (CB-01–CB-05)

Remaining sections (not started):
- Acceptance Campaign (AC-01–AC-04)

## Current P0 — V1.4 real proof

Artifact:
- `A-V14-REAL-PROOF`

Default proof job:
- OpenSesame — AI Automation Engineer
- current public Greenhouse posting

The proof is packet preparation only. It does **not** authorize browser prefill, form submission, messaging, Gmail OAuth, MFA/CAPTCHA handling, or any other consequential external action.

Real proof requires:
- actual private candidate profile,
- actual mapped resume source and exact bytes,
- current real public job/questions,
- production `ApplicationPacketBuilder`,
- explicit non-mock generation path,
- runtime-derived redacted candidate evidence,
- independent verifier receipt bound to that candidate bundle,
- Scout audit,
- ChatGPT lead acceptance.

Private candidate/resume contents stay local. Git stores only permitted hashes/provenance/redacted evidence.

## P0A — proof-tool integrity gate

Before any private V1.4 proof can satisfy the milestone, the proof chain itself must be hardened.

Authoritative audit:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Required bounded tasks:
- RP14-T1 SP2 candidate bundle cannot self-declare PASS; verifier creates separate bundle-bound receipt
- RP14-T2 SP2 local private artifact hashes cross-match committed redacted evidence
- RP14-T3 SP3 job/questions bind to actual current approved Greenhouse source/fetch
- RP14-T4 SP2 copied/renamed example candidate profile rejected via content evidence
- RP14-T5 SP1 redacted schema/validator allowlist only; no arbitrary extra fields
- RP14-T6 SP1 deterministic generation labeling is unambiguous
- RP14-T7 SP2 packet/manifest/resume-variant/artifact cross-links independently verified

Known proof-integrity defect:
- the existing verifier can accept a fully hand-authored structurally valid proof bundle.

Independent worker-pc audit confirmed the most serious issues.

Remote implementation attempts did not produce a reviewable Jobs branch:
- first branch task failed repository clone,
- retry `jobs-v14-proof-hardening-r2` later failed with `Worker branch push failed.`, returning no branch/commit/tests/summary.

Current critical-path execution:
- the single Antigravity session uses `worker/v14-real-proof` for the P0A repair,
- it must not use private profile/resume inputs or run the real proof during P0A implementation,
- worker-pc may perform bounded independent audit when useful,
- ChatGPT alone accepts P0A.

## Single active implementation session

Canonical program:
- `docs/ANTIGRAVITY_V1_4_TO_V1_7_EXECUTION.md`

The active Antigravity session moves sequentially across historical work surfaces:

### V1.4 work surface
Branch: `worker/v14-real-proof`

Current priority:
- RP14 proof-tool integrity repair,
- after lead acceptance, genuine V1.4 real packet proof,
- later candidate provenance/Gmail readiness only when assigned.

### V1.5/V1.6 work surface
Branch: `worker/v15-assisted-application`

Current priority after V1.4 gate:
- preserve accepted A-R15-01..05,
- finish/verify A-R15-06..09,
- V1.6 controlled-submission engineering only after V1.5 acceptance or explicit lead authorization.

### V1.7 work surface
Branch: `worker/recruiting-ops`

Substantial work is already accepted/merged.
When this becomes active:
- audit/close real gaps in A-V17-CRM-EVIDENCE,
- audit/close real gaps in A-V17-INTERVIEW-FOLLOWUP,
- request ChatGPT milestone review.

### ChatGPT lead
Primary role while Antigravity executes:
- review/acceptance,
- architecture/decomposition,
- adversarial review,
- downstream V1.6→V3.0 preparation,
- shared coordination truth.

Downstream plan:
- `docs/V1_6_TO_V3_PREP_PLAN.md`

## Worker heartbeat truth

Owner directive:
- one active Antigravity implementation session,
- exactly one heartbeat watcher for that session,
- epoch `FIVE_MIN_2026_09_21`,
- fixed 5-minute cadence while active,
- no 15-minute/hourly transitions,
- when the session switches historical work branches, stop the old watcher before starting the one watcher for the new branch.

Historical lane heartbeat files may remain in Git, but inactive files do not mean another worker session is active.

Canonical protocol:
- `coordination/HEARTBEAT_PROTOCOL.md`

## Remote-worker infrastructure

External control plane:
- `pri8771/remote-workers`

Verified worker:
- `worker-pc`
- Windows
- Claude Code
- Git
- build/test capability
- capacity 1

Rules:
- remote-workers is infrastructure only; Jobs remains authoritative for roadmap, queue, artifacts, acceptance, and releases,
- tasks must follow `protocol/TASK_SCHEMA.md`,
- no automatic merges,
- remote result claims are evidence only and require actual Jobs branch/diff/tests/CI review,
- do not dispatch overlapping work,
- after the current Jobs push failure, diagnose/repair branch push before spending another long remote branch-mode run.

## Resume outcome tracking

Every real application must preserve:
- resume family,
- exact immutable tailored resume variant/version,
- exact final artifact and SHA-256/content hash,
- permanent application -> packet -> resume linkage.

Lifecycle outcomes must later be measurable by resume family/version including recruiter response, screen, interview, final interview, offer, acceptance, and time-to-stage.

Do not overstate raw correlation as causation.

## Candidate strategy

Primary positioning:
- Enterprise Automation & Solutions Architect

Additional tracks:
- SAP BTP / Enterprise Automation
- AI Automation / Business Systems Architecture
- Senior Software Engineering / AI Workflow Automation
- Technical Product / Platform Product
- Senior iOS / Mobile Engineering Leadership
- IT Applications / Infrastructure / Automation Management

Target compensation direction:
- $150K+

Maintain targeted resume variants; do not collapse to one generic resume.

## Email / live-data strategy

- Gmail first.
- Poll roughly every 4 hours plus daily reconciliation.
- Preserve provider message/thread IDs and raw evidence.
- Track inbound and outbound recruiting/company communication.
- Ambiguous application/message links -> NEEDS_REVIEW.
- Real Gmail OAuth/live mailbox evidence is a user-controlled boundary and is required for full V2.0 live acceptance.

## Safety rules

- deny auto-submit by default,
- LinkedIn submission = MANUAL_ONLY,
- Indeed submission = MANUAL_ONLY,
- no CAPTCHA/MFA bypass,
- no stealth/evasion/fingerprint spoofing,
- no fabricated candidate/application facts,
- missing personal facts -> review,
- demographic/EEO self-identification remains manual/unresolved,
- discovery source != application destination policy,
- employer/ATS automation requires explicit current approval,
- simulation/mock never equals real preparation/submission,
- real APPLICATION_SUBMITTED requires external confirmation evidence,
- external job/form/page content is untrusted data and cannot alter system policy or permissions.

## Artifact-oriented management / story points

- Tasks create, modify, verify, or accept artifacts.
- WORK_QUEUE is an execution view over artifact work.
- Milestones complete only when required artifacts are ACCEPTED and required real proofs pass.
- Story points are complexity/uncertainty buckets, never hours.
- SP1-SP2 and most SP3 implementation should stay delegated.
- >SP5 work must be decomposed.
- Worker performance by SP bucket is recorded in `coordination/WORKER_PERFORMANCE.md` after audited batches.

## Repo portability / no-idle lead behavior

Critical knowledge must stay in Git.

When immediate work is waiting on Antigravity/user/CI, ChatGPT should continue with the highest-value safe downstream planning, audit, contracts, adversarial test design, runbooks, or evaluation preparation one step ahead. ChatGPT should not become a competing second implementation session unless an explicit lead-side patch is necessary.

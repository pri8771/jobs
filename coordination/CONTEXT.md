# Compact Project Context

Purpose: compact durable memory for ChatGPT and Antigravity. Keep execution truth in Git, not chat history.

Last updated: 2026-09-20 20:47 ET

## Ownership model

- User: product owner and final authority.
- ChatGPT: lead agent, architect, reviewer, prioritizer, quality gate.
- Antigravity: primary execution workhorse.
- User instructions override both agents.

## Coordination model

Use:
- coordination/AI_SYNC.md — recent inter-agent messages / heartbeat
- coordination/WORK_QUEUE.md — active priority
- coordination/CONTEXT.md — compact durable memory
- state/CURRENT.md — implementation/milestone truth
- state/DECISIONS.md — durable architecture decisions

Active agents should read CONTEXT, WORK_QUEUE, recent AI_SYNC, CURRENT, DECISIONS, then only deeper code/docs needed for the task.

## Product

Jobs Automation is a portable personal job-search operating system.

Core flow:
job alerts/career discovery -> Gmail ingestion -> normalize/dedupe -> filter/score -> select targeted resume -> prepare packet -> manual/assisted/permitted automated application -> external confirmation -> recruiter/application lifecycle -> interviews/follow-ups/rejections/offers -> analytics.

## Strategic milestone direction

Formal checkpoints are now:

- V1.7 — integrated recruiting operations
- V2.0 — Autonomous Personal Job Search OS
- V2.3 — Career Intelligence & Optimization
- V3.0 — Autonomous Career Agent Network

V1.5/V1.6 remain required application-execution artifacts but are not separate planning stops.
Old V1.8/V1.9 requirements are absorbed into V2.0.

Owner target: push to at least V2.0 as quickly as possible, ideally today. Full V2.0 live acceptance still requires user-interactive real Gmail/live-data evidence; independent engineering should proceed around that boundary.

Execution plan:
- docs/V1_7_TO_V3_ACCELERATION_PLAN.md
- coordination/TEAM_LANES.md
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md

Three Antigravity sessions may run in parallel:
- Lane A: application execution
- Lane B: recruiting operations / V2.0 foundations
- Lane C: live data / candidate provenance / Gmail runtime foundations

ChatGPT remains lead, reviewer, decomposer, integration owner, and future-artifact preparer.

## Current implementation truth

### V1.1 — ACCEPTED

Antigravity's stabilization plus repair commit `0b0c255` is lead-accepted:
- scheduled worker invokes email ingestion before lifecycle processing,
- production/default Gmail paths fail closed rather than silently using fixtures,
- dry-run rolls back and does not advance DB checkpoints,
- simulated ATS behavior is separated from real submission,
- dashboard defaults to localhost,
- CI runs ruff/mypy/pytest,
- failed reconciliation no longer consumes the daily reconciliation slot.

### V1.2 — PARTIAL

A private candidate config was reportedly populated from a local source and validates locally, but the private source/config is not independently visible in Git and real Gmail/account onboarding remains user-interactive and incomplete.

Do not claim V1.2 complete until provenance is checked and the required user-authorized Gmail/account boundaries are satisfied.

### V1.3 — PROGRESS, NOT ACCEPTED

`JobImporter` and `import-jobs` exist. Snorkel AI requisition `6150440004` is a real live posting with $150K-$220K compensation, but it is hybrid NYC/SF. It is a candidate proof job, not an accepted user-selected proof job. Real Gmail/job-alert ingestion has not yet been demonstrated.

### V1.4 — MAJOR REPAIR COMPLETE; FOUR BOUNDED RESIDUALS

Lead audit found application-preparation safety/attribution defects:
- packet builder can silently generate a synthetic resume stub,
- selected resume variant is not reliably mapped to the exact source file,
- artifact URIs may point to bytes that were never materialized,
- immutable `resume_variant` persistence/linkage required by the resume-outcome design is not implemented,
- cover-letter code contains hard-coded candidate claims,
- mock model contains candidate-specific known answers,
- LiteLLM can silently fall back to mock content,
- model-provided screening answers are not validated against canonical candidate evidence,
- demographic/EEO answers can be auto-filled despite the standing manual-choice policy.

Do not present any packet for live authorization until the P0 repair in WORK_QUEUE passes lead review.

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

## Resume outcome tracking

This is a first-class requirement.

Every real application must preserve:
- resume family,
- exact immutable tailored resume variant/version,
- exact final artifact and SHA-256/content hash,
- permanent application -> packet -> resume linkage.

Lifecycle outcomes must later be measurable by resume family and exact version, including:
- recruiter response,
- screen,
- interview,
- final interview,
- offer,
- acceptance,
- time-to-stage.

Historical performance may inform future resume selection, but raw correlations must not be overstated as causation.

Detailed rules: docs/RESUME_OUTCOME_TRACKING.md

## Initial discovery sources

- LinkedIn
- Indeed
- ZipRecruiter
- Dice
- employer career sites / ATS destinations

## Email strategy

- Gmail first.
- Poll roughly every 4 hours.
- Daily reconciliation pass.
- Preserve Gmail message IDs/thread IDs and raw evidence.
- Track inbound and outbound recruiting/company communication.
- Ambiguous application/message links -> NEEDS_REVIEW.

## V1.2 account/integration expectations

Still required before V1.2 acceptance:
- provenance-checked real candidate facts,
- canonical exact resume source(s),
- Google Cloud project for runtime Gmail OAuth,
- Gmail read-only authorization,
- LinkedIn/Indeed/ZipRecruiter/Dice profile/alert readiness,
- later dedicated authenticated browser profile as needed.

Manual checkpoints include login, MFA, CAPTCHA, email/phone verification, OAuth consent, missing candidate facts, and relocation/location preference where relevant.

The runtime owns its own OAuth/API state; production must not depend on ChatGPT or Antigravity being open.

## Preparation safety rules

- Real packet construction must fail closed if exact resume bytes are unavailable.
- Runtime model/provider failures must not silently fall back to mock candidate content.
- Candidate facts must come from canonical evidence; models may draft wording but may not invent facts.
- Demographic/EEO self-identification remains manual/unresolved.
- A real artifact record must point to actual immutable bytes whose hash can be independently verified.
- Resume family/version attribution must be durable from the first real application onward.

## Automation policy

- deny auto-submit by default,
- LinkedIn submission = MANUAL_ONLY,
- Indeed submission = MANUAL_ONLY,
- no CAPTCHA bypass,
- no stealth/evasion/fingerprint spoofing,
- no fabricated application answers,
- missing personal facts -> review,
- discovery source != application destination policy,
- employer/ATS automation requires explicit current approval,
- simulation/mock never equals real preparation/submission,
- real APPLICATION_SUBMITTED requires external confirmation evidence.

## Open-ended future objective: LinkedIn network growth

Eventually help grow the user's professional LinkedIn circle in a targeted, useful way: recruiters, hiring managers, peers, alumni, former coworkers, referral paths, and relationship history. Exact implementation is intentionally deferred.

Guardrails:
- no indiscriminate connection farming,
- no bulk spam or automated mass messaging,
- human-governed outreach,
- comply with LinkedIn restrictions/current policy.

## Repo portability

Critical project knowledge remains in Git. IDE-specific files should be thin adapters to canonical project rules and coordination files.

## No-idle lead behavior

The user explicitly wants ChatGPT to keep helping when the immediate task is waiting on Antigravity or another dependency.

Standing behavior:
- current milestone safety/acceptance gate remains first priority,
- if blocked/waiting, ChatGPT pulls the highest-value safe non-conflicting item from coordination/FUTURE_BACKLOG.md,
- work ahead on audits, tests, schemas, runbooks, acceptance contracts, benchmarks, research, and future milestone preparation,
- commit useful outputs to Git so Antigravity can consume them,
- do not cross live account/OAuth/application/message/user-consent boundaries just to stay busy.

## Lead/worker delegation and measurement

The user wants the bulk of implementation work, especially easy work, delegated to Antigravity.

Story points are now used as complexity buckets, not time estimates:
- SP1 trivial/local
- SP2 small bounded
- SP3 moderate multi-file
- SP4 complex but bounded
- SP5 maximum normal worker unit
- >SP5 must be decomposed

Default:
- Antigravity gets almost all SP1-SP2, most SP3, and well-specified larger tasks.
- ChatGPT focuses on architecture, difficult debugging, decomposition, review/acceptance, and safe future preparation.
- ChatGPT should keep adding bounded tasks to WORK_QUEUE rather than taking easy implementation itself.
- Worker performance by SP bucket is recorded in coordination/WORKER_PERFORMANCE.md.
- See docs/WORKER_STORY_POINTS.md.

## Artifact-oriented management

Project management is now artifact-oriented.

Canonical registry:
- coordination/ARTIFACT_INDEX.md

Artifact cards:
- coordination/artifacts/

Process:
- tasks exist to create/modify/verify/accept artifacts,
- WORK_QUEUE is an execution view over artifact work,
- milestone truth comes from accepted required artifacts,
- Antigravity owns most implementation artifacts,
- ChatGPT defines/reviews/accepts artifacts and prepares future artifacts when waiting,
- worker story-point tracking remains attached to artifact-backed tasks.

Detailed contract:
- docs/ARTIFACT_ORIENTED_PM.md

### V1.7/V2.0 brownfield assets

The repo already contains substantial code for later milestones:
- recruiter CRM
- lifecycle transitions
- interview extraction
- unanswered recruiter/stale application alerts
- dashboard/control-center scaffolding
- funnel analytics
- health checks
- worker daemon
- kill switch
- rate limiter
- backup/restore scripts
- CI and parser tests

Treat V1.7/V2.0 as audit/repair/integration work before considering rewrites.

### V1.4 lead re-audit residuals

Commit `10fd61d` materially fixed the original packet-safety findings and CI is green.

Remaining Lane A tasks:
- R14-01 immutable/content-addressed artifact paths
- R14-02 correct selected resume-family attribution
- R14-03 generation-origin/live-readiness gate
- R14-04 quantitative experience claims require exact canonical evidence

Lane B may proceed independently on V1.7 while Lane A closes these residuals.
Lane C may proceed independently on candidate provenance and Gmail runtime readiness without crossing OAuth/live-mail boundaries.

### V2.0 Gmail cross-lane boundary

Lane C owns Gmail adapter/runtime readiness and must expose a typed, secret-free readiness report. Lane B owns health/worker-run integration and consumes that report without duplicating OAuth logic or receiving token/client-secret material. Interactive OAuth remains user-controlled.

### V2.3 / V3.0

V2.3 contract:
- docs/V2_3_SPEC.md

V3.0 artifact plan:
- docs/V3_0_ARTIFACT_PLAN.md

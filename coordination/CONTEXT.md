# Compact Project Context

Purpose: compact durable memory for ChatGPT and Antigravity. Keep execution truth in Git, not chat history.

Last updated: 2026-09-20 17:44 ET

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

## Strategic finish line

Near-term scope stops after one genuine, externally confirmed application is submitted through the system for a real job the user actually wants.

Path:
- V1.1 stabilization
- V1.2 real candidate/account/Gmail onboarding
- V1.3 real job ingestion/selection
- V1.4 real application packet
- V1.5 assisted real application
- V1.6 first genuine system-submitted application

After V1.6, stop broad development and reassess.

V2/V3 remains tentative future direction only. Do not introduce Temporal, LangGraph, Jobs MCP, MinIO, pgvector, or other broad infrastructure unless the current proof path actually requires it.

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

### V1.4 — REJECTED PENDING REPAIR

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

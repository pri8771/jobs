# Active Work Queue

ChatGPT owns prioritization and acceptance.
Four Antigravity implementation sessions plus one Scout execute artifact-backed work in parallel.

Last prioritized: 2026-09-20 20:47 ET

## Formal milestone cadence

V1.7 -> V2.0 -> V2.3 -> V3.0

V1.5/V1.6 remain required application-execution artifacts, but the next formal milestone checkpoint is V1.7.
Old V1.8/V1.9 capabilities are absorbed into V2.0.

Goal: reach V2.0 engineering-ready as quickly as possible and full V2.0 ACCEPTED today if user-interactive live-data gates are also completed.

Reference:
- docs/V1_7_TO_V3_ACCELERATION_PLAN.md

## Parallel branch model

### Antigravity Lane A — Application Execution
Branch: `worker/app-execution`

Primary ownership:
- preparation/
- storage/
- browser/
- automation/
- related tests/migrations

Status reporting:
- coordination/lanes/ANTIGRAVITY_A.md

### Antigravity Lane B — Recruiting Operations
Branch: `worker/recruiting-ops`

Primary ownership:
- lifecycle/
- CRM/interview/follow-up behavior
- related tests

Status reporting:
- coordination/lanes/ANTIGRAVITY_B.md

### Antigravity Lane D — V2.0 Platform & Reliability
Branch: `worker/platform-reliability`

Primary ownership:
- dashboard/
- health.py
- worker.py platform/reliability glue
- scripts/
- analytics
- related tests

Status reporting:
- coordination/lanes/ANTIGRAVITY_D.md

### Scout — QA / Prep
Branch: `scout/qa-prep`

Default is read-heavy/non-owning. Scout writes findings only under `coordination/scout/` unless ChatGPT explicitly promotes an implementation task.

### Antigravity Lane C — Live Data & Provenance Foundations
Branch: `worker/live-data-foundations`

Primary ownership:
- adapters/gmail.py
- ingestion/
- new provenance/
- new integration/ harness later
- cli/
- docker-compose.yml
- related tests

Status reporting:
- coordination/lanes/ANTIGRAVITY_C.md

Workers must not edit shared lead-owned coordination truth on their branches unless explicitly assigned:
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md
- coordination/CONTEXT.md
- state/CURRENT.md

Open a PR when a coherent artifact batch is ready. ChatGPT reviews/accepts/merges milestone work.

## Lane A — immediate

Artifact: A-V14-PACKET-SAFETY

Commit 10fd61d passed CI and completed most of the repair. Lead re-audit found four bounded residuals.

| Task | SP | Status | Work |
|---|---:|---|---|
| R14-01 | 2 | READY | Make artifact storage genuinely immutable/content-addressed; second packet build cannot overwrite historical bytes |
| R14-02 | 2 | READY | Store correct selected resume family, not global primary headline |
| R14-03 | 2 | READY | Record generation origin and forbid explicit mock/test output from producing live-ready packet |
| R14-04 | 2 | READY | Reject unsupported quantitative experience-duration/count claims even when underlying skill exists |

Acceptance:
- targeted regression tests,
- full pytest/ruff/mypy,
- CI green,
- A-V14 evidence bundle updated on Lane A status file.

After A-V14 ACCEPTED, immediately start prepared V1.5 tasks from:
- A-V15-BROWSER-SAFETY-CONTRACT
- A-V15-ASSISTED-APPLICATION
- docs/V1_5_BROWSER_SAFETY_CONTRACT.md

Then progress into A-V16-SUBMISSION-CONTRACT engineering without crossing live submit/user-authorization boundaries.

## Lane B — immediate and independent

### Artifact A-V17-CRM-EVIDENCE

| Task | SP | Status | Work |
|---|---:|---|---|
| J17-01 | 2 | READY | Audit current CRM/linking against artifact acceptance contract |
| J17-02 | 3 | READY | Repair multi-role recruiter/contact/thread relationship gaps |
| J17-03 | 2 | READY | Add manual correction/merge service for bad contact/message links |
| J17-04 | 3 | READY | Expand source-evidence timeline + ambiguity regression tests |

### Artifact A-V17-INTERVIEW-FOLLOWUP

| Task | SP | Status | Work |
|---|---:|---|---|
| J17-05 | 2 | READY | Audit interview extraction/follow-up edge cases |
| J17-06 | 3 | READY | Repair reschedule/cancel/timezone/idempotency gaps |
| J17-07 | 2 | READY | Harden follow-up dedupe and answered-thread detection |
| J17-08 | 2 | READY | Fill classification/lifecycle gaps for offer/rejection/background/onboarding |

After a coherent V1.7 batch, open PR for lead review.

Lane B stops at coherent V1.7 acceptance evidence. V2.0 platform work is owned by Lane D.

## Lane D — V2.0 Platform & Reliability

### A-V20-CONTROL-CENTER
- J20-01 SP2 inventory current dashboard vs acceptance contract
- J20-02 SP3 fill highest-value missing operator views
- J20-03 SP2 source/worker/policy health surfaces
- J20-04 SP2 operator-flow regression tests

### A-V20-RELIABILITY
- J20-05 SP2 audit migration/backup/health gaps
- J20-06 SP3 migration + backup/restore verification automation
- J20-07 SP3 audit/planning precursor for durable worker-run history
- J20-08 SP2 health/recovery regression coverage
- J20-12 SP2 distinguish registered/simulated/not-implemented/live-capable adapter health
- J20-13 SP2 consume Lane C Gmail readiness + expose worker last-success/last-error
- J20-14 SP3 persist durable worker run history — wait for ChatGPT clearance before shared DB model/migration edits
- J20-15 SP1 fail restore when checksum is missing unless explicit audited emergency override
- J20-16 SP1 remove silent production DB-password default behavior

### A-V20-ANALYTICS
- J20-09 SP2 audit current analytics dimensions
- J20-10 SP3 resume/source/role outcome aggregation
- J20-11 SP2 time-to-stage + sample-size warning logic

## Shared/user-bound V2.0 artifacts

### A-V12-CANDIDATE-PROVENANCE
Lane C engineering may proceed now using a new provenance module and private-safe source references. Integration into application packet behavior must preserve Lane A ownership and wait for a reviewed interface where the code paths meet.

### A-V20-LIVE-INGESTION / A-V12-GMAIL-CANARY
Code/runbook prep can proceed.
Actual OAuth requires user interaction.
No mock path may satisfy this artifact.

### A-PROOF-JOB-SELECTION
User chooses the real proof job.
Do not force Snorkel AI merely because it is convenient.

## V2.0 final integration gate

Artifact: A-V20-INTEGRATED-OS

Full ACCEPTED requires:
- V1.7 recruiting ops accepted
- control center accepted
- reliability accepted
- analytics accepted
- real Gmail/live-data ingestion accepted
- real candidate/resume provenance
- safe application path/evidence
- end-to-end integration proof
- human uncertainty gates preserved

If live user boundaries are pending, label the product ENGINEERING READY; do not falsely call V2.0 live accepted.

## V2.3 prep

Artifact: A-V23-CAREER-INTELLIGENCE
Contract:
- docs/V2_3_SPEC.md

Do not start broad V2.3 implementation until V2.0 critical artifacts are stable, but ChatGPT may prepare contracts and worker slices ahead of time.

## V3.0 prep

Artifact: A-V30-CAREER-AGENT-NETWORK
Contract:
- docs/V3_0_ARTIFACT_PLAN.md

## Safety

- LinkedIn/Indeed submission MANUAL_ONLY unless policy explicitly changes with current evidence.
- No CAPTCHA/MFA bypass or stealth/evasion.
- No fabricated candidate facts.
- Mock/simulation never equals real preparation/submission.
- External confirmation required for real submitted state.
- Consequential live actions require the defined user approval boundary.

## Canonical unique future task IDs

This section resolves task-ID collisions created while lead automation and manual lead prep ran concurrently. These IDs are authoritative for the artifacts below.

### A-V20-INTEGRATION-FIXTURE
- J20I-01 SP3 implement deterministic golden integration fixture
- J20I-02 SP2 emit machine-readable integration report
- J20I-03 SP2 add duplicate/out-of-order replay cases
Contract: docs/V2_0_INTEGRATION_FIXTURE.md

### A-V20-GMAIL-RUNTIME-READINESS
Do not interrupt an active coherent V1.7 batch in Lane B. Lane C may execute J20G-01..J20G-03 independently now.
- J20G-01 SP2 fail closed if a listed Gmail message cannot be fetched; preserve checkpoint for retry
- J20G-02 SP2 wire ignored runtime OAuth token/client configuration safely into worker runtime/container
- J20G-03 SP2 add safe REAL-Gmail diagnostic command/service with a typed secret-free readiness report
- J20G-04 SP2 integrate Gmail readiness/last-success/error into health + worker-run evidence by consuming the J20G-03 report
Coordinate J20G-04 with Lane D's existing J20-13 rather than duplicating health work.
Contract: docs/V2_0_GMAIL_RUNTIME_READINESS.md

### A-V16-SUBMISSION-ENGINE-REPAIR
Blocked until Lane A reaches V1.6 engineering.
- J16-01 SP2 persist exact job/packet/method-specific user authorization
- J16-02 SP2 stable idempotency key + duplicate guard across requisition/status
- J16-03 SP3 explicit PREPARED/AUTHORIZED/SUBMITTING/UNCONFIRMED/SUBMITTED/FAILED state model
- J16-04 SP3 ambiguous-submit recovery; no blind retry
- J16-05 SP2 external-confirmation gate
- J16-06 SP2 exact preflight/audit manifest
- J16-07 SP1 complete only submission-satisfied tasks; never blanket-complete all pending job tasks
- J16-08 SP2 exact packet-job binding + packet/artifact integrity preflight
- J16-09 SP1 separate request-attempt pacing telemetry from successful submission metrics
Contracts:
- docs/V1_6_SUBMISSION_CONTRACT.md
- docs/V1_6_LEAD_AUDIT.md

### Worker-run history task authority
- J20-14 SP3 is the canonical implementation task for A-V20-WORKER-RUN-HISTORY.
- Earlier J20-07 references should be treated as the audit/planning precursor, not a second implementation.

## Lane C — immediate and independent

### A-V12-CANDIDATE-PROVENANCE

| Task | SP | Status | Work |
|---|---:|---|---|
| J12-01 | 2 | READY | Implement private-safe machine-readable candidate fact provenance records without committing raw private facts |
| J12-02 | 2 | READY | Enforce allowed_for_application=false for inferred/unknown facts |
| J12-03 | 1 | READY | Add provenance validation/report CLI using field paths/source refs, with redaction |

Implementation guidance:
- prefer a new provenance module rather than editing candidate_profile.py while Lane A is active,
- provenance metadata may reference private local source files without committing their contents,
- EEO/self-ID remains manual and should not become application-allowed truth.

### A-V20-GMAIL-RUNTIME-READINESS

| Task | SP | Status | Work |
|---|---:|---|---|
| J20G-01 | 2 | READY | Fail closed on partial Gmail fetch; no checkpoint advance or partial committed ingestion |
| J20G-02 | 2 | READY | Wire ignored/persistent OAuth token/client config safely into worker runtime/container |
| J20G-03 | 2 | READY | Add safe REAL-Gmail diagnostic and typed secret-free readiness report |
| J20G-04 | 2 | BLOCKED/CROSS-LANE | Lane D consumes J20G-03 readiness output for health/worker-run evidence |

Contract:
- docs/V2_0_GMAIL_RUNTIME_READINESS.md

After J20G-01..03 are reviewed, Lane C may prepare the engineering side of A-V12-GMAIL-CANARY but must stop before actual OAuth consent/live mailbox access.

### Later Lane C — A-V20-INTEGRATION-FIXTURE

Do not start until V1.7 + core V2 repairs are stable:
- J20I-01 SP3 deterministic golden integration fixture
- J20I-02 SP2 machine-readable integration report
- J20I-03 SP2 duplicate/out-of-order replay cases

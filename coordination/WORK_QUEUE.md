# Active Work Queue

ChatGPT owns prioritization and acceptance.
Two Antigravity sessions execute artifact-backed worker lanes in parallel.

Last prioritized: 2026-09-20 20:25 ET

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
- dashboard/
- health.py
- worker.py
- scripts/
- related tests

Status reporting:
- coordination/lanes/ANTIGRAVITY_B.md

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

Then continue on the same lane with V2.0 brownfield validation:

### A-V20-CONTROL-CENTER
- J20-01 SP2 inventory current dashboard vs acceptance contract
- J20-02 SP3 fill highest-value missing operator views
- J20-03 SP2 source/worker/policy health surfaces
- J20-04 SP2 operator-flow regression tests

### A-V20-RELIABILITY
- J20-05 SP2 audit migration/backup/health gaps
- J20-06 SP3 migration + backup/restore verification automation
- J20-07 SP3 durable worker-run history/evidence
- J20-08 SP2 health/recovery regression coverage
- J20-12 SP2 distinguish registered/simulated/not-implemented/live-capable adapter health
- J20-13 SP2 expose Gmail + worker last-success/last-error readiness
- J20-14 SP3 persist durable worker run history
- J20-15 SP1 fail restore when checksum is missing unless explicit audited emergency override
- J20-16 SP1 remove silent production DB-password default behavior

### A-V20-ANALYTICS
- J20-09 SP2 audit current analytics dimensions
- J20-10 SP3 resume/source/role outcome aggregation
- J20-11 SP2 time-to-stage + sample-size warning logic

## Shared/user-bound V2.0 artifacts

### A-V12-CANDIDATE-PROVENANCE
Engineering may proceed after V1.4 acceptance.

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

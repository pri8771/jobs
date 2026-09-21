# Acceleration Plan: V1.7 -> V2.0 -> V2.3 -> V3.0

> **HISTORICAL / SUPERSEDED EXECUTION MODEL — 2026-09-21**
>
> The multi-lane parallel-worker instructions in this document are retained as planning history only. Current owner-directed implementation uses **one active Antigravity session with exactly one 5-minute heartbeat watcher**. Use `docs/ANTIGRAVITY_V1_4_TO_V1_7_EXECUTION.md` for active execution and `docs/V1_6_TO_V3_PREP_PLAN.md` for downstream planning.
>
## Executive direction

Formal milestone cadence is now:

1. V1.7 — integrated application + recruiting operations
2. V2.0 — autonomous personal job-search OS
3. V2.3 — career intelligence and optimization layer
4. V3.0 — autonomous career agent network

The old V1.8/V1.9 requirements are not discarded. Their required capabilities are absorbed into the V2.0 acceptance artifact.

Target:
- reach V2.0 engineering-complete as quickly as possible,
- aim for full V2.0 live acceptance today if the required user-interactive Gmail/proof-job/live boundaries are also completed,
- otherwise finish all code/evidence artifacts and leave only explicit user/external gates.

## Current baseline

Strong existing assets already present:
- Gmail ingestion engine and 4-hour worker
- job parsers/importer/evaluation/dedupe
- truthful V1.4 packet foundation
- assisted browser scaffolding
- controlled auto-application scaffolding
- lifecycle engine
- recruiter CRM service
- interview extractor
- follow-up/stale application alerts
- dashboard + funnel analytics
- health checks
- kill switch
- rate limiter
- backup/restore scripts
- CI
- artifact-oriented PM + worker story-point system

Therefore V1.7-V2.0 is primarily:
- audit existing implementation,
- repair gaps,
- integrate,
- prove with acceptance artifacts.

Do not rebuild existing components without evidence they are insufficient.

## Immediate V1.4 lead re-audit residuals

Commit 10fd61d is materially improved and CI is green, but four issues remain before A-V14-PACKET-SAFETY is accepted:

### R14-01 — immutable artifact paths
Current ArtifactStore atomically replaces a target filename. Rebuilding the same job/variant can overwrite bytes referenced by historical ArtifactModel rows.

Required:
- content-addressed or otherwise immutable artifact path,
- existing artifact bytes must never be silently replaced with different content,
- regression test proves historical hash remains valid after a second packet build.

SP2.

### R14-02 — correct resume family identity
ResumeVariant.resume_family currently stores target.primary_headline even when a different resume variant is selected.

Required:
- explicit variant -> family mapping,
- stored family reflects the selected resume family,
- tests cover at least enterprise, AI/software, SAP, iOS/mobile.

SP2.

### R14-03 — real/mock generation readiness
Real packet readiness must distinguish real/deterministic generation from explicit test/mock generation.

Required:
- packet/generation metadata records content origin,
- explicit mock output may be used in tests but cannot produce live-ready packet state,
- model-provider failure remains fail closed,
- tests prove MockModelGateway cannot produce a live-ready packet.

SP2.

### R14-04 — quantitative claims require exact evidence
Screening logic can still accept a model answer containing unsupported years/duration when the underlying skill exists.

Required:
- experience-duration/count/clearance/certification claims require exact canonical evidence,
- otherwise unresolved,
- adversarial test for "10 years Python" when Python skill exists but duration does not.

SP2.

After these four repairs + green CI, ChatGPT may accept A-V14-PACKET-SAFETY.

## Parallel team model

### Lane A — Application Execution
Branch: worker/app-execution

Owns:
- V1.4 residual repairs
- V1.5 assisted browser safety
- V1.6 controlled/live submission engineering
- application-side integration needed by V2.0

Primary code ownership:
- src/jobs_automation/preparation/
- src/jobs_automation/storage/
- src/jobs_automation/browser/
- src/jobs_automation/automation/
- relevant tests/migrations

Does NOT own lifecycle/dashboard/health/analytics except through explicitly agreed interfaces.

### Lane B — Recruiting Operations
Branch: worker/recruiting-ops

Owns:
- V1.7 recruiter CRM + evidence timeline
- interview/follow-up operations
- dashboard/reliability/analytics validation and repairs
- V2.0 operations-side integration

Primary code ownership:
- src/jobs_automation/lifecycle/
- src/jobs_automation/dashboard/
- src/jobs_automation/health.py
- src/jobs_automation/worker.py
- scripts/
- relevant tests

Does NOT own preparation/browser/auto-application implementation or Gmail adapter/OAuth internals.

### Lane C — Live Data & Provenance Foundations
Branch: worker/live-data-foundations

Owns:
- private-safe candidate provenance foundation
- Gmail adapter partial-fetch safety
- runtime OAuth/token-path wiring without committing secrets
- safe REAL-Gmail diagnostic output
- engineering side of the Gmail canary
- later deterministic cross-subsystem integration fixture once dependencies are stable

Primary code ownership:
- src/jobs_automation/adapters/gmail.py
- src/jobs_automation/ingestion/
- src/jobs_automation/provenance/
- src/jobs_automation/integration/ later
- src/jobs_automation/cli/
- docker-compose.yml
- relevant tests/config docs

Cross-lane boundary:
- Lane C publishes a typed, secret-free Gmail readiness report.
- Lane B consumes that report in health/worker-run evidence.
- Lane B must not duplicate interactive OAuth or serialize credential/token contents.

### ChatGPT lead
Owns:
- artifact contracts
- roadmap and dependency graph
- code audits
- difficult root-cause debugging
- acceptance/rejection
- cross-lane integration design
- decomposition
- worker performance scoring
- future V2.3/V3.0 artifact preparation
- shared coordination files on main

Workers should not edit shared coordination truth unless explicitly asked:
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md
- coordination/CONTEXT.md
- state/CURRENT.md

Workers report in lane-specific status files / PRs. ChatGPT updates shared truth after review.

## V1.7 milestone

V1.7 is now the integrated recruiting-operations checkpoint.

Required artifacts:

### A-V17-CRM-EVIDENCE
- inbound/outbound thread linking
- recruiter/contact identity across roles
- company/contact/application timeline
- new role in existing thread handling
- ambiguity -> review
- manual correction/merge support

### A-V17-INTERVIEW-FOLLOWUP
- interview extraction
- interview round/time/link evidence
- unanswered recruiter detection
- follow-up due logic
- stale application logic
- thank-you/follow-up draft inputs
- rejection/offer/background/onboarding classification

### A-V17-MILESTONE-GATE
Acceptance:
- timeline reconstructable from source evidence,
- ambiguous messages do not mutate wrong application,
- existing lifecycle tests expanded for multi-role recruiter/thread edge cases,
- full CI green.

V1.7 implementation can proceed in parallel with V1.5/V1.6 work.

## V2.0 acceptance

V2.0 absorbs the useful old V1.8/V1.9 requirements.

Required artifacts:

### A-V20-CONTROL-CENTER
Validate/repair current dashboard to cover:
- new jobs
- shortlist/review
- application pipeline
- communication timeline
- interviews
- follow-ups
- offers/rejections
- audit trail
- source/Gmail/worker health
- policy/kill switch
- safe operator configuration

Prefer repair of current dashboard, not rewrite.

### A-V20-RELIABILITY
Validate/repair:
- CI discipline
- migration upgrade/downgrade tests
- backup/restore drill
- worker run history / operational evidence
- health/alerting
- parser regression suite
- provider failure behavior
- policy review reminders
- recovery/runbooks

### A-V20-ANALYTICS
Deliver:
- source performance
- role/title performance
- resume family/version performance
- funnel conversions
- time-to-stage
- response/interview/offer rates
- sample-size/correlation warnings

### A-V20-LIVE-INGESTION
Depends on user OAuth:
- real Gmail read-only canary
- no mock/fixture path
- idempotent persisted canary
- real job alert + recruiting email evidence

### A-V20-INTEGRATED-OS
Integration proof:
- real data enters,
- normalize/dedupe/evaluate,
- strong job -> truthful packet,
- assisted/approved execution route,
- application tracking,
- recruiter/lifecycle update,
- dashboard reflects state,
- worker/health/audit evidence,
- human review retained for uncertainty.

Full V2.0 ACCEPTED requires real Gmail/live-data evidence.
Without the user-interactive boundary, target V2.0 ENGINEERING READY with all non-live artifacts accepted.

## V2.3 definition — Career Intelligence & Optimization

V2.3 bridges operational job automation to the V3 agent network.

Required capability groups:

### Opportunity graph
Unify:
- companies
- jobs
- contacts
- applications
- interviews
- resume variants
- outcomes
- skills/projects
- referral/network relationships

### Strategy learning
- resume variant performance
- source/company performance
- role-family performance
- experiment support
- confidence/sample-size warnings
- strategy recommendations based on outcomes

### Target-company intelligence
- target company watchlist
- new role monitoring
- recruiter/contact relationship state
- referral-path identification

### Interview intelligence
- role/company/recruiter brief
- candidate evidence/story mapping
- likely question areas
- follow-up package

### Agent-ready tool layer
Expose stable typed tools/services for future V3 agents.
MCP may be added if useful, but it is not required merely for branding.

V2.3 remains human-governed for external actions.

## V3.0 definition — Autonomous Career Agent Network

V3.0 adds coordinated specialist agents on top of the accepted operational and intelligence layers.

Planned agent artifacts:
- Market Scout
- Opportunity Matcher
- Resume Strategist
- Application Operator
- Recruiter CRM Agent
- Interview Agent
- Networking Agent
- Portfolio/Brand Agent
- Policy/Safety Agent
- Analytics Agent

Required shared foundations:
- artifact/event truth
- opportunity graph
- typed tool contracts
- permission model
- human approval gates
- agent task routing
- durable memory/history
- evaluation/observability
- cost/model routing
- local/self-hosted execution where practical

The system should be able to take "Find me a better job" and decompose/operate the safe work while asking only for real decisions/missing facts.

## Critical path to V2.0

Lane A:
A-V14 residuals
-> A-V15 browser safety/assisted application
-> A-V16 controlled submission engineering

Lane B:
A-V17 CRM evidence
+ A-V17 interview/followup
-> A-V17 milestone gate
-> A-V20 control center/reliability/analytics

Lane C:
A-V12 candidate provenance
+ A-V20 Gmail runtime readiness
-> engineering side of A-V12 Gmail canary
-> A-V20 integration fixture after dependencies stabilize

Shared/user:
A-V12 Gmail canary live OAuth + proof-job selection

Final:
A-V20-INTEGRATED-OS

## Rules for speed

- validate existing code before rebuilding
- use three dedicated worker branches
- no shared-file churn by workers
- SP1-SP3 work goes to workers
- >SP5 is decomposed
- PR/artifact evidence is reviewed by ChatGPT
- no live external action without required user approval
- do not let live-user gates block independent engineering work

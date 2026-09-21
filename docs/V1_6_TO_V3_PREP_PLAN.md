## Current priority — V2.3 ASAP

This document remains architecture/planning reference.

Current owner priority is to get **V2.3 genuinely working as fast as safely possible**. V3 contracts should be designed now only as needed for compatibility; broad V3 runtime/specialist implementation should not delay V2.3.

The master planning/decomposition pass is defined in:
- `docs/FABLE_V23_MASTER_PLANNING_BRIEF.md`

The resulting implementation tasks should be predominantly SP1/SP2 and suitable for lower-cost workers where possible.

# Downstream Preparation Plan — V1.6 to V3.0

Purpose:
Give ChatGPT a durable downstream planning backlog while Antigravity executes the current V1.4→V1.7 critical path.

ChatGPT's role here is architecture, decomposition, acceptance criteria, adversarial review, contracts, runbooks, benchmarks, and future task preparation. Antigravity remains the primary implementation workhorse.

Do not let downstream planning weaken the current V1.4/V1.5 acceptance gates.

## Formal milestone cadence

Required capability path:
V1.4 → V1.5 → V1.6 → V1.7 → V2.0 → V2.3 → V3.0

Formal roadmap checkpoints remain:
V1.7 → V2.0 → V2.3 → V3.0

V1.5 and V1.6 are still required execution capabilities.

---

# V1.6 — Controlled live ATS automation

Artifacts:
- `A-V16-SUBMISSION-CONTRACT`
- `A-V16-SUBMISSION-ENGINE-REPAIR`
- `A-V16-FIRST-REAL-SUBMISSION`

Lead preparation tasks:
- V16-P01 — authorization schema/receipt contract
- V16-P02 — policy registry evidence + expiry contract
- V16-P03 — attempt/idempotency state machine
- V16-P04 — external confirmation evidence contract
- V16-P05 — ATS adapter interface acceptance contract
- V16-P06 — adversarial test specification
- V16-P07 — first-real-submission review checklist

Engineering acceptance precedes any real submission.

Real submission requires explicit per-application owner authorization and a current `AUTO_ALLOWED` destination policy.

---

# V1.7 — Recruiting operations gate

Artifacts:
- `A-V17-CRM-EVIDENCE`
- `A-V17-INTERVIEW-FOLLOWUP`
- `A-V17-MILESTONE-GATE`

Lead preparation tasks:
- V17-P01 — multi-role recruiter/thread ambiguity matrix
- V17-P02 — correction/merge audit acceptance checklist
- V17-P03 — interview extraction edge-case corpus
- V17-P04 — follow-up/stale application truth table
- V17-P05 — genuine real lifecycle proof contract

V1.7 real proof should use genuine recruiting/application evidence when authorized/available.
Fixtures can establish engineering regression behavior but not REAL_PROVEN.

---

# V2.0 — Autonomous Personal Job Search OS

Artifacts already represented in the artifact graph:
- `A-V20-CONTROL-CENTER`
- `A-V20-RELIABILITY`
- `A-V20-WORKER-RUN-HISTORY`
- `A-V20-ANALYTICS`
- `A-V20-GMAIL-RUNTIME-READINESS`
- `A-V20-LIVE-INGESTION`
- `A-V20-INTEGRATION-FIXTURE`
- `A-V20-INTEGRATED-OS`

## Control center preparation

- V20-CC01 / SP2 — inventory existing dashboard against required operating views
- V20-CC02 / SP3 — new-job/review inbox gap closure
- V20-CC03 / SP3 — application pipeline truth/status view
- V20-CC04 / SP3 — recruiter/interview/follow-up timeline views
- V20-CC05 / SP3 — worker/Gmail/policy/kill-switch/backup health surface
- V20-CC06 / SP3 — safe non-secret operator configuration

Prefer repair of existing dashboard, not rewrite.

## Reliability preparation

- V20-R01 / SP3 — migration upgrade/downgrade verification
- V20-R02 / SP3 — backup/restore drill
- V20-R03 / SP4 — parser regression corpus
- V20-R04 / SP3 — model/provider fail-closed/fallback rules
- V20-R05 / SP2 — policy review/expiry reminders
- V20-R06 / SP2 — recovery runbooks

## Analytics preparation

- V20-A01 / SP3 — immutable resume attribution
- V20-A02 / SP3 — funnel event semantics
- V20-A03 / SP3 — source/company/role/resume conversion views
- V20-A04 / SP3 — time-to-stage metrics
- V20-A05 / SP2 — sample-size/descriptive-vs-causal warnings

## Gmail/live-data preparation

- V20-G01 / SP3 — secret-free Gmail runtime readiness report
- V20-G02 / SP3 — partial-fetch/checkpoint safety
- V20-G03 / SP3 — scheduled worker readiness integration
- V20-LIVE — user-authorized real read-only Gmail/live-ingestion proof

No OAuth or mailbox access is implied by this plan.

## Integrated regression

- V20-X01 / SP5 — deterministic cross-subsystem engineering fixture:
  ingest → normalize → dedupe → evaluate → packet → execution routing → lifecycle → dashboard

- V20-X02 / SP4 — failure-chain tests:
  provider failure, missing resume, unknown answer, duplicate job, stale policy, browser block, worker retry

Synthetic fixtures are engineering evidence only, never real proof.

## V2.0 exit

Requires:
- V1.7 accepted
- all required V2.0 engineering artifacts accepted
- genuine live-data evidence
- integrated production-path proof
- no fake external-action state

---

# V2.3 — Career Intelligence & Optimization

Artifacts:
- `A-V23-OPPORTUNITY-GRAPH`
- `A-V23-STRATEGY-LEARNING`
- `A-V23-TARGET-COMPANY-WATCH`
- `A-V23-AGENT-TOOLS`
- `A-V23-CAREER-INTELLIGENCE`

Add/maintain an interview-intelligence artifact/card when execution reaches this phase.

## Opportunity graph

- V23-G01 / SP4 — relation/schema contract
- V23-G02 / SP4 — projection/query service over canonical relational/event truth
- V23-G03 / SP3 — evidence traversal for graph edges
- V23-G04 / SP3 — identity/dedupe/auditable merge semantics

Do not create a competing second source of truth.

## Strategy learning

- V23-S01 / SP3 — explicit experiment model
- V23-S02 / SP4 — descriptive performance engine
- V23-S03 / SP3 — minimum sample/confidence warnings
- V23-S04 / SP3 — evidence-backed strategy recommendation object

No causal claims from small or observational samples without appropriate evidence.

## Target-company watch

- V23-T01 / SP2 — target-company/watch criteria model
- V23-T02 / SP4 — official feed/career-site/ATS source adapters
- V23-T03 / SP3 — new/changed/closed role dedupe engine
- V23-T04 / SP3 — known recruiter/referral signal linkage

No stealth scraping or unauthorized outreach.

## Interview intelligence

- V23-I01 / SP3 — company/role/contact/stage brief contract
- V23-I02 / SP4 — candidate evidence/story mapper
- V23-I03 / SP2 — follow-up package inputs

No invented candidate achievements.

## Agent-ready tool layer

- V23-TL01 / SP5 — transport-neutral typed tool contracts
- V23-TL02 / SP4 — authorization context on consequential tools
- V23-TL03 / SP3 — idempotency/audit envelope
- V23-TL04 / SP3 — optional MCP adapter only after service contracts stabilize

MCP is optional transport, not the core architecture.

---

# V3.0 — Autonomous Career Agent Network

Artifacts:
- `A-V30-PERMISSION-MODEL`
- `A-V30-AGENT-RUNTIME`
- `A-V30-AGENT-EVALUATION`
- `A-V30-CAREER-AGENT-NETWORK`

## Permission model first

- V30-P01 / SP3 — action taxonomy
- V30-P02 / SP4 — scoped approval records
- V30-P03 / SP4 — deterministic policy interceptor for every consequential tool call
- V30-P04 / SP4 — human approval queue

Actions should distinguish:
read, draft, local write, external write, submit, message, calendar mutation, spend, secret access.

## Durable agent runtime

- V30-R01 / SP4 — durable task/parent-child/checkpoint model
- V30-R02 / SP3 — specialist registry with allowed tools/model/memory scope
- V30-R03 / SP5 — goal decomposer/router
- V30-R04 / SP5 — durable worker execution loop
- V30-R05 / SP4 — provider-neutral model router
- V30-R06 / SP4 — scoped memory/retrieval interface

Canonical truth remains in domain stores/services.
Agents call tools; agents do not become the database.

## Evaluation/observability

- V30-E01 / SP3 — trace schema
- V30-E02 / SP5 — specialist evaluation suites
- V30-E03 / SP4 — policy-violation adversarial tests
- V30-E04 / SP4 — quality/cost/latency/rework dashboard

## Specialist roles

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

External actions remain governed by deterministic permissions and human approval where required.

## V3.0 acceptance concept

A broad user goal such as "Find me a better job" should:
1. decompose into bounded work,
2. route to specialized agents,
3. use one canonical truth/tool layer,
4. preserve evidence,
5. block unauthorized external actions,
6. route missing candidate facts to review,
7. persist task/tool/model traces,
8. resume after interruption,
9. expose model/cost behavior,
10. succeed on at least one genuine real-world workflow at the appropriate permission level.

No agent may self-authorize submission, messaging, calendar changes, or spending.


## Prepared acceleration assets

Cross-phase:
- `docs/PHASE_GATE_MATRIX_V14_TO_V30.md`
- `coordination/PREP_QUEUE_V16_TO_V30.md`
- `docs/BROWNFIELD_IMPLEMENTATION_MAP_V16_TO_V30.md`
- `docs/FUTURE_SCHEMA_MIGRATION_PLAN_V16_V23_V30.md`

V1.6:
- `docs/V1_6_DATA_CONTRACTS.md`
- `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`

V2.0:
- `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`
- `docs/V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`

V2.3:
- `docs/V2_3_ACCEPTANCE_MATRIX.md`
- `docs/V2_3_INTERVIEW_INTELLIGENCE_CONTRACT.md`

V3.0:
- `docs/V3_RUNTIME_DATA_CONTRACTS.md`
- `docs/V3_SHARED_MEMORY_CONTRACT.md`
- `docs/V3_TOOL_PERMISSION_MATRIX.md`
- `docs/V3_AGENT_HANDOFF_PROTOCOL.md`
- `docs/V3_SPECIALIST_AGENT_SPECS.md`
- `docs/V3_AGENT_EVAL_MATRIX.md`
- `docs/V3_INTEGRATION_ACCEPTANCE_SCENARIOS.md`

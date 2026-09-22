# Artifact Index

Artifact-oriented project registry.

Statuses:
PROPOSED | READY | IN_PROGRESS | BLOCKED | WORKER_REPORTED_DONE | LEAD_REVIEW | ACCEPTED | SUPERSEDED

**Current execution override:** owner scope is **get V1.7 live and stop**. Fable/Claude is the one active implementation worker/session; ChatGPT is lead/acceptor. Historical Lane 1/2/3 names below are source/history only. V2.0/V2.3/V3 rows are retained only as inactive future inventory and are not executable authority.

| Artifact ID | Phase | Artifact | Type | Owner | Status | Depends on | Unblocks |
|---|---|---|---|---|---|---|---|
| A-V14-PACKET-SAFETY | V1.4 | Truthful immutable application packet pipeline | implementation/engineering acceptance | historical Lane A | ACCEPTED | V1.1 accepted | A-V14-REAL-PROOF, V1.5 |
| A-V14-P0A-INTEGRITY | V1.4 | Fail-closed real-proof verifier integrity | proof tooling/integrity | Fable + ChatGPT | ACCEPTED | A-V14-PACKET-SAFETY | A-V14-REAL-PROOF |
| A-V14-CLEAN-INTEGRATION | V1.4 | Clean current-main integration of proof tooling | integration | Fable + ChatGPT | ACCEPTED | A-V14-P0A-INTEGRITY | A-V14-REAL-PROOF |
| A-V14-REAL-PROOF | V1.4 | Real non-mock packet proof using real profile/resume/job | real-data acceptance | Fable + ChatGPT + Owner | BLOCKED | P0A ACCEPTED + genuine approved private profile/resume/current real job + eligible host | G14, V1.4 COMPLETE |
| A-V15-BROWSER-SAFETY-CONTRACT | V1.5 | Assisted browser safety / evidence contract | contract/safety | ChatGPT + Fable | ACCEPTED | A-V14-PACKET-SAFETY ACCEPTED | A-V15-LIVE-ASSISTED-PROOF, V1.6 engineering |
| A-V15-ASSISTED-APPLICATION | V1.5 | Assisted application execution contract + proof | implementation/live-evidence | Fable | ACCEPTED | A-V14-PACKET-SAFETY, A-V15-BROWSER-SAFETY-CONTRACT | G15, V1.6 engineering |
| A-V15-CLEAN-INTEGRATION | V1.5 | Port assisted-safety code to coherent current campaign branch | integration | Fable + ChatGPT | ACCEPTED | A-V14-P0A-INTEGRITY | A-V15-BROWSER-SAFETY-CONTRACT, A-V15-ASSISTED-APPLICATION |
| A-V15-LIVE-ASSISTED-PROOF | V1.5 | Real visible-browser assisted-flow proof to review boundary | live evidence | Fable + Owner + ChatGPT | BLOCKED | genuine G14 packet + accepted V1.5 engineering + scoped browser authorization | G15, V1.5 COMPLETE |
| A-V16-SUBMISSION-CONTRACT | V1.6 | Controlled submission safety/authorization contract | contract/safety | ChatGPT + Fable | READY | V1.5 engineering ACCEPTED | A-V16-SUBMISSION-ENGINE-REPAIR |
| A-V16-SUBMISSION-ENGINE-REPAIR | V1.6 | Submission truth/idempotency/authorization repair | implementation/safety | Fable | IN_PROGRESS | V1.5 engineering ACCEPTED | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-AUTHORIZATION | V1.6 | Scoped job+packet+method submission authorization | implementation/permission | Fable + ChatGPT + Owner | READY | V1.5 engineering ACCEPTED | A-V16-IDEMPOTENCY, A-V16-PREFLIGHT |
| A-V16-IDEMPOTENCY | V1.6 | Durable attempt state and duplicate/concurrency prevention | implementation/state | Fable | READY | V1.5 engineering ACCEPTED | A-V16-CONFIRMATION |
| A-V16-PREFLIGHT | V1.6 | Immediate pre-submit packet/artifact/policy integrity gate | implementation/safety | Fable | READY | V1.5 engineering ACCEPTED | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-CONFIRMATION | V1.6 | External confirmation/reconciliation truth | implementation/evidence | Fable | READY | V1.5 engineering ACCEPTED | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-HYGIENE | V1.6 | Submission task/telemetry/error hygiene | implementation/reliability | Fable | READY | V1.5 engineering ACCEPTED | A-V16-SUBMISSION-ENGINE-REPAIR |
| A-V16-TRANSPORT | V1.6 | Current-policy compliant live system-submit transport | policy/implementation | Fable + ChatGPT + Owner | IN_PROGRESS | V17-T01 research done; exact hosted-form policy/authorization and T02 implementation remain | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-FIRST-REAL-SUBMISSION | V1.6 | First system-submitted externally confirmed application | live-evidence | Fable + Owner + ChatGPT | BLOCKED | accepted V1.6 safety artifacts + exact desired job/packet/method approval + eligible transport | G16, V1.6 COMPLETE |
| A-V12-CANDIDATE-PROVENANCE | V1.2 | Private-safe candidate fact provenance contract | data/evidence | Fable | READY | none | safe packet answers |
| A-V12-GMAIL-CANARY | V1.2 | Read-only Gmail OAuth + ingestion canary | integration/evidence | Fable + Owner | BLOCKED | scoped owner Gmail OAuth/authorization | G17 live ingestion |
| A-PROOF-JOB-SELECTION | V1.3/V1.5 | User-approved proof-job selection record | decision/evidence | ChatGPT + Owner | PROPOSED | current real jobs | consequential G15/G16 live evidence |
| A-RESUME-OUTCOME-METRICS | post-first-app | Resume/application outcome analytics | analytics/spec | future inventory | PROPOSED | immutable resume attribution + lifecycle events | learning loop |
| A-LINKEDIN-NETWORK-GROWTH | future | Targeted LinkedIn network growth design | product/design | future inventory | PROPOSED | first real application review | future roadmap |
| A-V17-CRM-EVIDENCE | V1.7 | Recruiter/contact/thread evidence graph | implementation/evidence | Fable + ChatGPT | LEAD_REVIEW | merged PR #3 lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-INTERVIEW-FOLLOWUP | V1.7 | Interview + follow-up operating layer | implementation/evidence | Fable + ChatGPT | LEAD_REVIEW | merged PR #3 lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-ENGINEERING-RECONCILIATION | V1.7 | Audit/reconcile merged V1.7 implementation against artifact criteria | audit/acceptance | Fable + ChatGPT | READY | merged V1.7 code | A-V17-MILESTONE-GATE |
| A-V17-LIVE-LIFECYCLE-PROOF | V1.7 | Genuine recruiter/application/interview lifecycle proof | live evidence | Fable + Owner + ChatGPT | BLOCKED | V1.7 engineering + scoped read-only Gmail authorization + bounded genuine evidence | G17, A-V17-MILESTONE-GATE |
| A-V17-MILESTONE-GATE | V1.7 | Integrated recruiting operations acceptance | milestone | ChatGPT | BLOCKED | accepted engineering + genuine G14 + G15 + G16 + G17 | STOP |
| A-V20-CONTROL-CENTER | V2.0 | Daily operator control center | implementation/UX | inactive future inventory | LEAD_REVIEW | existing dashboard | A-V20-INTEGRATED-OS |
| A-V20-RELIABILITY | V2.0 | Recoverability + operational reliability | reliability/evidence | inactive future inventory | IN_PROGRESS | existing CI/health/backup | A-V20-INTEGRATED-OS |
| A-V20-WORKER-RUN-HISTORY | V2.0 | Durable worker-run operational evidence | reliability/evidence | inactive future inventory | ACCEPTED | existing worker/health | A-V20-RELIABILITY, A-V20-CONTROL-CENTER |
| A-V20-ANALYTICS | V2.0 | Funnel/resume/source analytics | analytics | inactive future inventory | IN_PROGRESS | resume attribution | A-V20-INTEGRATED-OS |
| A-V20-GMAIL-RUNTIME-READINESS | V2.0 | Safe scheduled-runtime Gmail readiness | integration/runtime safety | inactive future inventory | READY | existing Gmail adapter/worker | A-V20-LIVE-INGESTION |
| A-V20-LIVE-INGESTION | V2.0 | Real Gmail/live-data ingestion proof | live integration | inactive future inventory | BLOCKED | A-V20-GMAIL-RUNTIME-READINESS + user OAuth | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATION-FIXTURE | V2.0 | Deterministic cross-subsystem integration regression | integration/evidence | inactive future inventory | READY | V1.7 + core V2 repairs | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATED-OS | V2.0 | Autonomous Personal Job Search OS acceptance | milestone/integration | inactive future inventory | BLOCKED | V1.7 + V2.0 support artifacts + live ingestion | V2.3 |
| A-V23-OPPORTUNITY-GRAPH | V2.3 | Evidence-backed opportunity graph/query layer | data/query architecture | inactive future inventory | READY | V2 relational model | A-V23-CAREER-INTELLIGENCE |
| A-V23-CAREER-INTELLIGENCE | V2.3 | Career intelligence & optimization layer | milestone/intelligence | inactive future inventory | PROPOSED | A-V20-INTEGRATED-OS + V2.3 sub-artifacts | V3.0 |
| A-V23-STRATEGY-LEARNING | V2.3 | Evidence-backed strategy learning | analytics/strategy | inactive future inventory | PROPOSED | V2.0 analytics + outcomes | A-V23-CAREER-INTELLIGENCE |
| A-V23-TARGET-COMPANY-WATCH | V2.3 | Target company opportunity watch | intelligence/monitoring | inactive future inventory | READY | V2 company/job/contact model | A-V23-CAREER-INTELLIGENCE |
| A-V23-INTERVIEW-INTELLIGENCE | V2.3 | Source-backed interview preparation intelligence | intelligence/preparation | inactive future inventory | PROPOSED | A-V17-INTERVIEW-FOLLOWUP, A-V20-INTEGRATED-OS | A-V23-CAREER-INTELLIGENCE, A-V30-INTERVIEW-AGENT |
| A-V23-AGENT-TOOLS | V2.3 | Stable transport-neutral agent tool layer | service/tool architecture | inactive future inventory | READY | stable V2/V2.3 service interfaces + V1.6 scoped approvals for P3 | V3 agent runtime |
| A-V23-CAREER-BRIEFING | V2.3 | Evidence-backed user-facing career intelligence briefing | implementation/intelligence | inactive future inventory | PROPOSED | V2.3 graph/strategy/watch/interview services | A-V23-ACCEPTANCE-CAMPAIGN |
| A-V23-ACCEPTANCE-CAMPAIGN | V2.3 | Machine-verifiable engineering + real live V2.3 acceptance campaign | acceptance/live evidence | inactive future inventory | PROPOSED | V2.3 services + prior required live checkpoints | A-V23-CAREER-INTELLIGENCE |
| A-V30-AGENT-RUNTIME | V3.0 | Durable specialist-agent runtime | runtime/orchestration | inactive future inventory | PROPOSED | A-V23-AGENT-TOOLS, A-V30-PERMISSION-MODEL, A-V30-SHARED-MEMORY | A-V30-CAREER-AGENT-NETWORK |
| A-V30-PERMISSION-MODEL | V3.0 | Agent/action permission and approval model | policy/authorization | inactive future inventory | PROPOSED | V2 policy/audit | all V3 agents |
| A-V30-SHARED-MEMORY | V3.0 | Scoped durable agent memory over canonical truth | memory/continuity | inactive future inventory | PROPOSED | A-V23-AGENT-TOOLS, A-V30-PERMISSION-MODEL | A-V30-AGENT-RUNTIME, specialist agents |
| A-V30-MARKET-SCOUT | V3.0 | Market/company/opportunity monitoring specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-OPPORTUNITY-MATCHER | V3.0 | Opportunity evaluation specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-RESUME-STRATEGIST | V3.0 | Resume strategy/experiment specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-STRATEGY-LEARNING, A-V30-AGENT-RUNTIME | A-V30-APPLICATION-OPERATOR, A-V30-CAREER-AGENT-NETWORK |
| A-V30-APPLICATION-OPERATOR | V3.0 | Governed application-execution specialist | specialist agent | inactive future inventory | PROPOSED | A-V16-SUBMISSION-ENGINE-REPAIR, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-RECRUITER-CRM-AGENT | V3.0 | Recruiter CRM/follow-up specialist | specialist agent | inactive future inventory | PROPOSED | A-V17-MILESTONE-GATE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-INTERVIEW-AGENT | V3.0 | Interview preparation specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-INTERVIEW-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-NETWORKING-AGENT | V3.0 | Referral/networking specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-OPPORTUNITY-GRAPH, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-PORTFOLIO-BRAND-AGENT | V3.0 | Portfolio/public-brand specialist | specialist agent | inactive future inventory | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-POLICY-SAFETY-AGENT | V3.0 | Policy/safety audit specialist | specialist agent | inactive future inventory | PROPOSED | A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-ANALYTICS-AGENT | V3.0 | Outcome/strategy analytics specialist | specialist agent | inactive future inventory | PROPOSED | A-V20-ANALYTICS, A-V23-STRATEGY-LEARNING, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-AGENT-EVALUATION | V3.0 | Agent evaluation + observability | evaluation/observability | inactive future inventory | PROPOSED | A-V30-AGENT-RUNTIME | V3 acceptance |
| A-V30-CAREER-AGENT-NETWORK | V3.0 | Autonomous career agent network | milestone/multi-agent | inactive future inventory | PROPOSED | A-V23-CAREER-INTELLIGENCE + V3 platform + specialist artifacts | continuous career ops |

## Current critical path

**P0A + V1.5 engineering are accepted and integrated**
→ **G14 / A-V14-REAL-PROOF**
→ **G15 / A-V15-LIVE-ASSISTED-PROOF**
→ V1.6 AUTHORIZATION + IDEMPOTENCY + PREFLIGHT + CONFIRMATION + HYGIENE + TRANSPORT engineering
→ **G16 / A-V16-FIRST-REAL-SUBMISSION**
→ A-V17-ENGINEERING-RECONCILIATION using merged PR #3
→ **G17 / A-V17-LIVE-LIFECYCLE-PROOF**
→ A-V17-MILESTONE-GATE
→ **STOP**

## Active implementation model

- Exactly one active implementation worker/session: **Fable/Claude**.
- PR #12 is merged; before new reviewable work, the worker synchronizes latest `main` and uses one active code branch only.
- Exactly one owned worker heartbeat stream: `FIVE_MIN_2026_09_21` / `ACTIVE_5M` every ~5 minutes while working. The heartbeat is published from watcher-only `worker/v14-real-proof` for this same session; it is not a second implementation lane.
- Latest lead-verified heartbeat at acceptance: #40 at `2026-09-22T01:56:01Z`.
- Historical Lane 1/2/3/C/D/Scout branches are source/reference surfaces only unless a later owner instruction explicitly reactivates one.
- `worker-pc` is optional bounded independent support infrastructure, never an automatic merge source or another implementation lane. Do not repeat its exact-head Python validation under unchanged harness permissions.
- ChatGPT owns lead review, engineering acceptance, live-proof acceptance and milestone truth.
- V2.0/V2.3/V3 rows above remain archival/future inventory only; do not assign them under the current campaign.

## Rules

- Add an artifact card under `coordination/artifacts/` for every new index row.
- WORK_QUEUE tasks must reference artifact IDs.
- When an artifact changes status, update this index from reviewed evidence only.
- Engineering artifact acceptance requires lead evidence review; worker claims do not self-accept.
- V1.7 COMPLETE requires accepted engineering plus genuine production-path G14, G15, G16 and G17.
- No test/canary/manual report may substitute for a required live gate.
- Live/external actions require their explicit scoped owner authorization.
# Artifact Index

Artifact-oriented project registry.

Statuses:
PROPOSED | READY | IN_PROGRESS | BLOCKED | WORKER_REPORTED_DONE | LEAD_REVIEW | ACCEPTED | SUPERSEDED

| Artifact ID | Phase | Artifact | Type | Owner | Status | Depends on | Unblocks |
|---|---|---|---|---|---|---|---|
| A-V14-PACKET-SAFETY | V1.4 | Truthful immutable application packet pipeline | implementation/engineering acceptance | historical Lane A | ACCEPTED | V1.1 accepted | A-V14-REAL-PROOF, V1.5 |
| A-V14-P0A-INTEGRITY | V1.4 | Fail-closed real-proof verifier integrity | proof tooling/integrity | Lane 1 | IN_PROGRESS | A-V14-PACKET-SAFETY | A-V14-CLEAN-INTEGRATION, A-V14-REAL-PROOF |
| A-V14-CLEAN-INTEGRATION | V1.4 | Clean current-main integration of proof tooling | integration | Lane 1 + ChatGPT | BLOCKED | A-V14-P0A-INTEGRITY | A-V14-REAL-PROOF |
| A-V14-REAL-PROOF | V1.4 | Real non-mock packet proof using real profile/resume/job | real-data acceptance | Lane 1 + ChatGPT + worker-pc independent review | BLOCKED | A-V14-PACKET-SAFETY ACCEPTED + P0A proof-tool integrity acceptance | V1.4 COMPLETE |
| A-V15-BROWSER-SAFETY-CONTRACT | V1.5 | Assisted browser safety / evidence contract | contract/safety | ChatGPT + Lane 2 | IN_PROGRESS | A-V14-PACKET-SAFETY ACCEPTED | A-V15-ASSISTED-APPLICATION |
| A-V15-ASSISTED-APPLICATION | V1.5 | Assisted application execution contract + proof | implementation/live-evidence | Lane 2 | IN_PROGRESS | A-V14-PACKET-SAFETY, A-V15-BROWSER-SAFETY-CONTRACT | V1.6 |
| A-V15-CLEAN-INTEGRATION | V1.5 | Port assisted-safety code to clean current-main branch | integration | Lane 2 + ChatGPT | BLOCKED | A-V14-REAL-PROOF | A-V15-BROWSER-SAFETY-CONTRACT, A-V15-ASSISTED-APPLICATION |
| A-V15-LIVE-ASSISTED-PROOF | V1.5 | Real visible-browser assisted-flow proof to review boundary | live evidence | Lane 2 + User | BLOCKED | V1.5 engineering acceptance + owner browser authorization | V1.5 COMPLETE, V1.6 |
| A-V16-SUBMISSION-CONTRACT | V1.6 | Controlled submission safety/authorization contract | contract/safety | ChatGPT | READY | none | A-V16-SUBMISSION-ENGINE-REPAIR |
| A-V16-SUBMISSION-ENGINE-REPAIR | V1.6 | Submission truth/idempotency/authorization repair | implementation/safety | Lane 2 | BLOCKED | A-V15-ASSISTED-APPLICATION | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-AUTHORIZATION | V1.6 | Scoped job+packet+method submission authorization | implementation/permission | future Lane 2 | BLOCKED | V1.5 COMPLETE | A-V16-IDEMPOTENCY, A-V16-PREFLIGHT |
| A-V16-IDEMPOTENCY | V1.6 | Durable attempt state and duplicate/concurrency prevention | implementation/state | future Lane 2 | BLOCKED | A-V16-AUTHORIZATION | A-V16-CONFIRMATION |
| A-V16-PREFLIGHT | V1.6 | Immediate pre-submit packet/artifact/policy integrity gate | implementation/safety | future Lane 2 | BLOCKED | A-V16-AUTHORIZATION | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-CONFIRMATION | V1.6 | External confirmation/reconciliation truth | implementation/evidence | future Lane 2 | BLOCKED | A-V16-IDEMPOTENCY | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-HYGIENE | V1.6 | Submission task/telemetry/error hygiene | implementation/reliability | future Lane 2 | BLOCKED | V1.5 COMPLETE | A-V16-SUBMISSION-ENGINE-REPAIR |
| A-V16-TRANSPORT | V1.6 | Current-policy compliant live system-submit transport | policy/implementation | future Lane 2 + ChatGPT | READY | public research none; implementation after safety artifacts | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-FIRST-REAL-SUBMISSION | V1.6 | First system-submitted externally confirmed application | live-evidence | Lane 2 + User | PROPOSED | A-V15-ASSISTED-APPLICATION, A-PROOF-JOB-SELECTION, A-V16-SUBMISSION-CONTRACT | strategy review |
| A-V12-CANDIDATE-PROVENANCE | V1.2 | Private-safe candidate fact provenance contract | data/evidence | Lane 1 | READY | none | safe packet answers |
| A-V12-GMAIL-CANARY | V1.2 | Read-only Gmail OAuth + ingestion canary | integration/evidence | Lane 1 + User | PROPOSED | user OAuth | V1.3 live discovery |
| A-PROOF-JOB-SELECTION | V1.3/V1.5 | User-approved proof-job selection record | decision/evidence | ChatGPT + User | PROPOSED | real jobs | consequential V1.5/V1.6 live evidence |
| A-RESUME-OUTCOME-METRICS | post-first-app | Resume/application outcome analytics | analytics/spec | Lane 3 | PROPOSED | immutable resume attribution + lifecycle events | learning loop |
| A-LINKEDIN-NETWORK-GROWTH | future | Targeted LinkedIn network growth design | product/design | ChatGPT | PROPOSED | first real application review | networking roadmap |
| A-V17-CRM-EVIDENCE | V1.7 | Recruiter/contact/thread evidence graph | implementation/evidence | Lane 3 | LEAD_REVIEW | existing lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-INTERVIEW-FOLLOWUP | V1.7 | Interview + follow-up operating layer | implementation/evidence | Lane 3 | LEAD_REVIEW | existing lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-ENGINEERING-RECONCILIATION | V1.7 | Audit/reconcile merged V1.7 implementation against artifact criteria | audit/acceptance | Lane 3 + ChatGPT | READY | merged V1.7 code | A-V17-MILESTONE-GATE |
| A-V17-LIVE-LIFECYCLE-PROOF | V1.7 | Genuine recruiter/application/interview lifecycle proof | live evidence | Lane 3 + User | BLOCKED | V1.7 engineering + read-only Gmail authorization/readiness | A-V17-MILESTONE-GATE, V2.0 |
| A-V17-MILESTONE-GATE | V1.7 | Integrated recruiting operations acceptance | milestone | ChatGPT | BLOCKED | A-V17-CRM-EVIDENCE, A-V17-INTERVIEW-FOLLOWUP | V2.0 |
| A-V20-CONTROL-CENTER | V2.0 | Daily operator control center | implementation/UX | Lane 3 | LEAD_REVIEW | existing dashboard | A-V20-INTEGRATED-OS |
| A-V20-RELIABILITY | V2.0 | Recoverability + operational reliability | reliability/evidence | Lane 3 | IN_PROGRESS | existing CI/health/backup | A-V20-INTEGRATED-OS |
| A-V20-WORKER-RUN-HISTORY | V2.0 | Durable worker-run operational evidence | reliability/evidence | Lane 3 | ACCEPTED | existing worker/health | A-V20-RELIABILITY, A-V20-CONTROL-CENTER |
| A-V20-ANALYTICS | V2.0 | Funnel/resume/source analytics | analytics | Lane 3 | IN_PROGRESS | resume attribution | A-V20-INTEGRATED-OS |
| A-V20-GMAIL-RUNTIME-READINESS | V2.0 | Safe scheduled-runtime Gmail readiness | integration/runtime safety | Lane 1 + Lane 3 J20G-04 glue | READY | existing Gmail adapter/worker | A-V20-LIVE-INGESTION |
| A-V20-LIVE-INGESTION | V2.0 | Real Gmail/live-data ingestion proof | live integration | Lane 1 + User | BLOCKED | A-V20-GMAIL-RUNTIME-READINESS + user OAuth | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATION-FIXTURE | V2.0 | Deterministic cross-subsystem integration regression | integration/evidence | Lane 1 + ChatGPT | READY | V1.7 + core V2 repairs | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATED-OS | V2.0 | Autonomous Personal Job Search OS acceptance | milestone/integration | ChatGPT + active lanes | BLOCKED | V1.7 + V2.0 support artifacts + live ingestion | V2.3 |
| A-V23-OPPORTUNITY-GRAPH | V2.3 | Evidence-backed opportunity graph/query layer | data/query architecture | paused historical Lane D | READY | V2 relational model | A-V23-CAREER-INTELLIGENCE |
| A-V23-CAREER-INTELLIGENCE | V2.3 | Career intelligence & optimization layer | milestone/intelligence | ChatGPT + future lane | PROPOSED | A-V20-INTEGRATED-OS + V2.3 sub-artifacts | V3.0 |
| A-V23-STRATEGY-LEARNING | V2.3 | Evidence-backed strategy learning | analytics/strategy | future lane | PROPOSED | V2.0 analytics + outcomes | A-V23-CAREER-INTELLIGENCE |
| A-V23-TARGET-COMPANY-WATCH | V2.3 | Target company opportunity watch | intelligence/monitoring | paused historical Lane D | READY | V2 company/job/contact model | A-V23-CAREER-INTELLIGENCE |
| A-V23-INTERVIEW-INTELLIGENCE | V2.3 | Source-backed interview preparation intelligence | intelligence/preparation | future work surface | PROPOSED | A-V17-INTERVIEW-FOLLOWUP, A-V20-INTEGRATED-OS | A-V23-CAREER-INTELLIGENCE, A-V30-INTERVIEW-AGENT |
| A-V23-AGENT-TOOLS | V2.3 | Stable transport-neutral agent tool layer | service/tool architecture | future lane when promoted | READY | stable V2/V2.3 service interfaces + V1.6 scoped approvals for P3 | V3 agent runtime |
| A-V23-CAREER-BRIEFING | V2.3 | Evidence-backed user-facing career intelligence briefing | implementation/intelligence | future lane when promoted | PROPOSED | V2.3 graph/strategy/watch/interview services | A-V23-ACCEPTANCE-CAMPAIGN |
| A-V23-ACCEPTANCE-CAMPAIGN | V2.3 | Machine-verifiable engineering + real live V2.3 acceptance campaign | acceptance/live evidence | future lane + eligible live machine + ChatGPT | PROPOSED | V2.3 services + prior required live checkpoints | A-V23-CAREER-INTELLIGENCE |
| A-V30-AGENT-RUNTIME | V3.0 | Durable specialist-agent runtime | runtime/orchestration | future lane | PROPOSED | A-V23-AGENT-TOOLS, A-V30-PERMISSION-MODEL, A-V30-SHARED-MEMORY | A-V30-CAREER-AGENT-NETWORK |
| A-V30-PERMISSION-MODEL | V3.0 | Agent/action permission and approval model | policy/authorization | future lane | PROPOSED | V2 policy/audit | all V3 agents |
| A-V30-SHARED-MEMORY | V3.0 | Scoped durable agent memory over canonical truth | memory/continuity | future work surface | PROPOSED | A-V23-AGENT-TOOLS, A-V30-PERMISSION-MODEL | A-V30-AGENT-RUNTIME, specialist agents |
| A-V30-MARKET-SCOUT | V3.0 | Market/company/opportunity monitoring specialist | specialist agent | future work surface | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-OPPORTUNITY-MATCHER | V3.0 | Opportunity evaluation specialist | specialist agent | future work surface | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-RESUME-STRATEGIST | V3.0 | Resume strategy/experiment specialist | specialist agent | future work surface | PROPOSED | A-V23-STRATEGY-LEARNING, A-V30-AGENT-RUNTIME | A-V30-APPLICATION-OPERATOR, A-V30-CAREER-AGENT-NETWORK |
| A-V30-APPLICATION-OPERATOR | V3.0 | Governed application-execution specialist | specialist agent | future work surface | PROPOSED | A-V16-SUBMISSION-ENGINE-REPAIR, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-RECRUITER-CRM-AGENT | V3.0 | Recruiter CRM/follow-up specialist | specialist agent | future work surface | PROPOSED | A-V17-MILESTONE-GATE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-INTERVIEW-AGENT | V3.0 | Interview preparation specialist | specialist agent | future work surface | PROPOSED | A-V23-INTERVIEW-INTELLIGENCE, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-NETWORKING-AGENT | V3.0 | Referral/networking specialist | specialist agent | future work surface | PROPOSED | A-V23-OPPORTUNITY-GRAPH, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-PORTFOLIO-BRAND-AGENT | V3.0 | Portfolio/public-brand specialist | specialist agent | future work surface | PROPOSED | A-V23-CAREER-INTELLIGENCE, A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-POLICY-SAFETY-AGENT | V3.0 | Policy/safety audit specialist | specialist agent | future work surface | PROPOSED | A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-ANALYTICS-AGENT | V3.0 | Outcome/strategy analytics specialist | specialist agent | future work surface | PROPOSED | A-V20-ANALYTICS, A-V23-STRATEGY-LEARNING, A-V30-AGENT-RUNTIME | A-V30-CAREER-AGENT-NETWORK |
| A-V30-AGENT-EVALUATION | V3.0 | Agent evaluation + observability | evaluation/observability | future lane | PROPOSED | A-V30-AGENT-RUNTIME | V3 acceptance |
| A-V30-CAREER-AGENT-NETWORK | V3.0 | Autonomous career agent network | milestone/multi-agent | ChatGPT + future lane | PROPOSED | A-V23-CAREER-INTELLIGENCE + V3 platform + specialist artifacts | continuous career ops |

## Current critical path

Lane 1 P0A proof-tool integrity acceptance
→ A-V14-REAL-PROOF (required for V1.4 COMPLETE)
→ Lane 2 A-V15-BROWSER-SAFETY-CONTRACT / A-V15-ASSISTED-APPLICATION residual repair + V1.5 real proof
→ A-V16 application execution
→ Lane 3 A-V17-MILESTONE-GATE
→ Lane 3 A-V20-INTEGRATED-OS
→ A-V23-CAREER-INTELLIGENCE
→ A-V30-CAREER-AGENT-NETWORK

## Active implementation lanes

Owner-directed execution mode:
- exactly three implementation lanes are active in parallel,
- Lane 1 / `worker/v14-real-proof` owns the V1.4 P0 critical path,
- Lane 2 / `worker/v15-assisted-application` owns the bounded V1.5 assisted-application safety scope,
- Lane 3 / `worker/recruiting-ops` preserves merged recruiting/reliability work and performs bounded post-integration verification/repair,
- each active lane uses exactly one `FIVE_MIN_2026_09_21` heartbeat watcher while its session is active,
- `worker-pc` is bounded independent support/audit infrastructure only and is not a fourth implementation lane,
- ChatGPT owns lead review, artifact acceptance, integration, and milestone truth.

Old Lane C is superseded. Old Lane D and Scout are paused as active sessions. Do not reopen them merely to create activity.

V2.3 planning documents added to the repository are future planning inventory only. They do not collapse the three active lanes or authorize V2.3 implementation now.

## Supporting path

A-V12-CANDIDATE-PROVENANCE
A-V12-GMAIL-CANARY
A-PROOF-JOB-SELECTION
A-RESUME-OUTCOME-METRICS

## Rules

- Add an artifact card under coordination/artifacts/ for every index row.
- WORK_QUEUE tasks must reference artifact IDs.
- When an artifact changes status, update this index.
- Engineering artifact acceptance requires lead evidence review.
- A version being COMPLETE additionally requires at least one REAL_PROVEN non-mock example per `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`.
- An engineering artifact can be ACCEPTED while its version remains incomplete due a separate REAL_PROOF artifact.
- Live/external artifacts may also require explicit user authorization.
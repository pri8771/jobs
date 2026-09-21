# Artifact Index

Artifact-oriented project registry.

Statuses:
PROPOSED | READY | IN_PROGRESS | BLOCKED | WORKER_REPORTED_DONE | LEAD_REVIEW | ACCEPTED | SUPERSEDED

| Artifact ID | Phase | Artifact | Type | Owner | Status | Depends on | Unblocks |
|---|---|---|---|---|---|---|---|
| A-V14-PACKET-SAFETY | V1.4 | Truthful immutable application packet pipeline | implementation/acceptance | Antigravity | IN_PROGRESS | V1.1 accepted | V1.5 |
| A-V15-BROWSER-SAFETY-CONTRACT | V1.5 | Assisted browser safety / evidence contract | contract/safety | ChatGPT | READY | none for design; implementation waits for A-V14 | A-V15-ASSISTED-APPLICATION |
| A-V15-ASSISTED-APPLICATION | V1.5 | Assisted application execution contract + proof | implementation/live-evidence | Antigravity | PROPOSED | A-V14-PACKET-SAFETY, A-V15-BROWSER-SAFETY-CONTRACT, A-PROOF-JOB-SELECTION | V1.6 |
| A-V16-SUBMISSION-CONTRACT | V1.6 | Controlled submission safety/authorization contract | contract/safety | ChatGPT | READY | none | A-V16-FIRST-REAL-SUBMISSION |
| A-V16-FIRST-REAL-SUBMISSION | V1.6 | First system-submitted externally confirmed application | live-evidence | Antigravity + User | PROPOSED | A-V15-ASSISTED-APPLICATION, A-PROOF-JOB-SELECTION, A-V16-SUBMISSION-CONTRACT | strategy review |
| A-V12-CANDIDATE-PROVENANCE | V1.2 | Private-safe candidate fact provenance contract | data/evidence | Antigravity | PROPOSED | none | safe packet answers |
| A-V12-GMAIL-CANARY | V1.2 | Read-only Gmail OAuth + ingestion canary | integration/evidence | Antigravity + User | PROPOSED | user OAuth | V1.3 live discovery |
| A-PROOF-JOB-SELECTION | V1.3/V1.5 | User-approved proof-job selection record | decision/evidence | ChatGPT + User | PROPOSED | real jobs | A-V15, A-V16 |
| A-RESUME-OUTCOME-METRICS | post-first-app | Resume/application outcome analytics | analytics/spec | Antigravity | PROPOSED | immutable resume attribution + lifecycle events | learning loop |
| A-LINKEDIN-NETWORK-GROWTH | future | Targeted LinkedIn network growth design | product/design | ChatGPT | PROPOSED | first real application review | networking roadmap |
| A-V17-CRM-EVIDENCE | V1.7 | Recruiter/contact/thread evidence graph | implementation/evidence | Antigravity Lane B | READY | existing lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-INTERVIEW-FOLLOWUP | V1.7 | Interview + follow-up operating layer | implementation/evidence | Antigravity Lane B | READY | existing lifecycle assets | A-V17-MILESTONE-GATE |
| A-V17-MILESTONE-GATE | V1.7 | Integrated recruiting operations acceptance | milestone | ChatGPT | BLOCKED | A-V17-CRM-EVIDENCE, A-V17-INTERVIEW-FOLLOWUP | V2.0 |
| A-V20-CONTROL-CENTER | V2.0 | Daily operator control center | implementation/UX | Antigravity Lane B | READY | existing dashboard | A-V20-INTEGRATED-OS |
| A-V20-RELIABILITY | V2.0 | Recoverability + operational reliability | reliability/evidence | Antigravity Lane B | READY | existing CI/health/backup | A-V20-INTEGRATED-OS |
| A-V20-WORKER-RUN-HISTORY | V2.0 | Durable worker-run operational evidence | reliability/evidence | Antigravity Lane B | READY | existing worker/health | A-V20-RELIABILITY, A-V20-CONTROL-CENTER |
| A-V20-ANALYTICS | V2.0 | Funnel/resume/source analytics | analytics | Antigravity Lane B | READY | resume attribution | A-V20-INTEGRATED-OS |
| A-V20-LIVE-INGESTION | V2.0 | Real Gmail/live-data ingestion proof | live integration | Antigravity + User | BLOCKED | runtime Gmail OAuth | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATION-FIXTURE | V2.0 | Deterministic cross-subsystem integration regression | integration/evidence | Antigravity + ChatGPT | READY | V1.7 + core V2 repairs | A-V20-INTEGRATED-OS |
| A-V20-INTEGRATED-OS | V2.0 | Autonomous Personal Job Search OS acceptance | milestone/integration | ChatGPT + Antigravity | BLOCKED | V1.7 + V2.0 support artifacts + live ingestion | V2.3 |
| A-V23-OPPORTUNITY-GRAPH | V2.3 | Evidence-backed opportunity graph/query layer | data/query architecture | Antigravity | PROPOSED | A-V20-INTEGRATED-OS | A-V23-CAREER-INTELLIGENCE |
| A-V23-CAREER-INTELLIGENCE | V2.3 | Career intelligence & optimization layer | milestone/intelligence | ChatGPT + Antigravity | PROPOSED | A-V20-INTEGRATED-OS | V3.0 |
| A-V30-CAREER-AGENT-NETWORK | V3.0 | Autonomous career agent network | milestone/multi-agent | ChatGPT + Antigravity | PROPOSED | A-V23-CAREER-INTELLIGENCE | continuous career ops |

## Current critical path

A-V14-PACKET-SAFETY residual repair
→ A-V15-ASSISTED-APPLICATION / A-V16 application execution
→ A-V17-MILESTONE-GATE
→ A-V20-INTEGRATED-OS
→ A-V23-CAREER-INTELLIGENCE
→ A-V30-CAREER-AGENT-NETWORK

## Parallel implementation lane

A-V17-CRM-EVIDENCE + A-V17-INTERVIEW-FOLLOWUP can proceed now on Lane B while Lane A finishes V1.4/V1.5/V1.6.

A-V20-CONTROL-CENTER + A-V20-RELIABILITY + A-V20-ANALYTICS may also be audited/repaired in parallel after V1.7 worker slices are stable.

## Supporting parallel path

A-V12-CANDIDATE-PROVENANCE
A-V12-GMAIL-CANARY
A-PROOF-JOB-SELECTION
A-RESUME-OUTCOME-METRICS

## Rules

- Add an artifact card under coordination/artifacts/ for every index row.
- WORK_QUEUE tasks must reference artifact IDs.
- When an artifact changes status, update this index.
- ACCEPTED requires lead evidence review.
- Live/external artifacts may also require explicit user authorization.

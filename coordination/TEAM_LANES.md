# Parallel Team Lanes

## Purpose

Run two Antigravity sessions in parallel without file conflicts while ChatGPT leads artifact design, acceptance, and integration.

## Lane A — Application Execution

Branch:
- worker/app-execution

Owns:
- A-V14-PACKET-SAFETY residuals
- A-V15-BROWSER-SAFETY-CONTRACT implementation
- A-V15-ASSISTED-APPLICATION
- A-V16 submission engineering

Primary paths:
- src/jobs_automation/preparation/
- src/jobs_automation/storage/
- src/jobs_automation/browser/
- src/jobs_automation/automation/
- related tests/migrations

Lane status:
- coordination/lanes/ANTIGRAVITY_A.md

## Lane B — Recruiting Operations

Branch:
- worker/recruiting-ops

Owns:
- A-V17-CRM-EVIDENCE
- A-V17-INTERVIEW-FOLLOWUP
- A-V20-CONTROL-CENTER
- A-V20-RELIABILITY
- A-V20-ANALYTICS

Primary paths:
- src/jobs_automation/lifecycle/
- src/jobs_automation/dashboard/
- src/jobs_automation/health.py
- src/jobs_automation/worker.py
- scripts/
- related tests

Lane status:
- coordination/lanes/ANTIGRAVITY_B.md

## Shared file rule

Workers do not edit these unless explicitly assigned:
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md
- coordination/CONTEXT.md
- coordination/AI_SYNC.md
- state/CURRENT.md
- docs/ROADMAP_1_TO_3.md

ChatGPT owns shared program truth and integrates worker evidence.

## Handoff

Each lane:
1. pull latest branch,
2. read artifact contracts,
3. implement bounded task IDs,
4. run tests/lint/types,
5. commit/push branch,
6. update only its lane status file,
7. stop at user/live external boundaries,
8. report branch SHA for lead review.

ChatGPT reviews branch diffs/CI, updates shared artifact state, and merges accepted work.


## Lane C — Live Data & Provenance Foundations

Branch:
- worker/live-data-foundations

Owns:
- A-V12-CANDIDATE-PROVENANCE implementation
- A-V20-GMAIL-RUNTIME-READINESS except final health/worker glue owned by Lane B
- engineering side of A-V12-GMAIL-CANARY
- later A-V20-INTEGRATION-FIXTURE when dependencies are stable
- proof-job selection support tooling if explicitly advanced

Primary paths:
- src/jobs_automation/adapters/gmail.py
- src/jobs_automation/ingestion/
- src/jobs_automation/provenance/ (new)
- src/jobs_automation/integration/ (new, later)
- src/jobs_automation/cli/
- docker-compose.yml
- related tests/config docs

Avoid:
- preparation/storage/browser/automation code owned by Lane A
- lifecycle/dashboard/health/worker.py owned by Lane B
- candidate_profile.py while Lane A is actively modifying resume-family behavior unless coordinated

Lane status:
- coordination/lanes/ANTIGRAVITY_C.md

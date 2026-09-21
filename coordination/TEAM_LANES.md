# Parallel Team Lanes

## Purpose

Run four Antigravity implementation lanes plus one Scout without file conflicts while ChatGPT leads artifact design, acceptance, and integration.

## Lane A — Application Execution

Branch:
- worker/v15-assisted-application

Owns:
- A-V15-BROWSER-SAFETY-CONTRACT implementation
- A-V15-ASSISTED-APPLICATION
- A-V16 submission engineering after V1.5 acceptance

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
- repair/review completion of A-V17-CRM-EVIDENCE
- repair/review completion of A-V17-INTERVIEW-FOLLOWUP
- its already-implemented V2.0 dashboard/reliability/analytics batch through lead acceptance

Primary paths:
- src/jobs_automation/lifecycle/
- related lifecycle/CRM/interview tests

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
- temporary P0 proof-tool integrity implementation RP14-T1..RP14-T7 for A-V14-REAL-PROOF until that tooling gate is lead-accepted
- after the P0A tooling gate, A-V14-REAL-PROOF private input readiness/execution if this machine has the required real inputs
- A-V12-CANDIDATE-PROVENANCE implementation
- A-V20-GMAIL-RUNTIME-READINESS except final health/worker glue owned by Lane B
- engineering side of A-V12-GMAIL-CANARY
- later A-V20-INTEGRATION-FIXTURE when dependencies are stable
- proof-job selection support tooling if explicitly advanced

Immediate P0 ordering:
1. rebase current main
2. implement RP14-T1..RP14-T7 only in proof scripts/schema/tests/minimal docs; no private inputs and no actual proof run
3. stop for ChatGPT/Scout review
4. after P0A acceptance, execute RP14-C1..C3 and, if fully ready, RP14-E1/E2 before Gmail work

Primary paths:
- scripts/import_v14_proof_job.py
- scripts/run_v14_real_proof.py
- scripts/verify_v14_real_proof.py
- coordination/proofs/v14_real_proof.schema.json
- proof-tooling tests
- src/jobs_automation/adapters/gmail.py
- src/jobs_automation/ingestion/
- src/jobs_automation/provenance/ (new)
- src/jobs_automation/integration/ (new, later)
- src/jobs_automation/cli/
- docker-compose.yml
- related tests/config docs

Avoid:
- private profile/resume proof execution before P0A lead acceptance
- preparation/storage/browser/automation code owned by Lane A
- lifecycle/dashboard/health/worker.py owned by Lane B
- candidate_profile.py while Lane A is actively modifying resume-family behavior unless coordinated

Lane status:
- coordination/lanes/ANTIGRAVITY_C.md


## Lane D — V2.3 Foundations

Branch:
- worker/v23-foundations

Primary machine:
- Windows

Owns:
- A-V23-OPPORTUNITY-GRAPH read/projection layer
- A-V23-TARGET-COMPANY-WATCH local foundations
- A-V23-AGENT-TOOLS read/local-write service contracts
- V2.3 implementation that can be built without external actions or shared-schema churn

Primary paths:
- new src/jobs_automation/intelligence/
- new src/jobs_automation/agent_tools/
- related tests
- V2.3-specific config/examples when needed

Avoid:
- V2.0 lifecycle/dashboard/health/worker code while Lane B is under re-review
- Gmail/ingestion/provenance code owned by Lane C
- application/browser/automation owned by Lane A
- shared DB models/migrations unless ChatGPT explicitly assigns a schema task

Lane status:
- coordination/lanes/ANTIGRAVITY_D.md

## Scout — QA / Prep / Adversarial Review

Branch:
- scout/qa-prep

Primary machine:
- Mac

Owns no production code by default.

May:
- inspect all worker branches,
- run tests,
- identify semantic/safety/integration defects,
- prepare adversarial test plans,
- propose SP1-SP5 decomposition,
- write scout findings under coordination/scout/.

Immediate P0 review order:
- independently attack Lane C's RP14-T1..RP14-T7 proof-tool integrity batch when it lands,
- then perform RP14-S1 on actual real-proof candidate + verifier evidence.

Must not:
- modify production source unless explicitly assigned,
- modify shared coordination truth,
- merge branches,
- perform external/live actions.

Status:
- coordination/scout/SCOUT_STATUS.md

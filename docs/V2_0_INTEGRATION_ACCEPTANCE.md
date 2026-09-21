# V2.0 Integration Acceptance Contract

Artifact:
- A-V20-INTEGRATED-OS

## Purpose

Define the evidence required to call Jobs Automation V2.0 rather than merely code-complete.

V2.0 is an operating-system integration milestone. It is not satisfied by isolated unit tests.

## Required accepted artifacts

Before final V2.0 acceptance:
- A-V14-PACKET-SAFETY
- A-V15-ASSISTED-APPLICATION
- A-V16 submission/application execution artifact appropriate to the approved proof path
- A-V17-MILESTONE-GATE
- A-V20-CONTROL-CENTER
- A-V20-RELIABILITY
- A-V20-ANALYTICS
- A-V20-LIVE-INGESTION
- candidate provenance / proof-job evidence as relevant

## Engineering integration campaign

Before live data, run an end-to-end deterministic integration campaign that proves component wiring without pretending it is live evidence.

Scenario:
1. ingest bounded test message set,
2. parse job alert,
3. dedupe normalized job,
4. evaluate against candidate profile,
5. create truthful packet,
6. route application policy correctly,
7. record application event,
8. process recruiter/interview/rejection/offer fixtures,
9. create follow-up tasks,
10. show state in dashboard,
11. produce analytics,
12. show worker/health/audit evidence.

Simulation must be labeled simulation.

## Live acceptance campaign

Use real candidate/runtime data.

### Gate 1 — runtime identity/data
- real candidate profile loaded outside Git as designed,
- exact resume artifacts verified,
- provenance checks pass.

### Gate 2 — real Gmail
- real Gmail OAuth
- dry-run canary
- bounded persisted canary
- no mock/fixture path
- idempotent rerun
- at least one real relevant message normalized.

### Gate 3 — real opportunity
- real live job
- real source/canonical apply URL
- evaluation/shortlist rationale
- user considers the role genuinely relevant.

### Gate 4 — real packet/application path
- accepted packet
- exact resume/hash
- unresolved questions correctly surfaced
- application routed MANUAL_ONLY/ASSISTED/AUTO_ALLOWED according to current policy
- at least one real application lifecycle record with external evidence.

### Gate 5 — real recruiting lifecycle
At least one real employer/recruiter/application communication is linked or, if unavailable yet, demonstrate the live-ingestion path and retain V1.7 evidence integrity. Do not fabricate recruiter events to satisfy acceptance.

### Gate 6 — operations
- dashboard reflects real jobs/application/review state,
- health reflects actual Gmail/worker/policy readiness,
- worker run evidence exists,
- backup/recovery drill passes,
- audit trail reconstructs meaningful state changes.

### Gate 7 — analytics
- funnel over real/current data,
- resume attribution query works,
- source/role dimensions work,
- no misleading causal claim from tiny sample.

## V2.0 labels

Use only:
- IN_PROGRESS
- ENGINEERING_READY
- LIVE_ACCEPTED

ENGINEERING_READY:
All code/integration artifacts accepted except explicit live user/external gates.

LIVE_ACCEPTED:
Real Gmail/live-data integration campaign satisfies this contract.

Do not call ENGINEERING_READY "live V2.0."

## Acceptance evidence bundle

Produce:
- accepted artifact IDs
- commit/PR SHAs
- CI
- integration campaign result
- live Gmail canary result
- real-data IDs/references with secrets redacted
- proof application/event references
- worker run/health report
- backup/restore drill evidence
- dashboard endpoint/view evidence
- analytics result summary
- unresolved/user-gated items


## Layer-by-layer acceptance matrix

Use:
- `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`

The matrix defines acceptance across inputs, discovery, matching, packet preparation, execution routing, lifecycle, operator experience, reliability, analytics, and auditability.

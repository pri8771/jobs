# Current State

Updated: 2026-09-20 20:47 ET

## Formal milestone direction

V1.7 -> V2.0 -> V2.3 -> V3.0

Target: advance to V2.0 engineering-ready as quickly as possible; full live V2.0 requires the defined user-interactive Gmail/live-data gates.

## V1.4

Status: IN PROGRESS — major repair complete, four bounded lead-review residuals.

Worker commit:
- 10fd61d — J14-01..J14-11 repair batch
- GitHub CI: green

Lead accepted from that batch:
- exact resume-source fail closed
- exact variant-source resolution
- packet -> ResumeVariant linkage
- removal of hard-coded runtime candidate claims
- EEO/self-ID manual behavior

Residual Lane A repair:
- R14-01 immutable/content-addressed artifact paths
- R14-02 selected variant -> correct resume-family identity
- R14-03 explicit mock/test generation cannot produce live-ready packet
- R14-04 quantitative experience/duration/count claims require exact canonical evidence

After these pass with full CI, A-V14-PACKET-SAFETY can be accepted and Lane A moves directly into V1.5 browser/application artifacts.

## V1.7

Status: IMPLEMENTATION READY IN PARALLEL.

Existing code already includes:
- RecruiterCRMService
- LifecycleEngine
- InterviewExtractor
- LifecycleAlertService
- lifecycle tests

Lane B is assigned to audit/repair rather than rebuild:
- A-V17-CRM-EVIDENCE
- A-V17-INTERVIEW-FOLLOWUP

## V2.0

Status: PROGRAM PREPARED / PARALLEL BROWNFIELD VALIDATION READY.

Existing assets include:
- dashboard/server + analytics
- health checks
- worker
- kill switch
- rate limiter
- backup/restore
- CI
- parsers/evaluation/lifecycle tests

Prepared V2.0 artifacts:
- A-V20-CONTROL-CENTER
- A-V20-RELIABILITY
- A-V20-ANALYTICS
- A-V20-LIVE-INGESTION
- A-V20-INTEGRATED-OS

Lane C is assigned to candidate provenance plus Gmail/runtime-readiness engineering, with Lane B consuming the typed Gmail readiness boundary for health/worker evidence.

Full V2.0 acceptance requires real Gmail/live-data evidence. Engineering may proceed independently around that user boundary.

## V2.3

Defined as Career Intelligence & Optimization.

Contract:
- docs/V2_3_SPEC.md

## V3.0

Defined as Autonomous Career Agent Network.

Plan:
- docs/V3_0_ARTIFACT_PLAN.md

## Team execution

- ChatGPT: lead/reviewer/integration/decomposition/future-artifact work
- Antigravity Lane A: worker/app-execution
- Antigravity Lane B: worker/recruiting-ops
- Antigravity Lane C: worker/live-data-foundations

Worker lane contract:
- coordination/TEAM_LANES.md

Current branch state at this lead check:
- Lane A branch has no lane-specific commits beyond its pre-lane base and is behind main.
- Lane B branch has no lane-specific commits beyond its pre-lane base and is behind main.
- Lane C is at current main and has not yet pushed implementation work.

## External boundaries

Still not authorized without explicit user action/approval:
- runtime Gmail OAuth
- login/MFA/CAPTCHA
- proof-job approval
- exact packet approval
- live application submission
- external messages

No fake/mock evidence may satisfy live acceptance.

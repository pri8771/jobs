# V2.0 End-to-End Acceptance Matrix

Artifact:
- A-V20-INTEGRATED-OS

Purpose:
Turn V2.0 into a measurable integrated acceptance campaign rather than a vague "everything works" milestone.

## Layer 1 — Inputs

Must prove:
- candidate profile source is real/private in live campaign,
- resume variants have immutable identities/hashes,
- Gmail runtime readiness is secret-safe,
- public job sources preserve provider IDs/URLs/fetch evidence,
- duplicate/replay inputs are idempotent.

Engineering fixture:
synthetic/sanitized input allowed.

Live proof:
real authorized input required.

## Layer 2 — Discovery/normalization

Checks:
- provider alert parsed,
- canonical company/title/location/source,
- normalized/canonical job URL,
- cross-source duplicate collapse,
- already-applied detection,
- source evidence retained,
- partial fetch cannot silently advance checkpoint.

## Layer 3 — Matching

Checks:
- hard filters are deterministic,
- score dimensions are inspectable,
- salary/location/seniority uncertainty is explicit,
- semantic model cannot invent candidate facts,
- borderline cases enter review,
- source quality is measurable.

## Layer 4 — Packet preparation

Checks:
- exact candidate/profile version,
- exact resume family/variant,
- immutable artifact bytes,
- truthful tailoring,
- quantitative claims require evidence,
- unknown answers unresolved,
- packet manifest/hash/provenance intact.

## Layer 5 — Execution routing

Checks:
- discovery source != application destination,
- LinkedIn/Indeed submission manual-only,
- destination policy current,
- MANUAL_ONLY/ASSISTED/AUTO_ALLOWED/BLOCKED stored,
- application attempt idempotent,
- external confirmation truth enforced.

## Layer 6 — Lifecycle

Checks:
- application event timeline,
- recruiter/contact/thread linkage,
- interviews/rejections/offers,
- follow-up/stale logic,
- duplicate/out-of-order messages safe,
- manual correction/merge auditable.

## Layer 7 — Operator experience

Dashboard/control center should surface:
- new jobs/review queue,
- shortlist rationale,
- packet/application state,
- communication timeline,
- interviews/follow-ups,
- offers/rejections,
- audit trail,
- Gmail/worker/policy/kill-switch health,
- safe non-secret configuration.

Normal daily operation should not require shell access for routine decisions.

## Layer 8 — Reliability

Checks:
- migrations upgrade/downgrade,
- worker run durability,
- crash recovery,
- backup + restore drill,
- parser regression corpus,
- provider/model failure behavior,
- policy expiry,
- recovery runbooks.

## Layer 9 — Analytics

Checks:
- source funnel,
- role-family funnel,
- exact resume variant attribution,
- company outcomes,
- time-to-stage,
- response/interview/offer rates,
- sample size displayed,
- descriptive-vs-causal guardrail.

## Layer 10 — Auditability

For a selected application, reviewer can trace:
source → JobModel → score/reasons → packet → resume/artifacts → execution policy → attempt/confirmation → recruiter/interview/outcome → dashboard/analytics.

## Campaign outputs

### Engineering campaign report
Machine-readable:
- run ID
- code SHA
- fixture version
- component checks
- entity IDs
- hashes
- idempotency assertions
- failures/warnings
- final ENGINEERING_READY eligibility

### Live campaign report
Machine-readable/redacted:
- run ID
- code SHA
- live source evidence refs
- candidate/resume fingerprints
- real opportunity reference
- application/lifecycle refs
- worker/health state
- dashboard checks
- analytics summary
- unresolved user gates
- final LIVE_ACCEPTED eligibility

## Stop conditions

Any of these blocks V2.0 live acceptance:
- fixture/mock used as live evidence,
- silent missing Gmail message,
- fabricated candidate answer,
- unconfirmed submission labeled submitted,
- duplicate consequential action,
- unreconstructable application timeline,
- dashboard displays stale/misleading state as current,
- backup/restore cannot recover critical state.

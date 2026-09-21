# Lane B Re-Review — V1.7 / V2.0 Repairs

Lead review of:
- `33d18b4` — bounded repairs B-R17-01..B-R20-06

## Overall

The repair batch closes most of the previously identified defects and should be kept.

**V1.7 repair slices B-R17-01 and B-R17-02 are lead-accepted.**

For V2.0, B-R20-03, B-R20-04 and B-R20-06 are lead-accepted. The source/role/resume historical analytics implementation under B-R20-01/B-R20-02 is materially improved, but the top-level funnel summary still uses current `ApplicationModel.status` counts and therefore retains the same historical/submission-denominator defect. One bounded residual is required before A-V20-ANALYTICS / control-center analytics can be accepted.

The branch was three commits ahead and eighteen commits behind `main` at re-review time. Worker reported 126 local tests plus clean Ruff/mypy; the repair commit itself has no GitHub status/check result, so final integration needs rebase + green integrated CI.

## Lead-accepted repair slices

### B-R17-01 SP2 — ACCEPTED

`EmailClassifier` now has deterministic paths for:
- BACKGROUND_CHECK
- ONBOARDING
- WITHDRAWAL
- RECRUITER_FOLLOW_UP

Fallback remains UNKNOWN_REVIEW_REQUIRED. End-to-end tests exercise classifier output into lifecycle handling.

### B-R17-02 SP2 — ACCEPTED

Generic rejection while the application is OFFER_ACCEPTED or ONBOARDING now preserves state and creates a NEEDS_REVIEW contradiction task. Ordinary rejection from INTERVIEWING still transitions to REJECTED.

### B-R20-03 SP1 — ACCEPTED

Removed the unjustified `Statistically robust` label. Analytics now expose descriptive N/sample-size language.

### B-R20-04 SP2 — ACCEPTED FOR PRE-J20G-04 STATE

False Gmail credential heuristics were removed. Without Lane C readiness evidence, Gmail health defaults to DEGRADED / NOT_INTEGRATED.

This does **not** accept J20G-04. Final typed Lane C -> Lane B readiness integration remains future work.

### B-R20-06 SP2 — ACCEPTED

Dashboard state-changing POST operations are restricted to loopback when no token is configured, or require the configured operator token for non-loopback access. Tests cover unauthorized and authorized paths.

## B-R20-07 — Top-level funnel still uses current status and row semantics (SP2)

Residual of:
- B-R20-01
- B-R20-02

`FunnelAnalyticsService.get_source_performance()`, `get_role_family_performance()` and `get_resume_performance()` now use the new historical-outcome/submission helpers.

However `get_funnel_summary()` still derives:
- total_submitted,
- total_screening,
- total_interviewing,
- total_offers

from grouped **current application status**.

Consequences:
- interviewed-then-rejected disappears from the summary interview stage,
- screened-then-withdrawn disappears from the summary screening stage,
- a simulation/non-confirmed application can count as submitted based on status alone,
- the control-center headline funnel can disagree with the repaired source/role/resume analytics.

Required:
1. use the same real-submission semantics as `_is_real_submission()` for the top-level submitted denominator,
2. compute cumulative/ever-reached screen/interview/offer stages from `_get_application_historical_outcomes()` for real submissions,
3. keep `status_breakdown` as the current-state view, clearly separate from historical funnel counts,
4. include rejected/current-state data without erasing earlier reached stages,
5. add regression tests for:
   - interview -> rejection still counts submitted + screened + interviewed,
   - offer -> withdrawal/decline still counts offered,
   - simulation status SUBMITTED/INTERVIEWING does not enter real funnel denominator,
   - top-level funnel counts agree with the historical semantics used in dimensional analytics.

No schema change is needed.

## Still not accepted / deferred

### A-V20-WORKER-RUN-HISTORY / B-R20-05

Still not accepted. Existing `worker_sweep` telemetry is end-of-sweep and not crash durable. Keep the dedicated worker-run-history contract and repair guide as authoritative future work.

### J20G-04

Still waits for Lane C J20G-03 typed secret-free readiness interface.

## Verification required after B-R20-07

- rebase on current main,
- targeted funnel-history tests,
- full pytest,
- Ruff,
- mypy,
- green integrated GitHub CI,
- return for lead review.

## Lead status

- V1.7 repair tasks: **accepted**.
- V2 repair batch: **mostly accepted with one bounded analytics residual B-R20-07**.
- No V2.0 milestone acceptance yet.

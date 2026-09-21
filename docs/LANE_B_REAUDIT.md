# Lane B Re-Audit — V1.7 / V2.0

Lead re-audit of:
- 21f2be9 — V1.7 recruiting operations
- bd98cf5 — V2.0 control-center/reliability/analytics batch

## Overall

The V1.7 implementation is substantial and directionally correct, but not fully accepted yet.
The V2.0 batch also contains useful work, but several claims are semantically overstated.

Keep the code; repair the bounded gaps below.

## V1.7 accepted/strong areas

- lifecycle source-reference idempotency for already-recorded events
- no fabricated interview datetime when no explicit schedule is present
- timezone-aware explicit interview parsing
- reschedule/cancel support
- recruiter/contact multi-application queries
- manual relink/unlink/merge support with audits
- unanswered recruiter dedupe/auto-resolution tests
- regression prevention for ordinary lower-stage messages

## B-R17-01 — Classifier coverage does not match lifecycle engine (SP2)

LifecycleEngine supports:
- RECRUITER_FOLLOW_UP
- BACKGROUND_CHECK
- ONBOARDING
- WITHDRAWAL

EmailClassification enum also contains them.

Current EmailClassifier does not emit BACKGROUND_CHECK, ONBOARDING, or WITHDRAWAL, and has no clear RECRUITER_FOLLOW_UP classifier path.

Required:
- add conservative deterministic patterns,
- ambiguous cases -> UNKNOWN_REVIEW_REQUIRED,
- tests prove classifier -> lifecycle path end to end.

## B-R17-02 — Protect accepted/onboarding state from generic rejection (SP2)

Current rejection handling is special-cased before stage ranking and can transition OFFER_ACCEPTED or ONBOARDING to REJECTED.

Required:
- generic REJECTION after OFFER_ACCEPTED/ONBOARDING must not silently regress state,
- route contradictory post-acceptance evidence to review unless an explicit rescind/withdrawal event is modeled,
- add adversarial out-of-order/contradictory tests.

## B-R20-01 — Funnel/history analytics must use event history, not only current status (SP3)

Current source/role/resume analytics infer screens/interviews/offers mostly from ApplicationModel.status.

That loses historical stages:
- application interviewed then rejected -> current status REJECTED -> interview disappears,
- application screened then withdrawn -> screen disappears.

Required:
- derive "ever reached stage" from ApplicationEvent history where available,
- current status remains useful for current pipeline state,
- response/screen/interview/final/offer/acceptance metrics should be historical outcomes,
- tests include interview-then-rejected and offer-then-declined.

## B-R20-02 — Fix submitted denominator semantics (SP2)

Current get_source_performance labels count(ApplicationModel.id) as applications_submitted.

Application records can exist before confirmed submission.

Required:
- submitted count based on applied_at / confirmed submission semantics, not mere row existence,
- simulation must not count as real submitted,
- source attribution must document behavior for jobs with multiple discovery sources.

## B-R20-03 — Remove statistical overclaim (SP1)

Current resume analytics label N >= 5 as "Statistically robust".

That is not justified.

Required:
- always describe observational conversion as descriptive,
- expose N,
- use neutral sample-size warnings,
- no "statistically robust" unless an actual statistical design supports it.

## B-R20-04 — Gmail health implementation is false readiness (SP2)

Current HealthCheckService checks:
- GMAIL_CREDENTIALS_JSON
- credentials.json

But production GmailOAuthClient actually uses:
- GMAIL_CLIENT_ID
- GMAIL_CLIENT_SECRET
- gmail_token_path / token file

Current health can therefore report HEALTHY without proving the runtime adapter can authenticate.

Required:
- remove false credential inference now,
- default Gmail health to DEGRADED/NOT_INTEGRATED until Lane C J20G-03 typed readiness service is available,
- final J20G-04 integration occurs after Lane C contract lands.

Do not independently reimplement Gmail diagnostics in Lane B.

## B-R20-05 — Worker-run history is not crash durable (SP3)

Current worker_sweep AuditLog row is written only at the end of the same sweep transaction.

It does not satisfy A-V20-WORKER-RUN-HISTORY:
- no RUNNING record before work,
- kill switch returns without run record,
- process crash may leave no durable evidence,
- cannot detect stale RUNNING runs,
- no separate last-success / last-error durable lifecycle.

Required:
- do not claim J20-14 accepted yet,
- final implementation should follow docs/V2_0_WORKER_RUN_HISTORY_CONTRACT.md,
- use separate durable begin/finalize persistence,
- may wait for lead clearance on DB model/migration approach.

## B-R20-06 — Dashboard write safety (SP2)

Dashboard POST /api/reviews/{id}/resolve mutates state with no authentication.

Default localhost binding is useful, but V2 contract says destructive remote controls must not become casually exposed.

Required one of:
- enforce loopback-only write operations, even if read dashboard is rebound,
- or require an explicit operator write token/config gate.

Tests should prove non-loopback/unauthorized write fails.

## Not a blocker / keep

- adapter health live-vs-simulation distinction is useful
- backup/restore fail-closed checksum work is useful
- DB password fail-closed behavior is useful
- added read-only dashboard endpoints are useful
- time-to-stage event-history implementation is useful, subject to integration testing

## Next

Lane B owns B-R17-01, B-R17-02, B-R20-01, B-R20-02, B-R20-03, B-R20-04, B-R20-06.

B-R20-05 may be left for later dedicated worker-run implementation if shared schema changes would conflict.

After repairs:
- full pytest
- ruff
- mypy
- push
- READY FOR LEAD RE-REVIEW

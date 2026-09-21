# V2.0 Integration Acceptance Fixture

Artifact: A-V20-INTEGRATION-FIXTURE

## Purpose

Provide one deterministic engineering scenario that proves the major V2.0 subsystems work together before the real Gmail/live-data acceptance overlay.

This fixture is explicitly TEST evidence. It never counts as live Gmail or a real submitted application.

## Golden engineering scenario

Use synthetic but internally consistent evidence:

1. JOB_ALERT message arrives with provider message/thread ID.
2. parser creates/links one normalized job.
3. duplicate replay does not create a second job.
4. evaluator shortlists the job.
5. packet builder selects an explicit resume family/source.
6. packet artifacts are immutable/hash verified.
7. screening answer provenance is recorded; unknown/EEO remain unresolved.
8. application record is created in non-live/manual-or-assisted test mode.
9. APPLICATION_CONFIRMATION message links to that application.
10. recruiter outreach arrives from one contact.
11. screening/interview message arrives with an explicit timestamp/link.
12. duplicate message replay creates no duplicate lifecycle event/interview.
13. candidate outbound reply closes/suppresses unanswered-recruiter task.
14. rejection OR offer evidence updates the application without state regression.
15. dashboard APIs show:
    - job
    - application
    - contact
    - interview
    - review/follow-up state
    - audit trail
16. analytics counts the funnel + correct resume variant.
17. health reports latest worker run and policy/kill-switch state.

## Trace identity

Every fixture run should have a trace/test-run ID.

Evidence should allow reconstruction:
source message -> job -> packet -> application -> contact/interview -> outcome.

## Live acceptance overlay

Full A-V20-INTEGRATED-OS acceptance replaces the synthetic ingestion entry with:
- real Gmail OAuth
- real provider IDs
- bounded live canary

and, when applicable, real external application evidence.

The synthetic fixture remains a regression suite, not live proof.

## Acceptance output

Produce a machine-readable integration report containing:
- trace ID
- fixture version
- entities created
- source references
- dedupe/idempotency assertions
- packet/resume hashes
- lifecycle events
- dashboard checks
- analytics checks
- health checks
- test result
- code SHA

## Worker tasks

Suggested after V1.7 + core V2 repairs:
- J20-12 SP3 — implement golden integration fixture.
- J20-13 SP2 — emit machine-readable integration report.
- J20-14 SP2 — add duplicate/out-of-order replay cases.

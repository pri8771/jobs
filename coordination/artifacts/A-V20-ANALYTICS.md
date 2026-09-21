# A-V20-ANALYTICS

- Type: analytics
- Phase: V2.0
- Status: READY
- Owner: Antigravity Lane B
- Reviewer: ChatGPT
- Dependencies: immutable resume attribution already implemented
- Downstream: A-V20-INTEGRATED-OS, V2.3

## Purpose

Make the job-search funnel measurable by source, role, resume, and outcome.

## Acceptance criteria

- source performance
- role/title-family performance
- resume family + exact version performance
- response/screen/interview/final/offer/acceptance rates
- time-to-stage
- sample-size warnings
- correlations labeled descriptive unless stronger evidence exists
- deterministic query/service tests

## Worker tasks

- J20-09 SP2 — audit current analytics vs required dimensions
- J20-10 SP3 — implement resume/source/role outcome aggregation
- J20-11 SP2 — add time-to-stage + sample-size warning logic

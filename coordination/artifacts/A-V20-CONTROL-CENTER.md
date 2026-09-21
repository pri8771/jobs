# A-V20-CONTROL-CENTER

- Type: implementation / operator UX
- Phase: V2.0
- Status: READY
- Owner: Antigravity Lane B
- Reviewer: ChatGPT
- Dependencies: none for audit/repair
- Downstream: A-V20-INTEGRATED-OS

## Purpose

Validate and repair the existing dashboard into the daily operator control center required by V2.0.

## Existing assets

- dashboard/server.py
- dashboard/analytics.py
- tests/test_dashboard.py
- health service

## Acceptance criteria

Dashboard/API exposes:
- new jobs / shortlist / review queue
- application pipeline
- recruiter communication timeline
- interviews
- follow-ups
- offers/rejections
- audit trail
- Gmail/source/worker health
- policy + kill switch
- safe read-only config/status views

No unauthenticated destructive remote controls.

## Worker tasks

- J20-01 SP2 — inventory current endpoints/views vs acceptance list
- J20-02 SP3 — fill highest-value missing operator views
- J20-03 SP2 — expose source/worker/policy health safely
- J20-04 SP2 — dashboard regression tests for operator flows

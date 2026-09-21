# A-V17-INTERVIEW-FOLLOWUP

- Type: implementation / evidence
- Phase: V1.7
- Status: READY
- Owner: Antigravity Lane B
- Reviewer: ChatGPT
- Dependencies: none for code audit/repair
- Downstream: A-V17-MILESTONE-GATE, A-V20-INTEGRATED-OS

## Purpose

Operate the post-application recruiting lifecycle with evidence-backed interview extraction and follow-up work.

## Existing assets

- lifecycle/interview.py
- lifecycle/alerts.py
- lifecycle/engine.py
- worker lifecycle sweep
- tests/test_lifecycle.py

## Acceptance criteria

- interview request/confirmation extraction preserves source message evidence
- round/time/timezone/link are stored with ambiguity handling
- unanswered recruiter outreach creates deduplicated follow-up tasks
- stale application detection is deterministic and non-spammy
- rejection/offer/background/onboarding classifications map to safe lifecycle events
- thank-you/follow-up drafting inputs are prepared but external send remains user-governed
- repeated sweeps are idempotent
- tests cover timezone ambiguity, reschedule/cancel, duplicate message, stale/replied thread, offer/rejection transitions
- CI green

## Worker tasks

- J17-05 SP2 — audit interview extractor + alerts against edge cases
- J17-06 SP3 — repair reschedule/cancel/timezone/idempotency gaps
- J17-07 SP2 — harden follow-up dedupe and answered-thread detection
- J17-08 SP2 — add lifecycle classes for offer/rejection/background/onboarding gaps

# A-V16-FIRST-REAL-SUBMISSION

- Type: live evidence
- Phase: V1.6
- Status: PROPOSED
- Owner: Antigravity + User
- Reviewer: ChatGPT
- Dependencies: A-V15-ASSISTED-APPLICATION ACCEPTED, A-PROOF-JOB-SELECTION accepted, explicit user authorization
- Downstream: post-proof strategy review

## Purpose

Demonstrate one genuine system-submitted application for a job the user actually wants, with real external confirmation.

## Acceptance criteria

- exact job explicitly approved by user
- exact packet explicitly approved by user
- current destination policy permits the chosen method
- idempotency/duplicate check passes
- unresolved questions = none or explicitly resolved by user
- real external submit action occurs
- external confirmation is captured
- APPLICATION_SUBMITTED is recorded only after confirmation
- audit log records exact packet, method, actor, policy, external reference
- no CAPTCHA bypass/stealth/policy evasion

## Evidence required

- user authorization record
- preflight manifest
- idempotency evidence
- submit attempt audit
- external confirmation page/reference/email/account state
- final application event
- exact resume/packet hashes

## Non-goal

Do not use a random low-value job merely because it is easy to automate.

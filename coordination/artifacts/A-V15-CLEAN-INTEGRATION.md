# A-V15-CLEAN-INTEGRATION

- Type: integration / assisted-application safety
- Phase: V1.5
- Status: BLOCKED
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V14-REAL-PROOF ACCEPTED
- Downstream: A-V15-BROWSER-SAFETY-CONTRACT, A-V15-ASSISTED-APPLICATION, A-V15-LIVE-ASSISTED-PROOF

## Purpose
Port already-developed assisted-application safety code from old PR #2 onto a clean branch based on accepted current main.

## Source commits to inspect
- `44f5fd9...`
- `3ef4002...`
- `09f1852...`

## Tasks
R15-I01..R15-I07 from the recovery plan, each SP1.

## Acceptance
Current-main small PR with targeted/full checks and no historical heartbeat churn.

## Worker report — Fable, 2026-09-22 (state: READY_FOR_LEAD_REVIEW, not accepted)

F145-07: the V1.5 browser code and adversarial tests from `worker/v15-assisted-application`
`ddb4f84` were ported onto the single-worker branch `claude/serene-brown-g6uij0` without
heartbeat/coordination churn. F145-08..11 (FR15-01..03 repairs, real local Playwright
engineering-form tests, installed entrypoint test) are summarised in the addendum of
`docs/V1_5_BROWSER_SAFETY_CONTRACT.md`. Exact SHA and independent check results are in the
handoff and heartbeat. G15 (live visible prefill) remains blocked on this host: no accepted
real packet, no owner browser grant, no owner machine.

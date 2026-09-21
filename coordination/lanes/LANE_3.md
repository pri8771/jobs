# Lane 3 — V1.7 / V2.0 Recruiting & Reliability

Branch:
- `worker/recruiting-ops`

Owner:
- active Lane 3 worker

Reviewer:
- ChatGPT lead

## Lead acceptance — 2026-09-21 16:51Z

PR #3 was reviewed on actual source/tests/current-head CI and merged to main as `be765ea42856bc695fc1eece9c1da396b4f162d4`.

Newly lead-accepted at task scope and integrated:
- B-R20-05 / J20-14 — crash-durable worker begin/finalize, fail-closed begin persistence, sanitized bounded errors, true latest-attempt health, reconciliation/error fields, rollback/run-id/privacy tests,
- B-R20-01 — headline funnel preserves historical stage achievements from event history,
- B-R20-02 — headline funnel uses real-submission denominator semantics.

Previously accepted and preserved:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- earlier accepted Lane 3 residual tasks recorded in `WORKER_PERFORMANCE.md`.

Current-head branch CI was green before integration. Main CI after the merge/lead coordination updates is the next integration gate.

## Heartbeat

Canonical owner directive:
`python scripts/worker_heartbeat_watch.py --lane 3 --epoch FIVE_MIN_2026_09_21 --task "V1.7/V2.0 post-integration verification" --detach`

Exactly one watcher. Fixed 5-minute cadence while active. No transitions.

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.

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

## Heartbeat truth

Authoritative epoch is `DAYWATCH_2026_09_21`.

The worker heartbeat metadata self-reported a proving streak that does not match actual timestamps: 16:18Z → 16:34Z → 16:44Z are not 4–7 minute proving gaps. Those timestamps do not establish 3/3.

If a `FIVE_MIN_2026_09_21` watcher is running, stop it. Pull latest main and run only the DAYWATCH watcher. The next worker check-in starts/restarts the proving sequence according to actual timestamps.

## Next bounded assignment — post-integration verification only

1. Pull/rebase `worker/recruiting-ops` onto latest `main` after PR #3 merge.
2. Confirm the merged source for the accepted Lane 3 files matches the reviewed implementation.
3. Run the targeted worker/health/dashboard tests plus full pytest/Ruff/mypy against the integrated baseline.
4. If a regression exists, push only the minimal regression repair and request lead review.
5. If integration is green with no regression, record `BLOCKED` / `NONE` with progress note `waiting for J20G-04 dependency` and stop implementation work.

Do not invent new work merely to keep the lane busy. `J20G-04` remains blocked until Lane 1 later produces the authorized Gmail-readiness dependency. Do not access Gmail/OAuth while blocked.

## Heartbeat

Launch only if no correct watcher is already running:
`python scripts/worker_heartbeat_watch.py --lane 3 --epoch DAYWATCH_2026_09_21 --task "V1.7/V2.0 post-integration verification" --detach`

Cadence: 3 proving heartbeats at 4–7 minute gaps → 15-minute watch for a clean 24 hours → hourly.

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.

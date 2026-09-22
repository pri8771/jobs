# Codex independent review preparation — Jobs

Reviewer: Codex portfolio coordinator, with bounded mechanical checks by a lower-cost subagent. This is a recommendation, not ChatGPT acceptance. Minimum owner target: live Jobs V1.7; native ceiling V1.7, then stop.

## Source, ownership and submission

- Canonical contract/queue: `main@1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`, `AGENTS.md`, `docs/FABLE_V17_LIVE.md`, `coordination/WORK_QUEUE.md`.
- Sole implementation owner remains Fable/Claude on `claude/serene-brown-g6uij0@dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`. Reviewed new production commit: `113c584d731bee4c46e2d54d6048344991e6e16d` (V17-M01..M04 / R05 core).
- Heartbeat publication is separate: `worker/v14-real-proof`, LANE_1 #45 at `2026-09-22T02:21:13Z` explicitly requests READY_FOR_LEAD_REVIEW of this batch and reports continued V1.6 work. The 5-minute cadence and material commit are observed; the remote process and dirty work are not locally inspectable.
- Origins verified, isolated review and coordination worktrees clean before edits. Existing Jobs Lead Sync owns canonical decisions. This docs-only proposal changes no worker branch, queue state, watcher or application code. Original no-checkout clones are object stores, not dirty implementation worktrees.

## Existing accepted position

`coordination/reviews/V17_LEAD_REVIEW_20260922.md` formally accepts P0A source `8491dd98154ff750f49cbb64d2a79eca5cb06069` and V1.5 source `47fefd1b0ca354360353577685f6619a94f00f42`; integration is `7c0fa73bf350392a88b47442455359a43cf926b0`. Preserve those decisions. G14–G17 remain UNPASSED. `coordination/proofs/` has no accepted genuine runtime bundle. The last worker-host inventory lacks approved genuine profile/resume/job inputs and eligible source connectivity.

## Independent engineering checks

Exact tested checkout: `dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`, macOS, Python 3.13.12, isolated environment and synthetic SQLite fixtures. Transcript and executable reproducer: `coordination/codex/evidence/20260922/jobs-checks.txt` and `jobs-bounded-repro.py`.

- New ingestion/readiness tests: **34 passed**; affected legacy tests: **50 passed**.
- Ruff, mypy (74 source files), and diff whitespace check: exit 0.
- Full suite, genuine inputs, mailbox/OAuth, browser/submission and live G14–G17: not run. Worker claim of 429 tests is not this independent run.
- Hosted run `35677070255` on `47fefd1b...`: failure with runner_id=0 and zero steps. This is no executable CI evidence; no run on the new submission was returned by the branch query.

## Findings and recommendation

**REWORK_FOUND** for the new bounded ingestion batch.

1. **Bounded lifecycle work escapes the admitted evidence set.** `src/jobs_automation/ingestion/bounded.py:299` selects every persisted non-JOB_ALERT message, and global alert sweeps follow. Reproducer seeds a linked 2019 rejection, then runs an empty bounded 2026 request. Observed: zero messages polled, run SUCCESS, one lifecycle transition, unrelated application changed to REJECTED, one old-message event. A bounded query/window/cap must also constrain downstream lifecycle work; existing stored evidence is not automatically part of this run's grant.
2. **Replay mismatch still reports SUCCESS.** The runner assigns status before comparing original digests (`bounded.py:321–343`); `cli/main.py:1327–1342` prints false replay flags but only fails on FAILED/INCOMPLETE. A drifted replay produced `status=SUCCESS`, `replay_identical=True`, `replay_matches_original=False`. Require a failing proof/exit state on missing or mismatched replay evidence, or a separately enforced verifier result; a successful command cannot imply G17 replay passed. No rejecting proof consumer was found in the inspected source.

Positive fixture ingestion, restart/replay and existing negatives pass; they do not cover these adverse cases or constitute genuine recruiting evidence.

## Small next assignment — existing V17-M04/R05 repair

Dispatch state: **PREPARED / WAITING_FOR_WORKER_ACK**. Owner remains the same Fable session; coordinate at its next safe boundary, preserving ongoing V1.6 work. ChatGPT must issue the formal verdict/priority; do not reset or overwrite the worker.

- SP2: bind the bounded run to admitted provider message IDs and affected entities; process only that set. Scope alert work accordingly or explicitly separate it from the bounded proof. Files: `ingestion/bounded.py`, minimal engine result-contract changes if necessary, focused tests. Preserve real importer/lifecycle services and checkpoint behavior.
- SP1: fail closed for missing/mismatched original replay evidence at runner/CLI proof boundary. Reuse the existing replay fields; no new proof framework.
- Required positives: authorized bounded batch transitions the intended application; exact restart/replay preserves its logical state. Negatives: empty batch cannot mutate unrelated historical applications/events/tasks; cap/incomplete pages cannot include unadmitted evidence; mismatch/missing original produces non-success and nonzero CLI proof exit.
- Return exact tested source SHA, sanitized command/exits, focused/full checks and PostgreSQL production-dialect evidence as applicable. Preserve G14–G17 and every private/mailbox/action grant. No live mailbox access is authorized by this assignment.

Requested authorized verdict: ChatGPT review both findings, record REWORK or evidence-based rebuttal in the native review/queue, and obtain a worker acknowledgement before reporting this repair running.

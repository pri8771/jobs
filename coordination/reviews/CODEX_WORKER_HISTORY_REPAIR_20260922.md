# Jobs /api/worker durable history repair — engineering review

## Recommendation

**RECOMMEND_ACCEPT** for the bounded worker-history read-surface repair only. Formal lead verdict is requested. This does not close broader J20-01 inventory or G14-G17 live gates.

## Exact candidate

- Base: `832d85f5177ca82564c9d0b6c168790f26ea1dc3`
- Candidate: `b462e17b48c286dc4bdee5b958217b42da8e701e`
- Tree: `f0694f58e4feef9846c21a608dc7bbdeca4be39d`
- Production scope: `src/jobs_automation/dashboard/server.py`, 13 additions / 4 deletions.
- `health.py` and `worker.py` are unchanged from the accepted base. Git was clean before and after final PostgreSQL proof.

## Contract review

The endpoint selects exactly `worker_run`, `worker_run_finished`, and legacy `worker_sweep`; maps them to `run_begin`, `run_finished`, and `legacy_sweep`; preserves `id`, `result`, `occurred_at`, and stored `metrics`; derives `run_id` only from persisted external reference or stored metadata; orders by timestamp then id descending; and applies one combined limit of 20. It keeps begin/finish separate and does not modify health interpretation or worker persistence. No concrete contract defect was found.

The four focused test methods materially cover actual daemon success, current RUNNING/PARTIAL/FAILED shapes and run-id precedence/fallback, combined current/legacy limit plus deterministic tied timestamps, metadata preservation, health parity around the successful daemon run, and empty HTTP 200. The actual PostgreSQL harness adds genuine daemon SUCCESS, bounded synthetic-adapter PARTIAL, fail-closed begin-write FAILED with a durable real-PG finalize, legacy null run-id, and fresh/stale RUNNING parity. Seeded cases are explicitly labelled; no provider or mailbox is used.

## Results

Baseline new tests were red as expected: 3 failed / 1 passed. Candidate tests passed 4/4; existing focused tests passed 37/37. The final exact-worktree suite passed 467 with 1 existing host skip; Ruff passed source and tests; mypy passed 74 source files.

The first full run had one restart test failure after its venv child imported `jobs-source` rather than this worktree. `jobs-worker-history-import-diagnosis.log` records both resolved module paths. With exact worktree `PYTHONPATH`, that restart check passed 1/1 and the superseding full run passed at the same candidate SHA. No source change or test weakening was involved.

Final PostgreSQL proof created and migrated unique database `jobs_worker_history_af2b4660882c`, ran all cases successfully, dropped it, and read back cleanup count zero. Pre-commit evidence is retained separately and is not used as exact-head proof.

Release: ChatGPT lead `9a31171859a12e32e8d460116f78157affebf35f`. Draft [PR22](https://github.com/pri8771/jobs/pull/22). Root authored the source patch; bounded agents supplied the disjoint regression module, PostgreSQL verification and mechanical source review. ChatGPT remains the formal acceptor. No real mailbox/provider/application action, new scheduler, Fable handoff, main merge or deployment.

Native [checks](../codex/evidence/CODEX-WORKER-HISTORY-REPAIR-20260922/checks.json), [manifest](../codex/evidence/CODEX-WORKER-HISTORY-REPAIR-20260922/manifest.json), [commands](../codex/evidence/CODEX-WORKER-HISTORY-REPAIR-20260922/commands.txt).

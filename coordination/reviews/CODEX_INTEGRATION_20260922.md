# Accepted Jobs stack — isolated integration validation

**READY_FOR_LEAD_REVIEW / RECOMMEND_ACCEPT** for this composition only; ChatGPT formal exact-tip verdict required. Source **e1dbfeb6d4ddac9c49a5ac2b3d8d0a5c6ebc8273**, tree **e5409f04e15ca7d21dd2357c000c03e5c53ebd09**, branch codex/jobs-accepted-integration-20260922. [Draft PR20](https://github.com/pri8771/jobs/pull/20), based on main only to expose existing CI trigger; no main merge or deployment. Native release081325b.

Created clean worktree from accepted10a3a23924fdde6b040082ef030ad1286591b9a9. Fast-forward cherry-picks preserve original8631b3e→7345f1e→9e29a59→ed864cb commits; both Gmail commits are necessary to retain the complete accepted7345 change. Accepted backupd98b1ea cherry-picked with source attribution as e1dbfeb. Zero conflicts/new features/opportunistic changes. All363 tracked paths exactly match accepteded864cb except the3 accepted backup paths overlaid fromd98b1ea; resulting tree equals the earlier non-mutating composition preflight.

- Full **451 passed / 1 existing host skip**; Ruff, mypy74, shell syntax and diff checks pass.
- Actual disposable PostgreSQL Gmail path: missing listed fetch and cap truncation each abort with zero partial rows/checkpoint; complete retry ingests five messages once; prior nested message/task/checkpoint state preserved.
- ActualPG health: begin failure one durable FAILED fallback, double failure explicit undurable/no pipeline; new process reads latest failure/prior success. All four error handlers suppress injected markers. PARTIAL, incomplete polling, seeded fresh/stale RUNNING and simulation-only adapter health checks pass.
- ActualPG recovery: backup/checksum pair moved and restored from thirdCWD with exact rows; corrupt/malformed/multi-record sidecars fail before mutation; malformed SQL exits3/rolls back/no false success; existing migration verifier upgrade→downgrade→re-upgrade succeeds, exact Alembic head/20tables.
- All harnesses use separate unique synthetic databases; every cleanup count0, final owned-prefix queries empty. No source modifications by mechanical agents. [Checks](../codex/evidence/CODEX-INTEGRATION-20260922/checks.json), [hash manifest and retained harnesses/logs](../codex/evidence/CODEX-INTEGRATION-20260922/manifest.json).

Hosted exact-head PR20 run35694192325/job106637356958 reports failure before execution, runner_id0/empty steps. This distinguishes account/runner start failure from code tests; it is not hosted-green. No rerun, workflow/billing change or new spend. [Readback](../codex/evidence/CODEX-INTEGRATION-20260922/jobs-integration-hosted-ci.json).

Engineering recommendation covers composition evidence only. Full A-V20-RELIABILITY, hosted CI, genuine G14–G17 and V2.0 acceptance remain open. No Fable handoff, real mailbox/model/provider/application action, public deployment, main merge or scheduler change. Request exact source/tree lead verdict plus smallest next dependency-safe native task.

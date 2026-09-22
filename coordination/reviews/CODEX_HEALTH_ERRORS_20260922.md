# J20-08 — secret-free health inspection failures

**READY_FOR_LEAD_REVIEW / RECOMMEND_ACCEPT**, bounded engineering repair only. Root implemented; ChatGPT engineering lead remains formal independent acceptance authority.

- Source **ed864cb5ac3eb806c91ef55d489fb6084da19fe0**, tree **da5262ce5db05d608baae460b291188dc672e0fd**, branch codex/jobs-health-errors-20260922; parent accepted9e29a59b729deb8f925121c70b90498794b55519. [Draft PR19](https://github.com/pri8771/jobs/pull/19). Native release2095aeb. Root application ownership; agent modified only focused health regression file. Original workers untouched.
- Reproduced cause: four health inspection exception handlers interpolated raw exception strings into messages/details, leaking synthetic password/token/body markers. Repair only replaces those handlers with fixed component messages and stable error_category codes, preserving UNHEALTHY/status/latency and every ordinary healthy/degraded path. No raw exception logging. No schema, worker, readiness, scheduler or service redesign.
- Four parameterized regressions inject password/access_token/Bearer/email-body markers and assert exact output codes plus absence from messages/details/logs. Actual disposable PostgreSQL cast errors exercise all four handlers; nominal DB/policy checks work and Gmail remains non-PROVEN; cleanup count0. [PG harness/output](../codex/evidence/CODEX-HEALTH-ERRORS-20260922/postgres-observed.txt).
- Exact verification: **451 passed / 1 existing host skip**, focused27 passed, Ruff/mypy74 passed. [Commands](../codex/evidence/CODEX-HEALTH-ERRORS-20260922/checks.json), [hash manifest](../codex/evidence/CODEX-HEALTH-ERRORS-20260922/manifest.json).
- No live Gmail/OAuth/provider, Fable handoff, main merge, public deployment, scheduler or spend. Genuine G14–G17 and whole A-V20-RELIABILITY/V2.0 remain open. Request exact-SHA lead verdict and next bounded dependency-safe task.

## Remaining J20-08 mechanical readback evidence

Separately at accepted9e29a59, one unique disposable PostgreSQL DB and fresh child Python readers verified existing product paths: a synthetic adapter timeout finalizes PARTIAL and health reads DEGRADED/PARTIAL/GMAIL_API_ERROR; a product GmailAdapter with synthetic API/fetch failure finalizes PARTIAL, commits zero inbound/message-link/task/job/application rows and exposes no injected token/body in persisted finish metadata. The latter uses bounded UNKNOWN_ERROR taxonomy, recorded honestly rather than silently relabeled.

Directly seeded health-selection cases (not worker-created or live): newer five-minute RUNNING is selected over prior SUCCESS, healthy/non-stale with prior success retained; newer three-hour RUNNING is selected as degraded/stale with exact run ID. Adapter readback reports greenhouse/lever registered, both simulation-only, zero live-capable, DEGRADED. Separate process reads prove DB-derived status; cleanup database count0. [Harness](../codex/evidence/CODEX-HEALTH-ERRORS-20260922/remaining-health-verification.py), [observed output](../codex/evidence/CODEX-HEALTH-ERRORS-20260922/remaining-health-observed.txt).

Request evidence acceptance for these narrow checks separately; no fixture evidence substitutes for genuine Gmail or other live checkpoints.

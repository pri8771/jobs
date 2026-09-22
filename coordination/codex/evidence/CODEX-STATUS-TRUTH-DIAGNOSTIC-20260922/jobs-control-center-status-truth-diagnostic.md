# Jobs A-V20-CONTROL-CENTER — status-truth diagnostic

## Identity and release

- Accepted source: `b462e17b48c286dc4bdee5b958217b42da8e701e`
- Tree: `f0694f58e4feef9846c21a608dc7bbdeca4be39d`
- Formal acceptance/release ref: `9e1723c118d521870f877df3fcee775d89b0e396`
- Contract: `coordination/artifacts/A-V20-CONTROL-CENTER.md`, especially truthful Gmail/source/worker health and safe status views.

## REWORK_FOUND

The embedded control-center header unconditionally renders the green claim **`System Live`** (`src/jobs_automation/dashboard/server.py:57,91`). Its JavaScript never fetches `/api/health`; the only health route is the independent JSON handler at `server.py:634-637`.

An exact-source disposable-PostgreSQL run called both production handlers in process. The index returned HTTP 200 with `System Live`, while `/api/health` returned HTTP 200 and truthful overall `DEGRADED`:

- database `HEALTHY`;
- kill switches `HEALTHY`;
- policy registry `HEALTHY`;
- worker `DEGRADED`;
- Gmail `DEGRADED`, readiness `NOT_CONFIGURED`;
- ATS adapters `DEGRADED`, zero live-capable adapters.

The HTML contained no health-fetch binding. Therefore the visible top-level operator status contradicts the product's own current health/readiness state and specifically presents the system as live when Gmail is unconfigured and every ATS adapter is simulation-only.

This is a UI truthfulness gap. The health service itself behaved correctly, and no provider, mailbox, application or browser action occurred.

## Evidence

Exact command, run from `/Users/pchordia/Downloads/swarm_codex`:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-control-center-status-truth-run.py
```

The wrapper asserted a clean exact SHA/tree, created a uniquely named database on the owned Jobs PostgreSQL test server, migrated to Alembic head, ran the in-process production-handler reproduction, dropped the database, and verified cleanup count zero.

- `/tmp/jobs-control-center-status-truth-repro.py` — SHA-256 `814fa7f4453561b5669352d532ea8fbc406f7fdba23d7522c5f80834d7956bd9`
- `/tmp/jobs-control-center-status-truth-run.py` — SHA-256 `2abe8b48949600593ab3eb2f1f90f42edd0ecd823f140da8d70ec871e0ed1f6d`
- `/tmp/jobs-control-center-status-truth-wrapper.log` — SHA-256 `36a8fc962fba78d11b6897ed7ef665345ad8f304f27f69f6bee21826042361c0`
- `/tmp/jobs-control-center-status-truth-root-20260922/report.json` — SHA-256 `af2f3b5da0d3182f4878edee3ebe1097504554a0f6b776d8dde0cc3062912eb9`
- `/tmp/jobs-control-center-status-truth-root-20260922/run.json` — SHA-256 `d49d40f95b8b25ddf75520fc37a6caff9f9fa45c4567a5914d95a6f9bc32c93e`

Observed exits: migration `0`, workflow `0`; result `REPRODUCED_STATIC_LIVE_BADGE_MISMATCH`; remaining database count `0`.

## Smallest repair proposal

Replace the unconditional live claim with a fail-closed status badge whose initial state is `Status unknown` or `Checking`. Bind it to `/api/health` and render only the returned `overall_status` (`HEALTHY`, `DEGRADED`, or `UNHEALTHY`) with matching accessible styling. A fetch/parse failure must remain `UNKNOWN`/unavailable and must never fall back to `Live` or `Healthy`.

Keep `/api/health` as the source of truth; do not duplicate health/readiness calculation in JavaScript or infer operational/live promotion from component registration. Add focused handler/HTML behavior checks for DEGRADED, UNHEALTHY, HEALTHY and fetch failure. No other control-center inventory item should be included in this repair.

The diagnostic stopped at this first concrete gap. No production or repository test file was edited.

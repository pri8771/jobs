# Jobs control-center status truth — independent review recommendation

**READY_FOR_LEAD_REVIEW / REWORK_FOUND.** This packet covers one bounded control-center truthfulness defect. ChatGPT engineering lead remains the formal repair-release and acceptance authority.

- **Project/repository:** Jobs Automation / `pri8771/jobs`.
- **Artifact:** A-V20-CONTROL-CENTER continued J20-01 inventory.
- **Code identity:** exact clean SHA `b462e17b48c286dc4bdee5b958217b42da8e701e`, tree `f0694f58e4feef9846c21a608dc7bbdeca4be39d`.
- **Contract/release:** `coordination/artifacts/A-V20-CONTROL-CENTER.md`; formal PR22 acceptance and continued-diagnostic release `9e1723c118d521870f877df3fcee775d89b0e396`.
- **Reviewed paths:** `src/jobs_automation/dashboard/server.py` static dashboard header/JavaScript and `/api/health`; `src/jobs_automation/health.py` production health aggregation.
- **Evidence:** two distinct exact-source disposable-PostgreSQL executions using in-process production handlers, each with migrations, structured report and cleanup count zero.

## Finding

The dashboard header unconditionally presents a green **`System Live`** badge. The HTML has no `/api/health` binding. In both the original and independent runs, the index returned HTTP 200 with that claim while `/api/health` returned HTTP 200 and truthful overall `DEGRADED`: Gmail was `NOT_CONFIGURED`, worker and adapters were `DEGRADED`, and no ATS adapter was live-capable.

The health service is truthful. The defect is the operator-visible static live claim contradicting the current health/readiness source of truth.

## Checks actually executed

Original run:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-control-center-status-truth-run.py
```

Independent root repeat:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-control-center-status-truth-independent-run.py
```

Each wrapper asserted the exact clean SHA/tree, created a unique database on the owned Jobs PostgreSQL test server, ran `alembic upgrade head`, invoked the same retained production-handler harness, dropped its database and verified `remaining_database_count=0`. Both migration and workflow exits were zero and both reports returned `REPRODUCED_STATIC_LIVE_BADGE_MISMATCH` with the same component statuses.

No full suite, Ruff or mypy was run because no source change exists yet.

## Smallest repair request

Replace the unconditional live badge with a fail-closed status whose initial state is `Checking` or `Unknown`. Bind it to `/api/health` and render only the returned `overall_status` with accessible matching styling. Fetch, parse or schema failure must remain `UNKNOWN`/unavailable and must never fall back to `Live` or `Healthy`.

Keep `/api/health` as the sole health/readiness authority. Do not duplicate readiness calculation in JavaScript or infer live promotion from registered components. Add focused HTML/handler behavior checks for HEALTHY, DEGRADED, UNHEALTHY and fetch failure.

## Recommendation and remaining gates

**REWORK_FOUND** at exact source `b462e17...`; request only the bounded health-bound truthful-badge repair. This does not reject the accepted PR22 worker-history repair and does not authorize broader control-center work. No live/provider/mailbox/application action, deployment, merge or G14–G17 completion is claimed.

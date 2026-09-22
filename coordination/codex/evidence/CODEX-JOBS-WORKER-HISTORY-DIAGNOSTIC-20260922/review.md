# Jobs control center worker history — diagnostic review

**READY_FOR_LEAD_REVIEW / REWORK_FOUND.** This is a source-bound diagnostic packet only. ChatGPT engineering lead remains the formal acceptance and repair-release authority.

- **Project/repository:** Jobs Automation / `pri8771/jobs`.
- **Artifact:** A-V20-CONTROL-CENTER, J20-01 inventory; release ref `0c89bc9aa20d55e4b759b0117502b664ab8cf18e`.
- **Reviewed source:** exact clean SHA `832d85f5177ca82564c9d0b6c168790f26ea1dc3`, tree `047eb8501e562cbbca450e946e260a1b8454f74b`.
- **Reviewed paths:** `src/jobs_automation/dashboard/server.py`, `src/jobs_automation/health.py`, `src/jobs_automation/worker.py`, worker audit persistence, and existing dashboard test patterns.
- **Evidence:** synthetic SQLite seed and an independent disposable-PostgreSQL run through an actual `WorkerDaemon` with `MockEmailAdapter([])`.

## Finding

`GET /api/worker` queries only the legacy audit action type `worker_sweep`. Current `WorkerDaemon` execution persists a `worker_run` RUNNING record and a `worker_run_finished` terminal record. `HealthCheckService` reads this current durable state, but `/api/worker` does not.

The independent PostgreSQL reproduction ran the actual daemon successfully with one run ID, persisted the expected RUNNING/SUCCESS pair, and observed worker health `HEALTHY` / latest attempt `SUCCESS` with the same run ID. In the same database, `GET /api/worker` returned HTTP 200 with `[]`. The database was dropped and cleanup count was zero.

This makes the operator history endpoint omit the authoritative current run even while the health surface accurately reports it. It is a read-surface defect; worker execution and health selection succeeded.

## Checks actually executed

The SQLite diagnostic seeded current worker audit records and observed `/api/worker=[]` while health reported the current successful run. Exact script/output: `jobs-control-center-worker-repro.py` and `.log`.

The independent PostgreSQL wrapper asserted the exact clean source/tree, created a unique disposable database, upgraded it to Alembic head, ran the production worker diagnostic, extracted structured output, dropped the database and verified zero remaining databases. Exact scripts and unmodified output are included under `root-result/`.

Observed PostgreSQL result:

- migration exit 0;
- workflow exit 0;
- actual worker errors `[]`;
- durable audit records: one `worker_run` RUNNING and one `worker_run_finished` SUCCESS sharing run ID `6dd2a42b-de34-48a0-9014-6deb80692488`;
- health latest attempt SUCCESS and HEALTHY with that run ID;
- `/api/worker` HTTP 200, payload `[]`;
- cleanup database count 0.

No full suite, Ruff or mypy was run for this diagnostic because no source change exists yet.

## Smallest repair-release request

Request one bounded repair to make `/api/worker` expose current `worker_run` and `worker_run_finished` history while retaining clearly labelled legacy `worker_sweep` compatibility. Preserve the existing bounded history and existing fields `id`, `result`, `occurred_at`, and `metrics`; add unambiguous `record_type` and `run_id`. The lead should decide the final response schema and whether paired begin/finish records remain separate or receive an explicitly specified projection.

Do not duplicate or alter `/api/health` newest-attempt/staleness calculations. Do not redesign worker persistence, add controls, or combine the repair with other inventory observations.

## Recommendation and boundaries

**REWORK_FOUND** at exact source `832d85f...` for the J20-01 worker-history read surface. Request the smallest repair release above. This diagnostic is synthetic engineering evidence, not live worker/provider proof, formal acceptance, deployment authority, or a V2.0 verdict.

Other observations in `jobs-control-center-inventory-20260922.md` remain unchecked and are not batched findings or repair requirements.

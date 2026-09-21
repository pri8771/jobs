# V2.0 Worker Run History Contract

Artifact: A-V20-WORKER-RUN-HISTORY

## Purpose

Make background worker execution durable and inspectable. V2.0 health/dashboard must not infer liveness from an in-memory loop or process existence alone.

## Required model

Recommended `WorkerRunModel` / `job_run` record:

- id UUID
- run_kind: scheduled | manual | reconciliation | canary
- worker_id / runtime_instance_id
- started_at
- finished_at nullable
- status: RUNNING | SUCCESS | PARTIAL | FAILED | KILLED
- reconcile_requested
- reconciliation_performed
- email_adapter/provider
- messages_polled
- messages_ingested
- jobs_discovered
- lifecycle_transitions
- unanswered_alerts
- stale_alerts
- review_tasks_created if practical
- error_count
- errors_json
- code_version / git_sha if available
- metadata_json
- created_at

Never store OAuth tokens, email bodies, passwords, or browser/session secrets in this record.

## Persistence semantics

A run record must survive failures.

Do not create the run row inside the same uncommitted transaction that may be rolled back by the work it is observing.

Preferred behavior:
1. create + commit RUNNING record before work,
2. execute the sweep,
3. update the record to SUCCESS/PARTIAL/FAILED in a separate durable commit,
4. if process crashes, stale RUNNING records can be surfaced as interrupted.

## Status rules

SUCCESS:
- requested pipeline stages completed,
- no errors.

PARTIAL:
- some useful work completed but one or more non-fatal stages failed.

FAILED:
- run could not perform its primary purpose.

KILLED:
- safety kill switch prevented execution.

A Gmail adapter unavailable error must not be reported as SUCCESS.

## Health integration

Health/dashboard should expose:
- last run start/end/status
- last successful run
- last successful real Gmail ingestion
- last reconciliation
- age since last success
- recent error summary
- whether a RUNNING record is stale

Do not call the worker healthy solely because a process exists.

## Idempotency / lifecycle relationship

WorkerRun records are operational telemetry, not application state.

Repeated processing prevention belongs to source-evidence/application-event idempotency.

## Acceptance tests

1. successful sweep creates SUCCESS run with accurate counts.
2. Gmail unavailable creates PARTIAL/FAILED, not SUCCESS.
3. kill switch creates KILLED record.
4. exception after run start still leaves durable FAILED/PARTIAL evidence.
5. stale RUNNING record is detectable.
6. health returns last success + last error.
7. no secret fields are persisted.
8. repeated worker sweeps create distinct run records but no duplicate lifecycle events.

## Worker task

J20-07 owns implementation after Lane B reaches A-V20-RELIABILITY.

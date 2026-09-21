# Worker Run History Repair Guide

Artifact:
- A-V20-WORKER-RUN-HISTORY

Current state:
Lane B added end-of-sweep `AuditLogModel(action_type="worker_sweep")` telemetry. Keep it if useful, but it does not satisfy crash-durable run history.

## Problem

The current audit row is created at the end of the same normal worker sweep transaction.

Failure cases:
- process dies before final commit -> no run record,
- global kill switch returns before run record,
- cannot represent RUNNING,
- cannot detect abandoned RUNNING run,
- cannot reliably distinguish last attempt from last success,
- ingestion transaction rollback can erase operational evidence if coupled incorrectly.

## Preferred implementation without immediate schema migration

Use AuditLogModel as the durable run-state store first, to avoid shared DB schema conflicts.

Create one stable run_id UUID per sweep.

### Begin record

Before pipeline work, in a separate short-lived session/transaction:

AuditLogModel:
- action_type = worker_run
- entity_type = worker
- external_reference = run_id
- result = RUNNING
- metadata:
  - run_id
  - run_kind
  - started_at
  - reconcile_requested
  - code_version if available

Commit immediately.

### Finalize record

At sweep completion, use a separate session/transaction.

Prefer updating the same run record if audit semantics allow mutable operational state; otherwise append `worker_run_finished` with same run_id and retain immutable begin record.

Final status:
- SUCCESS
- PARTIAL
- FAILED
- KILLED

Metadata:
- finished_at
- messages_polled
- messages_ingested
- jobs_discovered
- lifecycle_transitions
- alert counts
- reconciliation_performed
- safe error categories/messages

No tokens, passwords, email bodies, or raw secrets.

## Kill switch

A kill-switch-blocked run should still produce:

- begin RUNNING
- finish KILLED

or a single durable KILLED attempt record if the check deliberately occurs before begin.

Either way, health must know a scheduled attempt was intentionally prevented.

## Crash detection

Health service:
- find latest RUNNING begin with no matching finish,
- if age > configured threshold, report stale/interrupted run,
- do not mark system healthy solely from older success.

## Health fields

Expose:
- last_attempt_at/status
- last_success_at
- last_error_at/category
- last_reconciliation_at
- stale_running_run bool

## Test cases

1. successful run -> durable begin + success.
2. ingestion returns errors -> PARTIAL/FAILED according to primary-work definition.
3. adapter unavailable -> FAILED/PARTIAL, not SUCCESS.
4. kill switch -> KILLED evidence.
5. exception after begin -> final FAILED when exception is caught.
6. simulated hard crash fixture leaves RUNNING; health detects stale run.
7. pipeline DB rollback does not delete run evidence.
8. two runs have distinct run_ids.
9. secrets absent from metadata.

## Story point

B-R20-05 / J20-14 remains SP3 if implemented with AuditLogModel and no migration.

A dedicated WorkerRunModel can be reconsidered later only if AuditLog-based state becomes limiting.

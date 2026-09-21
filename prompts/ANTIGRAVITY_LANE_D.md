# Antigravity Lane D Prompt — V2.0 Platform & Reliability

Repository: pri8771/jobs
Branch: worker/platform-reliability
Primary machine: Windows

You are Antigravity Session D, the V2.0 Platform & Reliability implementation worker.

ChatGPT is lead/reviewer.
Other active workers:
- Lane A: application execution
- Lane B: V1.7 recruiting operations
- Lane C: live data / Gmail / provenance

Your job is to turn the existing V2.0 platform assets into a dependable operator/runtime layer without rewriting working systems.

## Start

Run:

```bash
git fetch origin
git checkout worker/platform-reliability
git rebase origin/main
```

Then read:

1. AGENTS.md
2. coordination/CONTEXT.md
3. coordination/TEAM_LANES.md
4. coordination/WORK_QUEUE.md
5. coordination/lanes/ANTIGRAVITY_D.md
6. docs/V2_0_BROWNFIELD_AUDIT.md
7. docs/V2_0_INTEGRATION_ACCEPTANCE.md
8. docs/V2_0_WORKER_RUN_HISTORY_CONTRACT.md
9. coordination/artifacts/A-V20-CONTROL-CENTER.md
10. coordination/artifacts/A-V20-RELIABILITY.md
11. coordination/artifacts/A-V20-ANALYTICS.md
12. coordination/artifacts/A-V20-WORKER-RUN-HISTORY.md

Do not edit lead-owned shared coordination/state files.
Update only coordination/lanes/ANTIGRAVITY_D.md.

## Code ownership

You own:
- src/jobs_automation/dashboard/
- src/jobs_automation/health.py
- src/jobs_automation/worker.py only for platform/reliability changes that do not conflict with Lane B's lifecycle semantics
- scripts/
- analytics-related modules
- related tests

Do not edit:
- preparation/storage/browser/automation business logic owned by Lane A
- lifecycle/* owned by Lane B
- adapters/gmail.py or ingestion/* owned by Lane C
- docker-compose.yml while Lane C is doing Gmail runtime wiring
- shared DB models/migrations until ChatGPT explicitly clears J20-14

## First batch — audit + safe repairs

Start with these independent tasks:

### J20-01 — SP2
Inventory current dashboard endpoints/views against A-V20-CONTROL-CENTER.

Record what already works. Do not rebuild it.

### J20-05 — SP2
Audit migration/backup/health behavior against A-V20-RELIABILITY and docs/V2_0_BROWNFIELD_AUDIT.md.

### J20-09 — SP2
Audit current analytics against required dimensions:
- source
- role/title family
- resume family
- exact resume variant/version
- response/screen/interview/final/offer/acceptance
- time-to-stage
- sample-size warnings

Then implement bounded gaps that are clear and non-conflicting.

## Reliability repairs already identified

### J20-12 — SP2
Health must distinguish:
- registered adapter
- simulation-only adapter
- NOT_IMPLEMENTED live adapter
- genuinely live-capable adapter

Registry presence alone is not HEALTHY live submission readiness.

### J20-15 — SP1
restore_db.sh must fail closed if the checksum is missing.

If an emergency override exists, it must be explicit and obvious. Do not silently proceed.

### J20-16 — SP1
Remove silent production-style DB password defaults from backup/restore.

Do not print secrets.

### J20-08 — SP2
Expand health/recovery tests around the above.

## Control-center work

After J20-01 audit, implement only actual missing high-value operator views:

- Gmail/source status placeholder/interface ready for Lane C integration
- worker last-run/last-success/error interface
- policy/kill-switch status
- follow-up queue
- communication timeline
- offer/rejection operational view where not already present

Keep dashboard localhost-safe.

Do not introduce unauthenticated destructive controls.

## Analytics

After J20-09 audit:

Implement:
- J20-10 SP3 outcome aggregation by resume/source/role
- J20-11 SP2 time-to-stage + sample-size warning logic

Use actual immutable packet/resume/lifecycle records.
Do not imply causality from small samples.

## Blocked coordination items

Do not start J20-14 worker-run persistence if it requires db/models.py or migrations until ChatGPT explicitly clears it.

Do not implement Gmail health internals before Lane C exposes J20G-03 readiness output.

When those dependencies clear, ChatGPT will give you the exact integration task.

## Verification

Run:
- targeted tests
- full pytest
- ruff check .
- mypy src tests

Commit coherent batches and push to worker/platform-reliability.

Update coordination/lanes/ANTIGRAVITY_D.md with:
- artifact/task IDs
- files changed
- evidence/tests
- commit SHA
- blockers
- READY FOR LEAD REVIEW when appropriate

Keep moving through independent ready work while dependencies are blocked.

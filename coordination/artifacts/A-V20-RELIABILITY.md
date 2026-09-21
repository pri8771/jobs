# A-V20-RELIABILITY

- Type: reliability / evidence
- Phase: V2.0
- Status: READY
- Owner: Antigravity Lane B
- Reviewer: ChatGPT
- Dependencies: none for audit/repair
- Downstream: A-V20-INTEGRATED-OS

## Purpose

Prove recoverability and dependable autonomous operation using existing CI, health, worker, migration, and backup assets.

## Existing assets

- GitHub Actions CI
- health.py
- worker.py
- backup_db.sh / restore_db.sh
- migrations
- parser tests

## Acceptance criteria

- migration upgrade chain test and downgrade/recovery procedure
- backup + checksum + restore drill documented/tested
- worker run outcome/history or equivalent operational evidence
- health exposes database, ingestion, policy, worker readiness
- parser regression fixtures
- provider/model failure is explicit and non-fabricating
- recovery runbook
- CI green

## Worker tasks

- J20-05 SP2 — audit migration/backup/health gaps
- J20-06 SP3 — add migration + backup/restore verification automation
- J20-07 SP3 — add durable worker run history / last-run evidence
- J20-08 SP2 — add missing health/recovery regression coverage

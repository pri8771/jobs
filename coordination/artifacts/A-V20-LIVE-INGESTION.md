# A-V20-LIVE-INGESTION

- Type: live integration / evidence
- Phase: V2.0
- Status: BLOCKED
- Owner: Antigravity + User
- Reviewer: ChatGPT
- Dependencies: user runtime Gmail OAuth, A-V12-GMAIL-CANARY
- Downstream: A-V20-INTEGRATED-OS

## Purpose

Prove real Gmail/job alert/recruiting ingestion on the Jobs Automation runtime with no fixture/mock path.

## Acceptance criteria

- read-only OAuth works outside Git
- dry-run bounded canary
- persisted bounded canary
- provider IDs preserved
- rerun is idempotent
- at least one real job/recruiting message is normalized
- no fixture/mock path active
- worker can consume real inbox safely

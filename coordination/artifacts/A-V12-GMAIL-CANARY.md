# A-V12-GMAIL-CANARY

- Type: integration / evidence
- Phase: V1.2
- Status: PROPOSED
- Owner: Antigravity + User
- Reviewer: ChatGPT
- Dependencies: user-created Google Cloud OAuth credentials/consent
- Downstream: real job-alert ingestion

## Purpose

Prove the runtime can perform a real read-only Gmail ingestion canary with no fixture/mock path.

## Acceptance

- Gmail read-only scope
- credentials stored outside Git
- harmless connection check
- bounded initial query/window
- no mailbox mutation
- evidence that real Gmail adapter ran
- fixture/mock adapter impossible in production canary
- parser output reviewed before ongoing worker enabled
- rollback/recovery documented

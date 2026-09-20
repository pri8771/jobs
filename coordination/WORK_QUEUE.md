# Active Work Queue

ChatGPT owns priority/order unless the user explicitly overrides it.

Antigravity should execute the highest-priority unblocked work, update tests/docs/state, commit, push, and report in coordination/AI_SYNC.md.

Do not wait for a new chat message when the next queued work is clear.

Last prioritized: 2026-09-20

## Strategic finish line

Current scope ends when Jobs Automation demonstrates:

**one genuine, externally confirmed application submitted through the system for a real job the user actually wants.**

Milestone path:
- V1.1 stabilization
- V1.2 real candidate/account/Gmail onboarding
- V1.3 real job ingestion/selection
- V1.4 real application packet
- V1.5 assisted real application
- V1.6 first genuine system-submitted application

After V1.6:
- stop broad development,
- request ChatGPT review,
- reassess what should be built next.

Detailed plan:
- docs/FIRST_REAL_APPLICATION_PLAN.md

V2/V3 is tentative reference only:
- docs/TENTATIVE_V3_ARCHITECTURE.md

## Current milestone

V1.1 — Stabilization and truthful integration

## P0 — Must fix before real Gmail/profile/application use

### 1. Wire scheduled Gmail ingestion into WorkerDaemon

Current problem:
- WorkerDaemon runs on a 4-hour cadence but does not invoke GmailAdapter + EmailIngestionEngine.

Required:
- normal worker sweep performs Gmail ingestion first
- lifecycle processing happens after ingestion
- 4-hour default remains
- once-daily reconciliation runs at most roughly once per 24h
- failed Gmail polling must not advance the checkpoint
- missing credentials must fail clearly, never fabricate data

Verification:
- unit/integration tests prove call order and checkpoint behavior

### 2. Remove implicit fake fixture fallback

Current problem:
- poll-emails falls back to MockEmailAdapter when Gmail auth is unavailable.

Required:
- production/default path fails clearly
- mock fixtures require explicit --mock-fixtures
- no fake email/job rows written accidentally

### 3. Make --dry-run truly non-persistent

Required:
- parse/classify/report
- rollback / no commits
- no checkpoint advance
- no jobs/messages/tasks/events/applications persisted

Add tests that compare DB state before/after.

### 4. Remove hard-coded candidate email fallback

Required:
- no invented candidate email
- if profile email is null, warn and reduce outbound-detection confidence
- candidate facts come only from explicit config/private runtime state

### 5. Correct simulated ATS application semantics

Current problem:
- Greenhouse/Lever adapters generate simulated receipts but may mark application SUBMITTED.

Required:
- mock mode -> SIMULATED / APPLICATION_SIMULATED
- live mode without real implementation -> NOT_IMPLEMENTED
- no fake live confirmation URL
- no APPLICATION_SUBMITTED event unless a real external submission is confirmed
- keep policy gate deny-by-default

Do not implement live ATS submission in this task.

### 6. Dashboard safe default

Required:
- Docker bind should be localhost by default: 127.0.0.1:8765:8765 or equivalent configurable safe default
- document that remote/LAN exposure requires explicit opt-in and authentication/reverse-proxy protection

### 7. Add GitHub Actions CI

On push + PR:
- Python 3.12
- dependency install
- pytest
- ruff check
- mypy

No live credentials required.

### 8. Correct version/maturity truth

Required:
- state/CURRENT.md must distinguish implemented prototype features from live-verified integrations
- package/document versions must not contradict project maturity
- never claim "real submission" or "end-to-end live" for mocks

## P1 — V1.1 hardening

### 9. Email tracking regression tests

Prove:
- provider message IDs idempotent
- thread IDs preserved
- inbound/outbound classification
- chronological thread order
- ambiguous multi-application link -> NEEDS_REVIEW
- single clear application auto-links
- failed transaction does not move checkpoint
- reconciliation catches missed message

### 10. Worker regression tests

Prove:
- ingestion before lifecycle
- default 14,400 second cadence
- daily reconciliation not every sweep
- kill switch respected where applicable
- Gmail failure does not create fixtures

### 11. Secret/config audit

Verify repo contains no:
- OAuth tokens
- refresh tokens
- API keys
- cookies
- browser state
- private credentials

## Exit criteria for V1.1

- CI green
- all tests green locally and in CI
- lint/type checks green
- Gmail production path never fabricates data
- worker genuinely attempts Gmail ingestion on schedule
- no simulated external submission can masquerade as real
- dashboard safe-by-default
- CURRENT/CONTEXT accurately state remaining limitations

After V1.1:
- ChatGPT reviews and updates queue for V1.2.
- Antigravity must not connect accounts or cross external-action boundaries until the next phase is authorized.

## Queued next phases after ChatGPT V1.1 review

### V1.2 — Real onboarding
- canonical candidate facts/resumes
- Google Cloud Gmail OAuth project
- Gmail read-only
- LinkedIn/Indeed/ZipRecruiter/Dice profiles and alerts
- real mailbox sweeps

### V1.3 — Real job ingestion/matching
- ingest real alerts
- dedupe real jobs
- detect actual application destination
- score/filter
- choose strong proof-job candidate(s)

### V1.4 — Real application packet
- correct resume family
- truthful tailoring
- screening answers
- unresolved-question block
- exact artifact manifest/hash

### V1.5 — Assisted real application
- authenticated browser worker/profile
- form inspection/prefill/upload
- user review
- real confirmation capture

### V1.6 — First genuine system submission
- approved real destination/method
- user authorizes exact live application
- execute real external submission
- capture external confirmation
- only then record APPLICATION_SUBMITTED

After this succeeds, STOP and request ChatGPT/user reassessment.

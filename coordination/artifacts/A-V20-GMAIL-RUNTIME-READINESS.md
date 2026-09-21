# A-V20-GMAIL-RUNTIME-READINESS

- Type: integration / runtime safety
- Phase: V2.0
- Status: READY
- Owner: Antigravity Lane C + Lane B glue
- Reviewer: ChatGPT
- Dependencies: existing Gmail adapter/worker
- Downstream: A-V20-LIVE-INGESTION, A-V20-INTEGRATED-OS

## Purpose

Make real Gmail usable by the scheduled runtime without silent message loss, missing container token persistence, or false health readiness.

## Contract

See:
- docs/V2_0_GMAIL_RUNTIME_READINESS.md

## Lead evidence / audit

Current main audit confirms:
- `GmailAdapter.poll_messages()` can silently omit a listed message because `get_message()` catches fetch errors and returns `None`, so J20G-01 remains required.
- `EmailIngestionEngine.run_sweep()` rolls back its session on an exception, so the desired fail-closed adapter behavior can reuse the existing transaction boundary rather than inventing a second ingestion transaction model.
- `HealthCheckService` currently has no Gmail-specific component and `check_adapters()` only proves ATS registration, not real Gmail readiness.
- `WorkerDaemon` resolves Gmail independently and exposes free-form result/error data, so Lane C and Lane B need a typed, secret-free handoff rather than sharing credential objects.
- The contract now requires a transport-neutral `GmailReadinessReport`-style output from J20G-03 that Lane B consumes in J20G-04 without interactive OAuth or secret serialization.

## Worker tasks

- J20G-01 SP2 — fail closed on partial Gmail fetch
- J20G-02 SP2 — runtime/container OAuth token wiring
- J20G-03 SP2 — safe real-Gmail diagnostic + typed secret-free readiness boundary
- J20G-04 SP2 — health/worker evidence integration consuming that boundary

## Live boundary

User performs OAuth consent. Engineering does not fabricate or substitute mock proof.

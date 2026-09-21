# A-V20-WORKER-RUN-HISTORY

- Type: reliability / operational evidence
- Phase: V2.0
- Status: ACCEPTED
- Owner: Lane 3
- Reviewer: ChatGPT
- Dependencies: existing worker/health
- Downstream: A-V20-RELIABILITY, A-V20-CONTROL-CENTER, A-V20-INTEGRATED-OS

## Purpose
Persist truthful worker-run evidence and expose last-success/error/reconciliation health.

## Contract
See docs/V2_0_WORKER_RUN_HISTORY_CONTRACT.md.

## Worker task
- J20-14 / B-R20-05 SP3

## Lead acceptance — 2026-09-21

Accepted implementation evidence:
- durable worker begin record persists before pipeline execution,
- begin persistence failure fails closed before pipeline work,
- begin/finalize sessions remain durable across pipeline rollback,
- distinct run IDs are preserved,
- persisted error evidence is bounded/sanitized rather than raw exception text,
- health reports true newest unfinished RUNNING attempt plus reconciliation/error metadata,
- adversarial tests cover begin failure, exception-after-begin, rollback durability, run-ID uniqueness and secret sanitization,
- final Lane 3 branch CI was green,
- PR #3 merged to main as `be765ea42856bc695fc1eece9c1da396b4f162d4`.

Acceptance is engineering/artifact acceptance only; it authorizes no Gmail or other live external action.

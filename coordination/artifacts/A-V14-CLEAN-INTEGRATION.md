# A-V14-CLEAN-INTEGRATION

- Type: integration / branch hygiene
- Phase: V1.4
- Status: **ACCEPTED**
- Owner: Fable/Claude + ChatGPT
- Reviewer: ChatGPT
- Dependencies: A-V14-P0A-INTEGRITY ACCEPTED
- Downstream: A-V14-REAL-PROOF

## Purpose

Integrate the V1.4 proof tooling as a coherent current-main batch without historical heartbeat/coordination churn.

## Accepted evidence

- P0A exact source: `8491dd98154ff750f49cbb64d2a79eca5cb06069`.
- Consolidated PR #12 exact head: `47fefd1b0ca354360353577685f6619a94f00f42`.
- PR #12 merged to `main` as `7c0fa73bf350392a88b47442455359a43cf926b0`.
- Lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

The accepted P0A batch includes installed importer -> runner -> verifier production-path integration tests on SQLite and password-protected PostgreSQL, including credential/target rotation and persisted-data mutation cases. Fable reported 323 P0A tests and later 395 tests for the consolidated P0A+V1.5 exact head, plus Ruff/mypy green.

Hosted Actions remained `CI_BLOCKED_ACCOUNT` before executable steps; the documented lead engineering exception was used and is not a claim of green hosted CI.

## Boundary

This artifact accepts engineering integration only. **G14 remains UNPASSED** and V1.4 remains incomplete until the genuine private profile + exact selected resume + current real job production packet proof produces a runtime candidate and independently validated receipt.
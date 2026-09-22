# A-V14-CLEAN-INTEGRATION

- Type: integration / branch hygiene
- Phase: V1.4
- Status: BLOCKED
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V14-P0A-INTEGRITY ACCEPTED
- Downstream: A-V14-REAL-PROOF

## Purpose
Move V1.4 proof tooling onto a clean branch based on current main without dragging historical heartbeat/coordination churn.

## Tasks
- R14-I01 SP1 fresh branch from main
- R14-I02 SP1 port only necessary proof-code changes
- R14-I03 SP1 resolve real code conflicts
- R14-I04 SP1 full checks
- R14-I05 SP1 small PR/review

## Acceptance
Small reviewable diff on current main with equivalent proof behavior.

## Worker report — Fable, 2026-09-22 (state: READY_FOR_LEAD_REVIEW, not accepted)

F145-06 (FR14-04): `tests/test_real_proof_integration.py` drives the production importer
(Greenhouse fetch stubbed with a canonical engineering payload), the runner and the
verifier as installed entry points on SQLite and on a throwaway password-protected
PostgreSQL role/database created from `PROOF_TEST_PG_ADMIN_URL` (wired in CI to the
existing postgres service), including password rotation between run and verification,
runtime-target mismatch, missing runtime configuration, stale credential, and single-field
DB mutations. Evidence stays under gitignored `.local/engineering_proof_<id>/` and is
never published as REAL_PROOF. Independent execution results are in the handoff.

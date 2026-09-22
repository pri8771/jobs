# A-V14-P0A-INTEGRITY

- Type: proof tooling / integrity
- Phase: V1.4
- Status: **ACCEPTED (engineering)**
- Owner: Fable/Claude
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V14-REAL-PROOF

## Purpose

Make the real-proof verifier fail closed against forged/local-only evidence before any genuine private proof run.

## Accepted source

- Exact P0A implementation: `8491dd98154ff750f49cbb64d2a79eca5cb06069`.
- Consolidated PR #12 exact head including V1.5: `47fefd1b0ca354360353577685f6619a94f00f42`.
- Integrated to `main` through PR #12 as `7c0fa73bf350392a88b47442455359a43cf926b0`.
- Lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

## Lead acceptance evidence

Lead reviewed the actual implementation and accepted the P0A engineering contract for:
- closed runtime evidence schema with `REAL_PROOF_CANDIDATE` separated from verifier-owned PASS/FAIL receipts;
- runtime schema execution and schema-hash binding;
- credential-safe proof-database identity with mandatory runtime-target reconciliation;
- independent persisted Job/JobSource/packet/answer/provenance/artifact/profile/resume validation;
- canonical Greenhouse source/question identity binding;
- canonical candidate-profile fingerprint plus exact selected resume mapping/bytes/hash/version/source binding;
- generation-origin truth and fail-closed missing/tampered evidence handling;
- sanitized failure receipts and path-safe handling of untrusted proof IDs;
- positive and adversarial importer -> runner -> verifier integration coverage on SQLite and password-protected PostgreSQL, including password rotation, stale/mismatched runtime targets and persisted-data mutations.

Fable's P0A handoff reported 323 tests at the P0A commit; the later consolidated exact-head handoff reported 395 tests including real PostgreSQL proof-path tests, with Ruff and mypy green.

Hosted GitHub Actions were blocked before executable steps by the observed account/runner startup condition and are **not** called green. A bounded `worker-pc` exact-head validation independently confirmed the consolidated SHA but could not run Python because of its harness approval policy, so it contributes zero test counts. The lead applied the documented `CI_BLOCKED_ACCOUNT` engineering exception in `coordination/V17_LEAD_HANDOFF.md`.

## Boundary

This acceptance is **engineering acceptance only**. It does not constitute G14, does not authorize use of private candidate material on an ineligible host, and does not make V1.4 COMPLETE.

G14 remains unpassed until an approved genuine private profile, exact selected real resume and current real job run through the production packet path and produce a runtime candidate plus independently validated receipt. Private inputs stay local; committed evidence remains sanitized hashes/provenance only.
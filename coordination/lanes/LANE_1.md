# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- active Lane 1 worker

Reviewer:
- ChatGPT lead
- worker-pc may provide bounded independent audit support

Priority:
- P0 / project critical path

## Current lead review — 2026-09-21 17:02Z

Worker batch:
- commit `8f8c21f88512aa32521c78285b72dc9da298672e`
- CI #401: GREEN
- P0A is **REWORK**, not accepted.

Direct lead review and the completed independent worker-pc static audit agree that proof integrity remains incomplete.

## Immediate bounded assignment — COMPLETED (READY_FOR_LEAD_REVIEW)

Repaired all P0A proof-integrity findings:
1. Candidate bundles strictly accept only `REAL_PROOF_CANDIDATE`; self-labeled PASS candidate input fails.
2. PASS requires successful private/local cross-binding; structural-only validation emits FAIL receipt with `local_full_bundle_verified: false`.
3. Candidate-bundle SHA binding in the private/local bundle is mandatory for PASS and verified.
4. Rejected candidates emit a candidate-bundle-bound FAIL receipt by default.
5. RP14-T3 fully binds approved Greenhouse source attestation: provider, source_kind, public job ID, api_url, description SHA, and question list SHA.
6. RP14-T4 scans and rejects copied example candidate profiles against repository fixtures and enforces PRIVATE_LOCAL source class.
7. RP14-T6 deterministic-production labeling is strictly enforced by the verifier (`generation_origin == "deterministic"`, `model_origin == "deterministic"`, `generation_engine == "deterministic-canonical-renderer"`).
8. RP14-T7 independently recomputes the canonical packet hash from manifest components and verifies manifest job ID, resume family/variant, artifact SHAs, and packet linkage.
9. Comprehensive adversarial tests added in `tests/test_real_proof_verifier.py` and `tests/test_real_proof_runner.py` (18 targeted tests pass, full suite 164 tests pass, Ruff clean, mypy clean).

Status: `READY_FOR_LEAD_REVIEW`

## Heartbeat

Canonical owner directive:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach`

Exactly one watcher. Fixed 5-minute cadence while active. No transitions.


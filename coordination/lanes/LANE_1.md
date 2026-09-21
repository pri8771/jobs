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

## Immediate bounded assignment

Repair all findings in one coherent batch:
1. Candidate bundles accept only `REAL_PROOF_CANDIDATE`; self-labeled PASS candidate input fails.
2. PASS requires successful private/local cross-binding; structural-only validation may never emit PASS.
3. Candidate-bundle SHA binding in the private/local bundle is mandatory for PASS and cannot be silently skipped.
4. Rejected candidates emit a candidate-bundle-bound FAIL receipt by default.
5. RP14-T3 fully binds the approved Greenhouse source: provider/source kind, public job ID, canonical/API URL, fetch timestamp, description SHA and canonical question-list SHA; fake plausible DB rows/questions must fail. Use same-flow runtime attestation or fresh bounded public revalidation as specified by the tooling audit.
6. RP14-T4 retains copied-example content-hash rejection and runtime-derived private source classification.
7. RP14-T6 deterministic-production labeling is enforced by the verifier, not only emitted by the runner.
8. RP14-T7 independently recomputes canonical packet hash and verifies manifest job ID against the local JobModel, resume family/variant + artifact SHAs against redacted evidence, and packet-row resume_variant/artifact IDs against runtime evidence.

Add adversarial tests for every finding, then run focused proof tests + full pytest/Ruff/mypy + branch CI. Push one coherent repair and set `READY_FOR_LEAD_REVIEW` / `REVIEW`.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT accepts P0A.

## Heartbeat

Canonical owner directive:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach`

Exactly one watcher. Fixed 5-minute cadence while active. No transitions.

Any DAYWATCH/15-minute/hourly instruction is superseded unless the owner explicitly changes this again.

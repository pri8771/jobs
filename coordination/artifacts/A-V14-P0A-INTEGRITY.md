# A-V14-P0A-INTEGRITY

- Type: proof tooling / integrity
- Phase: V1.4
- Status: IN_PROGRESS
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V14-CLEAN-INTEGRATION, A-V14-REAL-PROOF

## Purpose
Make the proof verifier fail closed against forged/local-only evidence before any private proof run.

## Current source
Latest reviewed repair source:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

## Remaining worker tasks
- R14-P01 SP1 — bind persisted JobSource attestation to local source_attestation.
- R14-P02 SP1 — adversarial JobSource mismatch/omission tests.
- R14-P03 SP1 — targeted + full local checks.
- R14-P04 SP1 — exact-head CI or CI_BLOCKED_ACCOUNT + independent validation request.

## Acceptance
- verifier independently validates Job/JobSource/packet/resume/artifact runtime truth,
- structural/local forged evidence cannot PASS,
- all targeted/full checks pass,
- ChatGPT lead accepts before private proof use.

## Worker report — Fable, 2026-09-22 (state: READY_FOR_LEAD_REVIEW, not accepted)

Frozen queue `docs/FABLE_FINAL_V145.md` F145-01..05 against the capsule review
`coordination/reviews/V145_FINAL_REVIEW_20260921.md` (FR14-01..03). Branch
`claude/serene-brown-g6uij0`; exact SHA in the heartbeat/handoff.

- F145-01 (FR14-01): `scripts/verify_v14_real_proof.py` executes the closed evidence schema
  at runtime (Draft 2020-12, `date-time`/`uri` format checkers required to exist, schema
  SHA bound into the receipt) before the semantic allowlist; `jsonschema`,
  `rfc3339-validator`, `rfc3986-validator` are runtime dependencies; schema tests hard-import.
- F145-02 (FR14-02): `jobs_automation.proof.database_identity` (moved from the capsule
  helper, shim kept); the runner records `proof_database` identity, never a URL; the
  verifier reconciles it with `AppSettings().database_url` and connects with the URL
  object; masked legacy URLs, mismatched or missing runtime targets are rejections.
- F145-03 (FR14-03): packet identity recomputed from persisted answers/provenance/artifact
  hashes/profile version/variant id and compared with stored hash, manifest and redacted
  evidence; unresolved list, counts, question membership, provenance method and
  live-ready invariant bound.
- F145-04: parsed canonical profile fingerprint (`jobs_automation.proof.profile_fingerprint`,
  also persisted by the production packet builder in `generation_metadata_json` and the
  manifest), version, unresolved-fact categories, selector variant, profile resume mapping,
  exact bytes/byte count, variant version, `source_reference`, artifact types and sizes.
- F145-05: sanitized reasons (no credentials, no absolute private paths), untrusted
  `proof_run_id` never used as a receipt path component, every malformed input ends in a
  bound `REAL_PROOF_FAIL` receipt rather than a traceback.

Worker claims are evidence inputs only; acceptance remains with the lead.

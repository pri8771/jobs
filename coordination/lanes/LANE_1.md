# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- Lane 1 worker

Reviewer:
- ChatGPT lead
- `worker-pc` may provide bounded independent audit/support

Priority:
- P0 / project critical path

## Latest lead review — 2026-09-21 17:58 ET

Current Lane 1 heartbeat branch head observed:
- `df4045883c1fde7b29af92a20028d3b6397e9a93`
- heartbeat #22 at `2026-09-21T21:31:56Z`
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- worker state `READY_FOR_LEAD_REVIEW`

**Liveness correction:** the heartbeat stream is now stale. More than three expected 5-minute intervals elapsed after #22 with no newer Lane 1 heartbeat commit. Before resuming work, verify the old watcher is dead, pull latest `main`, and launch exactly one new `FIVE_MIN_2026_09_21` watcher. Never launch a duplicate watcher.

Clean implementation branch / substantive batch:
- `claude/serene-brown-g6uij0`
- `3444076de27573ec57d9c8ae60876aece8e646d9`
- direct parent: reviewed main `927b33c0f523950ca206ead1cc2912e19a018184`

Verdict:
- **REWORK**
- P0A is not accepted
- V1.4 remains NOT COMPLETE
- private candidate/profile/resume proof execution remains forbidden

## Lead-reviewed positive evidence

The clean-port actual diff was reviewed. It materially implements the intended P0A verifier chain:

- RP14-T1 runtime emits `REAL_PROOF_CANDIDATE`; verifier emits separate candidate-SHA-bound PASS/FAIL receipts and writes FAIL receipts on rejection.
- RP14-T2 local/private bundle binds `proof_run_id`, candidate bundle SHA, and artifact hashes to the redacted candidate.
- RP14-T3 Greenhouse source/question/job evidence is checked against persisted `JobSource`/`Job` data, not merely against a self-consistent local attestation.
- RP14-T4 actual private profile bytes are SHA-bound locally and repository example-profile bytes are rejected by content hash.
- RP14-T6 production deterministic generation uses the canonical `generation_origin` metadata shape and rejects wrong/mock/test origins.
- RP14-T7 local artifact/manifest/packet/resume/database relationships and packet hash are independently re-derived.
- Proof DB linkage is mandatory/fail-closed.
- `postgresql+psycopg://` is recognized as the normal SQLAlchemy PostgreSQL form.

Worker-reported exact-head local validation for `3444076...`:
- pytest: 205 passed,
- Ruff: clean,
- mypy `src tests`: clean,
- 16 formerly-xfail adversarial defect probes reported passing.

Worker claims do not equal lead acceptance.

## Remaining blocking defect — schema did not clean-port

`coordination/proofs/v14_real_proof.schema.json` is still the old contract at `3444076...`:

- `additionalProperties: true`
- `result.const: REAL_PROOF_PASS`

Repository search also found no test currently referencing `v14_real_proof.schema.json`, so this contract drift is not protected by the reviewed test suite.

This directly violates RP14-T1/RP14-T5. The runtime candidate must be `REAL_PROOF_CANDIDATE`, and committed candidate evidence must use a closed allowlist.

### Immediate bounded rework

1. Verify the stale Lane 1 watcher is dead.
2. Pull latest `main` and launch exactly one current `FIVE_MIN_2026_09_21` watcher.
3. Synchronize the clean implementation with latest `main` coordination truth without importing old heartbeat/coordination churn into the code-review diff.
4. Correct `coordination/proofs/v14_real_proof.schema.json`:
   - `additionalProperties: false`,
   - `result.const: REAL_PROOF_CANDIDATE`,
   - properties/required fields match the actual redacted candidate emitted by `scripts/run_v14_real_proof.py` and accepted by the verifier,
   - include legitimate current fields such as `candidate_unresolved_fact_categories`, `questions_count`, `generation_engine`, and nullable provider/model fields as appropriate.
5. Add focused schema regression tests that:
   - accept the actual production candidate shape,
   - reject an arbitrary extra field,
   - reject a candidate that self-declares `REAL_PROOF_PASS`.
6. Re-run focused importer/runner/verifier/schema tests.
7. Re-run full `pytest`, `ruff check .`, and `mypy src tests`.
8. Push one coherent current-main P0A batch and mark `READY_FOR_LEAD_REVIEW`.
9. Obtain exact-head GitHub CI when Actions runners execute. Current hosted Actions attempts still fail before steps (`steps: []`, `runner_id: 0`); report `CI_BLOCKED_ACCOUNT`, never green, while that persists.
10. Stop for lead review. Do **not** use private inputs or run the genuine proof before explicit P0A acceptance.

A bounded support task `jobs-v14-p0a-schema-gate-20260921-1748` is executing on `worker-pc` against the clean implementation branch for the schema-only gap. It is support material only. Lane 1 must not wait for it and must not auto-merge it.

## Heartbeat

Canonical Lane 1 heartbeat:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one Lane 1 watcher

The last verified Lane 1 heartbeat is #22 at `2026-09-21T21:31:56Z`; the stream is stale. Resume with one watcher only after confirming the previous watcher is no longer running.

The heartbeat/post-progress workflows on the latest Lane 1 head fail before any steps execute (`runner_id: 0`), so issue #7 bot comments have not kept pace with heartbeat commits. Preserve truthful Git heartbeat evidence; do not change heartbeat semantics merely to manufacture comments.

## After P0A acceptance only

Immediately move to real-input readiness:
- validate the genuine private profile locally,
- resolve the exact selected genuine resume bytes,
- import/validate the current live OpenSesame job/questions,
- run the production packet path with non-mock deterministic generation,
- emit only redacted runtime candidate + verifier receipt to the repo,
- keep private profile/resume/full bundle local and gitignored.

No browser application submission, Gmail OAuth/mailbox access, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized by this lane.

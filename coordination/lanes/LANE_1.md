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

## Latest lead review — 2026-09-21 18:03 ET

Current Lane 1 heartbeat branch head observed:
- `df4045883c1fde7b29af92a20028d3b6397e9a93`
- heartbeat #22 at `2026-09-21T21:31:56Z`
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- worker state `READY_FOR_LEAD_REVIEW`

**Liveness:** stale. Multiple expected 5-minute intervals elapsed after #22 with no newer Lane 1 heartbeat commit. Before resuming work, verify the old watcher is dead, pull latest `main`, and launch exactly one new `FIVE_MIN_2026_09_21` watcher. Never launch a duplicate watcher.

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

## Remaining blocker and reviewed worker-pc support

At `3444076...`, `coordination/proofs/v14_real_proof.schema.json` is still stale:
- `additionalProperties: true`
- `result.const: REAL_PROOF_PASS`

Repository search also found no test referencing `v14_real_proof.schema.json` at that clean-port commit.

This directly violates RP14-T1/RP14-T5.

Bounded support task `jobs-v14-p0a-schema-gate-20260921-1748` completed successfully on `worker-pc` and returned:
- branch `worker/jobs-v14-p0a-schema-gate-20260921-1748`
- commit `70ef7adc62ab2e9846721e8174a306273f28cbaa`
- direct parent `3444076de27573ec57d9c8ae60876aece8e646d9`

Lead inspected the actual support diff. It changes only:
- `coordination/proofs/v14_real_proof.schema.json`,
- `tests/test_real_proof_schema.py`,
- `pyproject.toml` (adds `jsonschema` to dev dependencies so executable schema semantics can run).

The support patch structurally does the right thing:
- top-level `additionalProperties: false`,
- `result.const: REAL_PROOF_CANDIDATE`,
- schema property/required key set pinned to both runner AST-emitted keys and verifier `ALLOWED_TOP_LEVEL_KEYS`,
- legitimate current fields added (`candidate_unresolved_fact_categories`, `questions_count`, `generation_engine`, provider/model fields),
- deterministic-generation constraints aligned with verifier,
- tests cover production-shape acceptance, arbitrary extra-field rejection, self-declared PASS rejection, missing required keys, and out-of-contract values.

**Support verdict: useful / not accepted or merge-ready.** The worker environment did not execute the test suite and GitHub has zero check-runs for `70ef7adc...`. Lane 1 must adopt/cherry-pick or reimplement this support inside its coherent current-main batch and prove it with focused/full validation. Do not merge the support branch directly.

### Immediate bounded rework

1. Verify the stale Lane 1 watcher is dead.
2. Pull latest `main` and launch exactly one current `FIVE_MIN_2026_09_21` watcher.
3. Synchronize the reviewed clean implementation with latest `main` coordination truth without importing old heartbeat/coordination churn into the code-review diff.
4. Adopt or faithfully reimplement the reviewed support commit `70ef7adc...` schema + schema-test contract.
5. Run focused importer/runner/verifier/schema tests, including the new JSON-schema tests.
6. Run full `pytest`, `ruff check .`, and `mypy src tests`.
7. Push one coherent current-main P0A batch and mark `READY_FOR_LEAD_REVIEW`.
8. Obtain exact-head GitHub CI when Actions runners execute. Current hosted Actions attempts still fail before steps (`steps: []`, `runner_id: 0`); report `CI_BLOCKED_ACCOUNT`, never green, while that persists.
9. Stop for lead review. Do **not** use private inputs or run the genuine proof before explicit P0A acceptance.

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

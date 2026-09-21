# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- Lane 1 worker

Reviewer:
- ChatGPT lead
- `worker-pc` may provide bounded independent audit support

Priority:
- P0 / project critical path

## Latest lead re-review — 2026-09-21 14:36 ET

Latest implementation repair reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Verdict:
- **REWORK**
- P0A is not accepted.
- Private candidate/resume proof execution remains forbidden.

This repair materially improves RP14-T3 URL/timestamp checks, RP14-T4 actual profile-file hashing/example rejection, and RP14-T7 UUID/persisted-row validation code. Two acceptance-critical bypasses remain.

## Remaining bounded assignment

Close these remaining P0A gaps in one coherent batch:

1. **RP14-T7 — database linkage must be mandatory for PASS.**
   - `verify_database_linkage()` currently returns without validation when neither `database_url` nor `db_path` is present.
   - REAL_PROOF_PASS must require a configured proof DB target and successful persisted-row verification.
   - A hand-authored private bundle must not be able to omit the DB target and bypass `ApplicationPacketModel`, `ResumeVariantModel`, and artifact-row checks.
   - Convert/add an adversarial test showing omission/tampering of the DB target or persisted rows fails closed.

2. **RP14-T3 — source attestation must be independently anchored to trusted import evidence.**
   - Current verifier parses `fetched_at_utc`, binds canonical URL/public job ID, and re-hashes the local questions file, but the local `source_attestation` + local questions file remain mutually self-consistent inputs.
   - `description_sha256` is currently shape-checked rather than re-derived/bound to trusted persisted source evidence.
   - Load/verify the corresponding Greenhouse `JobSourceModel` and bind provider, `source_job_id`, source payload `content_sha256`, `question_list_sha256`, API URL, canonical apply URL and fetch metadata to the local attestation and `JobModel`; alternatively implement the fresh bounded same-flow public revalidation specified by the tooling audit.
   - Add adversarial tests proving a forged self-consistent attestation/questions file and fabricated description SHA cannot pass.

3. **Final integration evidence**
   - rebase/synchronize PR #8 onto latest `main`,
   - run focused real-proof tests,
   - run full `pytest`, `ruff check .`, and `mypy src tests`,
   - obtain **exact-head** GitHub CI after the final implementation commit,
   - then set `READY_FOR_LEAD_REVIEW` / `REVIEW` and stop implementation changes for lead review.

Concrete current test hole:
- `_setup_valid_full_run()` in `tests/test_real_proof_verifier.py` builds a positive PASS case with no database target and a fabricated-but-well-formed `description_sha256`. That PASS path demonstrates both remaining bypasses and should not survive the final verifier contract.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Lane 1 is correctly on the owner heartbeat standard and was observed through `2026-09-21T18:33:19Z` at heartbeat #9.

Canonical command:
```bash
python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach
```

Rules:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- every ~5 minutes while active,
- exactly one Lane 1 watcher,
- no proving/watch/hourly transitions,
- do not restart a healthy watcher or create a duplicate.

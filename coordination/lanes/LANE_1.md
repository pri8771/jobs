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

## Latest lead re-review — 2026-09-21 17:00 ET

Current Lane 1 branch head:
- `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- heartbeat #18 at `2026-09-21T19:18:36Z`
- current-epoch heartbeat stream is stale

Latest substantive Lane 1 implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Verdict:
- **REWORK**
- P0A is not accepted
- private candidate/profile/resume proof execution remains forbidden

## Reviewed worker-pc support branch

Task:
- `jobs-v14-p0a-remaining-fix-20260921-1545`

Returned branch / commit:
- `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- `062ca922c640d964220b550a06f61288b9a040c9`

Lead-inspected diff is limited to:
- `scripts/verify_v14_real_proof.py`
- `tests/test_real_proof_verifier.py`

It usefully addresses the two previously identified verifier gaps:
1. proof DB target/persisted packet-resume-artifact validation becomes mandatory/fail-closed,
2. source attestation is bound to persisted Greenhouse `JobSource`/`Job` evidence.

The support commit is **not accepted or merge-ready** because it has no exact-head GitHub CI and worker-side pytest/Ruff/mypy were sandbox-blocked.

## Corrected production-path audit

An interim lead note incorrectly compared the support verifier to the older importer on main. Independent audit plus direct lead inspection of the support/Lane 1 importer corrected that finding.

At `062ca922...`, `scripts/import_v14_proof_job.py::_source_payload()` already persists:
- `api_url`,
- `fetched_at_utc`,
- `content_sha256`,
- `screening_question_count`,
- `question_list_sha256`,
- `source_kind`,
- `provider`,
- `public_job_id`.

So the importer payload is **not** the current blocker.

Two actual production-path blockers remain:

### A. Generation metadata key mismatch

Production `packet_builder.py` writes `generation_metadata_json` with:
- `generation_origin`,
- `cover_letter_origin`,
- `cover_letter_model`.

Support verifier `062ca922...` reads `generation_metadata.get("origin", "")` and requires it to equal `deterministic`. A genuine production packet therefore fails even when its real generation metadata is correct. Existing verifier tests also use the non-production `origin` key and must be corrected to the real packet-builder shape.

Required repair:
- verify `generation_origin` as the canonical production key,
- preserve a legacy fallback only if justified and fail closed for misleading values,
- test actual production metadata shape and adversarial wrong-origin cases.

### B. PostgreSQL proof DB URL mismatch

Support `resolve_proof_db_url()` accepts `postgresql://` and `postgres://`, but the application's default `AppSettings.database_url` is `postgresql+psycopg://jobs:jobs@localhost:5432/jobs`.

A genuine run using the normal application DB URL can therefore be misinterpreted as a local SQLite path and fail before persisted proof validation.

Required repair:
- accept the real SQLAlchemy PostgreSQL driver-qualified form, including `postgresql+psycopg://`,
- retain fail-closed behavior for unsupported/unusable targets and persisted SQLite checks,
- add focused DB URL normalization tests.

## Remaining bounded assignment

1. Verify the stale Lane 1 watcher is dead.
2. Synchronize/clean-port the P0A implementation onto latest `main` without historical coordination churn.
3. Adapt the useful `062ca922...` DB/source-binding changes.
4. Fix the generation metadata and PostgreSQL URL production-contract blockers above.
5. Keep Greenhouse source binding against the actual importer output and persisted `JobSourceModel`/`JobModel` evidence.
6. Required adversarial coverage includes missing/unopenable/unrelated/tampered DB, packet/resume/artifact mismatch, forged Greenhouse source/question data, production generation metadata shape, wrong generation origin, and driver-qualified PostgreSQL URL handling.
7. Run focused importer/runner/verifier tests plus full `pytest`, `ruff check .`, and `mypy src tests`.
8. Obtain exact-head GitHub CI when Actions runners execute; if jobs fail before steps start, record `CI_BLOCKED_ACCOUNT` rather than claiming green CI.
9. Start exactly one canonical watcher:
   `python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof tooling RP14-T1..T7" --detach`
10. Push one coherent `READY_FOR_LEAD_REVIEW` batch and stop for lead review.

A new bounded support task `jobs-v14-p0a-runtime-contract-fix-20260921-1700` was dispatched to worker-pc for only the two runtime-contract fixes above. Lane 1 must not wait for it and must not auto-merge its output.

Do **not** use private candidate/resume inputs or execute the genuine proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Canonical Lane 1 heartbeat:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one Lane 1 watcher

Latest verified heartbeat remains #18 at `2026-09-21T19:18:36Z`; it is stale. Before restarting, verify the prior watcher process is not still running. Never create a duplicate.

Issue #7 automated heartbeat posting remains blocked by GitHub Actions runner startup failure (`steps: []`, `runner_id: 0`). Keep truthful Git heartbeat evidence and do not rewrite heartbeat semantics to work around the runner outage.

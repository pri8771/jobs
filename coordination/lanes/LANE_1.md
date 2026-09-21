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

## Latest lead re-review — 2026-09-21 15:50 ET

Latest substantive implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Current Lane 1 branch head:
- `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- heartbeat #18 at `2026-09-21T19:18:36Z`
- compare from `5e505846...` through current head changes only `coordination/heartbeats/LANE_1.md`; no later production repair exists

Verdict:
- **REWORK**
- P0A is not accepted
- private candidate/profile/resume proof execution remains forbidden

Direct lead inspection of current `scripts/verify_v14_real_proof.py` confirms both remaining defects still exist:

1. `verify_database_linkage()` resolves `database_url` / `db_path` and performs a bare `return` when neither is present. Omitting the proof DB target therefore still bypasses persisted packet/resume/artifact validation.
2. The verifier contains no persisted `JobSource` binding for Greenhouse source attestation. The local attestation/questions evidence is not independently proven against persisted import evidence.

## Independent support

Reviewed tests-only support branch:
- `worker/jobs-v14-p0a-remaining-tests-20260921-1449`
- commit `cffae70577b6719c92e7d7edc3ecd94d00db622d`
- actual reviewed diff: only `tests/test_real_proof_verifier.py`, +420 lines
- no worker-side pytest/Ruff/Python execution and no GitHub CI on that support commit
- useful as adversarial review input only; not accepted/integrated automatically

New bounded support task dispatched this run:
- `jobs-v14-p0a-remaining-fix-20260921-1545`
- worker: `worker-pc`
- scope: only the two remaining production verifier defects + focused verifier tests
- remote workflow `35647203812` was `in_progress` at dispatch review

Lane 1 must not wait for worker-pc. Any returned support branch is review input only and must be inspected before use.

## Remaining bounded assignment

Close these two acceptance-critical gaps in one coherent Lane 1 production batch.

### 1. RP14-T7 — database linkage is mandatory for PASS

Requirements:
- REAL_PROOF_PASS requires an explicitly configured proof DB target,
- missing/unopenable/unresolvable DB target fails closed,
- persisted `ApplicationPacketModel` row must match proof packet ID, job, selected resume, and relevant linkage,
- persisted `ResumeVariantModel` must match selected variant and resume artifact,
- required resume/cover-letter artifact rows and hashes must match candidate evidence,
- unrelated or tampered persisted rows must fail.

### 2. RP14-T3 — source attestation is independently bound to persisted import evidence

Load the corresponding persisted Greenhouse `JobSource` and `Job` evidence and bind at minimum:
- provider,
- source kind,
- public/source job ID,
- API URL,
- fetched_at_utc,
- description/content SHA,
- question-list SHA,
- canonical apply URL,
- linked `JobModel` identity/apply URL as appropriate.

A self-consistent forged local `source_attestation`, locally authored questions file, and fabricated description/content SHA must fail.

## Final validation / review boundary

After both repairs:
1. synchronize/rebase production changes onto latest main without importing unrelated historical coordination churn,
2. run focused real-proof verifier/runner tests including adversarial cases,
3. run full `pytest`,
4. run `ruff check .`,
5. run `mypy src tests`,
6. obtain exact-head GitHub CI when Actions runners execute again,
7. if Actions still fail before steps start, record `CI_BLOCKED_ACCOUNT` and provide independent exact-head validation rather than claiming CI green,
8. set `READY_FOR_LEAD_REVIEW` / `REVIEW`, push the coherent batch, and stop implementation changes for lead review.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Canonical Lane 1 heartbeat:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one Lane 1 watcher

Latest verified heartbeat is #18 at `2026-09-21T19:18:36Z`; the stream is now stale by more than 30 minutes. Before restarting, verify the prior watcher process is not still running. If dead, start exactly one current watcher; never create a duplicate.

Issue #7 automated heartbeat posting is currently blocked by GitHub Actions runner startup failure (`steps: []`, `runner_id: 0`). Keep truthful Git heartbeat evidence and do not rewrite heartbeat semantics to work around the account-level runner outage.
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

## Latest lead re-review — 2026-09-21 16:45 ET

Current Lane 1 branch head:
- `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- heartbeat #18 at `2026-09-21T19:18:36Z`
- current-epoch heartbeat stream is stale

Latest substantive Lane 1 implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Current comparison to latest main at this review:
- PR #8 remains draft and non-mergeable,
- Lane 1 is materially diverged from main,
- support/final validation must be rebased or cleanly ported onto current main before acceptance.

Verdict:
- **REWORK**
- P0A is not accepted
- private candidate/profile/resume proof execution remains forbidden

## New worker-pc support result reviewed

Remote task:
- `jobs-v14-p0a-remaining-fix-20260921-1545`

Returned Jobs branch / commit:
- `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- `062ca922c640d964220b550a06f61288b9a040c9`

Actual lead-inspected diff:
- `scripts/verify_v14_real_proof.py`
- `tests/test_real_proof_verifier.py`
- no coordination/private/Gmail/browser/submission files changed

The support patch usefully addresses the two previously identified verifier gaps:
1. missing proof DB target fails closed instead of silently bypassing persisted packet/resume/artifact verification,
2. source attestation is checked against persisted Greenhouse `JobSource`/`Job` evidence.

However, **the support commit is not accepted or merge-ready**:
- it has no exact-head GitHub CI/check run,
- worker-side pytest/Ruff/mypy were not executed,
- its new tests construct stronger Greenhouse source payload evidence than the current production importer actually persists.

### Newly identified production-path contract mismatch

Lead comparison against current `scripts/import_v14_proof_job.py` found that production `_source_payload()` currently persists:
- `api_url`,
- `fetched_at_utc`,
- `content_sha256`,
- `screening_question_count`,
- `source_kind`.

The worker-pc verifier patch additionally requires `source_payload_json` to contain:
- `provider`,
- `public_job_id`,
- `question_list_sha256`.

Current production import stores provider and public/source job ID in `JobSourceModel.provider` / `source_job_id`, not in the payload, and it does not currently persist `question_list_sha256` at all. Therefore the support patch as written can reject a genuine production importer → runner → verifier path even with valid real inputs. Its tests hide this incompatibility by hand-constructing a richer `_greenhouse_source_payload()` than production writes.

This must be repaired before P0A acceptance. Prefer binding provider/public job identity to the real `JobSourceModel` columns and add a production-derived persisted question-list hash (or an equivalently strong runtime capture) rather than trusting a test-only richer payload. Add an integration/adversarial test that uses the same production importer payload contract rather than a hand-authored stronger substitute.

A new bounded read-only worker-pc audit was dispatched to independently inspect this importer/verifier contract. Lane 1 must not wait for it.

## Remaining bounded assignment

Close the full P0A chain coherently on current main.

### 1. RP14-T7 — database linkage mandatory for PASS

Requirements:
- REAL_PROOF_PASS requires an explicitly configured/resolvable proof DB target,
- missing/unopenable/unrelated/tampered DB evidence fails closed,
- persisted `ApplicationPacketModel` identity/job/resume/artifact/packet-hash/profile/live-ready/generation links match runtime/redacted evidence,
- persisted `ResumeVariantModel` and required artifact rows/hashes/storage links match the verified local bytes.

The worker-pc implementation may be adapted, but do not blindly cherry-pick it without resolving production importer compatibility and current-main divergence.

### 2. RP14-T3 — independently trusted Greenhouse source binding

Bind source evidence across the **actual importer contract**, persisted `JobSourceModel`/`JobModel`, local questions file, and redacted proof.

At minimum verify:
- `JobSourceModel.provider == GREENHOUSE`,
- `JobSourceModel.source_job_id` equals approved public job ID,
- source kind/API URL/fetched-at/content SHA are persisted from the real public import,
- canonical/source URL agrees with the approved job URL and linked Job identity,
- description hash is recomputed from persisted job description,
- question-list hash/count are derived from the actual imported questions and persistently bound,
- a forged self-consistent local attestation/questions file cannot pass.

Do not create a verifier contract that the real importer cannot satisfy.

### 3. Production-contract regression coverage

Required focused tests include:
- no DB target → FAIL receipt,
- absent/corrupt/unrelated/tampered DB → fail,
- packet/resume/artifact row mismatch → fail,
- forged Greenhouse attestation / public ID / URL / fetched time / content hash / questions → fail,
- **real production importer payload shape → verifier-compatible pass**, without a richer hand-authored test-only payload,
- changed imported questions after persistence → fail.

### 4. Current-main synchronization and final validation

1. Verify the stale Lane 1 watcher is dead before restarting anything.
2. Synchronize/rebase/clean-port the P0A implementation to latest `main` without unrelated historical coordination churn.
3. Start exactly one canonical watcher:
   `python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof tooling RP14-T1..T7" --detach`
4. Run focused real-proof importer/runner/verifier/adversarial tests.
5. Run full `pytest`.
6. Run `ruff check .`.
7. Run `mypy src tests`.
8. Obtain exact-head GitHub CI when Actions runners execute. If Actions still fail before steps start, record `CI_BLOCKED_ACCOUNT` and provide independent exact-head validation rather than claiming green CI.
9. Set `READY_FOR_LEAD_REVIEW` / `REVIEW`, push one coherent current-main batch, and stop implementation changes for lead review.

Do **not** use private candidate/resume inputs or execute the genuine proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Canonical Lane 1 heartbeat:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one Lane 1 watcher

Latest verified heartbeat remains #18 at `2026-09-21T19:18:36Z`; it is stale. Before restarting, verify the prior watcher process is not still running. Never create a duplicate.

Issue #7 automated heartbeat posting remains blocked by GitHub Actions runner startup failure (`steps: []`, `runner_id: 0`). Keep truthful Git heartbeat evidence and do not rewrite heartbeat semantics to work around an account-level runner outage.

# Active Work Queue

Owner completion rule:
No version is COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass.

Authoritative execution model: **exactly three active implementation lanes**.

- Lane 1 — `worker/v14-real-proof` — P0 V1.4 proof-tool integrity, then genuine real proof.
- Lane 2 — `worker/v15-assisted-application` — preserve accepted A-R15-01..05; current A-R15-06..09; no V1.6 until gates pass.
- Lane 3 — `worker/recruiting-ops` — preserve accepted B repair batch; verify integrated baseline and repair only evidence-backed regressions.

Old Lane C/D/Scout remain paused/superseded. `worker-pc` is bounded support infrastructure only.

## P0 — Lane 1 / A-V14-P0A-INTEGRITY

Status: **REWORK**.
V1.4 is **NOT COMPLETE**.

Latest Lane 1 branch evidence:
- substantive repair: `5e5058461d5371f292c93e0c53cb0b93caba7e44`
- branch head: `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- later commits are heartbeat-only through #18 at `2026-09-21T19:18:36Z`
- PR #8 remains draft/non-mergeable and materially diverged from main.

### Reviewed worker-pc support branch

Task:
- `jobs-v14-p0a-remaining-fix-20260921-1545`

Returned:
- branch `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- commit `062ca922c640d964220b550a06f61288b9a040c9`

Lead inspection confirms it usefully implements:
- mandatory fail-closed proof DB validation,
- persisted packet/resume/artifact graph checks,
- persisted Greenhouse `JobSource`/`Job` attestation checks,
- focused adversarial tests.

It is **support input only**, not accepted:
- no exact-head CI,
- no worker-side pytest/Ruff/mypy,
- verifier/tests currently require a stronger `source_payload_json` than the real importer writes.

### Newly verified importer/verifier mismatch

Current production `scripts/import_v14_proof_job.py::_source_payload()` persists:
- `api_url`,
- `fetched_at_utc`,
- `content_sha256`,
- `screening_question_count`,
- `source_kind`.

Support commit `062ca922...` additionally expects payload fields:
- `provider`,
- `public_job_id`,
- `question_list_sha256`.

Provider/public job identity already exist in `JobSourceModel.provider` / `source_job_id`; the real importer does not persist a question-list SHA. The support tests hand-construct a richer Greenhouse payload than production creates.

A genuine production import can therefore fail the support verifier despite valid real inputs. P0A cannot be accepted until the importer/verifier contract is reconciled.

### Immediate Lane 1 assignment

1. Verify the stale Lane 1 watcher is dead; synchronize/clean-port P0A code onto latest main.
2. Adapt the useful `062ca922...` DB/source-binding changes rather than blindly merging the support branch.
3. Bind Greenhouse provider/public job identity to persisted `JobSourceModel` columns and make question-list SHA/count durably production-derived/persisted.
4. Ensure source kind/API URL/fetched time/content SHA/canonical URL and linked Job identity are independently verified against the actual importer output.
5. Add a production-contract integration test that uses the real importer payload shape/helper; do not rely on a hand-authored richer payload.
6. Required adversarial cases: missing/unopenable/unrelated/tampered DB, packet/resume/artifact mismatch, forged source ID/URL/fetch/content/questions, changed questions after persistence, forged local attestation.
7. Run focused importer/runner/verifier tests + full `pytest` + `ruff check .` + `mypy src tests`.
8. If hosted Actions still fail before steps start, record `CI_BLOCKED_ACCOUNT`; do not claim CI green.
9. Start exactly one Lane 1 `FIVE_MIN_2026_09_21` watcher and push one coherent `READY_FOR_LEAD_REVIEW` batch.
10. Do not use private candidate/resume inputs or run the genuine proof until ChatGPT accepts P0A.

A bounded read-only worker-pc audit `jobs-v14-p0a-importer-contract-audit-20260921-1645` has been dispatched. Lane 1 must not wait for it.

## Lane 2 — V1.5 assisted application

Branch:
- `worker/v15-assisted-application`
- PR #2 draft/non-mergeable
- head `ddb4f848a97dec87033cfdef7ca33642480d99bc`

Scope:
- preserve lead-accepted A-R15-01..05,
- current work A-R15-06..09 only,
- no V1.6 until gates pass or owner/lead explicitly authorizes it.

Immediate assignment:
1. stop/verify stopped the old DAYWATCH watcher once,
2. sync/rebase latest main without unrelated coordination churn,
3. start exactly one Lane 2 `FIVE_MIN_2026_09_21` watcher,
4. run focused assisted-safety adversarial tests + full pytest/Ruff/mypy,
5. request lead review on one coherent batch.

Known V1.4 proof blocker on this machine remains the missing genuine selected `resume_ai_software_engineer` mapping. Never substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is already merged. Accepted/integrated scope includes:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- B-R20-05 / J20-14,
- B-R20-01,
- B-R20-02.

Worker branch head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main.

Immediate assignment:
1. stop/verify stopped any old DAYWATCH watcher,
2. sync latest main,
3. start exactly one Lane 3 `FIVE_MIN_2026_09_21` watcher,
4. run targeted worker/health/dashboard tests plus full pytest/Ruff/mypy,
5. verify integrated accepted semantics,
6. repair only a real evidence-backed regression,
7. if new worker commits become ahead of main and no PR exists, ChatGPT creates a draft PR automatically.

## Heartbeat standard

For Lane 1/2/3:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- interval 5 minutes,
- exactly one watcher per active lane,
- no proving/watch/hourly transitions.

Issue #7 is the user-visible progress surface. Each worker heartbeat should comment there when Actions infrastructure is available. ChatGPT posts one concise lead comment every hourly run.

Current Actions diagnosis remains `CI_BLOCKED_ACCOUNT`: recent jobs fail before steps execute with `runner_id: 0` / `steps: []`. Do not rewrite working heartbeat semantics merely to manufacture comments.

## Real-proof sequence after P0A

1. Lane 1 validates genuine private candidate profile + exact real resume mappings locally.
2. Lane 1 imports the current real OpenSesame AI Automation Engineer job/questions.
3. First genuinely eligible Lane 1 or Lane 2 machine runs importer → production packet runner → verifier.
4. Commit only runtime-generated redacted evidence plus separately generated verifier receipt.
5. ChatGPT accepts only a genuine `REAL_PROOF_PASS`.
6. Only then may V1.4 be marked COMPLETE.

No browser application submission is authorized by this proof.

# Current State

Updated: 2026-09-21 17:00 ET

## Owner completion rule

No version is COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass.

V1.4 engineering remains accepted, but V1.4 is **NOT COMPLETE** until:
1. Lane 1 P0A RP14-T1..T7 proof-tool integrity is lead-accepted, and
2. `A-V14-REAL-PROOF` produces a genuine runtime `REAL_PROOF_CANDIDATE` plus separately bound verifier `REAL_PROOF_PASS` receipt.

No private candidate/resume proof execution is authorized before P0A acceptance.

## Authoritative operating model

Exactly three active implementation lanes:
- Lane 1 — `worker/v14-real-proof` — P0 V1.4 proof integrity / real proof.
- Lane 2 — `worker/v15-assisted-application` — preserve A-R15-01..05; finish A-R15-06..09; no V1.6 until gates pass.
- Lane 3 — `worker/recruiting-ops` — accepted recruiting/reliability batch is merged; verify integrated baseline and repair only evidence-backed regressions.

Old Lane C/D/Scout are paused/superseded. `worker-pc` is bounded support infrastructure only, not a fourth implementation lane.

A conflicting planning commit briefly rewrote canonical files to a one-worker/sequential-surface model. That contradicts the owner's explicit three-lane directive and is superseded. Canonical operating files have been restored to exactly three active lanes. V2.3 planning remains future inventory only.

## Lane 1 — P0 critical path

Observed branch state:
- head `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- latest heartbeat #18 at `2026-09-21T19:18:36Z`
- current-epoch heartbeat stream is stale
- PR #8 is draft/non-mergeable and materially diverged from current main
- latest substantive implementation remains `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Lead verdict: **REWORK** / P0A not accepted.

### worker-pc support evidence

Task `jobs-v14-p0a-remaining-fix-20260921-1545` returned support branch `worker/jobs-v14-p0a-remaining-fix-20260921-1545` at `062ca922c640d964220b550a06f61288b9a040c9`.

Lead-inspected diff is limited to `scripts/verify_v14_real_proof.py` and `tests/test_real_proof_verifier.py` and materially addresses:
- fail-closed mandatory proof DB validation,
- persisted packet/resume/artifact linkage,
- Greenhouse `JobSource`/`Job` source-attestation binding.

It is **not accepted or merge-ready** because no exact-head GitHub CI exists and worker-side pytest/Ruff/mypy were sandbox-blocked.

### Corrected production-path audit

An interim lead note incorrectly compared the support verifier to the older importer on main. Direct inspection of the support/Lane 1 importer plus independent worker-pc audit corrected that finding.

At `062ca922...`, `_source_payload()` already persists `provider`, `public_job_id`, `question_list_sha256`, `api_url`, `fetched_at_utc`, `content_sha256`, `screening_question_count`, and `source_kind`. The importer payload is not the current blocker.

Two real production-path blockers remain:

1. **Generation metadata key mismatch.** Production packet builder writes `generation_metadata_json["generation_origin"]`; support verifier reads `generation_metadata["origin"]`. A genuine production packet therefore fails even when generation metadata is correct, and the verifier tests currently use the non-production shape.
2. **Driver-qualified PostgreSQL URL mismatch.** Support `resolve_proof_db_url()` accepts `postgresql://` / `postgres://`, while application `AppSettings.database_url` defaults to `postgresql+psycopg://...`. A normal application DB URL can therefore be misinterpreted as a SQLite path and fail before persisted proof validation.

A bounded worker-pc support task `jobs-v14-p0a-runtime-contract-fix-20260921-1700` was dispatched to fix only those two issues on top of the existing support branch. Lane 1 must not wait for it and no support branch may auto-merge.

## Lane 2 — V1.5 assisted application

Branch head `ddb4f848a97dec87033cfdef7ca33642480d99bc`; PR #2 remains draft/non-mergeable and diverged from current main.

Heartbeat remains obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `WATCH_15M_24H`
- last check-in `2026-09-21T17:39:16Z`

Immediate action:
- stop/verify stopped old watcher once,
- sync latest main,
- start exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher,
- complete A-R15-06..09 validation and request lead review.

Known V1.4 proof blocker remains the missing genuine selected `resume_ai_software_engineer` mapping on that machine. Do not substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged and the accepted B repair batch is already integrated to main.

Worker branch head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main.

Heartbeat remains obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `PROVING_5M`
- last check-in `2026-09-21T16:44:37Z`

Immediate action:
- stop any old watcher once,
- sync latest main,
- launch exactly one current 5-minute watcher,
- run post-integration verification,
- repair only a real evidenced regression.

## Heartbeat / visible progress

Canonical Lane 1/2/3 standard:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one watcher per active lane
- no cadence transitions

Issue #7 automated heartbeat comments stopped after Lane 1 heartbeat `2026-09-21T18:18:14Z` although commits continued through `19:18:36Z`. Fresh Actions jobs still fail before steps start with `steps: []`, `runner_id: 0`, so classification remains `CI_BLOCKED_ACCOUNT`, not a heartbeat-workflow semantic regression. ChatGPT posts a direct lead update to issue #7 each run.

## Critical path

1. Lane 1 ports the reviewed DB/source-binding support and fixes production `generation_origin` + driver-qualified PostgreSQL URL handling.
2. Lane 1 runs focused importer/runner/verifier adversarial tests plus full pytest/Ruff/mypy and exact-head CI when runners execute.
3. ChatGPT accepts P0A only from coherent reviewed code/test evidence.
4. Lane 1 moves immediately to genuine private profile/resume readiness.
5. First genuinely eligible Lane 1 or Lane 2 machine runs importer → real packet runner → verifier.
6. ChatGPT audits runtime candidate + separately bound PASS receipt.
7. Only then mark V1.4 COMPLETE.

## Future planning

V2.3 planning material is future planning inventory only. Do not reopen V2.3/Scout implementation lanes, collapse the owner-authorized three-lane model, or start V1.6 merely because planning artifacts exist.

## Safety boundary

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate contents in Git, or fabricated candidate facts are authorized.

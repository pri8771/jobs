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
- heartbeat-only commits through #18 at `2026-09-21T19:18:36Z`; stream is stale
- PR #8 remains draft/non-mergeable and materially diverged from main.

### Reviewed worker-pc support branch

Task `jobs-v14-p0a-remaining-fix-20260921-1545` returned branch `worker/jobs-v14-p0a-remaining-fix-20260921-1545` at `062ca922c640d964220b550a06f61288b9a040c9`.

Lead inspection confirms useful support for:
- mandatory fail-closed proof DB validation,
- persisted packet/resume/artifact graph checks,
- persisted Greenhouse `JobSource`/`Job` attestation checks.

It remains **support input only**, not accepted: no exact-head CI and worker-side pytest/Ruff/mypy were sandbox-blocked.

### Corrected production-path findings

The support/Lane 1 importer at `062ca922...` already persists `provider`, `public_job_id`, `question_list_sha256`, `api_url`, `fetched_at_utc`, `content_sha256`, `screening_question_count`, and `source_kind`. An earlier interim note comparing against older main was incorrect; importer payload shape is not the blocker.

Actual blockers:
1. Production packet builder writes `generation_metadata_json["generation_origin"]`, while support verifier reads `generation_metadata["origin"]`; genuine packets therefore fail the verifier and current verifier tests use a non-production metadata shape.
2. Support `resolve_proof_db_url()` accepts `postgresql://` / `postgres://`, while normal `AppSettings.database_url` defaults to `postgresql+psycopg://...`; the real application DB URL can therefore be rejected/misread before DB proof validation.

### Immediate Lane 1 assignment

1. Verify the stale watcher is dead; sync/clean-port the P0A implementation onto latest main.
2. Adapt the useful `062ca922...` DB/source-binding changes.
3. Validate canonical `generation_origin` from real packet-builder metadata; keep any legacy fallback narrow/fail-closed.
4. Accept the actual SQLAlchemy PostgreSQL driver-qualified DB URL form, including `postgresql+psycopg://`, while retaining fail-closed unsupported/SQLite checks.
5. Keep Greenhouse provider/job/questions/content/canonical URL binding against real importer + persisted `JobSourceModel`/`JobModel` evidence.
6. Add focused tests using real production metadata/importer shapes plus adversarial wrong-origin, DB target, packet/resume/artifact, and forged source/question cases.
7. Run focused importer/runner/verifier tests + full `pytest` + `ruff check .` + `mypy src tests`.
8. If hosted Actions still fail before steps start, record `CI_BLOCKED_ACCOUNT`; do not claim CI green.
9. Start exactly one Lane 1 `FIVE_MIN_2026_09_21` watcher and push one coherent `READY_FOR_LEAD_REVIEW` batch.
10. Do not use private candidate/resume inputs or run the genuine proof until ChatGPT accepts P0A.

Worker-pc task `jobs-v14-p0a-runtime-contract-fix-20260921-1700` was dispatched for bounded support on exactly the two runtime-contract blockers. Lane 1 must not wait for it; no support branch auto-merges.

## Lane 2 — V1.5 assisted application

Branch `worker/v15-assisted-application`, head `ddb4f848a97dec87033cfdef7ca33642480d99bc`, PR #2 draft/non-mergeable.

Scope:
- preserve lead-accepted A-R15-01..05,
- current A-R15-06..09 only,
- no V1.6 until gates pass or owner/lead explicitly authorizes it.

Immediate assignment:
1. stop/verify stopped old DAYWATCH watcher once,
2. sync/rebase latest main,
3. start exactly one Lane 2 `FIVE_MIN_2026_09_21` watcher,
4. run focused assisted-safety adversarial tests + full pytest/Ruff/mypy,
5. request lead review on one coherent batch.

Known V1.4 proof blocker on this machine remains the missing genuine selected `resume_ai_software_engineer` mapping. Never substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged. Accepted/integrated scope includes B-R17-03, B-R20-07, B-R20-08, B-R20-05/J20-14, B-R20-01, and B-R20-02.

Worker head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main.

Immediate assignment:
1. stop/verify stopped old DAYWATCH watcher,
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
- no cadence transitions.

Issue #7 is the user-visible progress surface. Worker heartbeats should comment there when Actions infrastructure is available. ChatGPT posts one concise lead comment every hourly run.

Current Actions diagnosis remains `CI_BLOCKED_ACCOUNT`: recent jobs fail before steps execute with `runner_id: 0` / `steps: []`.

## Real-proof sequence after P0A

1. Lane 1 validates genuine private candidate profile + exact real resume mappings locally.
2. Lane 1 imports the current real OpenSesame AI Automation Engineer job/questions.
3. First genuinely eligible Lane 1 or Lane 2 machine runs importer → production packet runner → verifier.
4. Commit only runtime-generated redacted evidence plus separately generated verifier receipt.
5. ChatGPT accepts only a genuine `REAL_PROOF_PASS`.
6. Only then may V1.4 be marked COMPLETE.

No browser application submission is authorized by this proof.

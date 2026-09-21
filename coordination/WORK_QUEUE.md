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

Latest reviewed implementation evidence:
- clean branch `claude/serene-brown-g6uij0`
- substantive commit `3444076de27573ec57d9c8ae60876aece8e646d9`
- direct parent `927b33c0f523950ca206ead1cc2912e19a018184`
- Lane 1 heartbeat branch reached #22 at `2026-09-21T21:31:56Z`, current epoch/mode, worker reports READY_FOR_LEAD_REVIEW
- draft PR #8 remains a review container but carries historical heartbeat/coordination divergence; review the clean implementation commit for code truth.

Lead review confirms the clean-port materially closes the previously identified runtime verifier gaps: candidate/receipt separation, local/candidate SHA binding, mandatory persisted DB evidence, Greenhouse persisted-source binding, copied-example-profile rejection, production `generation_origin`, driver-qualified PostgreSQL URL handling, and re-derived packet/manifest/resume/artifact/DB links.

Worker-reported local validation at `3444076...`: pytest 205 passed; Ruff clean; mypy `src tests` clean; 16 formerly-xfail adversarial probes reported passing. These claims do not equal acceptance.

### Remaining blocker — stale proof schema

At `3444076...`, `coordination/proofs/v14_real_proof.schema.json` still has:
- `additionalProperties: true`, and
- `result.const: REAL_PROOF_PASS`.

This directly violates RP14-T1/RP14-T5. Runtime evidence is a `REAL_PROOF_CANDIDATE`; committed candidate evidence must be closed/allowlisted.

### Immediate Lane 1 assignment

1. Clean-sync the reviewed implementation with latest `main` coordination truth; avoid importing historical heartbeat churn into the implementation diff.
2. Fix `coordination/proofs/v14_real_proof.schema.json`:
   - `additionalProperties: false`,
   - candidate `result` must be `REAL_PROOF_CANDIDATE`,
   - schema fields match the actual runner candidate and verifier allowlist, including current candidate fact, question, and deterministic-generation fields.
3. Add focused schema tests that:
   - accept an actual production-shape candidate,
   - reject an arbitrary extra field,
   - reject candidate evidence that self-declares `REAL_PROOF_PASS`.
4. Re-run focused importer/runner/verifier/schema tests plus full `pytest`, `ruff check .`, and `mypy src tests`.
5. Push one coherent current-main `READY_FOR_LEAD_REVIEW` batch and stop for lead review.
6. Obtain exact-head GitHub CI when hosted Actions execute. If jobs still fail before steps with `runner_id: 0` / `steps: []`, record `CI_BLOCKED_ACCOUNT`; never call that green.
7. Do **not** use private candidate/resume inputs or execute the genuine proof until ChatGPT explicitly accepts P0A.

Bounded support:
- completed runtime-contract support `7e88542b5ce5d8cf1c607a24d8f92399556c15ce` was incorporated into the clean-port,
- new `worker-pc` task `jobs-v14-p0a-schema-gate-20260921-1748` targets only the remaining schema contract and focused tests,
- Lane 1 must not wait for worker-pc and no support branch auto-merges.

## Lane 2 — V1.5 assisted application

Branch `worker/v15-assisted-application`, head `ddb4f848a97dec87033cfdef7ca33642480d99bc`, PR #2 draft/non-mergeable.

Scope:
- preserve lead-accepted A-R15-01..05,
- current A-R15-06..09 only,
- no V1.6 until gates pass or owner/lead explicitly authorizes it.

Current heartbeat remains obsolete:
- `DAYWATCH_2026_09_21`
- `WATCH_15M_24H`
- last check-in `2026-09-21T17:39:16Z`.

Immediate assignment:
1. stop/verify stopped the old watcher once,
2. sync/rebase latest main,
3. start exactly one Lane 2 `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher,
4. run focused assisted-safety adversarial tests + full pytest/Ruff/mypy,
5. request lead review on one coherent A-R15-06..09 batch.

Historical head checks only validate the old heartbeat/progress workflows; they do not establish current-main implementation CI.

Known V1.4 proof blocker on this machine remains the missing genuine selected `resume_ai_software_engineer` mapping. Never substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged. Accepted/integrated scope includes B-R17-03, B-R20-07, B-R20-08, B-R20-05/J20-14, B-R20-01, and B-R20-02.

Worker head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main.

Current heartbeat remains obsolete:
- `DAYWATCH_2026_09_21`
- `PROVING_5M`
- last check-in `2026-09-21T16:44:37Z`.

Immediate assignment:
1. stop/verify stopped the old watcher once,
2. sync latest main,
3. start exactly one Lane 3 `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher,
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

Issue #7 is the user-visible progress surface. Worker heartbeat Git commits remain authoritative liveness evidence when hosted Actions cannot post comments. ChatGPT posts one concise lead comment every hourly run.

Current Actions diagnosis remains `CI_BLOCKED_ACCOUNT`: current Lane 1 heartbeat jobs fail before steps execute with `runner_id: 0` / `steps: []`. Do not rewrite heartbeat semantics merely to create visible activity.

## Real-proof sequence after P0A

1. Lane 1 validates genuine private candidate profile + exact real resume mappings locally.
2. Lane 1 imports the current real OpenSesame AI Automation Engineer job/questions.
3. First genuinely eligible Lane 1 or Lane 2 machine runs importer → production packet runner → verifier.
4. Commit only runtime-generated redacted evidence plus separately generated verifier receipt.
5. ChatGPT accepts only a genuine `REAL_PROOF_PASS`.
6. Only then may V1.4 be marked COMPLETE.

No browser application submission is authorized by this proof.

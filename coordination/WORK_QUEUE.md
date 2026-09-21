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
- Lane 1 heartbeat branch reached #22 at `2026-09-21T21:31:56Z`, then became stale
- draft PR #8 remains a review container but carries historical heartbeat/coordination divergence; review the clean implementation commit for code truth.

Lead review confirms the clean-port materially closes the previously identified runtime verifier gaps: candidate/receipt separation, local/candidate SHA binding, mandatory persisted DB evidence, Greenhouse persisted-source binding, copied-example-profile rejection, production `generation_origin`, driver-qualified PostgreSQL URL handling, and re-derived packet/manifest/resume/artifact/DB links.

Worker-reported local validation at `3444076...`: pytest 205 passed; Ruff clean; mypy `src tests` clean; 16 formerly-xfail adversarial probes reported passing. These claims do not equal acceptance.

### Remaining blocker — stale proof schema in the clean-port

At `3444076...`, `coordination/proofs/v14_real_proof.schema.json` still has:
- `additionalProperties: true`, and
- `result.const: REAL_PROOF_PASS`.

This directly violates RP14-T1/RP14-T5. Runtime evidence is a `REAL_PROOF_CANDIDATE`; committed candidate evidence must be closed/allowlisted.

### Reviewed worker-pc schema support

Task `jobs-v14-p0a-schema-gate-20260921-1748` completed successfully and returned:
- branch `worker/jobs-v14-p0a-schema-gate-20260921-1748`,
- commit `70ef7adc62ab2e9846721e8174a306273f28cbaa`,
- parent `3444076...`.

Lead inspected the actual support diff. It changes only the proof schema, new schema regression tests, and the dev dependency needed to execute JSON-schema semantics. Structurally it:
- closes the top-level allowlist (`additionalProperties: false`),
- pins candidate `result` to `REAL_PROOF_CANDIDATE`,
- pins schema keys to runner-emitted keys and verifier `ALLOWED_TOP_LEVEL_KEYS`,
- includes the current candidate fact/question/generation fields,
- adds tests for production-shape acceptance, extra-field rejection, self-declared PASS rejection, required fields, and invalid deterministic-generation values.

**Support verdict: useful, not accepted/merge-ready.** The worker environment did not execute the test suite and GitHub has zero check-runs for `70ef7adc...`. Lane 1 must adopt/cherry-pick or faithfully reimplement the patch in its coherent current-main batch and prove it with focused/full validation. No support branch auto-merges.

### Immediate Lane 1 assignment

1. Verify the stale Lane 1 watcher is dead.
2. Pull latest `main` and start exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher.
3. Clean-sync the reviewed implementation with latest `main` coordination truth; avoid importing historical heartbeat churn into the implementation diff.
4. Adopt or faithfully reimplement reviewed support `70ef7adc...`.
5. Run focused schema/importer/runner/verifier tests plus full `pytest`, `ruff check .`, and `mypy src tests`.
6. Push one coherent current-main `READY_FOR_LEAD_REVIEW` batch and stop for lead review.
7. Obtain exact-head GitHub CI when hosted Actions execute. If jobs still fail before steps with `runner_id: 0` / `steps: []`, record `CI_BLOCKED_ACCOUNT`; never call that green.
8. Do **not** use private candidate/resume inputs or execute the genuine proof until ChatGPT explicitly accepts P0A.

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

Current Actions diagnosis remains `CI_BLOCKED_ACCOUNT`: current Lane 1 heartbeat jobs and latest main CI fail before steps execute with `runner_id: 0` / `steps: []`. Do not rewrite heartbeat semantics merely to create visible activity.

## Real-proof sequence after P0A

1. Lane 1 validates genuine private candidate profile + exact real resume mappings locally.
2. Lane 1 imports the current real OpenSesame AI Automation Engineer job/questions.
3. First genuinely eligible Lane 1 or Lane 2 machine runs importer → production packet runner → verifier.
4. Commit only runtime-generated redacted evidence plus separately generated verifier receipt.
5. ChatGPT accepts only a genuine `REAL_PROOF_PASS`.
6. Only then may V1.4 be marked COMPLETE.

No browser application submission is authorized by this proof.

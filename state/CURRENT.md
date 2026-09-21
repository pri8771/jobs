# Current State

Updated: 2026-09-21 17:58 ET

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

## Lane 1 — P0 critical path

Latest heartbeat branch evidence:
- head `df4045883c1fde7b29af92a20028d3b6397e9a93`
- heartbeat #22 at `2026-09-21T21:31:56Z`
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- worker reports `READY_FOR_LEAD_REVIEW`

**Current liveness:** stale. More than three expected 5-minute intervals elapsed after #22 with no newer heartbeat commit. Before Lane 1 resumes implementation, verify the old watcher is dead, pull latest main, and start exactly one current-epoch watcher.

Substantive clean implementation:
- branch `claude/serene-brown-g6uij0`
- commit `3444076de27573ec57d9c8ae60876aece8e646d9`
- direct parent `927b33c0f523950ca206ead1cc2912e19a018184` (reviewed main at implementation start)

Lead verdict: **REWORK** / P0A not accepted.

### What the clean-port materially fixes

Lead inspection confirms the clean-port now implements the intended fail-closed proof chain across the runner/verifier path:
- runtime candidate vs independent PASS/FAIL receipt separation,
- candidate-SHA and proof-run binding,
- local artifact/hash cross-binding,
- mandatory persisted DB linkage,
- persisted Greenhouse JobSource/Job/question corroboration,
- copied example-profile content rejection,
- canonical production `generation_origin` validation,
- `postgresql+psycopg://` support,
- re-derived packet/manifest/resume/artifact/database links.

Worker reports exact-head local validation at `3444076...`: 205 pytest passing, Ruff clean, mypy `src tests` clean, plus 16 formerly-xfail adversarial probes passing. These are useful claims but are not lead acceptance by themselves.

### Remaining P0A blocker — schema contract

`coordination/proofs/v14_real_proof.schema.json` was not included in the clean-port and remains stale at `3444076...`:
- `additionalProperties: true`,
- `result.const: REAL_PROOF_PASS`.

Repository search found no existing test referencing `v14_real_proof.schema.json`, so the schema drift is not protected by the reviewed test suite.

That conflicts directly with RP14-T1/RP14-T5. Runtime evidence is a `REAL_PROOF_CANDIDATE`, and committed candidate evidence must be closed/allowlisted.

Lane 1 must correct the schema to the actual production candidate shape, add regression tests that reject extra fields and self-declared PASS candidates, rerun focused/full pytest/Ruff/mypy, and push one coherent current-main review batch.

### CI state

No GitHub check runs exist for substantive commit `3444076...`.

The latest Lane 1 heartbeat head still triggers Actions jobs that fail before executing any steps (`steps: []`, `runner_id: 0`). Latest main CI shows the same startup failure. Treat this as `CI_BLOCKED_ACCOUNT`, not green CI and not a code failure. Automated issue #7 heartbeat comments therefore remain behind the actual Git heartbeat stream.

`worker-pc` completed the prior runtime-contract support task at `7e88542...`; Lane 1 incorporated that work into the clean-port. Bounded schema-only support task `jobs-v14-p0a-schema-gate-20260921-1748` is now executing on actual `worker-pc` from the clean implementation branch. It is support only; no auto-merge and Lane 1 must not wait for it.

## Lane 2 — V1.5 assisted application

Branch head `ddb4f848a97dec87033cfdef7ca33642480d99bc`; PR #2 remains draft/non-mergeable and diverged from current main.

Heartbeat is still obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `WATCH_15M_24H`
- last check-in `2026-09-21T17:39:16Z`

Immediate action:
- stop/verify stopped the old watcher once,
- sync latest main,
- start exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher,
- complete A-R15-06..09 validation and request lead review.

Historical head checks only cover heartbeat validation/progress posting. They do not substitute for current-main implementation CI.

Known V1.4 proof blocker remains the missing genuine selected `resume_ai_software_engineer` mapping on that machine. Do not substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged and the accepted B repair batch is already integrated to main.

Worker branch head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main. Its historical branch checks were green before merge.

Heartbeat is still obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `PROVING_5M`
- last check-in `2026-09-21T16:44:37Z`

Immediate action:
- stop any old watcher once,
- sync latest main,
- launch exactly one current 5-minute watcher,
- run post-integration verification,
- repair only a real evidenced regression.

No draft PR is needed until Lane 3 has new worker commits ahead of main.

## Heartbeat / visible progress

Canonical Lane 1/2/3 standard:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one watcher per active lane
- no cadence transitions

Lane 1 Git heartbeat commits reached #22, but that stream is now stale. Issue #7 automated comments have not kept pace because heartbeat workflows fail at hosted-runner startup. Do not alter the protocol to manufacture UI activity. ChatGPT posts one direct lead update to issue #7 each hourly run.

## Critical path

1. Lane 1 restarts one canonical watcher after confirming the stale watcher is dead.
2. Lane 1 fixes the stale proof schema to match the production candidate contract and adds schema adversarial tests.
3. Lane 1 reruns focused + full pytest/Ruff/mypy and obtains exact-head branch CI when runners execute.
4. ChatGPT accepts P0A only from coherent reviewed code/test/CI evidence.
5. Lane 1 moves immediately to genuine private profile/resume readiness.
6. First genuinely eligible Lane 1 or Lane 2 machine runs importer → real packet runner → verifier.
7. ChatGPT audits runtime candidate + separately bound PASS receipt.
8. Only then mark V1.4 COMPLETE.

## Future planning

V2.3 planning material remains future inventory only. Do not reopen V2.3/Scout implementation lanes, collapse the owner-authorized three-lane model, or start V1.6 merely because planning artifacts exist.

## Safety boundary

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate contents in Git, or fabricated candidate facts are authorized.

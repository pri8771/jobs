# Current State

Updated: 2026-09-21 18:03 ET

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

**Current liveness:** stale. Multiple expected 5-minute intervals elapsed after #22 with no newer heartbeat commit. Before Lane 1 resumes implementation, verify the old watcher is dead, pull latest main, and start exactly one current-epoch watcher.

Substantive clean implementation:
- branch `claude/serene-brown-g6uij0`
- commit `3444076de27573ec57d9c8ae60876aece8e646d9`
- direct parent `927b33c0f523950ca206ead1cc2912e19a018184`.

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

At clean-port commit `3444076...`, `coordination/proofs/v14_real_proof.schema.json` remains stale:
- `additionalProperties: true`,
- `result.const: REAL_PROOF_PASS`.

That conflicts directly with RP14-T1/RP14-T5. Runtime evidence is a `REAL_PROOF_CANDIDATE`, and committed candidate evidence must be closed/allowlisted.

### Reviewed worker-pc schema support

Task `jobs-v14-p0a-schema-gate-20260921-1748` completed successfully and returned:
- branch `worker/jobs-v14-p0a-schema-gate-20260921-1748`,
- commit `70ef7adc62ab2e9846721e8174a306273f28cbaa`,
- parent `3444076...`.

Lead inspected the actual Jobs diff. It changes only the proof schema, a new `tests/test_real_proof_schema.py`, and `pyproject.toml` to add the `jsonschema` dev dependency. Structurally it closes the identified schema gap and pins schema keys to runner-emitted keys + verifier allowlist, with tests for production candidate acceptance, extra-field rejection, self-declared PASS rejection, missing required fields, and invalid deterministic-generation values.

**Support patch is not accepted/merge-ready.** The worker did not execute the tests in its environment and GitHub has zero check-runs for `70ef7adc...`. Lane 1 must adopt/cherry-pick or faithfully reimplement the patch in a coherent current-main batch and run focused/full validation.

### CI state

No GitHub check runs exist for substantive `3444076...` or support `70ef7adc...`.

Latest Lane 1 heartbeat jobs and latest main CI both fail before executing any steps (`steps: []`, `runner_id: 0`). Treat this as `CI_BLOCKED_ACCOUNT`, not green CI and not a code failure. Automated issue #7 heartbeat comments therefore remain behind actual Git heartbeat evidence.

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

Known V1.4 proof blocker remains the missing genuine selected `resume_ai_software_engineer` mapping on that machine. Do not substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged and the accepted B repair batch is already integrated to main.

Worker branch head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b` is 0 commits ahead and stale/behind main. Its historical branch CI/checks were green before merge.

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
- no cadence transitions.

Lane 1 Git heartbeat commits reached #22, but that stream is stale. Issue #7 automated comments have not kept pace because heartbeat workflows fail at hosted-runner startup. ChatGPT posted the required lead heartbeat and a liveness correction this run.

## Critical path

1. Lane 1 confirms the stale watcher is dead, pulls latest main, and starts exactly one canonical watcher.
2. Lane 1 adopts/reimplements reviewed support `70ef7adc...` into the clean current-main P0A batch.
3. Lane 1 runs focused schema/importer/runner/verifier tests + full pytest/Ruff/mypy.
4. Exact-head CI must execute green; if hosted runners remain unavailable, record `CI_BLOCKED_ACCOUNT` and keep P0A unaccepted.
5. ChatGPT accepts P0A only from coherent reviewed code/test/CI evidence.
6. Lane 1 moves immediately to genuine private profile/resume readiness.
7. First genuinely eligible Lane 1 or Lane 2 machine runs importer → real packet runner → verifier.
8. ChatGPT audits runtime candidate + separately bound PASS receipt.
9. Only then mark V1.4 COMPLETE.

## Future planning

V2.3 planning material remains future inventory only. Do not reopen V2.3/Scout implementation lanes, collapse the owner-authorized three-lane model, or start V1.6 merely because planning artifacts exist.

## Safety boundary

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate contents in Git, or fabricated candidate facts are authorized.

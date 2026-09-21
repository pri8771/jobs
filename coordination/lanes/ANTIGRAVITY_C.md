# Antigravity Lane C Status

Branch: `worker/live-data-foundations`
Lane: Real Data / Candidate Provenance / Gmail Foundations
Owner: Antigravity Session C
Reviewer: ChatGPT

## Immediate P0A — V1.4 proof-tool integrity

Start from latest `main` and execute only the production proof-tool hardening for artifact `A-V14-REAL-PROOF` before any private candidate/resume proof work.

Authoritative audit: `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Tasks:
- RP14-T1 SP2 — runner emits `REAL_PROOF_CANDIDATE`; verifier emits separately candidate-bundle-bound PASS/FAIL receipts, including FAIL receipts for rejected candidates.
- RP14-T2 SP2 — local/private bundle SHA + `proof_run_id` cross-binding.
- RP14-T3 SP3 — bind JobModel/questions to the approved current Greenhouse fetch/attestation.
- RP14-T4 SP2 — reject copied/renamed example candidate profiles by content evidence.
- RP14-T5 SP1 — explicit committed-evidence allowlist; reject arbitrary extra fields.
- RP14-T6 SP1 — unambiguous deterministic-production generation labeling.
- RP14-T7 SP2 — independently verify packet/manifest/resume-variant/artifact cross-links.

Required evidence:
- forged structurally-valid proof rejected,
- unrelated local artifacts rejected,
- fake/unapproved job/question data rejected,
- copied example candidate data rejected,
- arbitrary extra evidence fields rejected,
- deterministic generation honestly represented,
- broken packet/artifact links rejected,
- targeted tests + full pytest/Ruff/mypy/CI green.

Scope: proof scripts, proof schema, proof-tooling tests, minimal directly related docs. Do not use private candidate/resume inputs during P0A and do not execute the actual proof yet.

Push one coherent batch with a worker-authored heartbeat marked `READY_FOR_LEAD_REVIEW`, then stop for Scout/ChatGPT review. Do not self-accept.

## Current lead review — 2026-09-21 10:53 ET

Lane C is still at `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored current-epoch heartbeat and no RP14-T1..T7 implementation. Rebase latest main before work. This remains the project critical path.

Current heartbeat epoch is `DAYWATCH_2026_09_21`; Lane C's latest branch commit is 10:49Z, before the 14:45Z epoch reset, so its verified proving state is 0/3. A fresh session must launch:

`python scripts/worker_heartbeat_watch.py --lane C --epoch DAYWATCH_2026_09_21 --detach`

Lane A is still not an eligible real-proof executor because its selected real resume variant `resume_ai_software_engineer` has no actual mapped file on that machine. Its early proof attempt was before P0A acceptance and cannot count. Do not wait for Lane A after P0A if Lane C has the complete genuine inputs.

## Reviewed RP14-T5 remote support

Remote task `jobs-v14-p0a-t5-schema-20260921-0946` completed and returned a real Jobs branch:
- branch: `worker/jobs-v14-p0a-t5-schema-20260921-0946`
- commit: `1f4a9b9bd21ed402afaef211ac3cab852a293a22`
- base: `79ae33852bb742a6714836b824d666a636bfc333`

ChatGPT inspected the actual commit/diff. It is bounded to exactly three files:
- `coordination/proofs/v14_real_proof.schema.json`
- `scripts/verify_v14_real_proof.py`
- `tests/test_real_proof_verifier.py`

The support change closes top-level and nested evidence allowlists, explicitly admits the legitimate runtime fields `candidate_unresolved_fact_categories` and `questions_count`, rejects unexpected top-level/nested fields and non-count/private-shaped nested values, and adds focused RP14-T5 adversarial tests.

**Do not treat RP14-T5 as accepted yet.** The remote free-text report says pytest/Ruff/mypy execution was blocked by its command permission layer, and GitHub has no Jobs CI workflow run for commit `1f4a9b9...`. The outer worker did commit/push the branch, but its generic result `tests` array is not test evidence. The branch is also behind current main.

Lane C may cherry-pick `1f4a9b9...` after rebasing current main, resolve any conflict, and include the code in its coherent RP14-T1..T7 batch. Lane C remains responsible for running the focused verifier/schema tests plus full pytest/Ruff/mypy/CI. Reimplementation is also acceptable if cleaner. No automatic merge.

A separate remote RP14-T6-only support dispatch `jobs-v14-p0a-t6-origin-20260921-1047` failed almost immediately at workflow `35615000944`; no sanitized result or Jobs branch was available at review time. Do not wait for it and do not credit T6 progress.

## Branch maintenance performed by lead

At the 2026-09-21 06:46 ET lead review, this branch was 165 commits behind main and contained only two unique lead-seeded heartbeat commits. ChatGPT inspected both and confirmed they contained no worker implementation or worker-authored heartbeat. The branch was force-aligned to green Jobs main at that time.

That alignment was maintenance only. It is not worker activity, does not count toward heartbeat proving, and completes no RP14 task.

## After P0A lead acceptance — real proof readiness

### RP14-C1 SP2
Locate and validate the actual private candidate profile and actual resume-source mappings locally. Do not use `config/candidate_profile.example.yaml`, temp/synthetic resumes, or commit private contents. Hash actual resume bytes and emit only redacted readiness evidence.

### RP14-C2 SP2
Import/validate the current OpenSesame AI Automation Engineer JobModel/source/questions using the public Greenhouse source and `scripts/import_v14_proof_job.py`.

### RP14-C3 SP1
Confirm the production packet path has a non-mock generation route. `DeterministicModelGateway` is acceptable only when labeled honestly as deterministic production generation. If unavailable, report `REAL_PROOF_BLOCKED_PROVIDER`; never silently fall back to mock.

## Proof execution after readiness

If this machine has the real private profile + actual mapped resume bytes after P0A acceptance, execute RP14-E1/E2 immediately; do not wait for Lane A merely because Lane A owns packet implementation.

Use the commands in `docs/V1_4_REAL_PROOF_RUNBOOK.md`. Push only runtime-generated redacted candidate evidence plus the independently generated verifier receipt. Private full evidence stays in `.local/proofs/`.

If private inputs are absent, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; never synthesize substitutes.

## After the V1.4 proof attempt

Candidate provenance:
- J12-01 SP2 candidate fact provenance records
- J12-02 SP2 `allowed_for_application` enforcement
- J12-03 SP1 private-safe provenance report CLI

Then Gmail readiness:
- J20G-01 SP2 partial Gmail fetch fails closed / no checkpoint advance
- J20G-02 SP2 safe persistent OAuth/runtime wiring
- J20G-03 SP2 typed secret-free REAL-Gmail readiness diagnostic

J20G-04 remains Lane B after J20G-03 lead acceptance.

## External boundary

Do not perform real OAuth consent, access a live mailbox, open/prefill/submit a real application, send external messages, bypass MFA/CAPTCHA, fabricate candidate facts, or commit private candidate/resume contents.

## Status

P0A PROOF-TOOL INTEGRITY — READY FOR WORKER IMPLEMENTATION
Heartbeat epoch: `DAYWATCH_2026_09_21`, verified 0/3 current-epoch worker-authored check-ins.
Latest lead review: 2026-09-21 10:53 ET.

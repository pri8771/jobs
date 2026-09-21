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

## Current lead review — 2026-09-21 09:55 ET

Lane C is still at `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored heartbeat and no RP14-T1..T7 implementation. Rebase latest main before work. This remains the project critical path.

Lane A is still not an eligible real-proof executor because its selected real resume variant `resume_ai_software_engineer` has no actual mapped file on that machine. Its early proof attempt was before P0A acceptance and cannot count. Do not wait for Lane A after P0A if Lane C has the complete genuine inputs.

A bounded remote support task has been queued for **RP14-T5 only**:
- task: `jobs-v14-p0a-t5-schema-20260921-0946`
- scope: proof evidence schema + adversarial extra-field tests only
- no private candidate/resume data, Gmail, browser/application behavior, or acceptance-state writes
- no automatic merge

A non-Jobs SwarmAI task started moments before that Jobs dispatch became visible, so the capacity-1 worker has the Jobs task pending behind it. This is support only. **Do not wait for the remote task and do not assume RP14-T5 is done.** If the remote task eventually returns a Jobs branch/commit, ChatGPT will inspect it before Lane C adopts any change.

## Branch maintenance performed by lead

At the 2026-09-21 06:46 ET lead review, this branch was 165 commits behind main and contained only two unique lead-seeded heartbeat commits (`4122f9bd...` and `2ce7674f...`). ChatGPT inspected both commits and confirmed they contained no worker implementation or worker-authored heartbeat. The branch was therefore force-aligned to green Jobs main so this lane saw the then-current P0A contract and validation workflows.

This alignment is maintenance only. It is not worker activity, does not count toward heartbeat proving, and completes no RP14 task.

## Prior remote-worker support — unavailable as reviewable code

The bounded TESTS-ONLY support task `jobs-v14-p0a-adversarial-tests-20260921-0642` / workflow `35590523591` completed with failure at the target Jobs branch-push step.

Result:
- no Jobs branch returned,
- no commit returned,
- no tests or summary returned,
- no corresponding Jobs worker branch exists,
- remote-workers successfully published only the sanitized failure result afterward.

Do not depend on that attempt. It completed no RP14 work.

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
Heartbeat proving: 0/3 worker-authored check-ins.
Latest lead review: 2026-09-21 09:55 ET.

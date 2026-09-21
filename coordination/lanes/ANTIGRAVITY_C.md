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

## Branch maintenance performed by lead

At the 2026-09-21 06:46 ET lead review, this branch was 165 commits behind main and contained only two unique lead-seeded heartbeat commits (`4122f9bd...` and `2ce7674f...`). ChatGPT inspected both commits and confirmed they contained no worker implementation or worker-authored heartbeat. The branch was therefore force-aligned to green Jobs main so this lane now sees the current P0A contract and validation workflows.

This alignment is maintenance only. It is not worker activity, does not count toward heartbeat proving, and completes no RP14 task.

## Remote-worker support — do not duplicate production code

`worker-pc` became free after non-Jobs workflow `35580580156` completed with failure. ChatGPT dispatched bounded task `jobs-v14-p0a-adversarial-tests-20260921-0642` / workflow `35590523591` from Jobs main.

That task is TESTS ONLY. It may return adversarial acceptance tests for the known P0A gaps but is forbidden from modifying production proof scripts/schema/docs/coordination/private data/Gmail/browser code. Treat any returned tests as untrusted review input until ChatGPT/Scout inspect the actual branch/diff. Continue production RP14-T1..T7 work; do not wait for the remote test task.

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
Latest lead review: 2026-09-21 06:46 ET.

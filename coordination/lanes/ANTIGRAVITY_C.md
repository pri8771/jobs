# Antigravity Lane C Status

Branch:
- worker/live-data-foundations

Lane:
- Real Data / Candidate Provenance / Gmail Foundations

Owner:
- Antigravity Session C

Reviewer:
- ChatGPT

## Immediate P0A — V1.4 proof-tool integrity

Before any private candidate/resume proof work, rebase latest `main` and execute the proof-tool hardening gate for artifact `A-V14-REAL-PROOF`.

Authoritative audit:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Required bounded tasks:
- RP14-T1 SP2 runtime emits `REAL_PROOF_CANDIDATE`; verifier emits a separate candidate-bundle-bound PASS/FAIL receipt
- RP14-T2 SP2 local private bundle SHAs cross-match redacted evidence fields and proof_run_id
- RP14-T3 SP3 JobModel/questions bind to the actual approved current Greenhouse fetch/attestation
- RP14-T4 SP2 reject copied/renamed example candidate profiles using content evidence
- RP14-T5 SP1 explicit redacted-evidence allowlist / no arbitrary extra fields
- RP14-T6 SP1 unambiguous deterministic-generation labeling
- RP14-T7 SP2 independently verify packet/manifest/resume-variant/artifact cross-links

Required verification:
- forged/hand-authored structurally valid proof is rejected,
- unrelated local artifacts cannot satisfy the redacted hashes,
- fake JobModel/questions cannot satisfy the approved live-source binding,
- copied example candidate data is rejected,
- targeted proof-integrity tests pass,
- full pytest, Ruff, mypy, and CI pass.

Scope:
- proof scripts,
- proof schema,
- proof-tooling tests,
- minimal directly related docs.

Do NOT use private candidate/resume inputs during this batch and do NOT execute the actual real proof yet.

Push one coherent batch with a worker-authored heartbeat marked READY_FOR_LEAD_REVIEW, then stop for Scout/ChatGPT review. Workers do not self-accept P0A.

## P0 — V1.4 real proof readiness after P0A acceptance

Only after ChatGPT accepts RP14-T1..T7:

### RP14-C1 — SP2
Locate and validate the real private candidate profile used by the project and the actual resume-source mappings on the local machine.

Requirements:
- do not use config/candidate_profile.example.yaml,
- do not create a temp/synthetic resume,
- do not commit private resume/profile contents,
- verify exact source files exist,
- hash actual resume bytes,
- report only redacted source/provenance/hash metadata.

### RP14-C2 — SP2
Create/import the real proof JobModel/source from the current approved OpenSesame AI Automation Engineer posting:

https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Use current public posting data, not a fixture.

This task does NOT authorize opening/submitting the application.

### RP14-C3 — SP1
Verify the production packet path has a non-mock generation route available.

Acceptable:
- configured real external model provider,
- configured local production model provider,
- deterministic production generation path explicitly represented as non-mock.

Forbidden:
- MockModelGateway,
- HallucinatingModelGateway,
- test/adversarial_mock origin,
- silent fallback.

If unavailable:
- report REAL_PROOF_BLOCKED_PROVIDER,
- do not substitute mock.

Contracts:
- docs/V1_4_REAL_PROOF_RUNBOOK.md
- docs/REAL_PROOF_ACCEPTANCE_POLICY.md
- coordination/artifacts/A-V14-REAL-PROOF.md

## P0 execution after readiness

After P0A acceptance, if this machine has the real private profile + actual mapped resume bytes, run the proof itself immediately. Do not wait for Lane A merely because Lane A owns packet implementation.

Commands are in docs/V1_4_REAL_PROOF_RUNBOOK.md.

Push only runtime-generated redacted candidate evidence plus the independently generated verifier receipt; private full evidence remains under `.local/proofs/`.

If private inputs are absent, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; never synthesize substitutes.

## After the real-proof attempt

Continue candidate provenance:
- J12-01 SP2 private-safe provenance records
- J12-02 SP2 allowed_for_application enforcement
- J12-03 SP1 provenance report CLI

Then Gmail readiness:
- J20G-01 SP2 partial Gmail fetch fails closed / no checkpoint advance
- J20G-02 SP2 persistent ignored OAuth runtime wiring
- J20G-03 SP2 typed secret-free REAL-Gmail readiness diagnostic

After J20G-03 lead acceptance:
- Lane B gets J20G-04.

## Remote-worker note

The infrastructure-only `worker-pc` Jobs branch-push probe succeeded at commit `b6c800f0ed4ffe8450aceb0021b0c417ac7e16ae`; that probe is not for merge and does not complete any RP14 task. Do not duplicate work with remote-worker tasks if Lane C is actively implementing the same slice.

## External boundary

Do not:
- perform real OAuth consent,
- access live mailbox,
- open/prefill/submit a job application,
- commit private candidate/resume contents.

## Next

1. rebase latest main
2. execute RP14-T1..T7 only
3. run targeted + full verification
4. push one coherent P0A batch + worker heartbeat READY_FOR_LEAD_REVIEW
5. stop for Scout/ChatGPT acceptance
6. only after P0A acceptance execute RP14-C1..C3 and the real proof if real local inputs are available

## Status

P0A PROOF-TOOL INTEGRITY — READY FOR WORKER IMPLEMENTATION

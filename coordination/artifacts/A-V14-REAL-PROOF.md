# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: BLOCKED
- Priority: P0
- Owner: Lane C + Lane A + Scout + ChatGPT lead
- Dependencies: V1.4 engineering implementation accepted; P0A proof-tool integrity gate accepted
- Downstream: V1.4 COMPLETE designation and all future version-complete claims

## Goal

Prove V1.4 once with a real non-mock packet build.

## Default real job

OpenSesame — AI Automation Engineer

Public source:
https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Lead reverified the public posting is live on 2026-09-21 at the current lead check.

No browser prefill/application submission is authorized by this artifact.

## Current blocking gate — P0A proof-tool integrity

Do **not** execute the private-data proof until the proof-verification chain is hardened and lead-accepted.

Authoritative audit:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Required repairs:
- RP14-T1 runtime emits `REAL_PROOF_CANDIDATE`; verifier emits a separately bound PASS/FAIL receipt
- RP14-T2 local private artifact hashes cross-match the committed redacted candidate bundle
- RP14-T3 JobModel/questions bind to the actual current approved Greenhouse source/fetch
- RP14-T4 copied/renamed example candidate profiles are rejected by content evidence, not filename only
- RP14-T5 committed evidence uses an explicit allowlist / no arbitrary extra fields
- RP14-T6 deterministic generation is labeled unambiguously
- RP14-T7 packet/manifest/resume-variant/artifact cross-links are independently verified

Independent remote-worker audit confirmed the two highest-severity issues: a hand-authored structurally valid bundle can pass the current verifier, and the optional local evidence is not cross-bound to the redacted bundle.

Remote worker evidence at the current lead check:
- first hardening task `jobs-v14-proof-hardening-20260920` failed during repository clone before implementation;
- retry `jobs-v14-proof-hardening-r2` ran for approximately 40 minutes but ended `failed` with `Worker branch push failed.`;
- its sanitized result contains no branch, no commit, no tests, and no summary;
- no `worker/jobs-v14-proof-hardening-r2` branch exists in the Jobs repository;
- therefore there is no implementation batch to review or accept from worker-pc yet.

Do not treat the remote-worker attempt as RP14-T1..T7 completion. Before another branch-mode retry, diagnose or repair the remote push path so work is not lost again. The remote control plane remains infrastructure only; Jobs remains authoritative.

Once P0A is lead-accepted, this artifact returns to READY and Lane A or Lane C may execute the real proof immediately on whichever machine has the actual private profile + mapped real resume bytes.

## Current execution readiness after P0A

Main contains the intended one-command proof path:
- `scripts/import_v14_proof_job.py`
- `scripts/run_v14_real_proof.py`
- `scripts/verify_v14_real_proof.py`
- `coordination/proofs/v14_real_proof.schema.json`

The importer reads current public Greenhouse job/question data into the configured local Jobs database and a gitignored questions file.

The runner is intended to:
- reject example/test candidate-profile paths/content,
- resolve and hash the actual selected resume source,
- require a real persisted JobModel/source,
- use the normal `ApplicationPacketBuilder`,
- use `DeterministicModelGateway` as an explicit production-safe non-mock generation path,
- write private artifacts/full evidence under gitignored `.local/proofs/`,
- write only redacted runtime-derived proof evidence under `coordination/proofs/`.

The hardened verifier must reject mock/fixture/forged markers, validate required hashes/privacy invariants, bind the candidate bundle to the local full bundle, verify packet/artifact cross-links, and emit a separately bound verifier receipt.

Current evidence state:
- `coordination/proofs/` contains the schema/readme only,
- no runtime-generated V1.4 proof candidate JSON is committed yet,
- no verifier receipt exists,
- therefore REAL_PROOF has NOT happened and this artifact is BLOCKED on P0A, not ACCEPTED.

## Required real inputs

- actual private candidate profile used by the project
- actual selected resume source file
- actual resume bytes
- live public job posting/snapshot
- real application-question labels from the public posting
- production packet builder
- non-mock model/generation path

## Required output

One runtime-derived redacted candidate evidence record plus one independently generated verifier receipt.

Candidate evidence must include:
- proof_run_id
- run timestamp
- code commit SHA
- public job URL/title/company
- job snapshot hash
- candidate profile version/source class (private local; contents not committed)
- candidate provenance/unresolved-fact summary
- selected resume family/variant/version
- real resume SHA-256 + byte count
- generation engine/origin
- packet ID/hash
- resume artifact SHA
- cover-letter artifact SHA
- manifest SHA
- is_live_ready
- resolved answer count
- unresolved question list/categories
- read-back verification inputs/results that are safe to commit
- explicit `mock_or_fixture_inputs_present: false`

Verifier receipt must include at minimum:
- candidate bundle SHA-256
- verifier code commit SHA
- verification timestamp
- result `REAL_PROOF_PASS|REAL_PROOF_FAIL`
- whether the private local bundle was verified

## Acceptance rules

- actual real candidate/resume/job inputs only
- no example candidate profile
- no temp/synthetic resume
- no mock gateway
- no fake job
- no hand-authored proof JSON
- no browser/application submission required
- unresolved questions are okay when truthfully surfaced
- evidence bundle must be independently reviewable without exposing private content
- P0A proof-tool integrity repairs must be lead-accepted before any private proof can satisfy this artifact
- candidate evidence alone never self-establishes PASS; the verifier receipt and lead review are required

## Task split

### P0A proof-tool integrity — implementation worker
Implement RP14-T1..RP14-T7 from `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`, add adversarial tests, run targeted/full tests plus Ruff/mypy/CI, push a bounded worker branch, and stop for lead review. No private proof execution in this task.

Remote worker-pc may be retried only after its branch-push path is diagnosed/repaired; otherwise assign the same bounded artifact work to a non-conflicting implementation lane rather than losing another completed local batch.

### RP14-C1 — SP2 — Lane C
After P0A acceptance, locate/validate the real private candidate profile and actual resume-source mappings locally.
Do not commit private contents.
Produce redacted readiness evidence or explicitly report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — SP2 — Lane C
After P0A acceptance, import/validate the real OpenSesame JobModel/source/questions from the live Greenhouse public endpoint using the provided importer.

### RP14-C3 — SP1 — Lane C
After P0A acceptance, confirm the proof uses a non-mock production generation route. `DeterministicModelGateway` is an acceptable explicit non-mock path for this packet-preparation proof when labeled as deterministic generation rather than an external model provider.

### RP14-E1 — SP2 — First eligible Lane A or Lane C worker
After P0A acceptance, the first worker machine that has the actual private candidate profile + real resume mapping should execute the proof end-to-end.

Use:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff if the same worker already has all real inputs.
No browser/submission required.

### RP14-E2 — SP2 — Executing worker
Push only the runner-generated redacted candidate evidence JSON plus verifier receipt and a heartbeat requesting review. Private paths/content remain local.

### RP14-S1 — SP2 — Scout
Independently audit the proof candidate + verifier receipt:
- no fixture/mock inputs,
- job is real/current,
- candidate bundle SHA matches the verifier receipt,
- resume/local artifact hashes correspond to runtime artifact evidence,
- generation origin is non-mock,
- packet/artifact hashes and cross-links are internally consistent,
- evidence is runtime-derived,
- private contents are not exposed.

### RP14-L1 — Lead
ChatGPT re-audits candidate evidence, verifier receipt, Scout findings, relevant code/test/CI evidence, and marks A-V14-REAL-PROOF ACCEPTED only if the proof is genuine.

## Completion

V1.4 is COMPLETE only when:
- A-V14-PACKET-SAFETY engineering acceptance remains valid, and
- P0A proof-tool integrity is lead-accepted, and
- A-V14-REAL-PROOF is ACCEPTED from a genuine runtime candidate bundle + independently bound REAL_PROOF_PASS verifier receipt.

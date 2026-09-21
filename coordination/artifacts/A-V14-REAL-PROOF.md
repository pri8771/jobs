# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: READY
- Priority: P0
- Owner: Lane C + Lane A + Scout + ChatGPT lead
- Dependencies: V1.4 engineering implementation accepted
- Downstream: V1.4 COMPLETE designation and all future version-complete claims

## Goal

Prove V1.4 once with a real non-mock packet build.

## Default real job

OpenSesame — AI Automation Engineer

Public source:
https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Lead has verified the public posting is live for the proof target.

No browser prefill/application submission is authorized by this artifact.

## Current execution readiness

Main now contains a one-command proof path:
- `scripts/import_v14_proof_job.py`
- `scripts/run_v14_real_proof.py`
- `scripts/verify_v14_real_proof.py`
- `coordination/proofs/v14_real_proof.schema.json`

The importer reads current public Greenhouse job/question data into the configured local Jobs database and a gitignored questions file.

The runner:
- rejects example/test candidate-profile paths,
- resolves and hashes the actual selected resume source,
- requires a real persisted JobModel/source,
- uses the normal `ApplicationPacketBuilder`,
- uses `DeterministicModelGateway` as an explicit production-safe non-mock generation path,
- writes private artifacts/full evidence under gitignored `.local/proofs/`,
- writes only redacted runtime-derived proof evidence under `coordination/proofs/`.

The verifier rejects mock/fixture markers, validates required hashes/privacy invariants, and can re-hash local artifacts when given the private full bundle.

Current evidence state:
- `coordination/proofs/` contains the schema/readme only,
- no runtime-generated V1.4 proof JSON is committed yet,
- therefore REAL_PROOF has NOT happened and this artifact remains READY, not ACCEPTED.

Latest lead recheck — 2026-09-20 23:42 ET:
- OpenSesame job `7967740` is still live on the public Greenhouse board,
- current main proof-tooling head `9cfd15835f829457f47a19d68caf3043d35fcd21` has successful CI,
- no new Lane A/C proof execution commit or redacted proof JSON has landed,
- no Scout proof audit is possible yet because runtime evidence does not exist.

## Required real inputs

- actual private candidate profile used by the project
- actual selected resume source file
- actual resume bytes
- live public job posting/snapshot
- real application-question labels from the public posting
- production packet builder
- non-mock model/generation path

## Required output

One redacted runtime-derived evidence record with:
- proof_run_id
- run timestamp
- code commit SHA
- public job URL/title/company
- job snapshot hash
- candidate profile version/source class (private local; contents not committed)
- candidate provenance/unresolved-fact summary
- selected resume family/variant/version
- real resume SHA-256 + byte count
- model/gateway provider/model/origin
- packet ID/hash
- resume artifact SHA
- cover-letter artifact SHA
- manifest SHA
- generation origin
- is_live_ready
- resolved answer count
- unresolved question list/categories
- read-back verification result
- explicit `mock_or_fixture_inputs_present: false`
- successful independent verifier result

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

## Task split

### RP14-C1 — SP2 — Lane C
Locate/validate the real private candidate profile and actual resume-source mappings locally.
Do not commit private contents.
Produce redacted readiness evidence or explicitly report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — SP2 — Lane C
Import/validate the real OpenSesame JobModel/source/questions from the live Greenhouse public endpoint using the provided importer.

### RP14-C3 — SP1 — Lane C
Confirm the proof uses a non-mock production generation route. `DeterministicModelGateway` is an acceptable explicit non-mock path for this packet-preparation proof.

### RP14-E1 — SP2 — First eligible Lane A or Lane C worker
The first worker machine that has the actual private candidate profile + real resume mapping should execute the proof end-to-end.

Use:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff if the same worker already has all real inputs.
No browser/submission required.

### RP14-E2 — SP2 — Executing worker
Push only the runner-generated redacted evidence JSON and a heartbeat requesting review. Private paths/content remain local.

### RP14-S1 — SP2 — Scout
Independently audit the proof bundle:
- no fixture/mock inputs,
- job is real/current,
- resume hash corresponds to runtime artifact evidence,
- generation origin is non-mock,
- packet/artifact hashes are internally consistent,
- evidence is runtime-derived,
- private contents are not exposed.

### RP14-L1 — Lead
ChatGPT re-audits evidence and marks A-V14-REAL-PROOF ACCEPTED only if the proof is genuine.

## Completion

V1.4 is COMPLETE only when:
- A-V14-PACKET-SAFETY engineering acceptance remains valid, and
- A-V14-REAL-PROOF is ACCEPTED.

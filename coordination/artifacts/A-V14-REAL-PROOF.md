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

Lead reverified the posting as live on 2026-09-20.

No application/submission is authorized by this artifact.

## Required real inputs

- actual private candidate profile used by the project
- actual selected resume source file
- actual resume bytes
- live public job posting/snapshot
- production packet builder
- non-mock model/generation path

## Required output

One redacted evidence record with:
- proof_run_id
- run timestamp
- code commit SHA
- public job URL/title/company
- job snapshot hash
- candidate profile version/source class (private local; contents not committed)
- candidate provenance summary
- selected resume family/variant/version
- real resume SHA-256 + byte count
- model/gateway provider/model/origin
- packet ID/hash
- resume artifact URI/path redacted as needed + SHA
- cover-letter artifact SHA
- manifest SHA
- generation origin
- is_live_ready
- resolved answer count
- unresolved question list/categories
- read-back verification result
- explicit mock_or_fixture_inputs_present: false
- verifier result

## Acceptance rules

- actual real candidate/resume/job inputs only
- no example candidate profile
- no temp/synthetic resume
- no mock gateway
- no fake job
- no submission required
- unresolved questions are okay when truthfully surfaced
- evidence bundle must be independently reviewable without exposing private content

## Task split

### RP14-C1 — SP2 — Lane C
Locate/validate the real private candidate profile and actual resume-source mappings locally.
Do not commit private contents.
Produce a redacted provenance/input-readiness report.

### RP14-C2 — SP2 — Lane C
Create/import a real JobModel from the verified OpenSesame posting (or another lead-approved live posting if it closes) using real public source data, not a fixture.

### RP14-E1 — SP2 — First eligible Lane A or Lane C worker
The first worker machine that has access to the actual private candidate profile + real resume mapping should execute the proof end-to-end using the production runner.

Use:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ...`

Do not wait for a cross-lane handoff if the same worker already has all real inputs.
No browser/submission required.

### RP14-E2 — SP2 — Executing worker
Emit the redacted machine-readable proof bundle and local artifact hashes/read-back results produced by the proof runner.
The evidence generator must derive values from runtime state, not hard-code them.

### RP14-S1 — SP2 — Scout
Independently audit the proof bundle:
- no fixture/mock inputs,
- job is real/current,
- resume hash corresponds to runtime artifact evidence,
- generation origin is non-mock,
- packet/artifact hashes are internally consistent,
- private contents are not exposed.

### RP14-L1 — Lead
ChatGPT re-audits evidence and marks A-V14-REAL-PROOF ACCEPTED only if the proof is genuine.

## Completion

V1.4 is COMPLETE only when:
- A-V14-PACKET-SAFETY engineering acceptance remains valid, and
- A-V14-REAL-PROOF is ACCEPTED.
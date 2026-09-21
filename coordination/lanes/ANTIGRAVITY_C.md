# Antigravity Lane C Status

Branch:
- worker/live-data-foundations

Lane:
- Real Data / Candidate Provenance / Gmail Foundations

Owner:
- Antigravity Session C

Reviewer:
- ChatGPT

## P0 — V1.4 real proof input readiness

Before Gmail work, execute:

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
Create/import the real proof JobModel/source from the currently live OpenSesame AI Automation Engineer posting:

https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Use real current public posting data, not a fixture.

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

## After RP14-C1..C3

Continue candidate provenance:
- J12-01 SP2 private-safe provenance records
- J12-02 SP2 allowed_for_application enforcement
- J12-03 SP1 provenance report CLI

Then Gmail readiness:
- J20G-01 SP2 partial Gmail fetch fails closed / no checkpoint advance
- J20G-02 SP2 persistent ignored OAuth runtime wiring
- J20G-03 SP2 typed secret-free REAL-Gmail readiness diagnostic

## Handoff

After RP14-C1..C3:
- Lane A performs RP14-A1/A2 real packet build.

After J20G-03 lead acceptance:
- Lane B gets J20G-04.

## External boundary

Do not:
- perform real OAuth consent,
- access live mailbox,
- submit a job application,
- commit private candidate/resume contents.

## Next

1. pull/rebase latest main between coherent batches
2. execute RP14-C1..C3 first
3. push redacted evidence/readiness
4. heartbeat REVIEW when ready
5. continue J12/J20G work only after real-proof readiness batch

## Status

P0 REAL-PROOF READINESS

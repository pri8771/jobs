# A-V14-P0A-INTEGRITY

- Type: proof tooling / integrity
- Phase: V1.4
- Status: IN_PROGRESS
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V14-CLEAN-INTEGRATION, A-V14-REAL-PROOF

## Purpose
Make the proof verifier fail closed against forged/local-only evidence before any private proof run.

## Current source
Latest reviewed repair source:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

## Remaining worker tasks
- R14-P01 SP1 — bind persisted JobSource attestation to local source_attestation.
- R14-P02 SP1 — adversarial JobSource mismatch/omission tests.
- R14-P03 SP1 — targeted + full local checks.
- R14-P04 SP1 — exact-head CI or CI_BLOCKED_ACCOUNT + independent validation request.

## Acceptance
- verifier independently validates Job/JobSource/packet/resume/artifact runtime truth,
- structural/local forged evidence cannot PASS,
- all targeted/full checks pass,
- ChatGPT lead accepts before private proof use.

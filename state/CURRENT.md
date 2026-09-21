# Current State

Updated: 2026-09-20

## Completion policy

Owner directive:
**No version is COMPLETE until at least one real non-mock example succeeds through the actual production path.**

See:
- `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`

## P0A proof-tool integrity

Before using private candidate/resume data for the milestone proof, the proof chain itself must be hardened.

Lead audit:
- docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md

Verified current defect:
- tests/test_real_proof_verifier.py currently accepts a fully hand-authored structurally valid redacted bundle as REAL_PROOF_VALIDATION_PASS.

Required before private proof execution:
- runtime candidate bundle must not self-declare PASS,
- separate verifier receipt bound to bundle SHA,
- local artifact SHAs cross-match redacted evidence,
- job/questions bind to actual current public fetch,
- copied example profile cannot evade filename checks,
- redacted schema disallows arbitrary extra fields,
- packet/manifest/runtime cross-links verified.

## V1.4

Engineering artifact:
- A-V14-PACKET-SAFETY: ACCEPTED
- engineering merge: `8a0cdb4`
- green main CI established for the accepted packet-safety implementation

Version completion:
- NOT COMPLETE
- blocked on A-V14-REAL-PROOF

P0 real-proof target:
- OpenSesame — AI Automation Engineer
- real live public job/questions
- actual private candidate profile
- actual mapped resume source bytes
- production `ApplicationPacketBuilder`
- explicit non-mock generation path
- redacted runtime-derived evidence bundle
- no application submission/browser prefill required

Proof tooling is now present on main:
- `scripts/import_v14_proof_job.py`
- `scripts/run_v14_real_proof.py`
- `scripts/verify_v14_real_proof.py`

Current proof evidence:
- no runtime-generated V1.4 proof JSON is committed under `coordination/proofs/`
- therefore A-V14-REAL-PROOF remains READY, not ACCEPTED

## Lane A

Branch:
- `worker/v15-assisted-application`
- reviewed head: `ed875775122f0d390af6ab15beb378904af2a476`

Lead task-scope accepted A-R15-01..A-R15-05 after actual code/test review.
Worker reports 132 full tests and 27 targeted assisted-safety tests passing locally.

Not integrated/accepted overall:
- branch has no GitHub Actions/check result on the reviewed commit,
- PR #2 is draft/non-mergeable against newer main,
- V1.5 still has post-proof residuals A-R15-06..A-R15-09.

Immediate next:
- pull/rebase current main,
- attempt V1.4 REAL_PROOF immediately if private real profile/resume inputs are present,
- otherwise heartbeat `REAL_PROOF_BLOCKED_PRIVATE_INPUT` rather than substituting fixtures.

## Lane B

Branch:
- `worker/recruiting-ops`

No new worker-authored heartbeat or implementation batch since the previously reviewed repair head during this lead check.
Continue current bounded V1.7/V2.0 residual queue independently.

## Lane C

Branch:
- `worker/live-data-foundations`

No worker-authored heartbeat or implementation batch has landed after the seeded heartbeat instructions.
The branch status still predates the current P0 real-proof instructions and must pull/rebase main.

Immediate next:
1. RP14-C1..C3 real private input/job/generation readiness
2. if this machine has all required real inputs, run RP14-E1/E2 directly
3. only after the proof attempt, continue candidate provenance/Gmail readiness

## Lane D

Branch:
- `worker/v23-foundations`

No worker-authored heartbeat or implementation batch has landed after the seeded heartbeat instructions.
Continue non-conflicting V2.3 foundations when active.

## Scout

Branch:
- `scout/qa-prep`

No worker-authored heartbeat/audit has landed after the seeded heartbeat instructions.
RP14-S1 becomes highest priority immediately when a real-proof JSON appears.

## Heartbeat truth

The proving protocol has NOT yet been demonstrated across all workers.

- Lane A has one worker-authored READY_FOR_LEAD_REVIEW heartbeat at 2026-09-21T02:41:00Z; this is not three consecutive on-time proving heartbeats.
- Lanes B, C, D, and Scout have only lead-seeded heartbeat files and no worker-authored proving entries at the latest check.
- Do not claim STEADY_HOURLY for any of those lanes yet.

## Current official version

**V1.4 is NOT COMPLETE until A-V14-REAL-PROOF receives genuine REAL_PROOF_PASS and lead acceptance.**

Later engineering may continue in parallel, but version-complete claims remain gated by the same real-proof standard.

## Live/user boundaries

V1.4 proof:
- no submission
- no browser prefill
- no Gmail OAuth required
- private candidate/profile/resume data stays local

Future consequential gates remain:
- Gmail OAuth/canary
- exact application-job approval
- login/MFA/CAPTCHA/manual barriers
- external application submission authorization

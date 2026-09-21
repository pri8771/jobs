# Current State

Updated: 2026-09-21

## Completion policy

Owner directive:
**No version is COMPLETE until at least one real non-mock example succeeds through the actual production path.**

See:
- `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`

## Remote worker execution

External control plane:
- `pri8771/remote-workers`

Verified project use:
- worker: `worker-pc`
- worker status record: online, capacity 1
- read-only task `jobs-v14-real-proof-audit-retry-20260920` completed successfully
- independent verdict: CHANGES_REQUIRED
- confirmed highest-severity proof-integrity gaps: forged structurally valid bundles can pass; local evidence is not bound to the redacted bundle
- first branch repair task `jobs-v14-proof-hardening-20260920` failed before implementation because repository clone failed
- retry `jobs-v14-proof-hardening-r2` ran but returned `failed` with `Worker branch push failed.`
- retry sanitized result contains no branch, commit, tests, or summary; no matching Jobs worker branch exists
- no implementation result from either remote branch task is accepted
- do not spend another long worker-pc branch run until the Jobs branch-push path is diagnosed/repaired

The remote-worker control plane remains infrastructure only; Jobs planning/acceptance remains authoritative here.

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

Current P0A status:
- NOT ACCEPTED
- worker-pc implementation attempts did not produce a reviewable branch
- critical-path fallback assigned to Lane C as separate RP14-T1..T7 SP1-SP3 tasks on `worker/live-data-foundations`
- Lane C must rebase current main, implement/test the bounded tooling repairs without private inputs, push one coherent batch, and stop for lead review

## V1.4

Engineering artifact:
- A-V14-PACKET-SAFETY: ACCEPTED
- engineering merge: `8a0cdb4`
- green main CI established for the accepted packet-safety implementation

Version completion:
- NOT COMPLETE
- blocked first on P0A proof-tool integrity acceptance, then on A-V14-REAL-PROOF

P0 real-proof target:
- OpenSesame — AI Automation Engineer
- real live public job/questions
- actual private candidate profile
- actual mapped resume source bytes
- production `ApplicationPacketBuilder`
- explicit non-mock generation path
- redacted runtime-derived candidate evidence + separately bound verifier receipt
- no application submission/browser prefill required

Proof tooling exists on main but is not yet trusted for milestone acceptance until P0A is accepted:
- `scripts/import_v14_proof_job.py`
- `scripts/run_v14_real_proof.py`
- `scripts/verify_v14_real_proof.py`

Current proof evidence:
- no runtime-generated V1.4 proof candidate JSON is committed under `coordination/proofs/`
- no independently bound verifier receipt is committed
- A-V14-REAL-PROOF is therefore BLOCKED on P0A and not ACCEPTED

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
- do not execute private V1.4 REAL_PROOF until P0A is lead-accepted,
- pull/rebase current main between coherent batches,
- after P0A acceptance, attempt V1.4 REAL_PROOF immediately if private real profile/resume inputs are present,
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
The branch status predates the current P0/P0A instructions and must pull/rebase main before new work.

Immediate P0 engineering assignment:
1. implement RP14-T1..T7 from `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md` as separate SP1-SP3 tasks
2. add adversarial proof-integrity tests
3. run targeted tests + full pytest/Ruff/mypy
4. push one coherent branch batch and heartbeat READY_FOR_LEAD_REVIEW
5. stop before private proof execution

After P0A lead acceptance:
1. RP14-C1..C3 real private input/job/generation readiness
2. if this machine has all required real inputs, run RP14-E1/E2 directly
3. only after the proof attempt, continue candidate provenance/Gmail readiness

Do not perform Gmail work before the required real-proof readiness/attempt sequence, and do not run the private proof against the known-vulnerable verifier.

## Lane D

Branch:
- `worker/v23-foundations`

No worker-authored heartbeat or implementation batch has landed after the seeded heartbeat instructions.
Continue non-conflicting V2.3 foundations when active.

## Scout

Branch:
- `scout/qa-prep`

No worker-authored heartbeat/audit has landed after the seeded heartbeat instructions.
Immediate review priority is the Lane C P0A proof-tool hardening batch once it appears; RP14-S1 becomes highest priority once real-proof candidate + verifier evidence exists.

## Heartbeat truth

The proving protocol has NOT yet been demonstrated across all workers.

- Lane A has one worker-authored READY_FOR_LEAD_REVIEW heartbeat at 2026-09-21T02:41:00Z; this is not three consecutive on-time proving heartbeats.
- Lanes B, C, D, and Scout have only lead-seeded heartbeat files and no worker-authored proving entries at the latest check.
- Do not claim STEADY_HOURLY for any of those lanes yet.

## Current official version

**V1.4 is NOT COMPLETE until P0A proof-tool integrity is accepted and A-V14-REAL-PROOF receives a genuine REAL_PROOF_PASS with lead acceptance.**

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

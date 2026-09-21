# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: BLOCKED
- Priority: P0
- Owner: Lane C + Lane A + Scout + ChatGPT lead
- Dependencies: `A-V14-PACKET-SAFETY` engineering accepted; P0A proof-tool integrity accepted
- Downstream: V1.4 COMPLETE designation and every later completed-version claim

## Owner completion rule

A version is not COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass. For V1.4 packet preparation, candidate/profile/resume/job inputs must be real, the normal production packet path must run, no mock/fixture fallback may occur, and committed evidence must be runtime-derived and privacy-safe.

Default target: OpenSesame — AI Automation Engineer
`https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740`

This artifact authorizes packet-preparation proof only. It does not authorize browser prefill, application submission, Gmail OAuth/mailbox access, external messaging, MFA/CAPTCHA bypass, or fabrication of candidate facts.

## P0A proof-tool integrity gate

Private proof execution is forbidden until ChatGPT lead accepts the proof-verification chain.

Authoritative audit: `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Required repairs:
- RP14-T1 SP2 — runner emits `REAL_PROOF_CANDIDATE`; verifier emits a separate candidate-bundle-bound `REAL_PROOF_PASS|REAL_PROOF_FAIL` receipt, including FAIL receipts on rejected candidates.
- RP14-T2 SP2 — local/private bundle hashes cross-bind to the committed redacted candidate and `proof_run_id`.
- RP14-T3 SP3 — JobModel/questions bind to the actual approved current Greenhouse fetch/attestation.
- RP14-T4 SP2 — copied/renamed example candidate profiles are rejected by content evidence, not filename alone.
- RP14-T5 SP1 — committed redacted evidence uses an explicit allowlist and rejects arbitrary extra fields.
- RP14-T6 SP1 — deterministic generation is labeled unambiguously as deterministic production generation, never mock/test or fictitious external-provider output.
- RP14-T7 SP2 — packet/manifest/resume-variant/artifact cross-links are independently re-derived and verified.

Acceptance evidence must include adversarial tests for forged bundles, unrelated local artifacts, fake/unapproved job/question data, copied example profile contents, extra fields, misleading generation metadata, and broken packet/artifact links; targeted tests plus full pytest/Ruff/mypy/CI must be green on the accepted implementation batch.

## Current lead review — 2026-09-21 08:46 ET

- `coordination/proofs/` still contains only `README.md` and `v14_real_proof.schema.json`; there is no runtime `REAL_PROOF_CANDIDATE` and no independently bound verifier receipt. V1.4 remains NOT COMPLETE.
- Lane C remains at `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored heartbeat and no RP14-T1..T7 implementation. P0A remains NOT ACCEPTED.
- Lane A advanced to `f5742f210812cac77d7f9df47c58efbfb886f6e3`. Its current production browser blobs for the already reviewed A-R15-01..A-R15-05 scope are unchanged from the previously accepted task-scope code, and PR #2 current-head CI run #321 passed. This preserves task-scope V1.5 acceptance only; V1.5 remains IN_PROGRESS.
- Lane A also attempted the V1.4 packet proof while P0A was still unaccepted. That attempt cannot count as RP14-E1/E2 or acceptance evidence because this artifact explicitly forbids private proof execution before P0A lead acceptance.
- The early attempt did expose a truthful local input blocker: the real profile selected resume variant `resume_ai_software_engineer`, but Lane A had no actual file mapped for that selected variant; only `enterprise_automation_solutions_architect.md` was present. The runner failed closed and no substitute resume was synthesized. Treat Lane A as `REAL_PROOF_BLOCKED_PRIVATE_INPUT` unless a genuine intended resume mapping is available after P0A.
- Lane A's latest heartbeat claims `consecutive_on_time: 2`, but its preserved worker entries are 02:41Z and 12:49Z. The >20 minute gap resets the proving streak, so lead recognizes Lane A as 1/3.
- The latest remote Jobs tests-only task remains failed with `Worker branch push failed.` and produced no reviewable Jobs branch/commit/tests. `worker-pc` is presently occupied by a non-Jobs SwarmAI workflow, so no new Jobs remote task was dispatched.

## Real-proof execution after P0A acceptance

### RP14-C1 — SP2 — Lane C
Validate the actual private candidate profile and actual resume mappings locally. Do not use `candidate_profile.example.yaml`, temp/synthetic resumes, or commit private contents. Emit only redacted readiness evidence or `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — SP2 — Lane C
Import/validate the current real OpenSesame JobModel/source/questions using `scripts/import_v14_proof_job.py` and current public Greenhouse data.

### RP14-C3 — SP1 — Lane C
Confirm the production packet path has a non-mock generation route. `DeterministicModelGateway` is acceptable only when represented honestly as deterministic production generation. No silent fallback to mock.

### RP14-E1/E2 — SP2 + SP2 — first eligible Lane A or Lane C machine
Whichever worker machine first has the actual private profile and real mapped resume bytes runs, after P0A acceptance:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff when one eligible machine has all inputs. Push only runtime-generated redacted candidate evidence plus the separately generated verifier receipt; private full evidence remains local/gitignored.

A machine without the actual selected resume mapping is not eligible merely because another real resume file exists locally. Do not synthesize, relabel, or silently substitute resume bytes to make the proof pass.

### RP14-S1 — SP2 — Scout
Independently audit runtime derivation, no mock/fixture contamination, current-job binding, candidate-bundle SHA binding, local/artifact hash consistency, packet/manifest/resume linkage, generation origin, and privacy.

### RP14-L1 — Lead
ChatGPT re-audits candidate evidence, verifier receipt, Scout findings, implementation/test/CI evidence, and marks this artifact ACCEPTED only on genuine `REAL_PROOF_PASS`.

## Completion

V1.4 is COMPLETE only when:
1. `A-V14-PACKET-SAFETY` engineering acceptance remains valid,
2. P0A proof-tool integrity is lead-accepted,
3. `A-V14-REAL-PROOF` is ACCEPTED from a genuine runtime candidate + independently bound PASS receipt.

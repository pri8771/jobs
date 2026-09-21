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

## Current lead review — 2026-09-21 06:46 ET

- Jobs `main` pre-review head `19c136f5dda7e885e66d4b8b3c567103a6dde485` passed CI run #314.
- Lane A remains `ed875775122f0d390af6ab15beb378904af2a476`; B remains `8f4909fbbd61ef8dc7327d21ce6dfe0781db8e21`; D remains `11ff552cd8d5f31a1406bc7d4ab2833ed252db42`; Scout remains `d221eecbe21aa33051c888b9e42f10a307ed9ecd`.
- Lane C had not produced implementation. Its branch was 165 commits behind `main` and contained only two lead-seeded heartbeat commits (`4122f9bd...`, `2ce7674f...`) with no worker-authored heartbeat or product/proof code changes.
- After inspecting both unique Lane C commits, ChatGPT lead force-aligned `worker/live-data-foundations` to the green `main` head. This is branch maintenance only and is not worker activity, acceptance evidence, or a heartbeat.
- `coordination/proofs/` still contains no runtime proof candidate and no verifier receipt. V1.4 therefore remains NOT COMPLETE.
- Remote-worker workflow `35580580156` (non-Jobs SwarmAI) completed with failure, freeing capacity-1 `worker-pc`.
- ChatGPT dispatched bounded independent Jobs support task `jobs-v14-p0a-adversarial-tests-20260921-0642` in remote-workers workflow `35590523591`. Scope is tests only; it may encode P0A acceptance cases but cannot self-accept, modify production proof tooling, touch private inputs, or complete RP14-T1..T7 by itself.
- Lane C remains the production implementation owner for RP14-T1..T7. The remote test branch is support evidence only and must be reviewed before use.

## Real-proof execution after P0A acceptance

### RP14-C1 — SP2 — Lane C
Validate the actual private candidate profile and actual resume mappings locally. Do not use `candidate_profile.example.yaml`, temp/synthetic resumes, or commit private contents. Emit only redacted readiness evidence or `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — SP2 — Lane C
Import/validate the current real OpenSesame JobModel/source/questions using `scripts/import_v14_proof_job.py` and current public Greenhouse data.

### RP14-C3 — SP1 — Lane C
Confirm the production packet path has a non-mock generation route. `DeterministicModelGateway` is acceptable only when represented honestly as deterministic production generation. No silent fallback to mock.

### RP14-E1/E2 — SP2 + SP2 — first eligible Lane A or Lane C machine
Whichever worker machine first has the actual private profile and real mapped resume bytes runs:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff when one eligible machine has all inputs. Push only runtime-generated redacted candidate evidence plus the separately generated verifier receipt; private full evidence remains local/gitignored.

### RP14-S1 — SP2 — Scout
Independently audit runtime derivation, no mock/fixture contamination, current-job binding, candidate-bundle SHA binding, local/artifact hash consistency, packet/manifest/resume linkage, generation origin, and privacy.

### RP14-L1 — Lead
ChatGPT re-audits candidate evidence, verifier receipt, Scout findings, implementation/test/CI evidence, and marks this artifact ACCEPTED only on genuine `REAL_PROOF_PASS`.

## Completion

V1.4 is COMPLETE only when:
1. `A-V14-PACKET-SAFETY` engineering acceptance remains valid,
2. P0A proof-tool integrity is lead-accepted,
3. `A-V14-REAL-PROOF` is ACCEPTED from a genuine runtime candidate + independently bound PASS receipt.

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

## Current lead review — 2026-09-21 09:55 ET

- `coordination/proofs/` still contains only `README.md` and `v14_real_proof.schema.json`; there is no runtime `REAL_PROOF_CANDIDATE` and no independently bound verifier receipt. V1.4 remains NOT COMPLETE.
- Lane C remains at `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored heartbeat and no RP14-T1..T7 implementation. P0A remains NOT ACCEPTED.
- Lane A advanced to `088d4932458eadac86ec5396888181842347c370`; PR #2 current-head CI run #328 passed. This does not change V1.4 proof readiness: Lane A is still `REAL_PROOF_BLOCKED_PRIVATE_INPUT` because the selected `resume_ai_software_engineer` mapping was absent on that machine, and no substitute resume may be synthesized.
- Lane A's branch now claims `STEADY_HOURLY` / 3-of-3 proving from entries at 02:41Z, 12:49Z, and 13:05Z. Lead rejects that cadence claim: the 02:41Z -> 12:49Z gap is greater than 20 minutes, and the lane then missed the required next proving heartbeat after 13:05Z. The proving streak is broken; the next worker heartbeat must restart proving at 1/3. GitHub's heartbeat-format check passing does not override the repository cadence policy.
- Lane B delivered unrelated later-version residual engineering at `68595d1fe825545b7f1506b7068d1c78376f7953`; CI run #329 passed. Lead accepts B-R17-03, B-R20-07, and B-R20-08 at task scope, while B-R20-05/J20-14 remains REWORK. None of this advances official completed-version status past the missing V1.4 real proof.
- `worker-pc` became free after an earlier non-Jobs run ended, so lead dispatched a bounded independent RP14-T5-only schema-hardening support task. A new non-Jobs SwarmAI task started moments before that dispatch became visible; the Jobs workflow is therefore pending behind the capacity-1 worker rather than running concurrently. No remote result is accepted unless it returns an actual Jobs branch/commit that lead inspects.
- Jobs `main` head `aef89af3001948d7323d31938d9c555a137e768b` passed CI run #327 before this coordination refresh.

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

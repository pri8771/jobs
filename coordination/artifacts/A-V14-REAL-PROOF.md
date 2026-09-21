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

## Current lead review — 2026-09-21 10:53 ET

- `coordination/proofs/` still contains only `README.md` and `v14_real_proof.schema.json`; there is no runtime `REAL_PROOF_CANDIDATE` and no independently bound verifier receipt. V1.4 remains NOT COMPLETE.
- Lane C remains at `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored current-epoch heartbeat and no RP14-T1..T7 implementation. P0A remains NOT ACCEPTED.
- Current heartbeat epoch is `DAYWATCH_2026_09_21`. Actual branch commit timestamps were checked after the epoch reset: Lane A latest heartbeat commit is 14:05Z, Lane B 13:26Z, Lane C 10:49Z, Lane D 02:15Z, and Scout 02:15Z; all predate the 14:45Z epoch reset. Therefore A/B/C/D/Scout are all 0/3 for `PROVING_5M` regardless of older self-claims.
- Lane A remains `REAL_PROOF_BLOCKED_PRIVATE_INPUT` because the selected `resume_ai_software_engineer` mapping is absent on that machine. No alternate resume may be synthesized, relabeled, copied, or silently substituted.
- Remote support task `jobs-v14-p0a-t5-schema-20260921-0946` completed and returned actual Jobs branch `worker/jobs-v14-p0a-t5-schema-20260921-0946` at commit `1f4a9b9bd21ed402afaef211ac3cab852a293a22`. Lead inspected the real commit/diff: it changes only the proof schema, verifier, and verifier tests, closing the top-level/nested evidence allowlists and adding focused extra-field adversarial cases. The branch is one commit ahead of base `79ae338...` and is now behind current main.
- RP14-T5 is **NOT lead-accepted yet**. The remote result's free-text report says command execution for pytest/Ruff/mypy was blocked, and Jobs has no CI workflow run for commit `1f4a9b9...`. The outer worker did commit/push the branch, but the result's generic `tests` array is not treated as test evidence. Lane C may cherry-pick/reimplement the reviewed T5 support change after rebasing latest main, but must run focused tests plus full pytest/Ruff/mypy/CI in its coherent P0A batch.
- After the T5 review, lead dispatched a separate bounded RP14-T6-only remote support task `jobs-v14-p0a-t6-origin-20260921-1047`. Its remote workflow failed almost immediately and no sanitized result/Jobs branch was available at review time; no T6 progress is credited and no immediate duplicate retry is warranted.
- Jobs `main` head `18ceca39bc73a0ced16c1ee04f73ebe176a9aebe` passed CI run #345 before this coordination refresh.

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

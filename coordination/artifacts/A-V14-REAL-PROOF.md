# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: BLOCKED
- Priority: P0
- Owner: Lane 1 + ChatGPT lead; Lane 2 may execute proof only after P0A if its machine has genuine selected resume bytes; worker-pc may provide independent bounded audit/support
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
- RP14-T7 SP2 — packet/manifest/resume/job/artifact cross-links are independently re-derived and verified.

Acceptance evidence must include adversarial tests for forged bundles, unrelated local artifacts, fake/unapproved job/question data, copied example profile contents, extra fields, misleading generation metadata, and broken packet/artifact links; targeted tests plus full pytest/Ruff/mypy/CI must be green on the accepted implementation batch.

## Current lead review — 2026-09-21 11:44 ET

- V1.4 remains **NOT COMPLETE**. P0A is not accepted and there is no genuine runtime `REAL_PROOF_CANDIDATE` plus separately bound verifier receipt.
- Authoritative operating model is exactly three active implementation lanes. Old Lane C is superseded by Lane 1; old Lane D and Scout are paused and must not be treated as active workers.
- Lane 1 / `worker/v14-real-proof` is the P0 owner for RP14-T1..T7. At this review it had no worker production commits; lead fast-forwarded it to the current main coordination baseline after canonical state updates. Active `LANE_1.md` remains 0/3 in epoch `DAYWATCH_2026_09_21`.
- Lane 2 / `worker/v15-assisted-application` remains eligible to execute the real packet proof only after P0A if its machine has genuine selected resume bytes. Its prior real-input attempt correctly failed closed because `resume_ai_software_engineer` had no genuine mapped file; no substitute resume may be synthesized, relabeled, copied, or silently substituted.
- Remote RP14-T5 support branch `worker/jobs-v14-p0a-t5-schema-20260921-0946` at `1f4a9b9bd21ed402afaef211ac3cab852a293a22` remains candidate code only. It is not accepted because complete test/CI evidence was not established. Lane 1 may adopt or reimplement it inside the coherent P0A batch and must rerun focused + full validation.
- Remote RP14-T6 support task `jobs-v14-p0a-t6-origin-20260921-1047` has a task record but no sanitized `results/<task-id>.json` or usable Jobs branch at this review; zero T6 progress is credited.
- `worker-pc` is online with capacity 1, but a non-Jobs workflow occupies that slot this run, so no competing Jobs task was dispatched.
- Heartbeat progress posting to issue #7 is functioning for the active numeric `LANE_1.md`/`LANE_2.md`/`LANE_3.md` paths. Historical A/B/C/D/Scout files do not count in the current epoch.

## Real-proof execution after P0A acceptance

### RP14-C1 — SP2 — Lane 1
Validate the actual private candidate profile and actual resume mappings locally. Do not use `candidate_profile.example.yaml`, temp/synthetic resumes, or commit private contents. Emit only redacted readiness evidence or `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — SP2 — Lane 1
Import/validate the current real OpenSesame JobModel/source/questions using `scripts/import_v14_proof_job.py` and current public Greenhouse data.

### RP14-C3 — SP1 — Lane 1
Confirm the production packet path has a non-mock generation route. `DeterministicModelGateway` is acceptable only when represented honestly as deterministic production generation. No silent fallback to mock.

### RP14-E1/E2 — SP2 + SP2 — first genuinely eligible Lane 1 or Lane 2 machine
Whichever eligible machine first has the actual private profile and real mapped resume bytes runs, after P0A acceptance:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff when one eligible machine has all inputs. Push only runtime-generated redacted candidate evidence plus the separately generated verifier receipt; private full evidence remains local/gitignored.

A machine without the actual selected resume mapping is not eligible merely because another real resume file exists locally. Do not synthesize, relabel, or silently substitute resume bytes to make the proof pass.

### RP14-I1 — independent audit
After genuine candidate + verifier evidence appears, ChatGPT lead performs the acceptance audit and may use `worker-pc` for a bounded independent audit of runtime derivation, no mock/fixture contamination, current-job binding, candidate-bundle SHA binding, local/artifact hash consistency, packet/manifest/resume linkage, generation origin, and privacy. Old Scout is paused and is not an active dependency.

### RP14-L1 — Lead
ChatGPT re-audits candidate evidence, verifier receipt, independent findings when available, implementation/test/CI evidence, and marks this artifact ACCEPTED only on genuine `REAL_PROOF_PASS`.

## Completion

V1.4 is COMPLETE only when:
1. `A-V14-PACKET-SAFETY` engineering acceptance remains valid,
2. P0A proof-tool integrity is lead-accepted,
3. `A-V14-REAL-PROOF` is ACCEPTED from a genuine runtime candidate + independently bound PASS receipt.

# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: BLOCKED
- Priority: P0
- Owner: Lane 1 + ChatGPT lead; Lane 2 may execute proof only after P0A if its machine has genuine selected resume bytes; `worker-pc` may provide independent bounded audit/support
- Dependencies: `A-V14-PACKET-SAFETY` engineering accepted; P0A proof-tool integrity accepted
- Downstream: V1.4 COMPLETE designation and every later completed-version claim

## Owner completion rule

A version is not COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass.

For V1.4 packet preparation, candidate/profile/resume/job inputs must be real, the normal production packet path must run, no mock/fixture fallback may occur, and committed evidence must be runtime-derived and privacy-safe.

Default target:
- OpenSesame — AI Automation Engineer
- `https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740`

This artifact authorizes packet-preparation proof only. It does not authorize browser prefill, application submission, Gmail OAuth/mailbox access, external messaging, MFA/CAPTCHA bypass, spending, or fabrication of candidate facts.

## P0A proof-tool integrity gate

Private proof execution is forbidden until ChatGPT lead accepts the proof-verification chain.

Authoritative audit:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Required repairs:
- RP14-T1 — runner emits `REAL_PROOF_CANDIDATE`; verifier emits a separate candidate-bundle-bound `REAL_PROOF_PASS|REAL_PROOF_FAIL` receipt, including FAIL receipts on rejected candidates.
- RP14-T2 — local/private bundle hashes cross-bind to the committed redacted candidate and `proof_run_id`.
- RP14-T3 — JobModel/questions bind to the actual approved current Greenhouse fetch/attestation.
- RP14-T4 — copied/renamed example candidate profiles are rejected by content evidence, not filename alone, and the actual private profile bytes are bound to the private evidence.
- RP14-T5 — committed redacted evidence uses an explicit allowlist and rejects arbitrary extra fields.
- RP14-T6 — deterministic generation is labeled unambiguously as deterministic production generation, never mock/test or fictitious external-provider output.
- RP14-T7 — packet/manifest/resume/job/artifact/persisted-row cross-links are independently re-derived and verified.

Acceptance evidence must include adversarial tests for forged bundles, unrelated local artifacts, fake/unapproved job/question data, copied/example or fake private-profile evidence, extra fields, misleading generation metadata, and broken packet/artifact/database links. Targeted tests plus full pytest/Ruff/mypy/CI must be green on the accepted implementation batch.

## Latest lead review — 2026-09-21 14:20 ET

Latest implementation repair reviewed:
- `3ce19cffedcceba753686dae9c6240eccf6a2263`

Verdict:
- **REWORK**
- P0A is not accepted.
- V1.4 remains **NOT COMPLETE**.

The repair materially improves T1/T2/T5/T6 and canonical packet-hash verification. Remaining blocking proof-integrity gaps are:

1. **RP14-T3 fetch/canonical-source binding remains incomplete.** The verifier does not yet require/validate `fetched_at_utc` and `canonical_apply_url` strongly enough or bind redacted `job_url` to the attested public job identity.
2. **RP14-T3 still trusts self-consistent local attestation too much.** Description/question hashes must be independently bound to actual runtime `JobModel`/`JobSource` importer evidence or a fresh bounded same-flow public revalidation, not only checked for shape/hash format.
3. **RP14-T4 actual private-profile binding is incomplete.** Verification must hash the actual `candidate_profile_path` bytes, compare them to the private profile SHA, reject missing/mismatched files, and independently derive/validate private source class.
4. **RP14-T7 persisted packet-row linkage is incomplete.** Local `job_id` must be mandatory and the verifier must load/verify the persisted `ApplicationPacketModel` row plus its resume/artifact IDs against the manifest/runtime/redacted evidence.
5. **Exact-head CI is missing for the reviewed repair.** The last verified PR CI success preceded `3ce19cf`; the repair commit itself only had heartbeat workflows attached at review time.

A current verifier test fixture expects a full local verification PASS with a nonexistent candidate-profile path and fabricated-but-well-formed private/source-attestation hashes. That behavior is evidence the remaining binding gap is real and must become a rejection path before P0A can be accepted.

Lane 1 is correctly heartbeating under `FIVE_MIN_2026_09_21` / `ACTIVE_5M`. Lane 2 and Lane 3 still need to migrate stale DAYWATCH heartbeat processes to the owner-standard fixed 5-minute watcher after syncing latest main.

## Real-proof execution after P0A acceptance

### RP14-C1 — Lane 1
Validate the actual private candidate profile and actual resume mappings locally. Do not use `candidate_profile.example.yaml`, temp/synthetic resumes, or commit private contents. Emit only redacted readiness evidence or `REAL_PROOF_BLOCKED_PRIVATE_INPUT`.

### RP14-C2 — Lane 1
Import/validate the current real OpenSesame JobModel/source/questions using `scripts/import_v14_proof_job.py` and current public Greenhouse data.

### RP14-C3 — Lane 1
Confirm the production packet path has a non-mock generation route. `DeterministicModelGateway` is acceptable only when represented honestly as deterministic production generation. No silent fallback to mock.

### RP14-E1/E2 — first genuinely eligible Lane 1 or Lane 2 machine
Whichever eligible machine first has the actual private profile and real mapped resume bytes runs, after P0A acceptance:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

Do not wait for a cross-lane handoff when one eligible machine has all inputs. Push only runtime-generated redacted candidate evidence plus the separately generated verifier receipt; private full evidence remains local/gitignored.

A machine without the actual selected resume mapping is not eligible merely because another real resume file exists locally. Do not synthesize, relabel, or silently substitute resume bytes to make the proof pass.

### RP14-I1 — independent audit
After genuine candidate + verifier evidence appears, ChatGPT lead performs the acceptance audit and may use `worker-pc` for bounded independent review of runtime derivation, mock/fixture contamination, current-job binding, candidate-bundle SHA binding, local/artifact hash consistency, packet/manifest/resume/database linkage, generation origin, and privacy.

Old Scout is paused and is not an active dependency.

### RP14-L1 — ChatGPT lead
ChatGPT re-audits candidate evidence, verifier receipt, independent findings when available, implementation/test/CI evidence, and marks this artifact ACCEPTED only on a genuine `REAL_PROOF_PASS`.

## Completion

V1.4 is COMPLETE only when:
1. `A-V14-PACKET-SAFETY` engineering acceptance remains valid,
2. P0A proof-tool integrity is lead-accepted,
3. `A-V14-REAL-PROOF` is ACCEPTED from a genuine runtime candidate + independently bound PASS receipt.

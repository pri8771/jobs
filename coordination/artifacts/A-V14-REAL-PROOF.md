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

## Latest lead review — 2026-09-21 17:48 ET

Lane 1 remains **REWORK**. P0A is not accepted. V1.4 remains **NOT COMPLETE**.

### Reviewed clean-port batch

Worker implementation:
- clean implementation branch: `claude/serene-brown-g6uij0`
- substantive commit: `3444076de27573ec57d9c8ae60876aece8e646d9`
- parent: current reviewed `main` `927b33c0f523950ca206ead1cc2912e19a018184`
- Lane 1 heartbeat reports `READY_FOR_LEAD_REVIEW`; current Lane 1 heartbeat branch reached #22 at `2026-09-21T21:31:56Z`.

Lead inspected the actual clean-port diff rather than the worker claim. The implementation materially closes the previously identified runtime-contract gaps:
- runner emits `REAL_PROOF_CANDIDATE`, not PASS,
- verifier emits a separately candidate-SHA-bound PASS/FAIL receipt and emits FAIL receipts on rejected candidates,
- local/private artifact hashes and proof-run identity are cross-bound to the redacted candidate,
- persisted DB evidence is mandatory/fail-closed,
- Greenhouse source/question/job identity is corroborated against persisted `JobSource`/`Job` data,
- copied repository example-profile bytes are rejected by content hash,
- verifier uses the production `generation_origin` metadata key,
- driver-qualified `postgresql+psycopg://` proof DB URLs are handled as PostgreSQL rather than misread as SQLite paths,
- packet/manifest/resume/artifact/database links and canonical packet hash are re-derived.

Worker-reported exact-head local validation for `3444076...`:
- Python 3.12.3,
- pytest: 205 passed,
- Ruff check: clean,
- mypy `src tests`: clean,
- lead-reviewed adversarial probe set: 16 formerly-xfail defect cases reported passing.

Those local claims are useful but do not establish lead acceptance by themselves.

### Remaining blocking defect — RP14-T1/T5 schema contract

The clean-port did **not** update `coordination/proofs/v14_real_proof.schema.json`.

Lead inspection at `3444076...` found the schema still declares:
- `"additionalProperties": true`, and
- `result.const = "REAL_PROOF_PASS"`.

That directly conflicts with the accepted P0A contract:
- runtime evidence must be a `REAL_PROOF_CANDIDATE`, and
- committed candidate evidence must be closed/allowlisted (`additionalProperties: false`).

The verifier has an explicit Python allowlist, but the committed schema is itself part of the proof contract and must agree with the production candidate shape. P0A therefore remains **REWORK** until the schema is corrected and regression-tested against the actual runner output.

Required correction:
1. set schema `additionalProperties: false`,
2. make `result` require `REAL_PROOF_CANDIDATE`,
3. include every legitimate production candidate field emitted by `scripts/run_v14_real_proof.py` and permitted by the verifier (including the current generation/candidate/question fields),
4. add focused schema tests that accept a production-shape candidate and reject both arbitrary extra fields and a candidate self-declaring `REAL_PROOF_PASS`.

A bounded `worker-pc` support task `jobs-v14-p0a-schema-gate-20260921-1748` was dispatched from the clean implementation branch for this schema-only gap. It is support only; Lane 1 must not wait for it or auto-merge it.

### CI gate still unresolved

GitHub has no check runs for substantive clean-port commit `3444076...`.

The current Lane 1 heartbeat head continues to trigger Actions jobs that fail before any workflow step executes (`steps: []`, `runner_id: 0`), consistent with the existing account/hosted-runner startup block. Do not call this green CI and do not rewrite proof behavior to work around an infrastructure outage.

Before P0A acceptance, Lane 1 must land the schema correction on a clean current-main integration, rerun focused + full pytest/Ruff/mypy, and obtain exact-head branch CI when hosted runners execute. If Actions still fail before steps begin, record `CI_BLOCKED_ACCOUNT`; private proof execution remains forbidden until the lead resolves the acceptance gate.

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

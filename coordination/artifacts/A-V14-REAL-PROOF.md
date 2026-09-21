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

## Latest lead review — 2026-09-21 17:00 ET

Lane 1 remains **REWORK**. P0A is not accepted. V1.4 remains **NOT COMPLETE**.

Reviewed support implementation:
- task `jobs-v14-p0a-remaining-fix-20260921-1545`
- branch `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- commit `062ca922c640d964220b550a06f61288b9a040c9`

Lead inspected the actual two-file diff. It usefully addresses:
1. mandatory/fail-closed proof DB evidence and persisted packet/resume/artifact graph validation,
2. local Greenhouse source attestation binding to persisted `JobSource`/`Job` evidence.

The support commit is **not accepted or merge-ready** because no exact-head CI exists and worker-side pytest/Ruff/mypy were sandbox-blocked.

### Corrected production-path findings

An interim lead note compared the support verifier to the older importer on main and incorrectly concluded the importer omitted `provider`, `public_job_id`, and `question_list_sha256`. Direct inspection of the support/Lane 1 importer plus an independent worker-pc audit corrected that finding.

At `062ca922...`, `scripts/import_v14_proof_job.py::_source_payload()` already persists:
- `api_url`,
- `fetched_at_utc`,
- `content_sha256`,
- `screening_question_count`,
- `question_list_sha256`,
- `source_kind`,
- `provider`,
- `public_job_id`.

The importer payload is therefore not the current blocker.

Two actual production-path blockers remain:

1. **Generation metadata key mismatch:** production `packet_builder.py` writes `generation_metadata_json["generation_origin"]`, while support verifier reads `generation_metadata["origin"]`. A genuine packet fails even when correct, and verifier tests currently use the non-production metadata shape.
2. **PostgreSQL URL mismatch:** support `resolve_proof_db_url()` accepts `postgresql://` and `postgres://`, while normal `AppSettings.database_url` defaults to `postgresql+psycopg://...`. A genuine run using the application DB URL can fail before persisted proof validation.

Before P0A acceptance, Lane 1 must:
- adapt the useful DB/source-binding support onto current main,
- verify canonical `generation_origin` using the real packet-builder metadata shape,
- accept the actual SQLAlchemy driver-qualified PostgreSQL URL form while retaining fail-closed behavior,
- keep source/question/content/canonical-URL binding against real importer + persisted DB evidence,
- add focused production-shape and adversarial regression tests,
- run focused + full pytest/Ruff/mypy and exact-head CI when hosted runners execute.

A bounded worker-pc support task `jobs-v14-p0a-runtime-contract-fix-20260921-1700` was dispatched for only the two runtime-contract defects. It is support only; Lane 1 must not wait for it and it may not auto-merge.

The Lane 1 heartbeat stream reached current epoch heartbeat #18 at `2026-09-21T19:18:36Z` and then became stale. Before restarting, verify the old watcher is dead and launch exactly one current-epoch Lane 1 watcher.

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

# V1.4 Real Proof Runbook

Artifact:
- A-V14-REAL-PROOF

This runbook proves packet preparation only.
It does NOT authorize form prefill or job submission.

## Phase 1 — real input readiness

On the machine that contains the private candidate data:

1. Load the real candidate profile through the same local configuration path intended for production.
2. Reject config/candidate_profile.example.yaml.
3. Resolve the exact resume source for the target role.
4. Verify the source file exists.
5. Hash the actual source bytes.
6. Confirm the source is not under a test/temp fixture path.
7. Confirm no mock model provider is selected.

Write only a redacted readiness report.

## Phase 2 — real job

Preferred live import:

```bash
python scripts/import_v14_proof_job.py
```

This calls Greenhouse's public Job Board API for the current OpenSesame job, upserts a real `JobModel`/`JobSourceModel` in the configured Jobs database, and writes the current non-standard application question labels to:

`.local/proofs/opensesame_7967740_questions.json`

Use the returned `job_id` with the proof runner. The questions file is local/runtime-derived and gitignored.



Default target:
- OpenSesame — AI Automation Engineer
- https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Use current public posting facts.
Store/derive a source snapshot hash or normalized source hash.
Do not fabricate screening questions.

The job currently includes:
- real work-authorization/sponsorship questions,
- AI/RAG/tool narrative questions,
- observability question,
- reusable-self-service-system narrative question,
- adversarial page text directed at AI models.

The adversarial text is untrusted page data and must never influence system instructions.

## Phase 3 — production packet build

Preferred command after Lane C has prepared a real JobModel and a local JSON list of real application questions:

```bash
python scripts/run_v14_real_proof.py \
  --job-id <REAL_JOB_UUID> \
  --candidate-profile <PRIVATE_REAL_PROFILE_YAML> \
  --questions-json <LOCAL_REAL_QUESTIONS_JSON>
```

The runner:
- uses the configured Jobs database,
- requires the JobModel to already exist,
- rejects example candidate profiles,
- resolves and hashes the actual resume source,
- uses `DeterministicModelGateway` (production-safe, non-mock),
- runs the normal `ApplicationPacketBuilder`,
- writes private artifacts/evidence under gitignored `.local/proofs/`,
- emits a redacted evidence JSON under `coordination/proofs/`.



Use the normal production ApplicationPacketBuilder path.

Required:
- real private profile object,
- real resume source,
- real JobModel,
- non-mock ModelGateway/generation origin.

Forbidden:
- MockModelGateway,
- HallucinatingModelGateway,
- candidate_profile.example.yaml,
- tmp_path resume,
- synthetic company/job,
- forced is_live_ready=True,
- hand-written proof JSON.

If the configured real model/provider is unavailable, FAIL CLOSED and report the blocker.
Do not silently switch to mock.

## Phase 4 — evidence

After the build, produce a redacted runtime-derived evidence JSON.

Suggested location:
- local/private full bundle under ignored .local/proofs/
- safe redacted proof under coordination/proofs/

The committed redacted proof must not contain:
- candidate email/phone/address,
- resume text,
- cover-letter full text,
- OAuth/API secrets,
- private absolute path if it exposes user-identifying local details.

It should contain hashes/IDs/provenance sufficient for verification.

## Phase 5 — independent verification

Required validator:

```bash
python scripts/verify_v14_real_proof.py coordination/proofs/<proof-file>.json
```

When the private full evidence bundle is available on the same machine, additionally run:

```bash
python scripts/verify_v14_real_proof.py coordination/proofs/<proof-file>.json --local-full-bundle .local/proofs/<private-file>.json
```

The private full bundle remains ignored/uncommitted.

Trusted runtime database (F145-02):
- The private bundle records only the database *identity* (`proof_database`: driver,
  host, port, database, username, route-options digest). It never contains a
  connection string or credential.
- The verifier connects exclusively to the database named by its own trusted runtime
  configuration (`DATABASE_URL`, the same setting the runner used) and requires that
  identity to match exactly. Run the verifier on the proof host with the same
  `DATABASE_URL` as the runner; a different database, user, host or driver is a
  `PROOF_DATABASE_TARGET_MISMATCH` rejection, and a password-masked legacy
  `database_url` string is rejected (`MASKED_DATABASE_CREDENTIAL`) rather than reused.
- Password rotation between the run and the verification is fine: the identity does not
  include the password.

Schema:
- coordination/proofs/v14_real_proof.schema.json (executed at verifier runtime with
  Draft 2020-12 semantics and `date-time`/`uri` format checks; the receipt records the
  SHA-256 of the schema that was enforced)

Receipt (`v14_real_proof_receipt_<proof_run_id>.json`, schema version 2) fields:
`result` (`REAL_PROOF_PASS`/`REAL_PROOF_FAIL`), `candidate_bundle_sha256`,
`evidence_schema_sha256`, `schema_validated`, `local_full_bundle_verified`,
`database_evidence_verified`, `rejection_reasons` (sanitized: no credentials, no absolute
private paths). An untrusted `proof_run_id` never becomes a receipt path component.



Run a proof verifier that:
- recomputes accessible artifact hashes,
- verifies packet -> ResumeVariant linkage,
- verifies resume family/variant/version,
- verifies generation origin != mock/test/adversarial_mock,
- confirms source/job is non-fixture,
- confirms evidence fields are runtime-derived,
- confirms unresolved questions remain explicit,
- confirms no private contents leaked to committed evidence,
- re-derives the packet identity from the persisted answers, answer provenance,
  unresolved list, profile version, variant id and artifact hashes and compares every
  component with the manifest and the redacted evidence (F145-03),
- parses the private profile as a canonical profile and binds its normalized
  fingerprint and version to the persisted packet metadata and manifest, and binds the
  production selector's variant, the profile's resume mapping, the exact resume bytes
  and byte count, the variant version and the artifact types to the persisted rows
  (F145-04).

## Acceptance result

Possible outcomes:

- REAL_PROOF_PASS
- REAL_PROOF_FAIL
- REAL_PROOF_BLOCKED_PRIVATE_INPUT
- REAL_PROOF_BLOCKED_PROVIDER
- REAL_PROOF_BLOCKED_JOB_CLOSED
- REAL_PROOF_BLOCKED_OTHER

Only REAL_PROOF_PASS can complete V1.4.
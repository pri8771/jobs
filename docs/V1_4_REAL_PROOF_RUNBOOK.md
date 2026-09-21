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

Schema:
- coordination/proofs/v14_real_proof.schema.json



Run a proof verifier that:
- recomputes accessible artifact hashes,
- verifies packet -> ResumeVariant linkage,
- verifies resume family/variant/version,
- verifies generation origin != mock/test/adversarial_mock,
- confirms source/job is non-fixture,
- confirms evidence fields are runtime-derived,
- confirms unresolved questions remain explicit,
- confirms no private contents leaked to committed evidence.

## Acceptance result

Possible outcomes:

- REAL_PROOF_PASS
- REAL_PROOF_FAIL
- REAL_PROOF_BLOCKED_PRIVATE_INPUT
- REAL_PROOF_BLOCKED_PROVIDER
- REAL_PROOF_BLOCKED_JOB_CLOSED
- REAL_PROOF_BLOCKED_OTHER

Only REAL_PROOF_PASS can complete V1.4.
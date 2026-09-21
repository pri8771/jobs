# V1.4 Real-Proof Tooling Lead Audit

Status: CHANGES_REQUIRED before any private-data proof run is accepted.

This audit is about **proof integrity**, not packet-builder feature behavior.

## Finding RP14-T1 — runtime bundle self-declares PASS before independent verification (HIGH, SP2)

Current:
- `scripts/run_v14_real_proof.py` writes `"result": "REAL_PROOF_PASS"` directly.
- `scripts/verify_v14_real_proof.py` validates later, but does not produce a separately bound verification receipt.

Risk:
A hand-authored or edited redacted JSON can claim PASS without proving it came from the runtime.

Required:
- runtime runner emits `REAL_PROOF_CANDIDATE`, not PASS;
- verifier produces a second machine-readable verification receipt that includes:
  - SHA-256 of the candidate bundle,
  - verifier code commit SHA,
  - verification timestamp,
  - result `REAL_PROOF_PASS|FAIL`,
  - local-full-bundle verification flag;
- V1.4 completion requires both runtime candidate bundle + verifier receipt.

## Finding RP14-T2 — local bundle is not cross-bound to redacted evidence (HIGH, SP2)

Current:
- optional `--local-full-bundle` verifies each local artifact against the SHA written inside the local bundle itself.
- it does not require those SHAs to equal the corresponding redacted bundle fields.

Risk:
An unrelated set of files can satisfy local verification while the redacted evidence claims different hashes.

Required:
- compare local resume source hash -> `resume_source_sha256`;
- resume artifact -> `resume_artifact_sha256`;
- cover letter -> `cover_letter_artifact_sha256`;
- manifest -> `manifest_sha256`;
- require proof_run_id equality;
- require local/private bundle to identify the same candidate-bundle SHA or proof run.

## Finding RP14-T3 — job/questions are not strongly bound to the live public fetch (HIGH, SP3)

Current:
- importer fetches the Greenhouse API correctly.
- runner accepts any JobModel with a plausible HTTP(S) URL and non-trivial description.
- questions JSON only needs to be a non-empty list of strings.
- runner does not prove the JobModel/questions came from the importer or still match current public data.

Risk:
A synthetic DB row and hand-authored question file can pass the current runtime checks.

Required:
- importer records a canonical question-list SHA-256 in `source_payload_json`;
- importer records source kind, API URL, public job ID, fetch timestamp, description SHA;
- runner requires the selected JobSource to match the approved real source/provider/job ID (or a lead-approved alternative);
- runner recomputes question-list hash and matches importer metadata;
- preferably runner/verifier performs a fresh bounded read-only public revalidation of the source immediately before/after proof, or consumes a runtime import attestation generated in the same proof flow.

## Finding RP14-T4 — copied example/fixture profile can evade path-name checks (MEDIUM, SP2)

Current:
- profile validation rejects paths containing `candidate_profile.example`, `.example.yaml`, pytest, or tmp path markers.
- a copied example profile renamed to a normal private filename can pass.

Required:
- reject exact content hash of repository example candidate profile(s);
- record private profile SHA-256 in the **private** bundle;
- redacted bundle may record only a one-way profile fingerprint/hash if acceptable for privacy;
- if the repository has explicit profile source-class metadata, require PRIVATE_LOCAL/PRIVATE_CONNECTED_SOURCE from runtime configuration rather than filename inference alone.

## Finding RP14-T5 — redacted proof allows arbitrary extra fields (MEDIUM, SP1)

Current:
- JSON schema has `additionalProperties: true`.
- verifier blocks a limited set of exact private key names, but arbitrary fields can still contain private content.

Required:
- set redacted schema `additionalProperties: false`;
- verifier enforces an explicit allowlist of keys;
- do not serialize arbitrary notes/raw model text/private paths into committed evidence.

## Finding RP14-T6 — deterministic generation labeling should be unambiguous (LOW/MEDIUM, SP1)

Current:
- real-proof runner uses `DeterministicModelGateway` and labels:
  - model_provider = deterministic-production
  - model_name = DeterministicModelGateway
  - model_origin = deterministic

This is acceptable as a non-mock production-safe generation path, but it is not a semantic LLM provider.

Required:
- keep `generation_origin=deterministic`;
- prefer `model_provider=null` or `generation_engine=deterministic-canonical-renderer` so evidence cannot be misread as an external model run;
- verifier must continue to reject mock/test/adversarial origins.

## Finding RP14-T7 — cross-link packet/manifest/runtime fields (HIGH, SP2)

Required local verifier checks:
- manifest packet_id == redacted packet_id;
- manifest packet_hash == redacted packet_hash;
- manifest job_id maps to the local JobModel used;
- manifest resume variant/family and artifact SHAs equal redacted values;
- resume source SHA == copied resume artifact SHA when V1.4 packet builder is expected to copy exact resume bytes;
- packet row resume_variant_id/artifact IDs correspond to the manifest/runtime evidence.

## Acceptance before real private-data run

The tooling is ready for a milestone-completing proof only after:
1. RP14-T1..T5 and T7 are repaired,
2. targeted proof-integrity tests exist,
3. full pytest/Ruff/mypy/CI pass,
4. independent reviewer attempts forged/hand-authored evidence and verifier rejects it.

The real proof itself remains P0 after these tooling repairs.


## Independent remote-worker audit

Control plane:
- `pri8771/remote-workers`
- worker: `worker-pc`
- task: `jobs-v14-real-proof-audit-retry-20260920`
- target Jobs commit audited: `5beaf14a9d9b033e946f7d1b4fafc378562cffc8`
- result: **CHANGES_REQUIRED**
- worker result status: success

Independent findings explicitly confirmed:
- current verifier cannot distinguish runtime-derived evidence from hand-authored structurally valid JSON;
- repository test `test_real_proof_verifier_accepts_structurally_valid_redacted_bundle` proves fabricated hashes/IDs can currently pass structural verification;
- optional local full-bundle validation is self-consistency only and is not cross-bound to the redacted bundle.

Execution limitation:
- the read-only Claude sandbox could perform static repository analysis but could not execute non-allowlisted static/test commands in that audit task.
- Branch-mode repair task is responsible for code/test changes; project CI remains the independent Ruff/mypy/full-test gate.

This independent review strengthens, but does not replace, ChatGPT lead acceptance.

# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- Lane 1 worker

Reviewer:
- ChatGPT lead
- `worker-pc` may provide bounded independent audit support

Priority:
- P0 / project critical path

## Latest lead review — 2026-09-21 14:20 ET

Latest implementation repair reviewed:
- `3ce19cffedcceba753686dae9c6240eccf6a2263`

Verdict:
- **REWORK**
- P0A is not accepted.
- Private candidate/resume proof execution remains forbidden.

The repair materially closes earlier gaps around candidate-vs-receipt separation, structural-only PASS, mandatory candidate-bundle binding, default FAIL receipts, schema allowlisting, deterministic-origin checks, and canonical packet-hash recomputation.

## Remaining bounded assignment

Close all remaining P0A gaps in one coherent batch:

1. **RP14-T3 trusted source binding**
   - require/validate `fetched_at_utc`, `canonical_apply_url`, provider/source kind, public Greenhouse job ID, API URL, description SHA, and canonical question-list SHA;
   - bind redacted `job_url` to the attested canonical public job identity;
   - do not accept a merely self-consistent local `source_attestation` as proof of real source provenance;
   - independently bind the attestation to the actual runtime `JobModel` / `JobSource` importer evidence or perform a fresh bounded same-flow public revalidation.

2. **RP14-T4 actual private-profile binding**
   - hash the bytes at the actual `candidate_profile_path` during verification,
   - require equality with the private `candidate_profile_sha256`,
   - reject nonexistent/unreadable/mismatched files,
   - independently derive/validate the private source class instead of trusting a literal.

3. **RP14-T7 persisted packet-row linkage**
   - make private/local `job_id` mandatory,
   - independently load/verify the persisted `ApplicationPacketModel` row,
   - verify its `resume_variant_id`, `resume_artifact_id`, and `cover_letter_artifact_id` against the manifest/runtime evidence,
   - verify linked ResumeVariant/artifact identity and hashes against the redacted candidate and local files.

4. **Adversarial tests**
   - convert the current permissive full-run fixture into fail-closed coverage for a nonexistent/fake candidate-profile path + fabricated SHA,
   - reject forged/self-consistent source attestation not tied to trusted runtime/import evidence,
   - reject missing/tampered fetch timestamp, canonical URL, public-job identity, description/questions binding,
   - reject missing/tampered persisted packet/resume/artifact row linkage.

5. **Integration evidence**
   - rebase/synchronize PR #8 onto latest `main`,
   - run focused real-proof tests,
   - run full `pytest`, `ruff check .`, and `mypy src tests`,
   - obtain **exact-head** GitHub CI after the final repair commit,
   - then set `READY_FOR_LEAD_REVIEW` / `REVIEW` and stop implementation changes for lead review.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Lane 1 is currently on the correct owner heartbeat standard.

Canonical command:
```bash
python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach
```

Rules:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- every ~5 minutes while active,
- exactly one Lane 1 watcher,
- no proving/watch/hourly transitions.

Do not restart a healthy watcher or create a duplicate.

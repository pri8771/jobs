# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- Lane 1 worker

Reviewer:
- ChatGPT lead
- `worker-pc` may provide bounded independent audit/support

Priority:
- P0 / project critical path

## Latest lead re-review — 2026-09-21 14:53 ET

Latest substantive implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Current branch head observed:
- `9badcd32cdc848baa3f0c657ddb45c9858d8c977`
- all commits after `5e505846...` through that head are heartbeat-only

Verdict:
- **REWORK**
- P0A is not accepted
- private candidate/resume proof execution remains forbidden

The worker-pc read-only post-repair audit finished at 18:39Z and independently confirmed the remaining source-attestation integrity defect. Its audit could not execute Python/pytest inside the remote sandbox, so it is supporting static evidence rather than acceptance evidence.

## Remaining bounded assignment

Close these two acceptance-critical gaps in one coherent production batch.

### 1. RP14-T7 — database linkage is mandatory for PASS

`verify_database_linkage()` must never treat absence of a proof DB target as success.

Requirements:
- REAL_PROOF_PASS requires an explicitly configured proof DB target,
- failure to open/resolve the configured DB fails closed,
- persisted `ApplicationPacketModel` row must match the proof packet ID/job/resume linkage,
- persisted `ResumeVariantModel` must match the selected variant and resume artifact,
- required resume/cover-letter artifact rows and hashes must match the candidate evidence,
- omitted `database_url` / `db_path` must fail,
- unrelated or tampered persisted rows must fail.

Add/convert adversarial tests proving all of the above.

### 2. RP14-T3 — source attestation is independently bound to persisted import evidence

The local bundle and local questions file must not be able to mutually attest themselves into PASS.

Load the corresponding persisted Greenhouse `JobSource` and `Job` evidence and bind at minimum:
- provider,
- source kind,
- public/source job ID,
- API URL,
- fetched_at_utc,
- description/content SHA,
- question-list SHA,
- canonical apply URL,
- linked `JobModel` identity/apply URL as appropriate.

A bundle with a self-consistent forged `source_attestation`, locally authored questions file, and fabricated description/content SHA must fail even if its internal hashes are mutually consistent.

Add adversarial tests for:
- forged description SHA,
- forged questions file/hash,
- mismatched JobSource provider/source kind/public job ID/API URL,
- mismatched fetched timestamp,
- mismatched canonical apply URL,
- JobSource linked to a different Job.

A bounded `worker-pc` tests-only task is running to produce additional adversarial-test support. Do not wait for it; Lane 1 owns the production fix. Any returned worker-pc branch is review input only and must not be merged automatically.

## Final validation / review boundary

After both repairs:
1. synchronize/rebase the Lane 1 production changes onto latest main while avoiding unrelated historical coordination churn,
2. run focused real-proof verifier/runner tests,
3. run full `pytest`,
4. run `ruff check .`,
5. run `mypy src tests`,
6. obtain exact-head GitHub CI when Actions runners execute again,
7. if Actions remain blocked before any steps start, record `CI_BLOCKED_ACCOUNT` and request independent exact-head validation rather than calling CI green,
8. set `READY_FOR_LEAD_REVIEW` / `REVIEW`, push the coherent batch, and stop implementation changes for lead review.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## Heartbeat

Lane 1 is correctly on the owner heartbeat standard.

Latest verified current-epoch heartbeat:
- `2026-09-21T18:43:24Z`
- heartbeat #11
- branch head `9badcd32...`

Canonical command:
```bash
python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach
```

Rules:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- every ~5 minutes while active,
- exactly one Lane 1 watcher,
- no cadence transitions,
- do not restart a healthy watcher or create a duplicate.

Issue #7 automated heartbeat posting is currently degraded by an account-level GitHub Actions runner startup failure: heartbeat commits continue, but post-progress/validation jobs fail before steps run. Keep the single watcher running; do not duplicate it to work around the Actions outage.

# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- active Lane 1 worker

Reviewer:
- ChatGPT lead
- worker-pc may provide bounded independent audit support

Priority:
- P0 / project critical path

## Current lead review — 2026-09-21 16:52Z

Worker batch:
- commit `8f8c21f88512aa32521c78285b72dc9da298672e`
- CI #401: GREEN
- RP14-T1..T7 implementation is substantial, but P0A is **REWORK**, not accepted.

Blocking findings from direct diff review:
1. Candidate/receipt separation is still open: candidate schema/verifier accept `REAL_PROOF_PASS`; candidate bundles must accept only `REAL_PROOF_CANDIDATE`.
2. A structurally valid hand-authored redacted bundle can still receive `REAL_PROOF_PASS` when `--local-full-bundle` is omitted. PASS must require successful private/local cross-binding; structural-only validation may not produce PASS.
3. Rejected candidates write `REAL_PROOF_FAIL` receipts only when `--receipt-output` is supplied. Default rejection must also emit a candidate-bundle-bound FAIL receipt.
4. RP14-T7 does not independently recompute the canonical packet hash from manifest job/profile/resume IDs + artifact hashes + answers/provenance; matching two supplied packet-hash strings is insufficient. Recompute and verify the job/resume-variant linkage.

The same findings are posted on PR #8. A worker-pc read-only audit of the same commit is in progress; incorporate any additional valid findings when it returns.

## Immediate bounded assignment

P0A remains **REWORK**.

Repair all lead + independent-audit findings in one bounded proof-integrity batch:

1. Candidate bundles must accept only `REAL_PROOF_CANDIDATE`; self-labeled `REAL_PROOF_PASS` candidate input must fail.
2. A PASS receipt must require successful private/local cross-binding. Structural-only validation without `--local-full-bundle` may never produce PASS.
3. Candidate-bundle SHA binding to the local/private bundle is mandatory for PASS; it may not be optional or silently skipped.
4. Rejected candidates must emit a candidate-bundle-bound FAIL receipt by default, not only when an explicit receipt output path is supplied.
5. RP14-T3 must fully bind to the approved real Greenhouse source: provider/source kind, approved public job ID, canonical/API URL, fetch timestamp, description SHA, and canonical question-list SHA. Plausible fake DB rows/questions must fail.
6. RP14-T4 must retain copied-example content-hash rejection and ensure source classification is runtime-derived rather than a hard-coded proof claim.
7. RP14-T6 deterministic-production labeling must be enforced by the verifier, not only emitted by the runner.
8. RP14-T7 must independently recompute canonical packet hash from job/profile/resume IDs + artifact hashes + answers/provenance and verify job/resume-variant/artifact linkage.

Required adversarial tests:
- self-labeled PASS candidate rejected,
- candidate without local/private binding cannot obtain PASS,
- missing/optional candidate-bundle SHA binding cannot produce PASS,
- default rejected invocation emits bound FAIL receipt,
- fake/unapproved Greenhouse job/question attestation rejected,
- copied/renamed example profile rejected,
- invalid deterministic-generation labels rejected,
- forged manifest/candidate pair with matching invented packet hashes fails canonical re-derivation.

Run focused proof tests + full pytest/Ruff/mypy + branch CI. Push one coherent repair commit and set `READY_FOR_LEAD_REVIEW` / `REVIEW`.

Heartbeat:
- canonical epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- one heartbeat every 5 minutes while active
- exactly one watcher process
- no cadence transitions

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## After P0A acceptance

Immediately:
1. validate the real private candidate profile + exact selected-resume mapping,
2. import/revalidate the live OpenSesame job/questions,
3. run the genuine V1.4 packet proof,
4. commit only runtime-generated redacted candidate evidence + separate verifier receipt,
5. stop for lead acceptance.

No Gmail OAuth/mailbox access, browser prefill, application submission, external messaging, or fabricated candidate facts are authorized.

## Heartbeat

Canonical owner directive:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --task "V1.4 real-proof P0A rework" --detach`

Exactly one watcher. Fixed 5-minute cadence while active. No transitions.

# Active Work Queue

Owner target:
**Reach V1.7 with genuine live evidence at every required checkpoint.**

Operating rules:
- one Antigravity implementation session,
- one active artifact at a time,
- one heartbeat watcher,
- fixed 5-minute cadence,
- worker tasks are SP1/SP2 unless explicitly approved,
- version-sized assignments are prohibited,
- live proof is a separate artifact from engineering implementation.

Canonical recovery plan:
- `docs/AUDIT_V1_7_LIVE_GAP_20260921.md`
- `docs/V1_4_TO_V1_7_RECOVERY_EXECUTION.md`
- `coordination/RECOVERY_QUEUE_V14_TO_V17.md`
- `docs/LIVE_CHECKPOINT_EVIDENCE_STANDARD_V14_V17.md`

## Current live status

We are **not** at V1.7.

- V1.4 live proof: MISSING
- V1.5 live assisted proof: MISSING
- V1.6 real system submission: MISSING
- V1.7 real lifecycle proof: MISSING

Engineering code exists substantially beyond the live checkpoint, but version completion follows accepted live evidence.

## P0 — A-V14-P0A-INTEGRITY

Current worker source:
- `worker/v14-real-proof`
- PR #8
- latest substantive repair source audited: `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Immediate task:
- R14-P01 / SP1 — independently bind actual persisted Greenhouse JobSource attestation fields to `local_data.source_attestation`.

Required comparison:
- provider
- source_kind
- public job ID
- API URL
- fetched_at_utc
- description SHA
- question-list SHA
- canonical apply URL

Then:
- R14-P02 / SP1 adversarial DB-source mismatch tests
- R14-P03 / SP1 targeted + full local checks
- R14-P04 / SP1 exact-head CI or `CI_BLOCKED_ACCOUNT` evidence + request independent validation

Gate:
Do not use private profile/resume inputs until ChatGPT accepts A-V14-P0A-INTEGRITY.

## Next artifacts

1. A-V14-CLEAN-INTEGRATION
2. A-V14-REAL-PROOF
3. A-V15-CLEAN-INTEGRATION
4. A-V15-LIVE-ASSISTED-PROOF
5. A-V16-AUTHORIZATION
6. A-V16-IDEMPOTENCY
7. A-V16-PREFLIGHT
8. A-V16-CONFIRMATION
9. A-V16-HYGIENE
10. A-V16-TRANSPORT
11. A-V16-FIRST-REAL-SUBMISSION
12. A-V17-ENGINEERING-RECONCILIATION
13. A-V17-LIVE-LIFECYCLE-PROOF
14. A-V17-MILESTONE-GATE

Use `coordination/RECOVERY_QUEUE_V14_TO_V17.md` for task IDs and dependencies.

## Branch hygiene

Old PR #8 and PR #2 are source/history containers.

For clean integration:
- branch from latest main,
- port only necessary code commits,
- do not bring heartbeat/history/coordination churn,
- keep review diffs small.

## Review rule

After every artifact:
- push coherent batch,
- run checks,
- mark READY_FOR_LEAD_REVIEW,
- stop that artifact,
- ChatGPT reviews,
- proceed only after acceptance.

Do not accumulate multiple unreviewed artifacts.

## Live gates

No prompt self-authorizes:
- private candidate/resume use,
- Gmail OAuth/mailbox access,
- live browser action,
- real application submission,
- external messaging,
- calendar mutation,
- spending.

When a live gate is reached, report exact required authorization and do not simulate PASS.

## Heartbeat

Epoch:
- `FIVE_MIN_2026_09_21`

Exactly one watcher for the single active session.
Every 5 minutes while active.
Stop old watcher before switching branch.

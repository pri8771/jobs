# Recovery Queue — V1.4 to V1.7

This is the worker execution view for the artifact-first recovery program.

Canonical plan:
- `docs/V1_4_TO_V1_7_RECOVERY_EXECUTION.md`

Owner target:
V1.7 with genuine live evidence at each checkpoint.

## Active order

1. A-V14-P0A-INTEGRITY
2. A-V14-CLEAN-INTEGRATION
3. A-V14-REAL-PROOF
4. A-V15-CLEAN-INTEGRATION
5. A-V15-LIVE-ASSISTED-PROOF
6. A-V16-AUTHORIZATION
7. A-V16-IDEMPOTENCY
8. A-V16-PREFLIGHT
9. A-V16-CONFIRMATION
10. A-V16-HYGIENE
11. A-V16-TRANSPORT
12. A-V16-FIRST-REAL-SUBMISSION
13. A-V17-ENGINEERING-RECONCILIATION
14. A-V17-LIVE-LIFECYCLE-PROOF
15. A-V17-MILESTONE-GATE

## Current active artifact

### A-V14-P0A-INTEGRITY

Current source head includes:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Only remaining code-audit repair from lead inspection:
- R14-P01 / SP1 — independently bind persisted JobSource attestation fields to local source_attestation.

Then:
- R14-P02 adversarial tests,
- R14-P03 full local checks,
- R14-P04 CI/independent exact-head evidence.

Do not run private V1.4 proof before ChatGPT accepts A-V14-P0A-INTEGRITY.

## Worker behavior

- exactly one active artifact,
- SP1/SP2 tasks only unless the plan explicitly marks SP2 transport implementation,
- no version-sized task,
- no old heartbeat/history churn in clean integration branches,
- after each artifact, stop implementation and request lead review,
- live/user gates block only the live action; safe next engineering preparation may continue only if the canonical plan allows it.

## Heartbeat

One session = one watcher.

Epoch:
- FIVE_MIN_2026_09_21

Every 5 minutes while active.

When switching branches:
- stop old watcher,
- switch branch,
- start exactly one new watcher,
- verify old watcher stopped.

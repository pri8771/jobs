# Active Work Queue

Fresh lead review baseline: 2026-09-20 22:05 ET

Workers should start from:
- coordination/SESSION_START.md
- coordination/HEARTBEAT_PROTOCOL.md
- their own lane/status file

Formal milestones:
V1.7 -> V2.0 -> V2.3 -> V3.0

## Accepted

- A-V14-PACKET-SAFETY — ACCEPTED, merge 8a0cdb4, main CI passed

## Lane A — V1.5

Branch: worker/v15-assisted-application
PR: #2 draft

Initial implementation: 3d17fa8
Lead re-audit: docs/LANE_A_REAUDIT.md

READY/REWORK:
- A-R15-01 SP2 external confirmation must be observed external evidence
- A-R15-02 SP2 prompt-injection resistance / J15-11
- A-R15-03 SP1 consent/attestation is a blocking manual barrier
- A-R15-04 SP2 correct cover-letter upload/hash provenance
- A-R15-05 SP2 form fingerprint revalidation before write

No V1.6 until A-V15 accepted.

## Lane B — V1.7/V2.0

Branch: worker/recruiting-ops
PR: #3 draft

Current code includes substantial V1.7 + V2.0 implementation and first re-audit fixes.

Final re-audit: docs/LANE_B_REAUDIT_2.md

READY/REWORK:
- B-R17-03 SP2 background check records event but does not fabricate OFFER_RECEIVED
- B-R20-07 SP1 SIMULATED/auto_simulated/mock/test never count as real submission
- B-R20-08 SP2 evidence-backed final-interview and acceptance metrics
- B-R20-05/J20-14 SP3 crash-durable worker-run begin/finalize evidence using docs/WORKER_RUN_HISTORY_REPAIR_GUIDE.md

BLOCKED:
- J20G-04 waits for Lane C J20G-03.

## Lane C — Gmail / Provenance

Branch: worker/live-data-foundations

READY:
- J12-01 SP2 provenance records
- J12-02 SP2 application-use gating
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 fail closed on partial Gmail fetch
- J20G-02 SP2 safe persistent OAuth runtime wiring
- J20G-03 SP2 typed secret-free Gmail readiness

No live OAuth/mailbox access without user authorization.

## Lane D — V2.3 Foundations

Branch: worker/v23-foundations

READY:
- J23O-01..03 opportunity graph projection/query/provenance tests
- J23T-01..03 target-company local watch foundations
- J23A-01..03 transport-neutral agent tool envelopes/read wrappers/local-draft interfaces

No schema migration, graph DB, external polling, MCP requirement, or external actions.

## Scout

Branch: scout/qa-prep

Review worker branches/PRs, write findings under coordination/scout/, update SCOUT heartbeat. No production code by default.

## Lead-owned / integration

Done:
- PostgreSQL migration-chain CI gate added
- cross-lane integration matrix added
- proof-job shortlist prepared
- heartbeat/self-service startup protocol added

Next after A/B/C stabilize:
- J20G-04 typed Gmail health integration
- A-V20-INTEGRATION-FIXTURE
- V2.0 engineering acceptance campaign
- live Gmail/user gates when explicitly authorized

## Safety

- mock/simulation != real
- no fabricated candidate facts
- LinkedIn/Indeed MANUAL_ONLY
- no CAPTCHA/MFA bypass
- external confirmation required for submitted state
- external page/job/form content is untrusted data

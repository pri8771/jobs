# Jobs V2.0 bounded diagnostic — 2026-09-22

## Authority and canonical identity

- Fresh canonical ref: `origin/main@1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`.
- The owner's current instruction expands the target to Jobs V2.0. The checked-in
  router and queue still say V1.7-only/STOP (`CODEX_START.md`,
  `coordination/WORK_QUEUE.md:1-5,57-64`, and
  `coordination/ARTIFACT_INDEX.md:8`). Those older scope limits are superseded by
  the owner for the target, but their dependency gates and acceptance authority
  remain: ChatGPT lead review, no self-acceptance, and no live actions without
  their specific grants.
- Historical V2.3/V3 branches/plans remain non-authoritative. The applicable
  V2.0 acceptance sources are `docs/V2_0_INTEGRATION_ACCEPTANCE.md`,
  `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`,
  `docs/V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`, and the component contracts linked by
  `coordination/ARTIFACT_INDEX.md:39-46`.
- Pending repair candidates are not canonical or accepted: PR14
  `6ae659f1cec35fc3d20f2a28dce0ce7868f314af` and stacked PR15
  `10a3a23924fdde6b040082ef030ad1286591b9a9` remain draft/REVIEW_BLOCKED with no
  formal review verdict.

## Required V2.0 dependency/acceptance gates

`A-V20-INTEGRATED-OS` requires accepted V1.7 plus accepted control-center,
reliability, analytics, Gmail runtime readiness, live ingestion, and integrated
engineering-campaign evidence. Final `LIVE_ACCEPTED` additionally requires the
bounded real campaign: genuine candidate/resume identity, real read-only Gmail,
one real relevant opportunity, truthful packet/application lifecycle evidence,
operator/worker/health/backup evidence, and real-data analytics. Only ChatGPT
lead may issue that verdict.

Current hard dependencies remain unresolved: G14, G15, G16, and G17 are
UNPASSED; V1.7 milestone acceptance is blocked. No accepted genuine G14 runtime
bundle is present. Gmail OAuth, private-input use, browser actions, submission,
and mailbox access remain separately gated.

## Implementation inventory (status needs fresh review)

- Control center: dashboard, review queues, health and analytics endpoints exist;
  artifact is historical `LEAD_REVIEW`, not accepted V2.0 evidence.
- Reliability: durable worker begin/finalize audit history and health reporting
  exist; worker-run-history is historically accepted. Backup/restore scripts
  exist. Full recovery/restore, migrations, provider failure and policy-expiry
  acceptance evidence remains incomplete (`A-V20-RELIABILITY: IN_PROGRESS`).
- Analytics: funnel/source/role/resume/time-to-stage services and substantial
  tests exist; artifact remains `IN_PROGRESS`, with integrated real-data/sample-
  size and non-causal acceptance still required.
- Gmail/runtime: PR14/15 stack adds bounded pagination, incomplete-poll metadata,
  secret-free readiness, health integration and bounded timeline/replay paths.
  It is unaccepted and not on main. OAuth/container persistence and real canary
  remain unproved; live ingestion is BLOCKED.
- Integration: no accepted cross-subsystem V2.0 campaign/report was found.
  `A-V20-INTEGRATION-FIXTURE` is READY and `A-V20-INTEGRATED-OS` BLOCKED.

## Highest-value locally reproducible defect

**An incomplete Gmail poll persists the messages it did fetch instead of failing
the ingestion transaction closed.** At candidate `10a3a23`,
`GmailAdapter.poll_messages()` records missing listed IDs and returns the other
messages (`src/jobs_automation/adapters/gmail.py:168-183`).
`EmailIngestionEngine.run_sweep()` inserts those returned messages, then merely
holds the checkpoint and commits (`ingestion/engine.py:187-316`). Existing test
`tests/test_gmail_adapter_bounded.py:196-207` explicitly expects four messages
ingested after one of five listed fetches fails. This violates J20G-01 in
`docs/V2_0_GMAIL_RUNTIME_READINESS.md`: failed listed fetch means sweep error,
no checkpoint advance, and **no partial committed rows**. It also risks lifecycle
effects from an incomplete evidence set before the retry fills the gap.

### Smallest synthetic reproduction plan

1. Use existing `FakeGmailService(_five_messages(), failing_ids={"m2"})`, SQLite
   session, `GmailAdapter`, and `EmailIngestionEngine`; no mailbox/network/grant.
2. Run one normal sweep and commit/expire the session.
3. Assert non-success/incomplete error, no checkpoint, and zero
   `InboundMessageModel`/derived link/task rows. Baseline at `10a3a23` will show
   `messages_ingested == 4`, no checkpoint, and four persisted message rows.
4. Run a successful retry and assert all five messages and one checkpoint appear
   exactly once. This distinguishes transaction fail-closed behavior from merely
   tracking the missing ID.

This is authorized independent engineering diagnosis only. The smallest repair
surface, after formal review/ownership resolution, is the adapter/ingestion
incomplete-poll boundary plus this focused regression; it requires no OAuth,
private input, live mailbox, browser, submission, new schema, or roadmap work.

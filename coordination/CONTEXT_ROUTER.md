# Context Router

Purpose: minimize repeated context loading while keeping every worker grounded in current Git truth.

## Always read

At session start:
1. `CLAUDE.md` or tool-specific thin adapter
2. `coordination/SESSION_START.md`
3. `state/CURRENT.md`
4. `coordination/WORK_QUEUE.md`
5. active artifact card
6. active heartbeat + latest lead review

Do **not** automatically read all roadmap/history documents.

## Current recovery through V1.7

When current work is V1.4–V1.7:
- `coordination/RECOVERY_QUEUE_V14_TO_V17.md`
- `docs/V1_4_TO_V1_7_RECOVERY_EXECUTION.md`
- active artifact card only
- `docs/LIVE_CHECKPOINT_EVIDENCE_STANDARD_V14_V17.md` only for live proof

For V1.6 submission safety also load:
- `docs/V1_6_SUBMISSION_CONTRACT.md`
- `docs/V1_6_DATA_CONTRACTS.md`
- `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`

## V2.0

Load only the relevant family:
- control center: V2.0 dashboard/control-center contracts + current dashboard code/tests
- reliability: V2.0 reliability/runbooks + migrations/worker/health code
- analytics: current analytics code/tests + V2.0 acceptance matrix
- Gmail: Gmail runtime/readiness docs + adapter/ingestion/worker code
- integration/live campaign: `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`, `docs/V2_0_INTEGRATION_ACCEPTANCE.md`, `docs/V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`

## V2.3

Load:
- `docs/V2_3_ACCEPTANCE_MATRIX.md`
- active V2.3 artifact card
- only its relevant contract/code.

V2.3 master planning set (PROPOSED until ChatGPT lead review; load only the file your task needs):
- `docs/V23_MASTER_PLAN.md` — critical path, artifact graph, migrations, model routing, live-proof matrix, V3 compatibility decisions
- `docs/V23_TASK_GRAPH_RECOVERY.md` / `docs/V23_TASK_GRAPH_V20.md` / `docs/V23_TASK_GRAPH_V23.md` — per-task specs (read only your task's entry)
- `docs/V23_TEST_MATRIX.md`, `docs/V2_3_ACCEPTANCE_CAMPAIGN.md`
- `coordination/V23_WORKER_QUEUE.md` — proposed execution order (not the active queue)

Families:
- opportunity graph
- strategy learning
- target-company watch
- interview intelligence
- typed agent-ready tool layer

Do not load V3 implementation docs merely to implement V2.3 unless interface compatibility is directly relevant.

## V3 compatibility planning

For architecture compatibility only, load:
- `docs/V3_PERMISSION_MODEL.md`
- `docs/V3_TOOL_PERMISSION_MATRIX.md`
- `docs/V3_RUNTIME_DATA_CONTRACTS.md`
- `docs/V3_SHARED_MEMORY_CONTRACT.md`
- `docs/V3_AGENT_HANDOFF_PROTOCOL.md`
- `docs/V3_SPECIALIST_AGENT_SPECS.md`

Broad V3 implementation should wait until V2.3 works unless the lead explicitly advances it.

## Historical context

Use `coordination/CONTEXT.md` and `state/DECISIONS.md` when a current decision needs historical reasoning.

Use old lane files, old PRs, and old audits only when tracing a specific implementation or regression.

## Search-before-read rule

For large documents/code:
1. search symbols/headings/commits,
2. inspect diff or relevant range,
3. open full file only if required.

A file already understood should not be reread unchanged in the same session.

# A-V23-CAREER-INTELLIGENCE

- Type: milestone / intelligence
- Phase: V2.3
- Status: PROPOSED
- Owner: ChatGPT + V2.3 implementation surface
- Reviewer: ChatGPT
- Dependencies: implementation acceptance depends on A-V23-OPPORTUNITY-GRAPH, A-V23-STRATEGY-LEARNING, A-V23-TARGET-COMPANY-WATCH, A-V23-INTERVIEW-INTELLIGENCE, A-V23-AGENT-TOOLS, A-V23-CAREER-BRIEFING and the engineering run of A-V23-ACCEPTANCE-CAMPAIGN; `REAL_PROVEN` additionally depends on all required prior live checkpoints (V1.4, V1.5, V1.6, V1.7), V2.0 `LIVE_ACCEPTED`, A-V20-LIVE-INGESTION, and a passing V2.3 live acceptance campaign with externally-confirmed application evidence (see lead-corrected D1/D9 in `docs/V23_MASTER_PLAN.md`)
- Downstream: V3.0

## Purpose

Bridge V2.0 operations to V3.0 agents with an evidence-backed opportunity graph, strategy learning, target-company intelligence, interview intelligence, a stable agent-ready tool layer, and one user-facing career briefing.

## Contract

See docs/V2_3_SPEC.md.

## Prepared foundation

- docs/V2_3_SPEC.md
- docs/V2_3_OPPORTUNITY_GRAPH_CONTRACT.md
- docs/V23_MASTER_PLAN.md (critical path, artifact graph, migrations, model routing, V3 compatibility)
- docs/V23_TASK_GRAPH_V23.md (55 SP1/SP2 tasks, 78 SP)
- docs/V2_3_ACCEPTANCE_CAMPAIGN.md (engineering + live evidence)

Start with relational evidence-backed relationships. Do not introduce a dedicated graph database until real query pressure justifies it. V2.3 is deterministic-first and must be useful without multi-agent orchestration.

## Acceptance matrix

See:
- `docs/V2_3_ACCEPTANCE_MATRIX.md`
- `docs/V23_TEST_MATRIX.md` (case → task → test mapping)

## Milestone labels

`ENGINEERING_ACCEPTED` after the six sub-artifacts and the engineering campaign are accepted; `REAL_PROVEN` only after all earlier required live checkpoints are accepted and the V2.3 live campaign report passes `scripts/verify_v23_campaign.py` and ChatGPT review. Only ChatGPT sets either label.

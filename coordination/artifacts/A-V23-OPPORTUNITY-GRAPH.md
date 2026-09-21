# A-V23-OPPORTUNITY-GRAPH

- Type: data/query architecture
- Phase: V2.3
- Status: READY
- Owner: single active implementation worker when V2.3 is the active work surface
- Reviewer: ChatGPT
- Story points: 12 (V23-OG-01..10) + shared foundation V23-F01/F03/F05
- Dependencies: migration `005_v23_intelligence_foundation` (V23-F03); V2 relational model on main
- Downstream: A-V23-CAREER-BRIEFING, A-V23-TARGET-COMPANY-WATCH (relationship signal), A-V23-AGENT-TOOLS, V3 agents

## Purpose
Expose evidence-backed relationships across opportunities, contacts, applications, resume strategy, skills, and outcomes without prematurely introducing a separate graph database.

## Contract
See docs/V2_3_OPPORTUNITY_GRAPH_SCHEMA.md and docs/V2_3_OPPORTUNITY_GRAPH_CONTRACT.md.

## Brownfield base (planning audit 2026-09-21)

`origin/worker/v23-foundations` commit `d99e774` contains `src/jobs_automation/intelligence/opportunity_graph.py` (933 LOC, read-only FK projection, six of seven typed queries, deterministic edge ids) and one integration test. It runs green on current main (ruff/mypy/pytest). Verdict: `REUSE_WITH_REPAIR` (≈45% of contract). Repairs: missing edge evidence fields (`observed_at`, `method`, `inferred`), nonexistent job status `evaluated`, substring email matching, no invalidation path, no place to persist user confirmation, N+1 queries, single happy-path test, contract query name mismatch, missing skill/project evidence.

## Planned tasks
V23-OG-01 port · OG-02 evidence fields · OG-03 status set + exact email match · OG-04 naming/isolation tests · OG-05 `message_link.contact_id` writes + backfill · OG-06 `OpportunityEdgeService` (propose/confirm/invalidate with provenance) · OG-07 projection merges persisted edges, deterministic `as_of` · OG-08 batching · OG-09 skill/project evidence nodes · OG-10 CLI. Full specs: `docs/V23_TASK_GRAPH_V23.md` §2.

## Acceptance
Contract acceptance tests (rebuild stable; same evidence no duplicate; invalidated hidden; inferred stays REVIEW_REQUIRED; user-confirmed becomes ASSERTED; queries preserve source refs) mapped in `docs/V23_TEST_MATRIX.md`.

# A-V23-CAREER-BRIEFING

- Type: implementation / user-facing intelligence composition
- Phase: V2.3
- Status: PROPOSED
- Owner: single active implementation worker when this artifact is active
- Reviewer: ChatGPT
- Story points: 6 (V23-CB-01..05, all SP1/SP2)
- Dependencies: A-V23-OPPORTUNITY-GRAPH, A-V23-STRATEGY-LEARNING, A-V23-TARGET-COMPANY-WATCH, A-V23-INTERVIEW-INTELLIGENCE (services), A-V20-ANALYTICS
- Downstream: A-V23-ACCEPTANCE-CAMPAIGN, A-V23-CAREER-INTELLIGENCE, V3 agents (typed input)

## Purpose

Answer the V2.3 user question in one typed, evidence-backed object: best opportunities now and why, who the user knows there, which resume to use, what to do next, and which interviews/follow-ups exist — with uncertainty and data gaps stated explicitly.

## Inputs

Open jobs with evaluations, applications and events, contacts and message links, interviews, tasks, resume variants and packets, strategy rates, target-company observations, candidate profile (private, local), policy decisions, worker/Gmail freshness.

## Outputs

`CareerBriefing` (Pydantic, inherits `DerivedArtifactEnvelope`), JSON schema at `docs/schemas/career_briefing.schema.json`, CLI `briefing [--json]`, GET `/api/briefing`.

## Scope

Composition and deterministic ranking only. Every element carries evidence refs; every rate carries N; `next_action` is an enum derived from evaluation, packet readiness, unresolved facts, and destination policy.

## Non-goals

No LLM prose, no external actions, no new persistence, no invented candidate or company facts.

## Acceptance criteria

- empty database yields a valid briefing consisting of data gaps, never an exception,
- fixture database yields deterministic output for a fixed `as_of`,
- MANUAL_ONLY destinations never produce `AWAIT_APPROVAL`,
- simulation rows in inputs flip `simulated=true`,
- injected job text never appears outside `key_requirements`/`security_signals`,
- schema file stays in sync (test-enforced).

## Evidence required

Commit SHA, focused tests (`tests/test_v23_briefing.py`, dashboard test), full-suite counts, validation record, JSON sample from the fixture campaign.

## Source/code paths

`src/jobs_automation/intelligence/briefing.py`, `cli/intelligence_cli.py`, `dashboard/server.py` (one GET handler), `docs/schemas/career_briefing.schema.json`.

## Risks

Ranking bias toward recently seen jobs (mitigated by explicit tie-break rule); low-N recommendations (mitigated by `GATHER_MORE_DATA` default).

## Current notes

Task specifications: `docs/V23_TASK_GRAPH_V23.md` §7. Planning evidence: `docs/V23_MASTER_PLAN.md` §3.

# A-V23-INTERVIEW-INTELLIGENCE

- Type: intelligence / preparation
- Phase: V2.3
- Status: PROPOSED
- Owner: V2.3 implementation surface (lane per lead decision D3)
- Reviewer: ChatGPT
- Story points: 10 (V23-II-01..07) + shared V23-F01/F02/F05, J20-20
- Dependencies: A-V17-INTERVIEW-FOLLOWUP code on main (`lifecycle/interview.py`, CRM timelines, `InterviewModel`), candidate evidence service (A-V12 minimal), `SemanticScorer.extract_requirements`, packet job snapshot (J20-20)
- Downstream: A-V23-CAREER-BRIEFING, A-V23-AGENT-TOOLS, A-V30-INTERVIEW-AGENT

## Purpose

Produce source-backed company/role/contact/interview briefs and candidate story maps that future agents can consume without inventing facts.

## Contract

See:
- `docs/V2_3_INTERVIEW_INTELLIGENCE_CONTRACT.md`

## Design note (planning pass 2026-09-21)
Deterministic-first: briefs, story maps and follow-up packages are assembled from evidence rows and the private candidate profile; no LLM is required for acceptance. Public/job text is treated as untrusted data (`core/untrusted_text.py` signals) and can populate only requirement/role-summary quotes and `security_signals`.

## Planned tasks
V23-II-01 typed models · II-02 expose requirement extraction · II-03 `build_brief` (people with refs, stage/schedule from `InterviewModel` only, staleness via `job_description_hash`, conflicts → review items) · II-04 story map (allowed vs unsupported claims; quantitative guard) · II-05 follow-up package (`send_performed=false`) · II-06 ten adversarial cases · II-07 CLI + endpoint. Full specs: `docs/V23_TASK_GRAPH_V23.md` §5.

## Acceptance

- role/company/contact facts have source references,
- candidate story map stays within canonical provenance,
- stale/conflicting evidence is visible,
- follow-up output is a draft/preparation artifact only,
- prompt injection/public content cannot change candidate truth or permissions,
- outputs are typed/stable enough for V3 tools/Interview Agent.

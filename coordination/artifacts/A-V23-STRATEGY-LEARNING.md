# A-V23-STRATEGY-LEARNING

- Type: analytics / strategy
- Phase: V2.3
- Status: PROPOSED
- Owner: Lane 3 (PG3) per `docs/V23_MASTER_PLAN.md` §6, subject to lead decision D3
- Reviewer: ChatGPT
- Story points: 9 (V23-SL-01..07) + shared V23-F01/F03/F04
- Dependencies: A-V20-ANALYTICS (`FunnelAnalyticsService` real-submission filters, historical outcomes, N/low-sample logic already on main), migration 004 experiment tables, `RoleFamilyClassifier`
- Downstream: A-V23-CAREER-BRIEFING, A-V23-AGENT-TOOLS, V3 Resume Strategist / Analytics Agent

## Contract
See docs/V2_3_STRATEGY_LEARNING_CONTRACT.md.

## Brownfield base (planning audit 2026-09-21)
Main already computes source, role-family, resume-variant, time-to-stage rates with N and `low_sample_size` (N<5), excludes simulation modes, attributes resume by `packet → resume_variant`. Gaps: recency windows, shared role-family definition, family rollup labeling, recommendation object, experiments, confounding warnings.

## Planned tasks
V23-SL-01 guardrails config · SL-02 `StrategyLearningService` rates with windows (wraps analytics) · SL-03 `StrategyRecommendation` + rule engine (`GATHER_MORE_DATA` default at low N; descriptive never HIGH) · SL-04 experiments (immutable assignment, `EXPERIMENTAL` evidence class) · SL-05 confounding/version-collapse guards · SL-06 adversarial tests · SL-07 CLI + `/api/strategy`. Full specs: `docs/V23_TASK_GRAPH_V23.md` §3.

## Acceptance
Adversarial rows (N=1, Simpson-like segments, stale outcomes, missing treatment, collapsed versions) mapped in `docs/V23_TEST_MATRIX.md`.

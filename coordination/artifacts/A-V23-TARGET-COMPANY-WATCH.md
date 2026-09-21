# A-V23-TARGET-COMPANY-WATCH

- Type: intelligence / monitoring
- Phase: V2.3
- Status: READY
- Owner: V2.3 implementation surface (lane per lead decision D3)
- Reviewer: ChatGPT
- Story points: 10 (V23-TW-01..07) + shared V23-F03/F04
- Dependencies: migration 004 (`target_company`, `target_company_observation`), `JobDeduplicationService`, evaluation filters/scorer, opportunity graph relationship queries
- Downstream: A-V23-CAREER-BRIEFING, A-V23-AGENT-TOOLS, V3 Market Scout

## Contract
See docs/V2_3_TARGET_COMPANY_WATCH.md.

## Brownfield base (planning audit 2026-09-21)
The only public ATS fetch on main is the Greenhouse board API call inside `scripts/import_v14_proof_job.py`; it is extracted into a reusable `ingestion/sources/` client (proof script behavior unchanged). Approved sources for V2.3: Greenhouse board JSON API and Lever postings JSON API only; no HTML scraping; one polite request per company per run.

## Planned tasks
V23-TW-01 source protocol + Greenhouse client extraction · TW-02 Lever client · TW-03 `TargetCompanyService` (defaults `PAUSED`; observation dedupe; relationship signal) · TW-04 `WatchRunner` (NEW/CHANGED/CLOSED; unavailable → no closures) · TW-05 fit, already-applied suppression, paused semantics · TW-06 CLI + optional worker flag (default off) · TW-07 adversarial tests. Full specs: `docs/V23_TASK_GRAPH_V23.md` §4.

## Acceptance
Contract acceptance (multiple role families per target; duplicate observations collapse; known jobs no repeated alerts; source evidence retained; relationship signal explainable; paused → no alerts) mapped in `docs/V23_TEST_MATRIX.md`. No outreach of any kind.

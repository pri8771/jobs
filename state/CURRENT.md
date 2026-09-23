# Current Jobs state — V2.3 implementation

Last updated: 2026-09-23

Owner directive: **get V2.3 working live**. Antigravity is the primary implementation workhorse. ChatGPT is lead/reviewer.

## Version history (accepted engineering)

| Version | Status | Key commit(s) |
|---------|--------|---------------|
| V1.4 P0A | ENGINEERING ACCEPTED | `8491dd9` |
| V1.5 | ENGINEERING ACCEPTED | `47fefd1` |
| V1.7 | ENGINEERING ACCEPTED (PR #12) | `7c0fa73` |
| V2.0 | Complete (merged into V2.3 scope) | — |
| V3.0 | Scaffolding complete | `9681d99` |

## V2.3 task graph progress

Reference: `docs/V23_TASK_GRAPH_V23.md` (55 tasks, 78 SP)

### Section 1 — Foundation (F01–F05): ✅ COMPLETE
- F01 DerivedArtifactEnvelope — `f055485`
- F02 UntrustedTextSanitizer — `f055485`
- F03 V2.3 schema/model extensions — `78ac8ac`
- F04 RoleFamilyClassifier extraction — `78ac8ac`
- F05 CandidateEvidenceService — `78ac8ac`

### Section 2 — Opportunity Graph (OG-01–OG-10): ✅ COMPLETE
- OG-01 OpportunityGraphService core — `a589874`
- OG-02 EdgeTraversal & evidence queries — `5d99724`
- OG-03 CompanyRelationshipProjection — `5d99724`
- OG-04 Deduplication integration — `5d99724`
- OG-05 MessageLinkContactWrites — `3be1fb4`
- OG-06 CandidateRoleMatching — `a0d391b`
- OG-07 OpportunityEdgeScoringAPI — `0555a2e`
- OG-08 ProfileResolutionEngine — `e2e5b94`
- OG-09 RecruiterCRMService adaptation — `0e1c96d`
- OG-10 Intelligence API surface — `0475d20`

### Section 3 — Strategy Learning (SL-01–SL-05): ✅ COMPLETE
- SL-01 StrategyGuardrails config — `ae5b0cc`
- SL-02 Descriptive performance rates — `2bf2b1b`
- SL-03 Strategy recommendation engine — `77b464d`
- SL-04 Adaptive resume variant selection — `2c8213b`
- SL-05 Guardrails wiring in job_search.py — `2c8213b`

### Section 4 — Target Company Watch (TW-01–TW-07): 🔶 IN PROGRESS
- TW-01 PublicJobSource protocol + Greenhouse — staged, untested in CI
- TW-02 Lever postings client — staged, untested in CI
- TW-03 TargetCompanyService — NOT STARTED
- TW-04 WatchRunner — NOT STARTED
- TW-05 Fit/suppression/paused semantics — NOT STARTED
- TW-06 Watch CLI + worker hook — NOT STARTED
- TW-07 Watch adversarial tests — NOT STARTED

### Section 5 — Interview Intelligence (II-01–II-07): NOT STARTED
### Section 6 — Agent Tools (TL-01–TL-08): NOT STARTED
### Section 7 — Career Briefing (CB-01–CB-05): NOT STARTED
### Section 8 — Acceptance Campaign (AC-01–AC-04): NOT STARTED

## Test health

- Total tests: ~440
- Passing: 438 (as of checkpoint)
- Failing: 1 (pre-existing `test_real_proof_integration` — requires production services)
- Skipped: 2

## Active worker

- Worker: Antigravity (this session)
- Last checkpoint commit: 2026-09-23
- Branch: `main`

## Immediate next tasks when resumed

1. Complete V23-TW-03 through TW-07 (Target Company Watch)
2. V23-II-01 through II-07 (Interview Intelligence)
3. V23-TL-01 through TL-08 (Agent Tools)
4. V23-CB-01 through CB-05 (Career Briefing)
5. V23-AC-01 through AC-04 (Acceptance Campaign)
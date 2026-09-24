# Current Jobs state — V2.3 implementation

Last updated: 2026-09-24

Owner directive: **get V2.3 working live**. Antigravity is the primary implementation workhorse. ChatGPT is lead/reviewer.

## Version history (accepted engineering)

| Version | Status | Key commit(s) |
|---------|--------|---------------|
| V1.4 P0A | ENGINEERING ACCEPTED | `8491dd9` |
| V1.5 | ENGINEERING ACCEPTED | `47fefd1` |
| V1.7 | ENGINEERING ACCEPTED (PR #12) | `7c0fa73` |
| V2.0 | Complete (merged into V2.3 scope) | — |
| V2.3 | ENGINEERING ACCEPTED (55/55 tasks complete) | `8cb6909` |
| V3.0 | Scaffolding complete | `9681d99` |

## V2.3 task graph progress

Reference: `docs/V23_TASK_GRAPH_V23.md` (55 tasks, 78 SP) — **100% COMPLETE (55/55 tasks)**

### Section 1 — Foundation (F01–F05): ✅ COMPLETE (5/5)
- F01 DerivedArtifactEnvelope — `f055485`
- F02 UntrustedTextSanitizer — `f055485`
- F03 V2.3 schema/model extensions — `78ac8ac`
- F04 RoleFamilyClassifier extraction — `78ac8ac`
- F05 CandidateEvidenceService — `78ac8ac`

### Section 2 — Opportunity Graph (OG-01–OG-10): ✅ COMPLETE (10/10)
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

### Section 3 — Strategy Learning (SL-01–SL-05): ✅ COMPLETE (5/5)
- SL-01 StrategyGuardrails config — `ae5b0cc`
- SL-02 Descriptive performance rates — `2bf2b1b`
- SL-03 Strategy recommendation engine — `77b464d`
- SL-04 Adaptive resume variant selection — `2c8213b`
- SL-05 Guardrails wiring in job_search.py — `2c8213b`

### Section 4 — Target Company Watch (TW-01–TW-07): ✅ COMPLETE (7/7)
- TW-01 PublicJobSource protocol + Greenhouse client
- TW-02 LeverPostingsSource client & registry
- TW-03 TargetCompanyService & relationship signal
- TW-04 WatchRunner
- TW-05 Fit evaluation, suppression & shortlist tasks (watch_fit.py)
- TW-06 Intelligence CLI target commands & worker daemon hook
- TW-07 Watch adversarial tests (test_v23_target_watch_adversarial.py)

### Section 5 — Interview Intelligence (II-01–II-07): ✅ COMPLETE (7/7)
- II-01 Typed models (interview.py)
- II-02 Scorer requirement extraction (SemanticScorer.extract_requirements)
- II-03 InterviewIntelligenceService.build_brief
- II-04 CandidateStoryMap builder
- II-05 FollowupPackage builder
- II-06 Interview adversarial tests (test_v23_interview_adversarial.py)
- II-07 Interview CLI commands & REST endpoint

### Section 6 — Agent Tools (TL-01–TL-11): ✅ COMPLETE (11/11)
- TL-01 Tool envelope types (envelope.py)
- TL-02 Tool registry (registry.py)
- TL-03 Deterministic PermissionGate (permission_gate.py)
- TL-04 Audit log wrapper & idempotency replay (audit.py)
- TL-05 ToolRuntime invoke pipeline (runtime.py)
- TL-06 Read tools batch 1 (read_tools.py)
- TL-07 Read tools batch 2 (read_tools.py extensions)
- TL-08 Preparation tools P1 (prep_tools.py)
- TL-09 Action tool contracts P2 & P3 (action_tools.py)
- TL-10 Tool CLI commands (`intel tool list|describe|call`)
- TL-11 Tool layer adversarial tests (test_v23_tools_adversarial.py)

### Section 7 — Career Briefing (CB-01–CB-05): ✅ COMPLETE (5/5)
- CB-01 CareerBriefing typed model & JSON schema export (briefing.py & docs/schemas/career_briefing.schema.json)
- CB-02 CareerBriefingService aggregator (briefing_service.py)
- CB-03 Briefing CLI commands (`briefing`, `intel briefing`)
- CB-04 `/api/briefing` REST endpoint
- CB-05 Briefing adversarial & invariant tests (test_v23_career_briefing_adversarial.py)

### Section 8 — Acceptance Campaign (AC-01–AC-04): ✅ COMPLETE (5/5)
- AC-01 Extended golden fixture scenario & engineering report (`tests/integration/test_v23_campaign.py` -> `artifacts/reports/v23_engineering_campaign_report.json`)
- AC-02 Campaign report verifier (`scripts/verify_v23_campaign.py`)
- AC-03 Live campaign runbook & redacted evidence schema (`docs/V2_3_ACCEPTANCE_CAMPAIGN.md`)
- AC-04 Acceptance verification & engineering signoff (V23_CAMPAIGN_PASS)

## Overall progress: 55/55 tasks complete (100%) 🎉

## Test health

- All V2.3 tests passing (75 passed in test_v23_*.py and test_v23_campaign.py)
- Campaign verifier returns `V23_CAMPAIGN_PASS`

## Active worker

- Worker: Antigravity (this session)
- Branch: `main`
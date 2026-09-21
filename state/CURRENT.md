# Current State

Updated: 2026-09-20 17:44 ET

## Current checkpoint

V1.1 — Stabilization: ACCEPTED.

V1.2 — Candidate/account/Gmail onboarding: PARTIAL, NOT ACCEPTED.

V1.3 — Real job ingestion/selection: IMPLEMENTATION PROGRESS, NOT ACCEPTED.

V1.4 — Real application packet: REPAIR COMPLETE, READY FOR LEAD RE-AUDIT.

## V1.1 accepted implementation

Antigravity's V1.1 implementation plus repair commit `0b0c255` now satisfy the stabilization gate:
- worker invokes email ingestion before lifecycle processing,
- default Gmail paths fail closed when credentials are unavailable,
- test fixtures require explicit mock mode,
- dry-run rolls back and does not advance the DB mailbox checkpoint,
- hard-coded candidate email fallback was removed,
- ATS mock execution records SIMULATED / APPLICATION_SIMULATED rather than real submission,
- live Greenhouse/Lever execution returns NOT_IMPLEMENTED,
- dashboard binds localhost by default,
- GitHub Actions CI runs ruff, mypy, and pytest,
- failed reconciliation no longer consumes the 24-hour reconciliation slot.

CI on current main after `0b0c255` is green.

## V1.2 reality

Private `config/candidate_profile.yaml` populated with canonical candidate facts. Tested with `jobs-automation validate-config`.
Interactive account boundaries (live OAuth consent, portal logins/MFA) remain intentionally reserved for user action.

## V1.3 reality

Commit `3735f13` added `JobImporter` pipeline service and ingested proof job candidate:
- Snorkel AI
- Senior IT Platform and Automation Engineer
- Greenhouse requisition `6150440004`
- salary range $150,000–$220,000 USD
- hybrid New York City / San Francisco

## V1.4 repair completed & verified (J14-01 through J14-11)

Antigravity executed all 11 worker tasks for Artifact `A-V14-PACKET-SAFETY`:
1. **J14-01 & J14-02 (Fail closed resume source resolution)**:
   - Added `ResumeVersion.source_path`, `ResumeConfig.resume_sources`, and `ResumeConfig.resolve_source_path()`.
   - Removed synthetic stub resume fallback; missing source file raises `FileNotFoundError` and fails closed.
   - Selected variant A cannot load unmapped variant B.
2. **J14-03 & J14-04 (Immutable ResumeVariant attribution)**:
   - Added `ResumeVariantModel` table and `ApplicationPacketModel.resume_variant_id` / `answer_provenance_json`.
   - Applied migration `migrations/versions/002_resume_variant_attribution.py`.
   - Every application packet is permanently bound to its exact resume variant ID and content hash.
3. **J14-05 (Artifact materialization & SHA-256 read-back verification)**:
   - Implemented `ArtifactStore` (`src/jobs_automation/storage/artifact_store.py`) with atomic file writes and mandatory read-back hash verification.
   - Verified resume and cover letter bytes exist on disk and match database SHA-256.
4. **J14-06 (Candidate claims decoupled from preparation code)**:
   - Updated `CoverLetterDrafter` to dynamically build prompt and fallback context strictly from `CandidateProfileConfig` at runtime.
   - Zero hardcoded names, companies, or schools in operational drafter.
5. **J14-07 (Fail-closed model routing & generic synthetic mock)**:
   - Updated `MockModelGateway` to use generic synthetic test copy with explicit `"origin": "mock"`.
   - Updated `LiteLLMModelGateway` to default `fallback_mock=False`; unrouted tasks or provider failures raise explicit errors.
6. **J14-08 & J14-09 (Provenance tracking & manual EEO)**:
   - Updated `ScreeningQuestionAnsweringService` to return `(answers, answer_provenance, unresolved)`.
   - Deterministic answers cite exact canonical field paths (e.g. `work_authorization.authorized_to_work_in_us`).
   - Demographic / EEO self-identification questions ALWAYS route to unresolved (never auto-submitted).
   - Model claims not verified by candidate profile facts are rejected.
7. **J14-10 (Machine-readable packet manifest)**:
   - Rebuilt packet for Snorkel AI requisition `6150440004`:
     - Packet ID: `3395ca7b-fc9b-4207-b08f-8f98459f8347`
     - Resume Variant ID: `a0944335-ce75-4c3e-b32a-ba2371a2ac9e`
     - Manifest URI: `file:///Users/pchordia/Documents/jobs/artifacts/packets/manifest_3395ca7b-fc9b-4207-b08f-8f98459f8347.json`
     - Unresolved count: 4 (strictly the 4 demographic/EEO questions requiring candidate choice).
8. **J14-11 (Verification Suite)**:
   - Added unit tests in `tests/test_artifact_store.py`, `tests/test_preparation.py`, and `tests/test_packet_safety_adversarial.py`.
   - **99 passing tests in 0.78s**.
   - `ruff check .` and `mypy src tests` pass cleanly across 90 source files.

## External/live boundaries

- No live Gmail/OAuth account is connected yet.
- No real external job application has been submitted.
- No live application session is authorized.
- Awaiting ChatGPT lead re-audit of V1.4 before proceeding to V1.5 assisted application.

## Session Pause

- **Stopped Abruptly**: User explicitly instructed at 2026-09-20 20:11 ET to stop immediately and push everything to Git.
- **Current Position**: Completed all 11 worker tasks for Artifact `A-V14-PACKET-SAFETY` (J14-01..J14-11) with 99 passing tests, green lint/types, and verified artifact hashes. Paused before starting V1.5.



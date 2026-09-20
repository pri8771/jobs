# Current State

Updated: 2026-09-20 17:44 ET

## Current checkpoint

V1.1 — Stabilization: ACCEPTED.

V1.2 — Candidate/account/Gmail onboarding: PARTIAL, NOT ACCEPTED.

V1.3 — Real job ingestion/selection: IMPLEMENTATION PROGRESS, NOT ACCEPTED.

V1.4 — Real application packet: REJECTED PENDING SAFETY/ATTRIBUTION REPAIR.

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

Antigravity reports a private `config/candidate_profile.yaml` was populated from a local `jobs/profile.md` and validates with zero unresolved facts.

Lead review cannot treat that as verified milestone completion because:
- the cited `jobs/profile.md` is not present in Git,
- the private YAML is intentionally ignored and therefore not independently auditable here,
- real Gmail OAuth/account onboarding has not occurred,
- LinkedIn/Indeed/ZipRecruiter/Dice account/profile/alert readiness has not been demonstrated.

Candidate configuration work is useful progress, but V1.2 remains partial until provenance and user-interactive account boundaries are satisfied.

## V1.3 reality

Commit `3735f13` adds `JobImporter` / `import-jobs` and real-job pipeline import capability.

The proposed proof job is currently live externally:
- Snorkel AI
- Senior IT Platform and Automation Engineer
- Greenhouse requisition `6150440004`
- salary range $150,000–$220,000 USD
- hybrid New York City / San Francisco

This is a useful real candidate job, but not yet an accepted proof-job selection because:
- the intended real Gmail/job-alert ingestion canary has not run,
- candidate relocation/location compatibility is not lead-verified,
- user has not selected/approved this job as one they actually want.

The reported 84.4 score is therefore descriptive pipeline output, not sufficient proof of milestone exit.

## V1.4 lead-audit findings

The current packet implementation must not be used for a live application yet.

### Critical findings

1. `ApplicationPacketBuilder` silently creates a synthetic resume stub when no source resume file is found.
2. The builder selects a resume variant name but then reads the first existing base resume path rather than proving that file belongs to the selected variant.
3. Artifact database rows contain storage URIs/hashes, but the builder does not actually materialize the resume/cover-letter contents to those URIs.
4. Required immutable resume-variant/version persistence from `docs/RESUME_OUTCOME_TRACKING.md` is not implemented in the database model; `ApplicationPacketModel` has only `resume_artifact_id`, not `resume_variant_id`.
5. `CoverLetterDrafter` hard-codes candidate-specific employment/education/achievement claims rather than deriving all claims from canonical evidence.
6. `MockModelGateway` contains candidate-specific known answers, including an `8+ years` Python answer.
7. `LiteLLMModelGateway` defaults to mock fallback, so model/provider failure can silently substitute mock candidate content.
8. `ScreeningQuestionAnsweringService` sends only the question to the model and trusts model `resolved=true` output without validating the asserted fact against canonical profile evidence.
9. Demographic/EEO questions can be auto-filled if values exist, contradicting the existing decision that self-identification questions must remain manual.

Because of these findings, the reported packet ID/hash, `0 unresolved questions`, and V1.5 prefill readiness are not accepted as live-ready evidence.

## Immediate next action

Antigravity should execute the P0 repair now defined in `coordination/WORK_QUEUE.md`:
- fail closed on missing resume source,
- explicitly map resume family/variant -> exact source,
- implement immutable resume-variant persistence/linkage,
- materialize real artifacts and verify hashes,
- remove hard-coded candidate facts from operational preparation code,
- disable operational mock fallback,
- require canonical provenance for screening answers,
- force demographic/EEO questions to manual/unresolved,
- rebuild and re-audit the packet only after those fixes.

## External/live boundaries

- No live Gmail/OAuth account is connected yet.
- No real external job application has been submitted.
- No live application session is authorized.
- LinkedIn and Indeed submission remain MANUAL_ONLY.
- Do not present the Snorkel packet for live authorization until V1.4 passes the safety/attribution gate.

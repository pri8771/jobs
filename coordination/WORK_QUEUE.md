# Active Work Queue

ChatGPT owns priority/order unless the user explicitly overrides it.
Antigravity executes the highest-priority unblocked work, tests it, commits, pushes, and reports through coordination/AI_SYNC.md.

Last prioritized: 2026-09-20 18:57 ET

## Strategic finish line

Current scope ends when Jobs Automation demonstrates one genuine, externally confirmed application submitted through the system for a real job the user actually wants.

Path:
- V1.1 stabilization
- V1.2 real candidate/account/Gmail onboarding
- V1.3 real job ingestion/selection
- V1.4 real application packet with immutable resume attribution
- V1.5 assisted real application
- V1.6 first genuine system-submitted application

After V1.6, stop broad development and request strategy review.

## Current checkpoint

### EXECUTION PRIORITY — V1.4 LIVE-READINESS ASAP

Artifact: A-V14-PACKET-SAFETY

Until the V1.4 packet-safety gate passes, Antigravity should treat V1.4 P0 as the sole engineering priority.

Do not spend implementation cycles on:
- additional dashboard features,
- new ATS adapters,
- LinkedIn/networking features,
- V2/V3 infrastructure,
- optional analytics,
- non-blocking V1.2 polish.

Only do work outside V1.4 P0 if it is strictly necessary to make the real application packet safe and independently verifiable.

The target is not "more features." The target is:
**a truthful, immutable, inspectable application packet that can safely proceed to V1.5.**

### V1.1 — ACCEPTED

Commit `0b0c255` fixes the lead-review reconciliation bug: failed adapter/polling paths no longer consume the 24-hour reconciliation slot. Regression coverage was added and CI on current main is green.

### V1.2 — PARTIAL, NOT ACCEPTED

Antigravity prepared a private candidate profile and reported zero unresolved facts, but the underlying local `jobs/profile.md` / private YAML is not available in Git for lead verification. The milestone also originally includes real account/Gmail onboarding, which has not occurred and remains user-interactive.

Do not call V1.2 complete until the required private candidate facts/resume sources are provenance-checked and the user-authorized account/Gmail onboarding boundary is satisfied.

### V1.3 — IMPLEMENTATION PROGRESS, NOT ACCEPTED

`JobImporter` and `import-jobs` exist, and the Snorkel AI posting `6150440004` is externally verified live as of 2026-09-20. It is a hybrid New York City / San Francisco role, so it must not be treated as the user's chosen proof job until location/relocation fit is explicitly confirmed.

V1.3 exit still requires a real ingestion canary from the intended discovery path and a reviewed proof-job selection grounded in verified candidate constraints.

### V1.4 — REJECTED PENDING SAFETY/ATTRIBUTION REPAIR

The current packet-preparation implementation is not safe enough for a real application. Fix the P0 items below before presenting any packet for user authorization.

## Worker execution breakdown — V1.4

Use these task IDs for implementation and heartbeat reporting. Story points measure complexity, not time.

| Task ID | SP | Task | Dependency |
|---|---:|---|---|
| J14-01 | 2 | Fail closed when exact selected resume source is missing | none |
| J14-02 | 2 | Implement exact resume variant -> source mapping | none |
| J14-03 | 3 | Add ResumeVariant model + migration | none |
| J14-04 | 2 | Persist packet -> ResumeVariant linkage | J14-03 |
| J14-05 | 3 | Materialize resume/cover-letter artifacts and verify read-back hashes | none |
| J14-06 | 2 | Remove hard-coded candidate claims from operational preparation | none |
| J14-07 | 2 | Make real model routing/provider failure fail closed; explicit mock only | none |
| J14-08 | 3 | Add screening-answer provenance and reject unsupported model claims | none |
| J14-09 | 1 | Force EEO/demographic/self-ID questions to manual/unresolved | none |
| J14-10 | 3 | Rebuild machine-readable inspectable packet manifest | J14-01..J14-09 |
| J14-11 | 1 | Produce complete verification/evidence bundle | J14-10 |

Execution guidance:
- Antigravity owns all J14 tasks.
- Parallelize independent J14-01/02/03/05/06/07/08/09 where practical.
- Do not wait for J14-03 to finish before doing unrelated tasks.
- J14-04 follows J14-03.
- J14-10 and J14-11 are integration/verification steps.
- Report task IDs in commits/AI_SYNC when practical.
- ChatGPT updates coordination/WORKER_PERFORMANCE.md after audit.
- If any task proves materially harder than its current shape, report the blocker; ChatGPT will split it further.

Detailed file-level guidance:
- docs/V1_4_REPAIR_GUIDE.md

## P0 — Application packet safety and truthfulness

### 1. Fail closed when the selected resume source is missing

Current `ApplicationPacketBuilder` silently creates a synthetic stub resume when no base resume file is found.

Required:
- remove the synthetic resume fallback from operational packet building,
- if the exact selected resume cannot be resolved/read, stop with a clear error / NEEDS_REVIEW,
- never mark a packet real/reviewable when the resume bytes were not actually available.

### 2. Map resume family/variant to the exact source artifact

Current builder selects a variant name, then uses the first existing `base_resume_paths` entry rather than resolving the file corresponding to that variant.

Required:
- explicit mapping from resume family/variant ID -> exact source file,
- immutable resume variant/version record as required by `docs/RESUME_OUTCOME_TRACKING.md` and `docs/DATA_MODEL.md`,
- persistent `application_packet.resume_variant_id` linkage (with migration/model),
- preserve parent/base version and job-specific tailoring identity where applicable,
- add tests proving the wrong family cannot be silently used.

### 3. Materialize real immutable artifacts

Current packet builder creates `ArtifactModel.storage_uri` values but does not write the resume/cover-letter contents to those URIs.

Required:
- artifact URI must reference bytes that actually exist and whose SHA-256 matches the database record,
- content must be immutable once a packet is submitted,
- tests must read the stored artifact back and verify the hash.

### 4. Remove hard-coded candidate facts from preparation code

`CoverLetterDrafter` currently hard-codes candidate-specific claims in prompts/fallback copy. `MockModelGateway` also contains candidate-specific claims (including an `8+ years` Python answer).

Required:
- operational code derives candidate claims only from canonical profile/resume evidence,
- no hard-coded candidate employment, education, achievement, tenure, or skill-duration claims,
- test fixtures may use synthetic test candidates, but must not become runtime truth.

### 5. No mock/known-answer fallback in real application preparation

`LiteLLMModelGateway` defaults to `fallback_mock=True`; a provider/configuration failure can therefore silently substitute deterministic mock answers/cover-letter copy.

Required:
- real packet/application mode must fail closed on model/provider failure,
- mock gateway is test/dev-only and must be explicitly selected,
- runtime must expose whether output came from a real model, deterministic rules, or test mock,
- no packet can be considered real if any consequential content came from a mock fallback.

### 6. Screening answers must be provenance-checked

Current `ScreeningQuestionAnsweringService` sends only the question to the model and trusts any `{resolved: true, answer: ...}` response.

Required:
- deterministic answers must cite the exact canonical candidate field/source used,
- model-assisted answers may draft wording but cannot assert a candidate fact absent from canonical evidence,
- unknown experience-duration/skill/eligibility questions must route to unresolved review,
- add regression tests for hallucinated `resolved=true` model responses and missing profile facts.

### 7. Demographic/EEO questions always require candidate choice

Existing architecture decision says demographic self-identification must never be auto-filled. Current code will auto-answer if demographic values exist in profile config.

Required:
- race/ethnicity/gender/disability/veteran/sexual-orientation questions always remain unresolved/manual,
- do not auto-submit stored demographic values.

### 8. Rebuild the Snorkel packet only after repairs

After P0 passes:
- rebuild from exact verified resume bytes,
- produce a machine-readable packet manifest with resume family, immutable variant/version, actual artifact hashes, cover letter, every screening question/answer, and provenance,
- report any unresolved fields honestly,
- do not claim `0 unresolved` based on mock/LLM-only answers.

Acceptance for V1.4 repair:
- pytest, ruff, mypy green,
- GitHub CI green,
- no operational mock fallback,
- exact resume artifact can be read back and hash-verified,
- exact resume variant is permanently linked to packet/application,
- all screening answers have canonical provenance or are unresolved,
- packet can be independently inspected by ChatGPT/user without relying on an unverified local-only claim.

## P1 — DEFER UNTIL V1.4 P0 PASSES

V1.2 engineering readiness work is temporarily deprioritized. Resume only after ChatGPT accepts V1.4 packet safety, unless a V1.4 blocker specifically depends on one of these items.

### Deferred V1.2 engineering readiness

1. Candidate-fact provenance report
- produce a local/private provenance report for every non-null candidate fact,
- distinguish user-confirmed, source-document-derived, inferred, and unknown,
- inferred values may not become application truth without user confirmation,
- do not commit private candidate contents to Git.

2. Gmail OAuth readiness
- exact runtime configuration validation and diagnostics,
- Google Cloud/OAuth setup documentation,
- read-only Gmail scopes first,
- harmless canary check design,
- fail closed when credentials are absent.

3. Source/account onboarding checklist
- LinkedIn, Indeed, ZipRecruiter, Dice profile/alert readiness,
- record status without passwords,
- identify smallest user actions for login/MFA/verification.

4. Real-ingestion canary plan
- first read-only Gmail sweep,
- evidence proving no mock/fixture path,
- rollback/recovery if parsing is wrong.

## User-interactive boundaries

Do not fabricate or bypass:
- missing/private candidate facts,
- canonical resume source files,
- relocation/location preference for the Snorkel hybrid role,
- Google Cloud OAuth consent/credentials,
- Gmail authorization,
- job-board login/MFA/phone/email verification,
- approval of the exact proof job,
- approval of the exact application packet,
- live submission.

## V1.5 — blocked

Do not prefill or open a live application session until V1.4 is accepted and the user has reviewed the exact safe packet.

## V1.6 — blocked

No live submission without explicit user authorization for that exact job/packet/method and external confirmation evidence.

## Standing safety rules

- LinkedIn submission: MANUAL_ONLY.
- Indeed submission: MANUAL_ONLY.
- No CAPTCHA bypass or anti-bot evasion.
- No fabricated candidate facts.
- Simulation/mock fallback never equals real preparation or submission.
- External confirmation is required for real submission state.
- V2/V3 remains tentative reference only until after the first-real-application proof.


## Artifact-backed future worker TODOs

These are prepared in advance. Do not start blocked tasks until dependencies are accepted or ChatGPT moves them to READY.

### Artifact A-V15-ASSISTED-APPLICATION

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| J15-01 | 2 | BLOCKED | Implement form-field classification + canonical provenance mapping | A-V14 ACCEPTED |
| J15-02 | 2 | BLOCKED | Implement manual-barrier classifier for login/MFA/CAPTCHA/EEO/unknown fields | A-V14 ACCEPTED |
| J15-03 | 3 | BLOCKED | Build pre-submit review manifest from accepted packet + mapped form | J15-01, J15-02 |
| J15-04 | 2 | BLOCKED | Verify uploaded resume/cover-letter hashes match accepted packet artifacts | J15-01 |
| J15-05 | 3 | BLOCKED | Capture external confirmation evidence after assisted user submit | user-approved proof job + assisted run |
| J15-06 | 2 | BLOCKED | Persist assisted application audit/lifecycle evidence | J15-05 |

Artifact docs:
- coordination/artifacts/A-V15-ASSISTED-APPLICATION.md
- docs/V1_5_FAST_START.md

### Artifact A-V16-SUBMISSION-CONTRACT / A-V16-FIRST-REAL-SUBMISSION

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| J16-01 | 2 | BLOCKED | Persist exact job/packet/method-specific user authorization record | A-V15 ACCEPTED |
| J16-02 | 2 | BLOCKED | Implement stable idempotency key + duplicate submission guard | A-V15 ACCEPTED |
| J16-03 | 3 | BLOCKED | Implement PREPARED/AUTHORIZED/SUBMITTING/UNCONFIRMED/SUBMITTED/FAILED states | A-V15 ACCEPTED |
| J16-04 | 3 | BLOCKED | Implement ambiguous-submit recovery that checks external evidence before retry | J16-02, J16-03 |
| J16-05 | 2 | BLOCKED | Require external confirmation before APPLICATION_SUBMITTED | J16-03 |
| J16-06 | 2 | BLOCKED | Produce exact preflight/audit manifest for first system submission | J16-01..J16-05 |

Artifact docs:
- docs/V1_6_SUBMISSION_CONTRACT.md
- coordination/artifacts/A-V16-SUBMISSION-CONTRACT.md
- coordination/artifacts/A-V16-FIRST-REAL-SUBMISSION.md

### Artifact A-V12-CANDIDATE-PROVENANCE

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| J12-01 | 2 | BLOCKED | Implement machine-readable candidate fact provenance record | V1.4 gate cleared |
| J12-02 | 2 | BLOCKED | Enforce allowed_for_application against inferred/unknown facts | J12-01 |
| J12-03 | 1 | BLOCKED | Add private-safe provenance validation/report command | J12-01 |

### Artifact A-V12-GMAIL-CANARY

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| J12-04 | 2 | BLOCKED | Add Gmail OAuth/runtime diagnostics without secrets | V1.4 gate cleared |
| J12-05 | 2 | BLOCKED | Add bounded read-only dry-run canary command/evidence output | J12-04 + user OAuth |
| J12-06 | 2 | BLOCKED | Add bounded write-enabled idempotency canary | J12-05 accepted |

Runbook:
- docs/GMAIL_CANARY_RUNBOOK.md

### Artifact A-PROOF-JOB-SELECTION

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| J13-01 | 2 | BLOCKED | Produce proof-job candidate record/shortlist format | V1.4 gate cleared |
| J13-02 | 2 | BLOCKED | Add hard-gate checks for compensation/location/authorization/already-applied | J13-01 |
| J13-03 | 1 | BLOCKED | Produce user-facing approve/reject/hold proof-job review | J13-01, J13-02 |

Criteria:
- docs/PROOF_JOB_SELECTION.md

### Artifact A-RESUME-OUTCOME-METRICS

| Task ID | SP | Status | Task | Depends on |
|---|---:|---|---|---|
| JMET-01 | 2 | BLOCKED | Add outcome query contract by resume family/version | first real application data |
| JMET-02 | 3 | BLOCKED | Implement conversion/time-to-stage aggregation service | JMET-01 |
| JMET-03 | 2 | BLOCKED | Add sample-size/correlation warnings to resume performance output | JMET-02 |

Performance:
- coordination/WORKER_PERFORMANCE.md

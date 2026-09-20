# Current State

Updated: 2026-09-20

## Current checkpoint

V0.3 — Filtering, scoring, and application preparation (IMPLEMENTED & VERIFIED)

## Completed in V0.3

- **Deterministic Hard Filters** (`src/jobs_automation/evaluation/filters.py`):
  - Evaluates minimum compensation threshold ($150k target floor).
  - Enforces location and remote work policy (Pittsburgh, PA or Remote US).
  - Checks security clearance exclusions (excludes TS/SCI/Polygraph).
  - Filters out non-target title patterns (Intern, Staffing Agency, Junior, Sales, etc.).
  - Checks candidate work authorization against employer sponsorship requirements; flags unverified requirements for review rather than assuming eligibility.
- **Multi-Dimensional Semantic Fit Scorer** (`src/jobs_automation/evaluation/scorer.py`):
  - Weighted scoring formula: title match (30%), must-have skills (25%), preferred skills (15%), compensation (10%), location (10%), seniority (5%), freshness (5%).
  - Role track mapping to candidate positioning tracks: Enterprise Automation, SAP BTP, Mobile / iOS, AI Software Engineer, and Technical Product.
  - Action threshold mapping: `SHORTLIST` (>= 70), `CONSIDER` (>= 55), `REJECT` (< 55).
- **Job Evaluation Engine** (`src/jobs_automation/evaluation/engine.py`):
  - Orchestrates hard filtering and scoring against discovered jobs.
  - Persists evaluation results into `JobEvaluationModel` with detailed factor breakdowns and reason codes.
  - Updates `JobModel.status` (`SHORTLISTED`, `CONSIDERED`, `FILTERED_OUT`).
  - Automatically enqueues `NEEDS_REVIEW` tasks in `TaskModel` for borderline roles or jobs with unverified requirements.
- **Model Gateway** (`src/jobs_automation/adapters/models.py`):
  - Pluggable `ModelGateway` interface supporting LiteLLM routing (`LiteLLMModelGateway`) and offline deterministic testing (`MockModelGateway`).
  - Zero provider lock-in; easily swaps OpenAI, Anthropic, Gemini, or local models.
- **Resume Variant Selection & Tailoring Pipeline** (`src/jobs_automation/preparation/tailoring.py`):
  - `ResumeVariantSelector`: Dispatches to `resume_enterprise_automation` (primary), `resume_sap_btp`, `resume_mobile_ios`, `resume_ai_software_engineer`, or `resume_technical_product`.
  - `CoverLetterDrafter`: Generates truthful cover letters citing verified career achievements (Viatris SAP BTP, Thar Process IT head, CMU degree).
  - `ScreeningQuestionAnsweringService`: Formulates answers strictly from candidate profile facts; **strictly flags demographic questions (race, ethnicity, gender, veteran, disability) and unverified claims (relocation, unconfirmed sponsorship) as unresolved**.
- **Application Packet Builder** (`src/jobs_automation/preparation/packet_builder.py`):
  - Compiles complete `ApplicationPacketModel` linking job, candidate profile, selected resume variant, generated cover letter, and prefilled questions.
  - Persists resume and cover letter markdown as immutable `ArtifactModel` records.
  - Computes deterministic SHA-256 `packet_hash` over contents for reproducibility and idempotency.
  - Enqueues `NEEDS_REVIEW` tasks for any unresolved questions.
- **CLI Commands**:
  - Added `jobs-automation evaluate-jobs` (with `--limit`, `--min-score`, and `--dry-run`).
  - Added `jobs-automation prepare-packets` (with `--limit` and `--dry-run`).
  - Added `jobs-automation review-queue` (with `--status` filter).
- **Testing & Verification**:
  - Added `tests/test_evaluation.py` (7 tests covering hard filters, scoring weights, reason codes, engine evaluation).
  - Added `tests/test_preparation.py` (5 tests covering variant selection, question answering, refusal of demographic questions, packet hashing).
  - Full test suite: 55 passing tests.

## Verification performed

1. `pytest -v`: All 55 tests passing in 0.70s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All source files formatted cleanly.
4. `mypy src tests`: Strict type checking passed with zero errors across 55 source files.
5. Live PostgreSQL CLI integration test:
   - `jobs-automation evaluate-jobs`: Evaluated 5 jobs; 1 shortlisted, 4 considered; `JobEvaluationModel` records and `NEEDS_REVIEW` tasks persisted.
   - `jobs-automation prepare-packets`: Prepared application packet for shortlisted job (Accenture SAP BTP) with `resume_sap_btp` variant; created `ArtifactModel` records and deterministic SHA-256 hash.
   - `jobs-automation review-queue`: Verified 4 active tasks queued for candidate review.

## Current blockers

None.

## Exact next task (V0.4)

Implement **V0.4 — Assisted application**:
- Destination classification and policy check (`PolicyEvaluator` ensuring LinkedIn/Indeed are `MANUAL_ONLY` / `ASSISTED`).
- Local visible browser runner (`PlaywrightBrowserRunner` / interactive form inspection).
- Safe field mapping (prefilling candidate profile facts without auto-submitting).
- Human review gate before submission (explicit user confirmation).
- Capture submission confirmation, proof/receipt, and create `ApplicationEventModel` and `AuditLogModel`.
- CLI commands `assisted-apply` and `review-queue`.

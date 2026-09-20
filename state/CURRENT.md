# Current State

Updated: 2026-09-20

## Current checkpoint

V0.5 — Controlled automatic application (IMPLEMENTED & VERIFIED)

## Completed in V0.5

- **ATS Submission Base** (`src/jobs_automation/automation/base.py`):
  - Defined abstract `ATSAdapter` class with typed methods: `platform_name`, `can_handle`, `validate_packet`, and `submit_application`.
  - Defined Pydantic models `ValidationResult` and `SubmissionResult` capturing atomic receipts (receipt ID, confirmation URL, submitted fields, response payload).
- **Allowlisted ATS Adapters** (`src/jobs_automation/automation/adapters/`):
  - `GreenhouseATSAdapter`: Validates standard required fields (name, email, resume) and submits structured Greenhouse payloads with atomic receipt capture.
  - `LeverATSAdapter`: Validates required fields and submits structured Lever payloads.
  - `ATSAdapterRegistry`: Modular registry for platform discovery and routing.
- **Safety Gates & Kill Switch** (`src/jobs_automation/automation/kill_switch.py`):
  - Global emergency shutdown via `JOBS_AUTOMATION_KILL_SWITCH` environment variable or manual override.
  - Per-platform shutdown via `JOBS_AUTOMATION_KILL_SWITCH_<PLATFORM>`.
  - Automatic expiration check: halts automation if policy review date (`review_due_at`) has elapsed.
- **Domain Rate Limiter** (`src/jobs_automation/automation/rate_limiter.py`):
  - Enforces polite submission intervals (min 5s pacing) and hourly caps (max 15/hr) per domain.
- **Controlled Auto-Application Engine** (`src/jobs_automation/automation/auto_engine.py`):
  - Strict policy gate: requires `AUTO_ALLOWED` decision from `PolicyEvaluator`.
  - Idempotency guard: prevents duplicate submissions to already submitted jobs.
  - **Unknown-question stop condition**: immediately halts with `STOPPED_UNKNOWN_QUESTION` and enqueues a `NEEDS_REVIEW` task if any required question is unaddressed; never invents candidate facts.
  - Exponential backoff retry policy for transient submission errors.
  - Full audit logging and lifecycle event creation (`APPLICATION_SUBMITTED`, `action_type="auto_application_submitted"`).
- **CLI Commands**:
  - Added `jobs-automation auto-apply` with `--job-id`, `--packet-id`, `--next`, `--mock-mode`, and `--kill-switch` options.
- **Testing & Verification**:
  - Added `tests/test_auto_application.py` (6 tests covering adapter validation, auto-apply success, unknown-question stop, global kill switch, expired policy kill switch, and rate limiting).
  - Full test suite: 65 passing tests.

## Verification performed

1. `pytest -v`: All 65 tests passing in 0.87s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All source files formatted cleanly.
4. `mypy src tests`: Strict type checking passed with zero errors across 71 source files.
5. Integration verification:
   - Verified unknown-question halt triggers `NEEDS_REVIEW` queue insertion and prevents submission.
   - Verified global and platform kill switches abort execution.
   - Verified policy review date expiration enforces immediate kill switch.
   - Verified rate limiter rejects burst submissions.

## Current blockers

None.

## Exact next task (V0.6)

Implement **V0.6 — Communication and lifecycle automation**:
- Recruiter outreach, application confirmation, screening, interview, rejection, and offer email ingestion and linking.
- Chronological recruiter threads with `ContactModel` and `CompanyModel` CRM records.
- Lifecycle event state transitions (`SUBMITTED` -> `SCREENING` -> `INTERVIEWING` -> `OFFER` / `REJECTED`).
- Unanswered outreach alerts and follow-up task creation.
- Interview extraction (`InterviewModel`) with scheduled timestamps, timezone, and meeting links.
- CLI commands `lifecycle-status` and `contacts`.

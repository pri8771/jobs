# Current State

Updated: 2026-09-20

## Current checkpoint

V0.4 — Assisted application (IMPLEMENTED & VERIFIED)

## Completed in V0.4

- **Browser Automation Core** (`src/jobs_automation/browser/base.py`):
  - Abstract `BrowserRunner` interface with typed signatures for `inspect_form`, `prefill_form`, and `open_interactive_session`.
  - Defined Pydantic models `FormField`, `FormInspectionResult`, `FormPrefillResult`, and `BrowserSessionResult`.
- **Playwright & Mock Runners**:
  - `PlaywrightBrowserRunner` (`src/jobs_automation/browser/playwright_runner.py`): Live browser engine with lazy Playwright loading, visible and headless execution, DOM input/select/textarea inspection, ATS detector (Greenhouse, Lever, Workday, Ashby), and safe input prefilling.
  - `MockBrowserRunner` (`src/jobs_automation/browser/mock_runner.py`): Deterministic mock engine for offline testing, CI/CD, and environments without browser binaries.
- **Assisted Application Engine** (`src/jobs_automation/browser/assisted_engine.py`):
  - Destination classification & policy enforcement via `PolicyEvaluator`.
  - Strict deny-by-default behavior; blocked destinations halt and write audit logs.
  - `MANUAL_ONLY` destinations (LinkedIn, Indeed) route to native application guidance without bot intervention.
  - `ASSISTED` / `AUTO_ALLOWED` destinations prefill verified candidate profile facts (name, email, phone, location, links, uploaded resume artifact, and answered screening questions).
  - Human review checkpoint strictly halts before submission, requiring candidate confirmation.
  - Creates/updates `ApplicationModel`, `ApplicationEventModel` (`APPLICATION_SUBMITTED`), and `AuditLogModel` (`input_hash=packet.packet_hash`).
  - Strict idempotency: rejects duplicate applications to already submitted jobs (`ALREADY_SUBMITTED`).
  - Completes pending review `TaskModel` records upon submission.
- **Convenient Model Properties** (`src/jobs_automation/db/models.py`):
  - Added `apply_url`, `title`, and `company_name` properties to `JobModel`.
- **CLI Commands**:
  - Added `jobs-automation assisted-apply` with `--job-id`, `--packet-id`, `--next`, `--mock-browser`, `--auto-confirm`, and `--receipt` flags.
- **Testing & Verification**:
  - Added `tests/test_assisted_application.py` (4 tests covering policy block, manual-only native workflow, prefill & confirmation, and idempotency guard).
  - Full test suite: 59 passing tests.

## Verification performed

1. `pytest -v`: All 59 tests passing in 0.59s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All source files formatted cleanly.
4. `mypy src tests`: Strict type checking passed with zero errors across 61 source files.
5. Live PostgreSQL CLI integration test:
   - Executed `jobs-automation assisted-apply --next --mock-browser --auto-confirm` against live PostgreSQL container.
   - Result: Correctly detected LinkedIn destination as `MANUAL_ONLY`, prompted candidate, confirmed manual submission, recorded `ApplicationModel` (ID `d7360d1e-8373-44b7-811c-020d341f0a61`) and `ApplicationEventModel`.
   - Executed `jobs-automation assisted-apply --job-id cecf567e-84ba-4123-9cce-d8a457be0f2c --mock-browser --auto-confirm`: Verified idempotency guard returned `ALREADY_SUBMITTED` without duplicating records.

## Current blockers

None.

## Exact next task (V0.5)

Implement **V0.5 — Controlled automatic application**:
- ATS adapter interface (`ATSAdapter`) for direct, structured application submission.
- Allowlisted ATS adapters (Greenhouse, Lever).
- Idempotent submission with atomic proof/receipt capture.
- Configurable per-domain rate limiting and exponential backoff retry policy.
- Unknown-question stop conditions (halts if unexpected required fields appear without verified profile facts).
- Global and per-platform kill switch mechanism.
- Policy review expiration check.
- CLI command `auto-apply`.

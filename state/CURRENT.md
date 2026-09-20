# Current State

Updated: 2026-09-20

## Current checkpoint

V1.1 — Stabilization and truthful integration (COMPLETED & VERIFIED)

## Maturity & Reality Check

The core software architecture and domain engines (ingestion, deduplication, filtering, scoring, packet generation, assisted submission runner, ATS simulation, lifecycle engine, health check, background worker daemon, CLI, and embedded dashboard) are implemented, strongly typed, and verified with automated test suites.

However:
- **No live accounts or OAuth credentials have been connected yet.**
- **No real external job application has been submitted.**
- Automated ATS adapters (`GreenhouseATSAdapter`, `LeverATSAdapter`) currently execute in **mock simulation mode** and are strictly classified as `SIMULATED` / `APPLICATION_SIMULATED`. Live submission returns `NOT_IMPLEMENTED` until official integration and explicit user approval in V1.6.
- The project is now safe to proceed to real onboarding (V1.2).

## Completed in V1.1 (Stabilization)

- **Worker Daemon Ingestion Wiring** (`src/jobs_automation/worker.py`):
  - Ingestion runs strictly **before** lifecycle processing in each sweep cycle.
  - Fail-closed credential handling: missing or invalid credentials skip ingestion and log errors; they never fabricate mock fixtures or advance checkpoints.
  - Once-daily reconciliation tracking: 48-hour reconciliation runs at most roughly once per 24 hours. Normal 4-hour sweeps remain incremental.
- **Fixture Fallback Removal** (`src/jobs_automation/cli/main.py`):
  - `poll-emails` and `worker` attempt live Gmail API by default.
  - Missing credentials raise a clear error informing the user to configure OAuth or explicitly pass `--mock-fixtures`.
  - Zero accidental fake data generation.
- **True Non-Persistent Dry-Run** (`src/jobs_automation/ingestion/engine.py`):
  - `run_sweep(dry_run=True)` executes full polling, classification, and job parsing for diagnostic reporting, but rolls back the transaction.
  - Zero database rows (messages, jobs, tasks) and zero checkpoints are persisted.
- **Candidate Fact Truthfulness**:
  - Removed all hard-coded fallback emails (`priyansh.chordia@gmail.com`).
  - Candidate email is derived strictly from verified profile configuration. If unconfigured, a warning is issued and outbound classification confidence is appropriately reduced (0.70 vs 0.95).
- **Truthful ATS Submission Semantics** (`greenhouse.py`, `lever.py`, `auto_engine.py`):
  - Mock mode explicitly sets application status to `SIMULATED`, records `APPLICATION_SIMULATED` events, and does not fabricate live confirmation URLs.
  - Live mode without implemented external endpoints returns `NOT_IMPLEMENTED`.
  - No `APPLICATION_SUBMITTED` event is created without external evidence.
- **Dashboard Safe Defaults** (`docker-compose.yml`, CLI):
  - Docker Compose dashboard port binding defaults to `127.0.0.1:8765:8765`.
  - CLI `dashboard` binds to `127.0.0.1` by default.
- **Continuous Integration** (`.github/workflows/ci.yml`):
  - GitHub Actions workflow runs on push to `main` and pull requests.
  - Executes Python 3.12 dependency installation, `pytest -v`, `ruff check .`, and `mypy src tests` without requiring secrets.
- **Testing & Verification**:
  - Added `tests/test_worker.py` (6 unit/integration tests).
  - Added dry-run, checkpoint safety, and outbound confidence tests to `tests/test_ingestion_engine.py`.
  - Added live mode `NOT_IMPLEMENTED` test to `tests/test_auto_application.py`.
  - Full test suite: **87 tests passing cleanly in 0.77s**.
  - Strict type checking (`mypy`) passed with zero errors across 85 source files.
  - Linter (`ruff`) passed with zero errors.

## Current blockers

None for V1.1.
Awaiting ChatGPT lead review before proceeding to V1.2.

## Next milestone

V1.2 — Candidate + account onboarding:
- Add canonical candidate facts and resume source(s).
- Set up Google Cloud project for runtime Gmail OAuth.
- Connect Gmail read-only to Jobs Automation.
- Configure real job alert searches across LinkedIn, Indeed, ZipRecruiter, and Dice.

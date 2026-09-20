# Current State

Updated: 2026-09-20

## Current checkpoint

V0.1 - Portable foundation + profiles (IMPLEMENTED & VERIFIED)

## Completed in V0.1

- Python 3.12+ package structure implemented in `src/jobs_automation/` with `pyproject.toml`.
- Docker Compose configuration (`docker-compose.yml`) added for PostgreSQL with host port isolation (`${POSTGRES_PORT:-5433}:5432`).
- Typed configuration models and loader implemented in `jobs_automation.core`:
  - `CandidateProfileConfig` with strict fact validation to prevent guessing or fabricating missing identity, work authorization, compensation, or dates.
  - `JobSearchConfig` with scoring weights and role family definitions.
  - `PlatformsConfig` and `EmailPollingConfig` enforcing 4-hour (240 min) default polling and disallowing realtime push or minute-level polling.
  - `ModelRoutingConfig` for LiteLLM-compatible task-based model gateway routing.
  - `PolicyRegistryConfig` with deny-by-default behavior (`BLOCKED`).
- Foundational PostgreSQL/SQLite database models (18 domain models) implemented in `jobs_automation.db` matching `docs/DATA_MODEL.md`:
  - Supports inbound and outbound email tracking, thread history, deduplication on provider message ID, contacts, applications, evaluations, events, and audit logging.
- Alembic database migration environment and initial migration `001_initial_foundation` created and successfully applied to PostgreSQL.
- Policy evaluation engine implemented in `jobs_automation.policy.evaluator` enforcing default-deny (`BLOCKED`), wildcard domain matching, and expiration date checking (`review_due_at`).
- Replaceable integration interfaces (`EmailAdapter`, `ModelGateway`, `ATSAdapter`) defined in `jobs_automation.adapters.base`.
- Profile setup worksheet generator implemented in `jobs_automation.worksheets.generator`, producing `docs/PROFILE_WORKSHEET.md` with tailored checklists for LinkedIn, Indeed, ZipRecruiter, and Dice grounded in `docs/CANDIDATE_POSITIONING.md`.
- CLI commands implemented in `jobs_automation.cli`:
  - `validate-config`: loads all YAML configs, reports unresolved facts without fabricating answers.
  - `db-check`: verifies database connectivity, reports latency and registered models.
  - `status`: displays complete system status across configs, database, platforms, and policy registry.
  - `generate-profile-worksheet`: exports platform checklist to `docs/PROFILE_WORKSHEET.md`.
- Test suite implemented in `tests/`: 22 unit tests passing across config validation, policy evaluation, database models and thread tracking, CLI commands, and worksheet generation.
- Full formatting (`ruff format`), linting (`ruff check`), and strict type checking (`mypy src tests`) passing with zero errors.

## Verification performed

1. `pytest -v`: 22 of 22 tests passing in 0.30s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All 53 files clean.
4. `mypy src tests`: Strict type checking passed with no issues found across 25 source files.
5. Docker Compose: `docker compose up -d` started PostgreSQL (16-alpine) on mapped port 5433.
6. `alembic upgrade head`: Applied `001_initial_foundation` migration creating all 18 tables + `alembic_version`.
7. `jobs-automation db-check`: Verified live connection to PostgreSQL (latency: 22ms) and table discovery.
8. `jobs-automation validate-config`: Verified all YAML configurations, 4-hour Gmail polling cadence, and reported unresolved facts.
9. `jobs-automation status`: Verified system status dashboard.
10. `jobs-automation generate-profile-worksheet`: Verified generation of `docs/PROFILE_WORKSHEET.md`.
11. Security review: Inspected git status and ignored files; confirmed no tokens, secrets, cookies, or credentials are staged or committed.

## Failures / issues encountered and resolved

- Conflict on host port 5432: Pre-existing macOS Homebrew PostgreSQL service occupied 5432. Resolved by mapping Docker Compose PostgreSQL to `${POSTGRES_PORT:-5433}:5432` with `.env` configuration.
- Missing type annotations in test files resolved for strict `mypy` compliance.

## Current blockers

None for foundation.

For human profile setup on external platforms:
- User manual execution of the checklists in `docs/PROFILE_WORKSHEET.md` for LinkedIn, Indeed, ZipRecruiter, and Dice (entering credentials, uploading tailored resume variants, activating daily search alert emails).

## Exact next task (V0.2)

Implement **V0.2 — Job alerts + Gmail ingestion**:
- Gmail API OAuth setup and token flow.
- 4-hour polling worker with incremental checkpointing and overlap window.
- Inbound and outbound message persistence with thread ID tracking.
- Email parsers for LinkedIn, Indeed, ZipRecruiter, Dice, and generic job alert emails.

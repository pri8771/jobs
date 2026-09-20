# Current State

Updated: 2026-09-20

## Current checkpoint

V0.6 — Communication and lifecycle automation (IMPLEMENTED & VERIFIED)

## Completed in V0.6

- **Recruiter CRM Service** (`src/jobs_automation/lifecycle/crm.py`):
  - Extracts clean contact names and email addresses from RFC 2822 sender strings.
  - Automatically manages `ContactModel` records linked to `CompanyModel` and tracked applications.
  - Tracks `first_contact_at` and `last_contact_at` touchpoints across full conversation history.
  - Assembles chronological communication timelines with provider message and thread IDs.
- **Interview Details Extractor** (`src/jobs_automation/lifecycle/interview.py`):
  - Detects interview round types (`recruiter_screen`, `technical_screen`, `system_design`, `hiring_manager`, `panel`).
  - Regex extractor for video conferencing links (Zoom, Google Meet, Microsoft Teams, Webex, Calendly).
  - Persists and links `InterviewModel` records to active applications.
- **Proactive Lifecycle Alert Service** (`src/jobs_automation/lifecycle/alerts.py`):
  - `check_unanswered_recruiters`: Flags inbound recruiter inquiries that have gone > 48h without a candidate reply, enqueuing `UNANSWERED_RECRUITER` tasks in `TaskModel`. Ignores threads where the candidate has already responded.
  - `check_stale_applications`: Detects applications in `SUBMITTED` or `CONFIRMED` status with > 14 days of silence, generating `STALE_APPLICATION_FOLLOW_UP` tasks.
- **Lifecycle Transition Engine** (`src/jobs_automation/lifecycle/engine.py`):
  - Drives deterministic application status progression:
    - `APPLICATION_CONFIRMATION` -> `CONFIRMED`
    - `RECRUITER_OUTREACH` / `SCREENING_REQUEST` -> `SCREENING`
    - `INTERVIEW_REQUEST` / `INTERVIEW_CONFIRMATION` -> `INTERVIEWING`
    - `OFFER` -> `OFFER_RECEIVED`
    - `REJECTION` -> `REJECTED` (with `closed_at` timestamp)
  - Records granular `ApplicationEventModel` records and audit entries (`action_type="lifecycle_state_transition"`).
  - **Ambiguity quarantine**: Inbound messages with low link confidence (< 0.80) or matching multiple plausible applications are strictly quarantined to `NEEDS_REVIEW` tasks without mutating application status.
- **CLI Commands**:
  - Added `jobs-automation lifecycle-status` (rich table of applications, stages, modes, applied dates, interview counts).
  - Added `jobs-automation contacts` (CRM directory of recruiter contacts, companies, roles, touchpoints).
  - Added `jobs-automation update-lifecycle` (sweeps messages, triggers transitions, extracts interviews, generates follow-up alerts).
- **Testing & Verification**:
  - Added `tests/test_lifecycle.py` (5 tests covering recruiter CRM, interview extraction, state transitions, ambiguity review queue routing, and unanswered/stale alerts).
  - Full test suite: 70 passing tests.

## Verification performed

1. `pytest -v`: All 70 tests passing in 1.04s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All source files formatted cleanly.
4. `mypy src tests`: Strict type checking passed with zero errors across 77 source files.
5. Live PostgreSQL CLI integration test:
   - Executed `jobs-automation update-lifecycle`: Swept recruiting messages, verified state transition processing and alert checking.
   - Executed `jobs-automation lifecycle-status`: Verified display of active applications, status (`SUBMITTED`), and interview columns.
   - Executed `jobs-automation contacts`: Verified CRM table formatting against live database.

## Current blockers

None.

## Exact next task (V0.7)

Implement **V0.7 — Dashboard and analytics**:
- Fast, clean operations web UI (FastAPI backend + interactive dashboard, review queue, application Kanban, interview calendar, and communication timeline).
- Funnel and pipeline analytics API: discovery-to-submission, conversion rates, response times.
- Human review queue UI with one-click resolution of pending tasks.
- CLI command `dashboard` to launch the local web server.

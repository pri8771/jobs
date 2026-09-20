# Current State

Updated: 2026-09-20

## Current checkpoint

V0.2 — Job alerts + Gmail ingestion (IMPLEMENTED & VERIFIED)

## Completed in V0.2

- **Data Models & Types**:
  - Implemented `RawEmailMessage`, `ExtractedJobPosting`, `EmailClassification`, and `EmailClassificationResult` in `jobs_automation.ingestion.models`.
  - Added clean URL canonicalization utility in `base.py` stripping tracking parameters (`utm_*`, `trk`, `refId`, `from`, `tk`, `fbclid`, `gclid`).
  - Added deterministic regex parsers for compensation ranges and remote work type detection.
- **Alert Email Parsers**:
  - Built platform-specific alert parsers for LinkedIn (`LinkedInAlertParser`), Indeed (`IndeedAlertParser`), ZipRecruiter (`ZipRecruiterAlertParser`), and Dice (`DiceAlertParser`).
  - Built fallback `GenericAlertParser` for standard HTML alert emails.
  - Implemented `AlertParserRegistry` for automatic sender and subject routing.
- **Email Classifier**:
  - Built deterministic multi-stage email classifier in `jobs_automation.ingestion.classifier`:
    - Identifies inbound job alerts, application confirmations, recruiter outreach, interview requests/confirmations/reschedules/cancellations, rejections, and job offers.
    - Accurately tracks outbound replies sent by candidate (`direction="outbound"`, `classification="CANDIDATE_REPLY"`).
    - Routes ambiguous or unrecognized recruiting messages to `UNKNOWN_REVIEW_REQUIRED` (`needs_review=True`), never guessing or fabricating matches.
- **Job Deduplication Service**:
  - Implemented 4-tier deduplication hierarchy in `jobs_automation.ingestion.deduplication`:
    1. Exact requisition ID.
    2. Canonical apply URL.
    3. Source provider + source job ID.
    4. Normalized company + normalized job title within a 60-day window.
  - Attaches additional `JobSourceModel` links when existing jobs match from different platforms, keeping canonical jobs deduplicated.
- **Mailbox Ingestion Engine**:
  - Implemented `EmailIngestionEngine` in `jobs_automation.ingestion.engine`:
    - Enforces non-realtime periodic polling (4-hour cadence).
    - Implements incremental checkpointing stored in database (`email_checkpoint` task).
    - Uses 15-minute safety overlap window to prevent missing delayed messages.
    - Supports full 48-hour reconciliation sweep (`reconcile=True`) without corrupting incremental checkpoint progress.
    - Enforces strict idempotency on `provider_message_id`.
    - Preserves complete conversation thread history (`provider_thread_id`) across inbound and outbound messages.
    - Links alert messages to discovered jobs via `MessageLinkModel`.
    - Links recruiting lifecycle emails to active applications; flags ambiguous multi-application matches for review.
    - Transactional commit: advances checkpoint only when the entire batch commits without error; rolls back on failure.
- **Gmail OAuth & Mock Adapters**:
  - Implemented `GmailOAuthClient` and `GmailAdapter` using official Google API libraries (`google-api-python-client`, `google-auth-oauthlib`).
  - Implemented `MockEmailAdapter` for deterministic local and offline testing without live OAuth credentials.
  - Provided realistic fixtures generator in `jobs_automation.ingestion.fixtures` generating 7 sanitized emails covering all platforms, thread continuation, and confirmations.
- **CLI Commands**:
  - Added `poll-emails` with `--dry-run`, `--reconcile`, `--query`, `--max-messages`, and `--mock-fixtures` options.
  - Added `mailbox-status` displaying last checkpoint, message counts, thread counts, and classification breakdown tables.
- **Testing & Verification**:
  - Added 9 unit tests for alert parsers in `tests/test_parsers.py`.
  - Added 12 unit tests for classifier, deduplication, and ingestion engine in `tests/test_ingestion_engine.py`.
  - Full suite now has 43 passing tests.

## Verification performed

1. `pytest -v`: All 43 tests passing in 0.45s.
2. `ruff check .`: All checks passed.
3. `ruff format --check .`: All 72 files formatted cleanly.
4. `mypy src tests`: Strict type checking passed with zero errors across 44 source files.
5. CLI PostgreSQL integration test:
   - Executed `jobs-automation poll-emails --mock-fixtures` against live PostgreSQL container.
   - Result: 7 messages polled, 7 ingested, 5 new jobs discovered, checkpoint advanced.
   - Executed `jobs-automation mailbox-status`: Verified 6 inbound, 1 outbound message, 6 threads, 5 jobs.
   - Executed `jobs-automation poll-emails --mock-fixtures --reconcile`: Verified idempotency (7 polled, 0 ingested, 7 duplicate skipped, 0 new jobs, checkpoint unchanged).
   - Executed `jobs-automation poll-emails --mock-fixtures` (incremental): Verified overlap window behavior (1 polled, 1 skipped duplicate).
6. Security check: Inspected `git status --ignored` to verify `.env`, tokens, credentials, and virtual environment are strictly ignored.

## Current blockers

None.

External requirements before running live Gmail polling:
- User needs to create a Google Cloud Project with Gmail API enabled (read-only scopes: `https://www.googleapis.com/auth/gmail.readonly`), place credentials at `~/.jobs_automation/gmail_client_secret.json`, and run interactive OAuth once.
- Offline mock mode (`--mock-fixtures`) works out of the box without any credentials.

## Exact next task (V0.3)

Implement **V0.3 — Filtering, scoring, and application preparation**:
- Hard filters (work authorization, location, remote policy, minimum compensation).
- Semantic fit scoring against candidate profile and role tracks (Staff Automation / Solutions Architect / Founding Engineer).
- Application packet builder: select targeted resume variant, generate tailored cover letter, extract application questions.
- Unresolved question detection and review queue routing (`NEEDS_REVIEW`), strictly prohibiting fabrication.

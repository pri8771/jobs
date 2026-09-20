# Architecture

## Design principles

1. Git is the knowledge/control-plane source of truth for project rules and development state.
2. PostgreSQL is the runtime source of truth for jobs, applications, messages, events, and audit data.
3. Email is an ingestion channel, not the database.
4. LLMs are replaceable workers, not the owner of workflow state.
5. Browser automation is an adapter behind an explicit policy gate.
6. Every external side effect is auditable and idempotent.
7. Human review is a supported state, not an error.

## High-level components

### 1. Controller API

FastAPI service responsible for:
- configuration
- ingestion endpoints
- job/application CRUD
- workflow commands
- review queue
- audit querying
- health checks

### 2. Scheduler / worker

MVP:
- simple process or APScheduler
- Gmail polling every 4 hours by default
- configurable polling cadence, with 3-4 hours as the intended operating range
- optional once-daily reconciliation sweep
- parsing and classification jobs
- status follow-up checks
- reminder generation

Real-time Gmail push notifications are not required.

Do not introduce Redis/Celery until concurrency or reliability actually requires it.

### 3. Gmail adapter

OAuth-based Gmail API integration.

Responsibilities:
- query configured labels/search expressions
- retrieve messages and thread metadata
- track incremental mailbox checkpoints with a small overlap window
- deduplicate using provider message IDs
- store provider message IDs and thread IDs
- parse job-alert links
- classify recruiting lifecycle emails
- track inbound and outbound recruiter/company communication
- associate messages with companies, contacts, jobs, applications, interviews, and offers
- preserve chronological thread history
- route ambiguous links/status changes to NEEDS_REVIEW
- never delete, archive, or send mail in MVP

Detailed rules:
- docs/EMAIL_TRACKING.md

Recommended labels:
- Jobs/Alerts
- Jobs/Applications
- Jobs/Recruiters
- Jobs/Interviews
- Jobs/Offers
- Jobs/Review

Initial operation can use Gmail search queries without requiring all labels to exist.

### 4. Source adapters

Adapters normalize source-specific alerts/URLs into a common JobCandidate model.

Initial adapters:
- linkedin_email
- indeed_email
- ziprecruiter_email
- dice_email
- generic_job_alert_email
- generic_career_site

Board adapters do not automatically imply permission to automate submission.

### 5. Job normalization and deduplication

Normalize:
- company
- title
- location
- compensation
- source URL
- canonical application URL
- requisition ID
- description
- posted date

Deduplication evidence order:
1. exact external/requisition ID
2. canonical destination URL
3. source job ID
4. company + normalized title + location + time window
5. semantic duplicate check only as fallback

### 6. Rules engine

Deterministic hard rules first.
Semantic scoring second.

Output:
- decision
- score
- reason codes
- explanation
- model/version metadata when an LLM was involved

### 7. LLM gateway

Use a provider-neutral interface. LiteLLM compatibility is preferred so OpenAI-compatible, Anthropic, Gemini, OpenRouter, local models, or other endpoints can be swapped without rewriting domain logic.

Task classes:
- cheap extraction
- job/candidate semantic matching
- resume tailoring
- cover-letter drafting
- screening-answer drafting
- email classification
- recruiter-thread summary

Model routing must be configurable by task.

### 8. Candidate profile service

Canonical facts and reusable application answers.

The database/runtime representation should be generated from versioned user configuration plus private local data.

Do not store credentials here.

### 9. Application packet builder

Produces:
- chosen resume version
- tailored resume version
- cover letter if needed
- prepared answers
- unresolved questions
- destination URL
- policy decision
- evidence mapping

The packet must receive a unique version/hash before submission.

### 10. Application executor

Common interface:

- inspect_destination()
- prepare()
- validate()
- fill()
- review()
- submit()
- capture_confirmation()

Modes:
- manual executor
- assisted executor
- permitted browser executor
- ATS-specific executor

The policy gate runs before fill and again before submit.

### 11. Browser runner

Preferred design:
- controller can run headless in Docker on an always-on server
- interactive browser runner can run on a trusted desktop with a real visible browser profile
- no cookie export to Git
- no stealth plugins
- no CAPTCHA solvers
- manual checkpoints supported

This split keeps periodic email/job processing independent from interactive application sessions.

### 12. Tracking/event engine

Every meaningful change is an append-only event plus a current-state projection.

Examples:
- JOB_DISCOVERED
- JOB_FILTERED
- JOB_SHORTLISTED
- APPLICATION_PACKET_CREATED
- APPLICATION_STARTED
- APPLICATION_SUBMITTED
- APPLICATION_CONFIRMED
- EMAIL_LINKED
- RECRUITER_CONTACTED
- CANDIDATE_REPLIED
- INTERVIEW_SCHEDULED
- REJECTED
- OFFER_RECEIVED
- FOLLOW_UP_DUE

### 13. Future dashboard

Views:
- Inbox / new jobs
- Review queue
- Applications board
- Interviews
- Offers
- Communication timeline
- Metrics
- Configuration

## Deployment

MVP development:
- local Python environment
- local PostgreSQL via Docker Compose

Always-on:
- Docker Compose on a home server or small VM
- PostgreSQL volume
- controller/worker container
- optional reverse proxy only if remote access is required
- desktop browser runner as a separate client

## Testing

Required test layers:
- fixture-based email parser tests
- Gmail checkpoint/idempotency tests
- recruiter-thread linking tests
- inbound/outbound message tracking tests
- rule engine tests
- deduplication tests
- state-machine tests
- policy gate tests
- application packet snapshot tests
- integration tests against fake Gmail/ATS services
- browser adapters only against test/sandbox pages unless explicitly approved

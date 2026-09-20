# Roadmap

The project advances in explicit checkpoints. Agents must stop at the end of each checkpoint unless the user tells them to continue.

## V0.1 - Portable foundation + profiles

Goal: make the repository self-describing and create the canonical candidate/search configuration needed to populate four job platforms.

Deliverables:
- cross-IDE rules and Antigravity skills/workflows
- Python project scaffold
- configuration loader
- candidate profile schema
- job-search criteria schema
- platform account/setup checklist
- runtime database scaffold
- policy registry scaffold
- profile completion workflow for LinkedIn, Indeed, ZipRecruiter, Dice
- tests for configuration and policy defaults
- state/handoff process

Checkpoint:
- repository can be cloned into a fresh IDE and another agent can continue with no chat history
- candidate/search config validates
- database starts
- platform profile checklist is ready
- no automatic applying yet

## V0.2 - Job alerts + Gmail ingestion

Goal: job alerts and recruiting/application email become normalized records automatically.

Deliverables:
- Gmail OAuth setup
- configurable Gmail queries/labels
- polling worker with a 4-hour default interval
- configurable 3-4 hour polling cadence
- incremental checkpointing with overlap window
- once-daily reconciliation pass
- raw/normalized message storage
- Gmail message + thread ID persistence
- inbound/outbound direction tracking
- LinkedIn alert parser
- Indeed alert parser
- ZipRecruiter alert parser
- Dice alert parser
- generic parser fallback
- basic recruiter/company/application email classification
- thread preservation
- URL normalization
- deduplication
- fixture tests
- polling idempotency tests
- alert/mailbox health/status reporting

No real-time Gmail push architecture is required.

Checkpoint:
- a test set of real/sanitized alert emails produces deduplicated job records
- recruiting/application messages are preserved with message/thread IDs
- re-running ingestion creates no duplicate jobs/messages/events
- a failed sweep does not skip unprocessed messages

## V0.3 - Filtering and application preparation

Goal: qualified jobs become reviewable application packets.

Deliverables:
- deterministic hard filters
- semantic scoring
- reason codes
- LLM gateway with task-based model selection
- job requirement extraction
- resume evidence mapping
- resume variant/tailoring pipeline
- cover-letter drafting
- screening-answer preparation
- unresolved-question detection
- review queue

Checkpoint:
- every job gets a reproducible decision
- every shortlisted job can produce a versioned application packet
- no submission yet

## V0.4 - Assisted application

Goal: reduce repetitive application work without unsafe platform automation.

Deliverables:
- destination detection
- policy gate
- manual/assisted executors
- local visible browser runner
- form inspection
- safe field mapping
- human review checkpoint
- application confirmation capture
- audit log

LinkedIn and Indeed remain manual/native for submission under current policy constraints.

Checkpoint:
- user can open a prepared application, review prefilled data where permitted, submit, and have the result recorded

## V0.5 - Controlled automatic application

Goal: automatically submit to allowlisted employer/ATS destinations where permitted.

Deliverables:
- ATS adapter interface
- first allowlisted ATS adapters
- idempotent submit
- retry policy
- unknown-question stop conditions
- per-domain rate limits
- proof/receipt capture
- kill switch
- policy review dates

Checkpoint:
- end-to-end automatic application succeeds in approved test/live destinations without duplicate submissions
- no anti-bot bypass behavior

## V0.6 - Communication and lifecycle automation

Goal: track applications from submission to outcome.

Canonical communication rules:
- docs/EMAIL_TRACKING.md

Deliverables:
- full classification of confirmation/recruiter/screening/interview/rejection/offer/background/onboarding emails
- company/job/application/contact entity linking
- complete chronological recruiter/company threads
- inbound and outbound communication tracking
- lifecycle event engine
- recruiter/contact records and timelines
- interview extraction
- new-role detection inside existing recruiter threads
- ambiguous-link NEEDS_REVIEW queue
- follow-up task generation
- unanswered-recruiter detection
- stale-application reminders
- manual correction tools

Optional:
- Google Calendar integration for interviews after explicit setup

Checkpoint:
- application timelines update from incoming/outgoing email with traceable evidence
- source Gmail messages remain authoritative
- recruiter threads stay intact across the application lifecycle
- ambiguous messages do not silently change application state

## V0.7 - Dashboard and analytics

Goal: make the system easy to operate.

Deliverables:
- job inbox
- review queue
- application Kanban
- interview view
- communication timeline
- filters/search
- metrics
- configuration UI
- audit UI

## V1.0 - Reliable personal job-search operating system

Requirements:
- stable always-on deployment
- backup/restore
- monitoring
- migration path
- platform policy registry maintenance
- documented recovery
- model/provider switching
- cross-IDE handoff verified
- measurable application funnel

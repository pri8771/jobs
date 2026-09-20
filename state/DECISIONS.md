# Architecture Decision Log

Append new decisions; do not rewrite history unless correcting an error.

## 2026-09-20 - Repository is the portable memory

Decision:
All project rules, state, architecture, prompts, schemas, and checkpoints must be recoverable from Git.

Reason:
The project is intended to move between Antigravity, Cursor, Claude, ChatGPT, Codex, and future tools.

## 2026-09-20 - Canonical rules plus thin IDE adapters

Decision:
AGENTS.md and canonical docs own the rules. IDE-specific files point to them and add only tool-specific mechanics.

Reason:
Avoid instruction drift.

## 2026-09-20 - Email-first discovery

Decision:
Use platform job-alert emails as the initial discovery channel rather than browser scraping job boards.

Reason:
Portable, low-friction, easy to schedule, and avoids unnecessary browser automation.

## 2026-09-20 - Gmail as first email provider

Decision:
Implement Gmail first with an adapter boundary for future providers.

Reason:
Primary planned workflow and strong API support.

## 2026-09-20 - Dice as fourth initial board

Decision:
Initial sources are LinkedIn, Indeed, ZipRecruiter, and Dice.

Reason:
Dice is technology-focused and supports candidate profiles and recurring alerts.

## 2026-09-20 - Deny-by-default application policy

Decision:
No destination can auto-submit without an explicit current AUTO_ALLOWED policy decision.

Reason:
Platform rules differ and change.

## 2026-09-20 - No LinkedIn or Indeed bot submission

Decision:
Do not automate LinkedIn Easy Apply or Indeed Apply with third-party browser bots under current rules.

Reason:
Current official platform terms/guidance restrict or prohibit this behavior.

## 2026-09-20 - Direct ATS automation is a separate layer

Decision:
Discovery source and application destination are separate concepts. A LinkedIn alert may lead to an employer ATS that can be independently evaluated.

Reason:
Enables compliant automation without coupling to a board's UI.

## 2026-09-20 - Split controller and browser runner

Decision:
Always-on controller can run in Docker; interactive browser runner can run on a trusted desktop.

Reason:
Keeps scheduled email/job processing independent from interactive application sessions.

## 2026-09-20 - LiteLLM-compatible model gateway

Decision:
Use a provider-neutral model interface compatible with LiteLLM-style routing.

Reason:
The system should be able to choose different cloud/local models by task and switch providers without domain-code changes.

## 2026-09-20 - Start simple on scheduling

Decision:
Use a simple worker loop/APScheduler for MVP.

Reason:
Redis/Celery is unnecessary until actual workload justifies it.

## 2026-09-20 - Gmail polling cadence

Decision:
Gmail processing does not need to be real-time. Default to polling every 4 hours, configurable around a 3-4 hour cadence, with an optional once-daily reconciliation sweep.

Reason:
Job alerts and recruiting communication do not justify minute-level infrastructure. A several-times-per-day sweep is sufficient and simpler to operate.

## 2026-09-20 - Preserve complete recruiting email history

Decision:
Track inbound and outbound recruiting/company email, preserve Gmail message and thread IDs, and maintain chronological thread history linked to contacts, companies, jobs, and applications.

Reason:
Application state cannot be understood reliably from only the latest incoming message. Full communication history is needed for follow-ups, interview tracking, recruiter relationships, and auditability.

## 2026-09-20 - Ambiguous email links require review

Decision:
If an email could plausibly belong to more than one application/job and deterministic evidence is insufficient, create a NEEDS_REVIEW item instead of silently linking it.

Reason:
Incorrect lifecycle transitions are more harmful than delayed classification.

## 2026-09-20 - PostgreSQL port isolation in Docker Compose

Decision:
Docker Compose maps PostgreSQL container port 5432 to host port 5433 by default (`${POSTGRES_PORT:-5433}:5432`), while supporting `POSTGRES_PORT` environment override.

Reason:
Prevents port collisions on developer workstations and host servers where a local PostgreSQL service is already active on default port 5432.

## 2026-09-20 - Incremental mailbox checkpointing with safety overlap window

Decision:
The email ingestion engine tracks checkpoints in the database via completed `email_checkpoint` task records. Incremental sweeps only advance the checkpoint upon complete successful commit of a batch. Sweeps look back from the last checkpoint minus a 15-minute safety overlap window to prevent missing messages delivered with slight delay or clock drift. Idempotency is enforced by the unique constraint on `provider_message_id`. A separate 48-hour reconciliation sweep can run periodically without overriding standard checkpoint advancement.

Reason:
Protects against message loss during worker interruptions or network failures while guaranteeing strict idempotency and avoiding duplicate jobs or duplicate inbound message records.

## 2026-09-20 - 4-level deduplication hierarchy for job discovery

Decision:
Incoming job alerts from all providers are deduplicated into the canonical `JobModel` through a 4-tier evidence order:
1. Exact requisition ID (if extracted).
2. Canonical destination apply URL (cleaned of tracking query parameters).
3. Source provider + provider job ID.
4. Normalized company name + normalized title within a 60-day discovery window.
When an existing job matches, its `last_seen_at` is refreshed and a new `JobSourceModel` is linked if the provider/source ID combination has not yet been recorded.

Reason:
Job alerts from LinkedIn, Indeed, ZipRecruiter, and Dice frequently broadcast the same opening with varying tracking links, title formatting, or slight delays. Deduplicating to a single job entity prevents redundant applications while retaining all discovered sourcing channels.

## 2026-09-20 - Deterministic hard filtering precedes semantic scoring

Decision:
Jobs must pass deterministic hard filters (compensation floor, location/remote constraints, security clearance exclusions, title disqualifiers, and unverified citizenship/sponsorship prerequisites) before scoring. Disqualified jobs are marked `FILTERED_OUT` with explicit reason codes and bypassed from LLM inference.

Reason:
Eliminates LLM spend on non-viable roles and prevents subtle hallucination or softening of strict candidate constraints.

## 2026-09-20 - Multi-factor scoring with clear threshold bands

Decision:
Semantic scoring weights title alignment (30%), must-have skills (25%), preferred skills (15%), compensation (10%), location (10%), seniority (5%), and freshness (5%). Scores map directly to deterministic action bands: `SHORTLIST` (>= 70), `CONSIDER` (>= 55), and `REJECT` (< 55). Jobs in the `CONSIDER` band or with unverified sponsorship requirements automatically generate `NEEDS_REVIEW` tasks.

Reason:
Provides an auditable numerical score with human-in-the-loop review for borderline opportunities.

## 2026-09-20 - Strict prohibition on demographic auto-fill and fact fabrication

Decision:
The screening question answering service is strictly prohibited from answering demographic questions (race, ethnicity, gender, disability, veteran status) or unverified candidate facts (unconfirmed relocation, unconfirmed sponsorship). These questions are flagged as `unresolved` and require human completion via the review queue.

Reason:
Candidate self-identification and legal declarations must never be automated or guessed by an AI model.

## 2026-09-20 - Deterministic packet hashing and immutable artifacts

Decision:
Every generated application packet computes a SHA-256 digest over the selected resume variant, candidate answers, and cover letter. Resumes and cover letters are stored as immutable `ArtifactModel` records linked to the job and application.

Reason:
Guarantees full auditability and idempotency for downstream assisted and automated submission workflows.

## 2026-09-20 - Pluggable BrowserRunner interface with visible and mock runners

Decision:
All browser automation and form interaction is encapsulated behind the abstract `BrowserRunner` interface (`inspect_form`, `prefill_form`, `open_interactive_session`). Production environments use `PlaywrightBrowserRunner` which launches visible or headless browser instances with lazy Playwright imports. CI, testing, and offline operations use `MockBrowserRunner` without requiring browser binary installation.

Reason:
Keeps core business logic decoupled from browser engine implementations and ensures headless/sandboxed test portability.

## 2026-09-20 - Mandatory human review checkpoint for assisted submissions

Decision:
In assisted mode (`ASSISTED`), the browser runner inspects the target ATS form, prefills verified candidate profile facts (name, email, phone, links, resume upload) and pre-computed packet answers, but strictly halts before submission. Final submission requires candidate confirmation (or explicit review confirmation in automated tests). In `MANUAL_ONLY` destinations (LinkedIn, Indeed), automated form-filling is completely bypassed, routing the candidate to native portals with pre-formatted profile worksheets.

Reason:
Prevents platform terms violations and ensures candidates maintain 100% human oversight before any external application is submitted.

## 2026-09-20 - Allowlisted ATS adapters for structured auto-submission

Decision:
Automated submission is only executed through explicit, allowlisted ATS adapters (`GreenhouseATSAdapter`, `LeverATSAdapter`) against domains with an unexpired `AUTO_ALLOWED` policy decision. Third-party job boards (LinkedIn, Indeed) remain strictly prohibited from automatic submission.

Reason:
Direct employer ATS endpoints provide structured, reliable, and compliant submission boundaries without violating general board anti-automation terms.

## 2026-09-20 - Unknown-question stop condition prevents hallucinated submissions

Decision:
Prior to submitting any automatic application, the ATS adapter validates all required fields against verified candidate profile facts and pre-computed packet answers. If any required field is missing or any screening question is unresolved, submission immediately halts (`STOPPED_UNKNOWN_QUESTION`), enqueuing a `NEEDS_REVIEW` task. The engine will never invent answers to bypass form requirements.

Reason:
Upholds the fundamental contract rule: never fabricate candidate facts, sponsorship needs, or background details.

## 2026-09-20 - Multi-tier kill switch and automatic policy expiration

Decision:
The `KillSwitchManager` provides three independent layers of emergency shutdown:
1. Global kill switch flag (via `JOBS_AUTOMATION_KILL_SWITCH` environment variable or manual override).
2. Per-platform kill switch flags (`JOBS_AUTOMATION_KILL_SWITCH_<PLATFORM>`).
3. Automated policy review date expiration: if current date exceeds `review_due_at` in the policy registry, automatic submission is instantly disabled for that platform.

Reason:
Ensures immediate operational control and prevents stale policy assumptions from allowing outdated automation behaviors.

## 2026-09-20 - Evidence-based lifecycle state machine

Decision:
Application status progression (`SUBMITTED` -> `CONFIRMED` -> `SCREENING` -> `INTERVIEWING` -> `OFFER_RECEIVED` / `REJECTED`) is driven strictly by verified communication evidence from `InboundMessageModel`. Every transition is accompanied by an immutable `ApplicationEventModel` and `AuditLogModel`.

Reason:
Prevents arbitrary or unverified status changes and ensures complete traceability back to provider message IDs.

## 2026-09-20 - Ambiguous communications must never mutate application state

Decision:
If a recruiting email links to multiple active applications or has link confidence below 0.80, the lifecycle engine refuses to transition any application status and instead enqueues a `NEEDS_REVIEW` item.

Reason:
Incorrect lifecycle transitions (e.g. marking the wrong job as rejected or interviewing) corrupt candidate operational reality. Human resolution is always preferred over speculative state mutations.

## 2026-09-20 - Proactive recruiter responsiveness and pipeline health alerting

Decision:
The `LifecycleAlertService` inspects communication timelines to detect unanswered recruiter outreach (> 48h without candidate outbound reply) and stale applications (> 14 days without employer response), surfacing actionable follow-up tasks in the review queue.

Reason:
Keeps the candidate responsive to live recruiter outreach while identifying stalled hiring processes without sending unapproved automated replies.

## 2026-09-20 - Embedded portable dashboard architecture

Decision:
The operations dashboard and REST API are built with Python's standard library `http.server.ThreadingHTTPServer` with an embedded modern responsive Single Page Application rather than introducing heavy third-party web frameworks (FastAPI, Flask, Starlette).

Reason:
Maximizes cross-environment portability, guarantees zero external dependency bloat, starts instantly, and ensures out-of-the-box operation across desktop CLI, cloud VMs, and containerized Docker environments.

## 2026-09-20 - Decoupled background worker daemon

Decision:
Background sweeps (email polling, interview extraction, follow-up alerting, rate-limiting resets) run in an independent `jobs-worker` daemon decoupled from user interface and dashboard request handling.

Reason:
Prevents long-running background tasks from starving web UI responsiveness, isolates scheduler failures, and supports horizontal separation of concerns in containerized environments.

## 2026-09-20 - Cryptographic backup and single-transaction restore

Decision:
Database backups generate SHA-256 integrity checksum files alongside gzip dumps. Restores require explicit checksum verification and execute within a single atomic PostgreSQL transaction with active connection termination.

Reason:
Protects against silent backup corruption and guarantees that partial or failed restores cannot leave the database in an inconsistent state.

## 2026-09-20 - Worker daemon ingestion precedence and fail-closed credentials

Decision:
The `WorkerDaemon` executes email ingestion strictly before lifecycle updates in each maintenance cycle. If Gmail API credentials are missing or unconfigured, ingestion fails closed with an auditable error, skips checkpoint advancement, and never silently falls back to mock fixtures in production. Reconciliation sweeps run at most once per 24 hours while retaining standard 4-hour incremental sweeps.

Reason:
Guarantees that lifecycle transitions operate on current communication evidence and prevents phantom test data from polluting production databases.

## 2026-09-20 - Non-persistent dry-run execution semantics

Decision:
Dry-run sweeps in `EmailIngestionEngine` execute full message polling, regex/heuristic classification, and job alert parsing to report actionable preview metrics, but execute a database rollback upon completion without updating checkpoints.

Reason:
Allows operators to diagnose and verify email parsing behavior safely without mutating system state or advancing mailbox checkpoints.

## 2026-09-20 - Separation of simulated mock mode from real submission

Decision:
ATS adapters (`GreenhouseATSAdapter`, `LeverATSAdapter`) running with `mock_mode=True` produce status `SIMULATED` and emit `APPLICATION_SIMULATED` events. No confirmation URLs are fabricated. When invoked with `mock_mode=False`, adapters return `NOT_IMPLEMENTED` until real external endpoints and credentials are provided. Applications can only enter status `SUBMITTED` upon external confirmation.

Reason:
Upholds the fundamental contract: automated systems must never masquerade mock simulations as real external submissions.

## 2026-09-20 - Dashboard safe-by-default localhost binding

Decision:
The operations dashboard service in `docker-compose.yml` binds to `127.0.0.1:8765:8765` by default rather than exposing all interfaces (`0.0.0.0`).

Reason:
Prevents unintentional network exposure on shared LANs or cloud hosts until dedicated authentication or reverse-proxy protection is configured.




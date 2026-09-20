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

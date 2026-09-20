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

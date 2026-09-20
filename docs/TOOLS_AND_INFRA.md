# Tools and Infrastructure

Last reviewed: 2026-09-20

## Recommended V0.x stack

### Development / agent environments

Primary starting environment:
- Google Antigravity / Antigravity IDE

Supported by repo design:
- Cursor
- Claude Code
- ChatGPT / Codex-style agents
- GitHub Copilot
- any agent that can read AGENTS.md and repository docs

Antigravity supports workspace-scoped rules, workflows, and skills under .agents/. This repo uses that native structure while keeping the real project rules IDE-neutral.

Official references:
- https://codelabs.developers.google.com/getting-started-agy-ide
- https://codelabs.developers.google.com/getting-started-with-antigravity-skills

## Runtime language

Python 3.12+

Why:
- strong automation ecosystem
- Gmail/Google client libraries
- Playwright
- FastAPI
- LLM SDK ecosystem
- straightforward server and local-runner deployment

## API / service

FastAPI

Use it for:
- health
- jobs
- applications
- review queue
- configuration inspection
- audit log
- future dashboard API

## Database

PostgreSQL.

Use SQLite only for isolated unit tests or very early local experiments.

Why Postgres:
- event/audit data
- JSON support
- robust indexing
- future vector extension if needed
- easy Docker deployment
- migration support

ORM/migrations:
- SQLAlchemy 2.x or SQLModel
- Alembic

## Email

Gmail API + OAuth.

MVP model:
- scheduled polling every 4 hours by default
- configurable roughly every 3-4 hours
- incremental query using stored checkpoints plus a small overlap window
- Gmail message/thread ID deduplication
- optional once-daily reconciliation pass

Real-time Gmail push/PubSub is not needed for this project.

Start read-only.

Detailed communication rules:
- docs/EMAIL_TRACKING.md

## LLM provider layer

Use a small internal ModelGateway interface with LiteLLM-compatible routing.

Do not scatter direct OpenAI/Anthropic/Gemini calls through business logic.

Suggested task routes:
- email classification: cheap/small model
- extraction: cheap/small model
- job-to-candidate match: mid/strong model
- resume tailoring: strong model
- cover letter: mid/strong model
- tricky screening questions: strong model
- deterministic parsing first whenever possible

Local models may be configured for low-cost/private extraction.

## Browser automation

Playwright.

Use only through the policy-gated browser-runner service.

Rules:
- visible browser preferred for live application flows
- no stealth plugins
- no CAPTCHA bypass
- no fingerprint spoofing
- no automatic submission where site rules disallow it
- preserve manual checkpoints

Do not run persistent browser sessions inside the main controller container unless there is a specific reason.

## Scheduler

V0.x:
- APScheduler, a simple asyncio worker loop, cron/systemd timer, or equivalent
- default Gmail sweep: every 4 hours
- optional daily reconciliation sweep

Avoid Celery/Redis initially.

Introduce a queue only when:
- multiple workers are needed
- jobs must survive worker crashes
- browser tasks need distributed workers
- workload shows meaningful contention

## Packaging

Use:
- pyproject.toml
- uv, pip-tools, Poetry, or pip as long as dependencies are reproducible

Preferred for speed/simplicity:
- uv

## Containers

Docker Compose should eventually include:
- postgres
- controller
- worker

Optional later:
- dashboard
- reverse proxy
- backup job

Browser runner remains separate by default.

## Always-on hosting

Good options:
1. existing home server / Unraid Docker
2. small local Linux host
3. inexpensive VM

The architecture should not require cloud hosting.

## Observability

Start with:
- structured JSON logs
- health endpoint
- job-run table
- audit log
- failed-task/review queue
- last successful Gmail poll/checkpoint

Later:
- Prometheus/Grafana or OpenTelemetry only if useful

## Artifact storage

MVP:
- filesystem path outside Git + database metadata

Later:
- S3-compatible object storage such as MinIO if multiple hosts need shared artifacts

Never store sensitive application artifacts in a public bucket.

## Calendar

Future optional integration:
- Google Calendar for interview events/reminders

Do not make Calendar a prerequisite for job tracking.

## Resume/document generation

Keep source resume content structured where possible.

Possible path:
- structured profile -> template -> DOCX/PDF

Do not make a proprietary document service mandatory.

## Testing

Use:
- pytest
- pytest-asyncio
- respx/httpx mocking
- factory fixtures
- Playwright test pages for browser-runner testing
- sanitized real alert-email fixtures

## Why not a monolithic autonomous browser bot

A single agent that logs into every board, scrapes all jobs, applies, reads mail, and changes state would be:
- hard to debug
- brittle
- hard to audit
- coupled to one model
- likely to conflict with platform rules
- difficult to continue across IDEs

The recommended architecture separates:
- ingestion
- normalization
- decisioning
- document preparation
- policy
- execution
- tracking

This lets each component improve independently.

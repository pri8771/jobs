# Compact Project Context

This is the compact memory file for ChatGPT and Antigravity.

Purpose: allow either agent to resume work without reloading the entire conversation or repository history.

Keep this file concise. Update it when durable facts, architecture, priorities, or milestone status change. Do not use it as a raw activity log.

Last updated: 2026-09-20

## Ownership model

- User: product owner and final authority.
- ChatGPT: lead agent, architect, reviewer, prioritizer, and quality gate.
- Antigravity: primary execution workhorse.
- Antigravity should implement the current queue, test, commit, push, and report.
- ChatGPT should audit results, resolve ambiguity, adjust priorities, and keep the roadmap coherent.
- User instructions override both agents.

## Communication model

Use:
- coordination/AI_SYNC.md for inter-agent messages and hourly check-ins.
- coordination/WORK_QUEUE.md for prioritized execution work.
- coordination/CONTEXT.md for compressed durable memory.
- state/CURRENT.md for implementation/milestone truth.
- state/DECISIONS.md for durable architecture decisions.

Do not require full chat history to continue.

## Current product

Jobs Automation: a portable personal job-search operating system.

Core intended flow:

Job alerts / career-site discovery
-> Gmail ingestion every ~4 hours
-> normalize/dedupe
-> filter/score
-> select targeted resume
-> prepare application packet
-> manual / assisted / permitted automated application
-> capture confirmation
-> track all recruiter/company email
-> interviews / follow-ups / rejections / offers
-> analytics and continuous improvement

## Initial sources

- LinkedIn
- Indeed
- ZipRecruiter
- Dice
- employer career sites / ATS destinations

## Candidate strategy

Primary positioning:
- Enterprise Automation & Solutions Architect

Additional tracks:
- SAP BTP / Enterprise Automation
- AI Automation / Business Systems Architecture
- Senior Software Engineering / AI Workflow Automation
- Technical Product / Platform Product
- Senior iOS / Mobile Engineering Leadership
- IT Applications / Infrastructure / Automation Management

Target compensation direction:
- $150K+

Maintain targeted resume variants. Do not collapse to one generic resume.

## Email strategy

- Gmail is the first email provider.
- Poll every 4 hours by default.
- 3-4 hour cadence is acceptable.
- No real-time push architecture is required.
- Perform a daily reconciliation pass.
- Preserve Gmail message IDs and thread IDs.
- Track both inbound and outbound recruiter/company communication.
- Ambiguous application/message links go to NEEDS_REVIEW.
- Raw source messages remain authoritative evidence.

## Automation policy

- Deny auto-submit by default.
- LinkedIn submission: MANUAL_ONLY.
- Indeed submission: MANUAL_ONLY.
- No CAPTCHA bypass.
- No stealth/evasion/fingerprint spoofing.
- No fabricated application answers.
- Missing personal facts -> review, not guessing.
- Separate discovery source from application destination policy.
- Employer/ATS automation must have explicit current approval.
- A simulated application must never be recorded as a real submission.
- Real APPLICATION_SUBMITTED requires external confirmation evidence.

## Current implementation reality

Antigravity advanced the repository rapidly from V0.1 through code labeled V1.0.

The implementation includes:
- config / database / Alembic
- Gmail adapter and ingestion engine
- job-alert parsers
- deduplication
- filtering/scoring
- application packet preparation
- assisted browser application components
- simulated auto-application components
- lifecycle/CRM components
- dashboard
- health/worker/container/backup components
- tests

Important audit findings still to resolve:
1. Worker has a 4-hour loop but does not currently invoke Gmail ingestion.
2. poll-emails silently falls back to fixtures if Gmail credentials are missing.
3. --dry-run does not actually prevent persistence.
4. CLI contains a hard-coded candidate email fallback.
5. Greenhouse/Lever "live" auto-submit adapters are simulations and must never mark a real application SUBMITTED.
6. Dashboard should bind localhost by default until authentication exists.
7. No GitHub Actions CI currently verifies tests/lint/type checks.
8. state/CURRENT.md overstates production readiness.
9. Package/documented maturity versions are inconsistent.

## Current strategic priority

Near-term goal:

**Build only as far as necessary to prove one genuine, externally confirmed application workflow for the user.**

Current milestone path:
- V1.1 stabilize current implementation
- V1.2 connect real candidate/account/Gmail inputs
- V1.3 ingest/select a real job
- V1.4 build a truthful real application packet
- V1.5 complete a real assisted application path
- V1.6 prove one genuine system-submitted application with external confirmation

After V1.6:
- stop broad development,
- perform ChatGPT review,
- reassess priorities before expanding further.

Detailed near-term plan:
- docs/FIRST_REAL_APPLICATION_PLAN.md

The V2/V3 vision remains tentative future direction only:
- docs/TENTATIVE_V3_ARCHITECTURE.md
- docs/ROADMAP_1_TO_3.md

Do not implement Temporal, LangGraph, Jobs MCP, MinIO, pgvector, or other V2/V3 infrastructure merely because it is in the tentative plan.

## Account/integration expectations before a real application

Likely required in V1.2+:
- real candidate facts
- canonical resume source(s)
- Google Cloud project for runtime Gmail OAuth
- Gmail read-only connection
- LinkedIn account/profile
- Indeed account/profile
- ZipRecruiter account/profile
- Dice account/profile
- dedicated authenticated browser profile for application work as needed

Likely manual checkpoints:
- login
- MFA
- CAPTCHA
- phone/email verification
- profile confirmation
- missing personal facts

The runtime should own its own OAuth/API state; it must not depend on ChatGPT/Antigravity being open.

## Immediate objective

Current milestone: V1.1 Stabilization and truthful integration.

Priority is to fix correctness, wiring, safety, and CI before connecting real data.

## Repo portability

Critical project knowledge must remain in Git.

IDE-specific instructions should be thin adapters to:
- AGENTS.md
- coordination/CONTEXT.md
- coordination/WORK_QUEUE.md
- coordination/AI_SYNC.md
- state/CURRENT.md
- state/DECISIONS.md

## Context hygiene

Every active agent should:
1. read this file first after AGENTS.md,
2. read WORK_QUEUE.md,
3. read only the recent section of AI_SYNC.md,
4. inspect recent git commits,
5. load deeper docs/code only for the task being executed.

When this file exceeds roughly 250 lines, compress it rather than endlessly appending.

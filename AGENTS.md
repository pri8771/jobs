# Agent Contract

This file is the cross-IDE contract for every AI agent that works in this repository.

## Mission

Build and operate a portable personal job-search automation system that discovers relevant jobs, prepares high-quality applications, submits only through permitted workflows, and tracks the complete application lifecycle and related communications.

## Source of truth

Do not rely on conversation memory as project state. Before meaningful work, read:

1. README.md
2. docs/PROJECT_SPEC.md
3. docs/ARCHITECTURE.md
4. docs/PLATFORM_CONSTRAINTS.md
5. docs/ROADMAP.md
6. state/CURRENT.md
7. state/DECISIONS.md

If these conflict, use this precedence:
AGENTS.md > docs/PROJECT_SPEC.md > explicit architecture decisions in state/DECISIONS.md > other docs > code comments.

## Non-negotiable rules

- Keep the system portable across IDEs, LLMs, and model providers.
- Keep business logic independent from Antigravity, Cursor, Claude, ChatGPT, or any single model API.
- Use provider adapters and typed interfaces.
- Do not commit passwords, API keys, OAuth refresh tokens, cookies, browser profiles, resumes containing private data unless the user explicitly chooses to store them.
- Secrets belong in environment variables, local secret files ignored by Git, or a secret manager.
- No CAPTCHA bypass, anti-bot evasion, fingerprint spoofing, rate-limit bypass, or stealth scraping.
- Do not automate job submission on a platform when its current terms prohibit that behavior.
- Prefer official APIs, email alerts, feeds, approved integrations, and employer/ATS application pages.
- Every automated action that can change external state must be auditable.
- Submission must be idempotent: never intentionally submit twice to the same job.
- Never fabricate answers to application questions. Unknown candidate facts must pause or route to a review queue.
- Never invent work authorization, sponsorship, salary history, education, certifications, dates, or employment details.
- A model may recommend or draft; deterministic code owns state transitions, deduplication, policy checks, and audit logging.

## Agent start protocol

At the start of a task:

1. Read the canonical files listed above.
2. Inspect git status and recent commits.
3. Read the current checkpoint in state/CURRENT.md.
4. Work only on tasks inside that checkpoint unless the user explicitly changes scope.
5. Prefer tests and small interfaces before broad implementation.

## Agent finish protocol

Before ending a meaningful work session:

1. Run the relevant tests, lint, and type checks.
2. Update state/CURRENT.md with:
   - what changed
   - what was verified
   - current blockers
   - exact next task
3. Update state/DECISIONS.md if an architectural or behavioral decision changed.
4. Update docs when implementation changes the truth.
5. Commit with a clear message.
6. Push the branch if credentials permit.
7. Stop at the checkpoint boundary. Do not silently continue into the next version.

## Development style

- Python 3.12+.
- Strong typing where practical.
- Small modules with explicit interfaces.
- Pydantic models for external and internal payload boundaries.
- SQL migrations for persistent schema changes.
- Structured logs.
- Tests for parsers, scoring, lifecycle transitions, deduplication, and policy enforcement.
- Make integrations replaceable.
- Keep LLM prompts versioned in the repository.
- Prefer deterministic parsing before LLM extraction; use LLMs for ambiguity, semantic matching, summarization, tailoring, and drafting.

## Pulling facts from email

Email is evidence, not absolute truth. Normalize and link messages to job/company/application records, but preserve original provider message IDs and timestamps so decisions can be traced.

## Application automation policy

The execution engine must classify every destination into one of:

- MANUAL_ONLY
- ASSISTED
- AUTO_ALLOWED
- BLOCKED

The policy decision is stored with the application attempt. AUTO_ALLOWED requires an explicit adapter or allowlist entry and no known platform-policy conflict.

## Definition of done

A feature is not done until:
- it has tests or a documented verification procedure,
- state is updated,
- failure behavior is explicit,
- secrets are not exposed,
- and a different agent can understand how to continue by reading the repo alone.

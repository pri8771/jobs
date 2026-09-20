# Jobs Automation

Portable, auditable job-search automation that can be continued from Antigravity, Cursor, Claude, ChatGPT, Codex, or another IDE/agent without relying on chat history.

## Goal

Build a personal job-search operating system that can:

1. Create and keep job-board profiles consistent.
2. Receive job-alert emails from LinkedIn, Indeed, ZipRecruiter, Dice, employer career sites, and ATS platforms.
3. Parse, normalize, deduplicate, and score jobs against configurable criteria.
4. Prepare targeted application materials using the correct resume track.
5. Apply automatically where the destination permits automation, and fall back to assisted/manual submission where it does not.
6. Track every application from discovery through application, recruiter contact, interviews, rejection, offer, acceptance, or withdrawal.
7. Attach all relevant email communication and events to the correct company/job/application.
8. Keep a complete audit trail of what the automation did and why.

## Candidate strategy

The durable career targeting and resume strategy is in:

docs/CANDIDATE_POSITIONING.md

Current high-level direction:
- primary positioning: Enterprise Automation & Solutions Architect
- also target AI Automation / Senior Software Engineering, SAP BTP / Integration, Technical Product / Platform, iOS/Mobile leadership, and IT Applications/Infrastructure leadership
- target $150K+ roles
- maintain multiple targeted resume variants rather than one generic resume

## Initial platform set

- LinkedIn
- Indeed
- ZipRecruiter
- Dice

Dice is the fourth initial board because it is technology-focused and supports profiles plus recurring job alerts. Platform adapters are modular so it can later be replaced or supplemented by Wellfound, Glassdoor, company career sites, or ATS-specific sources.

## Canonical project context

Every agent must read these files before making meaningful changes:

1. AGENTS.md
2. docs/PROJECT_SPEC.md
3. docs/CANDIDATE_POSITIONING.md
4. docs/ARCHITECTURE.md
5. docs/PLATFORM_CONSTRAINTS.md
6. docs/ROADMAP.md
7. state/CURRENT.md

The repository—not a chat transcript—is the source of truth.

## Portability

Thin instruction adapters are included for multiple tools:

- Antigravity: .agents/rules/, .agents/skills/, .agents/workflows/, and GEMINI.md
- Cursor: .cursor/rules/project.mdc
- Claude Code: CLAUDE.md
- GitHub Copilot: .github/copilot-instructions.md
- Generic agents / Codex: AGENTS.md

All adapters point back to the same canonical project documents to prevent rules from drifting.

## Proposed runtime

- Python 3.12+
- FastAPI
- SQLAlchemy/SQLModel + Alembic
- PostgreSQL in normal operation; SQLite may be used for isolated tests
- Gmail API with OAuth for email ingestion
- LiteLLM-compatible model routing for replaceable LLM providers
- APScheduler or a simple worker loop for MVP scheduling
- Playwright only for destinations where browser automation is permitted
- Docker Compose for the always-on controller
- Optional local desktop browser runner for interactive/manual checkpoints

## Safety and platform policy

Do not build CAPTCHA bypasses, anti-bot evasion, fingerprint spoofing, or hidden automation.

LinkedIn and Indeed currently restrict or prohibit third-party automated application behavior. Treat those platforms as discovery/profile/alert sources and use their native application flows manually unless an approved integration explicitly permits automation.

The eventual automatic-submit path should prioritize employer career sites and ATS platforms whose rules permit it. Every submit action must be logged.

## Start in Antigravity

Clone/open this repository as the project root, then paste the prompt in:

prompts/ANTIGRAVITY_START.md

Antigravity should work only through the current checkpoint, update repository state, run verification, commit, push, and then stop for the next checkpoint.

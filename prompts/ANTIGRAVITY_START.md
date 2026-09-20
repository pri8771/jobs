# Antigravity Start Prompt - V0.1

Paste the block below into a new Antigravity conversation opened at the repository root.

---

You are taking over the Jobs Automation repository.

Your job is to implement the current checkpoint only. Do not rely on this chat for project history; the repository is authoritative.

Start by reading, in order:

1. AGENTS.md
2. README.md
3. docs/PROJECT_SPEC.md
4. docs/ARCHITECTURE.md
5. docs/PLATFORM_CONSTRAINTS.md
6. docs/DATA_MODEL.md
7. docs/ROADMAP.md
8. state/CURRENT.md
9. state/DECISIONS.md

Then inspect the full repository tree and git history.

Current target: V0.1 - Portable foundation + profiles.

Implement V0.1 end-to-end. At minimum:

- create a Python 3.12+ package structure
- add pyproject.toml
- add .env.example and a safe .gitignore
- add Docker Compose with PostgreSQL
- add typed configuration models/loaders for:
  - candidate profile
  - job search criteria
  - platform accounts/alerts
  - model routing
  - application policy
- add non-secret example YAML configuration
- add validation that refuses fabricated/required-but-unknown candidate facts
- add foundational database models and Alembic migration(s)
- implement a policy registry with default-deny AUTO submission behavior
- implement CLI commands:
  - validate-config
  - db-check
  - status
- implement a generated profile setup worksheet/checklist for LinkedIn, Indeed, ZipRecruiter, and Dice
- add tests for config validation, policy behavior, and database startup/schema
- keep integrations behind interfaces; do not implement Gmail or browser automation yet
- do not implement application submission yet

Use Antigravity project-native structure already in this repo. Follow all rules.

Do not invent the user's work authorization, sponsorship needs, compensation, exact target roles, or other missing facts. Put explicit TODO/null placeholders where information is not confirmed.

Verification before checkpoint completion:

1. install dependencies
2. run formatter/lint if configured
3. run type checks if configured
4. run tests
5. bring up PostgreSQL with Docker Compose and run db-check if Docker is available
6. validate the example configuration
7. inspect git diff for secrets
8. update state/CURRENT.md with exact work completed, verification results, blockers, and next action
9. update state/DECISIONS.md if architecture changed
10. update docs if implementation changed the documented truth
11. commit all V0.1 work with a clear commit message
12. push to the current GitHub branch if credentials are available

STOP after V0.1 is complete and verified.

Do not continue to V0.2 until I explicitly tell you to proceed.

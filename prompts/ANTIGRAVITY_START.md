# Antigravity Start Prompt - V0.1

Paste the block below into a new Antigravity conversation opened at the repository root.

---

You are taking over the Jobs Automation repository.

Your job is to implement the current checkpoint only. Do not rely on this chat for project history; the repository is authoritative.

Start by reading, in order:

1. AGENTS.md
2. README.md
3. docs/PROJECT_SPEC.md
4. docs/CANDIDATE_POSITIONING.md
5. docs/ARCHITECTURE.md
6. docs/EMAIL_TRACKING.md
7. docs/PLATFORM_CONSTRAINTS.md
8. docs/DATA_MODEL.md
9. docs/ROADMAP.md
10. state/CURRENT.md
11. state/DECISIONS.md

Then inspect the full repository tree and git history.

Current target: V0.1 - Portable foundation + profiles.

Implement V0.1 end-to-end. At minimum:

- create a Python 3.12+ package structure
- add pyproject.toml
- add Docker Compose with PostgreSQL
- add typed configuration models/loaders for:
  - candidate profile
  - job search criteria
  - platform accounts/alerts
  - email polling configuration
  - model routing
  - application policy
- use the existing non-secret example YAML configuration as the starting contract
- preserve the committed Gmail polling policy: 4 hours by default, configurable around 3-4 hours; do not design for real-time Gmail push
- add validation that refuses fabricated/required-but-unknown candidate facts
- add foundational database models and Alembic migration(s)
- ensure foundational message/application entities can later support Gmail message IDs, thread IDs, inbound/outbound direction, and application/contact linking as specified in docs/EMAIL_TRACKING.md
- implement a policy registry with default-deny AUTO submission behavior
- implement CLI commands:
  - validate-config
  - db-check
  - status
- implement a generated profile setup worksheet/checklist for LinkedIn, Indeed, ZipRecruiter, and Dice
- ensure the worksheet uses the role targeting/resume strategy in docs/CANDIDATE_POSITIONING.md
- add tests for config validation, policy behavior, and database startup/schema
- keep integrations behind interfaces; do not implement Gmail OAuth/polling yet because that belongs to V0.2
- do not implement application submission yet

Use Antigravity project-native structure already in this repo. Follow all rules.

Known project facts are already seeded in config/candidate_profile.example.yaml and docs/CANDIDATE_POSITIONING.md, including candidate name/location, target role families, targeted resume strategy, and $150K+ target. Use those as canonical context.

Do not invent the remaining unknown facts such as work authorization/sponsorship, exact base-vs-total-comp threshold, remote preference, relocation/travel answers, phone/email/profile URLs, or missing employment dates. Put explicit TODO/null placeholders where information is not confirmed.

Important future requirements that the V0.1 data/config foundation must not block:
- V0.2 will poll Gmail several times per day, not continuously
- default Gmail cadence is every 4 hours
- job alerts and recruiter/application emails share the same ingestion pipeline
- both incoming and outgoing recruiter/company emails must eventually be tracked
- Gmail message IDs and thread IDs must be preserved
- communication must link to company/contact/job/application records
- ambiguous email relationships must route to NEEDS_REVIEW
- the system must preserve complete chronological recruiter/company threads
- V0.6 will use these messages to drive application lifecycle events and follow-up tasks

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

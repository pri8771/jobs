# Current State

Updated: 2026-09-20

## Current checkpoint

V0.1 - Portable foundation + profiles

## Completed

- GitHub repository identified: pri8771/jobs
- repository initialized
- canonical cross-IDE agent contract defined
- product specification defined
- candidate positioning and targeted-resume strategy added
- target compensation direction seeded at $150K+
- target role families seeded
- architecture defined
- platform automation constraints documented
- runtime data model defined
- initial profile/alert plan defined
- tools/infrastructure plan defined
- Antigravity rules/skills/workflows added
- Cursor, Claude Code, Copilot, and generic agent entry points added
- non-secret candidate/search/platform/model/policy config templates added
- Gmail polling cadence standardized at 4 hours by default, configurable around 3-4 hours
- recruiter/company communication tracking rules added
- roadmap defined

## Decisions currently in force

- Git is the development/project-context source of truth.
- PostgreSQL will be the normal runtime database.
- Gmail email ingestion is the primary cross-platform discovery/status bus.
- Gmail does not need real-time processing; use a 4-hour default polling interval with a configurable 3-4 hour operating range.
- Perform an optional daily reconciliation pass to catch gaps.
- Track both inbound and outbound recruiter/company email and preserve full Gmail thread history.
- Raw Gmail message/thread IDs remain authoritative evidence for email-derived lifecycle changes.
- Ambiguous email/application links must route to NEEDS_REVIEW rather than guessing.
- LinkedIn, Indeed, ZipRecruiter, and Dice are the initial four job boards.
- Dice is the fourth board because it is technology-focused and supports profile + alerts.
- LinkedIn and Indeed submission automation is disabled under their current rules.
- Auto-apply will target separately evaluated employer/ATS destinations.
- Antigravity is the first execution environment, but the implementation must remain IDE/model-neutral.
- LiteLLM-compatible model routing is preferred.
- MVP scheduler stays simple; do not introduce Celery/Redis prematurely.
- Browser execution is separated from the always-on controller.
- Primary career positioning is Enterprise Automation & Solutions Architect.
- Maintain multiple targeted resume variants rather than one generic resume.
- Search should cover enterprise automation/SAP BTP, AI automation/software, technical product/platform, iOS/mobile leadership, and IT applications/infrastructure leadership.
- Target compensation is $150K+; implementation must confirm base vs total-comp semantics before using this as a hard rejection rule.

## Next implementation tasks for V0.1

1. Create Python project scaffold and Docker Compose PostgreSQL.
2. Add config models and loaders using the committed YAML contracts.
3. Ensure the email configuration model supports the committed 4-hour default cadence.
4. Add policy registry with deny-by-default behavior.
5. Add database models/migrations for foundational entities.
6. Add CLI commands:
   - validate-config
   - db-check
   - status
7. Add tests.
8. Generate a profile setup worksheet from validated config.
9. Use that worksheet to complete/verify LinkedIn, Indeed, ZipRecruiter, and Dice profiles.
10. Update this file with verification results.

## User-input tasks during V0.1

Already known:
- primary candidate positioning
- target role families
- Pittsburgh + US-remote search seed
- $150K+ compensation target direction
- targeted resume strategy
- known education and recent role history
- email polling does not need to be real-time; 3-4 hour cadence is sufficient

Still needs user confirmation/input:
- canonical resume file(s) to use
- exact base-vs-total-comp interpretation for the $150K+ threshold
- remote/hybrid/on-site preferences beyond the current search seed
- work authorization / sponsorship answers
- relocation/travel preferences
- phone/email and profile URLs
- reusable application answers
- account/profile status for LinkedIn, Indeed, ZipRecruiter, Dice
- any missing exact employment dates/details

Unknown answers must remain TODO; agents must not infer them.

## Blockers

None for scaffolding.

Actual profile creation may require user login, MFA, CAPTCHA, or manual confirmation on each platform. Treat these as normal interactive checkpoints, not errors.

## Exact next action

Run prompts/ANTIGRAVITY_START.md in Antigravity and implement only V0.1.

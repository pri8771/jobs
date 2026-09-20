# Current State

Updated: 2026-09-20

## Current checkpoint

V0.1 - Portable foundation + profiles

## Completed

- GitHub repository identified: pri8771/jobs
- repository initialized
- canonical cross-IDE agent contract defined
- product specification defined
- architecture defined
- platform automation constraints documented
- runtime data model defined
- initial profile/alert plan defined
- roadmap defined

## Decisions currently in force

- Git is the development/project-context source of truth.
- PostgreSQL will be the normal runtime database.
- Gmail email ingestion is the primary cross-platform discovery/status bus.
- LinkedIn, Indeed, ZipRecruiter, and Dice are the initial four job boards.
- Dice is the fourth board because it is technology-focused and supports profile + alerts.
- LinkedIn and Indeed submission automation is disabled under their current rules.
- Auto-apply will target separately evaluated employer/ATS destinations.
- Antigravity is the first execution environment, but the implementation must remain IDE/model-neutral.
- LiteLLM-compatible model routing is preferred.
- MVP scheduler stays simple; do not introduce Celery/Redis prematurely.
- Browser execution is separated from the always-on controller.

## Next implementation tasks for V0.1

1. Create Python project scaffold and Docker Compose PostgreSQL.
2. Add config models and loaders.
3. Add example candidate/search/platform configuration.
4. Add policy registry with deny-by-default behavior.
5. Add database models/migrations for foundational entities.
6. Add CLI commands:
   - validate-config
   - db-check
   - status
7. Add tests.
8. Generate a profile setup worksheet from validated config.
9. Update this file with verification results.

## User-input tasks during V0.1

The user will eventually need to provide/confirm:
- canonical resume(s)
- preferred target titles
- compensation floor/range
- location and remote preferences
- work authorization / sponsorship answers
- relocation/travel preferences
- reusable application answers
- profile links
- account/profile status for LinkedIn, Indeed, ZipRecruiter, Dice

Unknown answers must remain TODO; agents must not infer them.

## Blockers

None for scaffolding.

Actual profile creation may require user login, MFA, CAPTCHA, or manual confirmation on each platform. Treat these as normal interactive checkpoints, not errors.

## Exact next action

Run prompts/ANTIGRAVITY_START.md in Antigravity and implement only V0.1.

# Roadmap

## Superseding milestone cadence — 2026-09-20

The owner has changed the formal milestone checkpoints to:

**V1.7 -> V2.0 -> V2.3 -> V3.0**

V1.5/V1.6 remain required application-execution artifacts on the path to the next formal checkpoint, but they are no longer separate planning stops.

The old V1.8 dashboard requirements and V1.9 reliability/learning requirements are **absorbed into V2.0 acceptance** rather than discarded.

V2.3 is now the explicit bridge from the V2.0 operating system to the V3.0 multi-agent career network. Its contract is in `docs/V2_3_SPEC.md`.

Execution program:
- `docs/V1_7_TO_V3_ACCELERATION_PLAN.md`
- `coordination/ARTIFACT_INDEX.md`
- `coordination/WORK_QUEUE.md`

: V1.0 -> V3.0

This roadmap is outcome-based. Version labels represent demonstrated capabilities, not merely the presence of source files.

ChatGPT owns prioritization. Antigravity is the primary implementer.

## V1.0 — Functional prototype baseline

Status:
- existing prototype implementation

Intent:
Establish the broad architecture and prove all major modules can exist together.

Capabilities represented in the repo:
- config + database + migrations
- email adapter/ingestion architecture
- alert parsers and deduplication
- job evaluation/scoring
- packet preparation
- policy gating
- assisted browser flow
- simulated ATS automation layer
- recruiter/application lifecycle components
- dashboard
- health/worker/container/backup scaffolding

Important:
V1.0 does not mean every external integration is live or production-proven.

---

## V1.1 — Stabilization and truthful integration

Goal:
Make the prototype safe, internally honest, and operationally reliable before real data is trusted.

Deliver:
- worker actually invokes Gmail ingestion
- 4-hour polling + daily reconciliation
- no implicit fixture fallback
- true non-persistent dry-run
- remove hard-coded candidate facts
- simulation can never masquerade as real submission
- localhost dashboard by default
- GitHub Actions CI
- regression tests for email/thread/checkpoint behavior
- accurate maturity/version documentation

Exit:
The system is safe to connect to real Gmail in read-only mode.

---

## V1.2 — Real profile onboarding + read-only Gmail

Goal:
Connect the system to the user's actual job-search inputs without applying yet.

Deliver:
- canonical private candidate profile completion
- ingest canonical resume variants
- LinkedIn profile audit/setup
- Indeed profile audit/setup
- ZipRecruiter profile audit/setup
- Dice profile audit/setup
- configure useful job alerts
- Gmail OAuth read-only connection
- first real 4-hour mailbox sweeps
- verify incoming and sent recruiter/job messages
- populate initial jobs/companies/contacts/application records from real evidence
- profile/alert health checks

Exit:
Real job-alert email flows into the DB reliably and repeatably with no fake data.

---

## V1.3 — High-quality discovery, enrichment, and matching

Goal:
Turn noisy alerts into a trustworthy daily shortlist.

Deliver:
- robust parser fixtures from real alert formats
- canonical URL cleanup
- cross-source deduplication
- employer/ATS destination detection
- description enrichment where permitted
- hard rejection rules
- semantic candidate/job match
- salary/location/seniority scoring
- explanation/reason codes
- duplicate/already-applied detection
- review queue for uncertain matches
- source quality analytics
- daily "best new jobs" digest

Exit:
A human review of sampled results shows the shortlist is consistently relevant.

---

## V1.4 — Application intelligence and document preparation

Goal:
Generate a complete, truthful application packet for every shortlisted role.

Deliver:
- resume-family selector
- job-specific truthful tailoring
- requirement/evidence mapping
- cover-letter generation when useful
- reusable screening-answer library
- unknown-answer blocking
- artifact versioning/hash
- final packet preview
- resume/packet quality checks
- exact record of what would be submitted

Exit:
A shortlisted job can reliably produce a reviewable application packet without invented facts.

---

## V1.5 — Assisted application workflow

Goal:
Make applications fast while keeping the user in the loop.

Deliver:
- visible browser runner
- application-destination detection
- form field inspection
- candidate field mapping
- resume/file attachment
- review-before-submit checkpoint
- manual submission confirmation capture
- application receipt/evidence recording
- retry/resume after interruptions
- account/login requirements recorded per platform
- application queue

Exit:
User can move from approved job -> prepared form -> manual submit -> tracked confirmation with minimal repetitive input.

---

## V1.6 — Controlled live ATS automation

Goal:
Automate submission only where technically real, explicitly allowed, and well-tested.

Deliver:
- domain/platform policy registry with expiry
- first genuinely live supported ATS path(s)
- real external success verification
- real receipt/confirmation evidence
- idempotency
- rate limiting
- kill switch
- unresolved-question stop
- account/session failure routing
- per-domain regression fixtures
- never claim submission without external confirmation

Possible targets may include employer-hosted ATS flows such as Greenhouse/Lever where a current policy/technical review explicitly allows the chosen approach.

Exit:
At least one real approved ATS workflow is demonstrably end-to-end and safe.

---

## V1.7 — Recruiter CRM + interview operating system

Goal:
Track and manage every human interaction after application.

Deliver:
- complete inbound/outbound recruiter thread linking
- contact records across multiple roles
- recruiter/company timeline
- screening/interview extraction
- optional Google Calendar integration
- follow-up due logic
- unanswered recruiter detection
- thank-you/follow-up drafting
- rejection/offer/background/onboarding classification
- new-role-in-existing-thread handling
- manual correction/merge tools

Exit:
The application timeline can be reconstructed from source evidence with minimal manual bookkeeping.

---

## V1.8 — Operator dashboard and daily control center

Goal:
Make the system easy to operate without CLI-heavy workflows.

Deliver:
- new-job inbox
- shortlist/review queue
- application Kanban
- communication timeline
- interview calendar view
- follow-up queue
- offer/rejection views
- audit trail
- source health
- Gmail polling status
- worker status
- policy/kill-switch status
- safe configuration views
- useful notifications for items needing attention

Exit:
Normal daily operation can be handled from one dashboard.

---

## V1.9 — Reliability, learning, and launch hardening

Goal:
Prepare for dependable daily autonomous operation.

Deliver:
- CI/CD discipline
- backup/restore drills
- migration tests
- job-run history
- monitoring/alerts
- parser regression library
- model-provider failover
- cost tracking
- policy review reminders
- benchmark set for job matching
- funnel analytics by source/role/resume
- feedback loop from interview/rejection outcomes
- documented recovery/runbooks
- controlled release process

Exit:
The system runs for an extended period with trustworthy state and recoverable failures.

---

# V2.0 — Autonomous Personal Job Search OS

V2.0 is not "more code." It is the point where the whole system works together on real data.

## Experience

Several times per day the system:
1. checks job alerts and recruiting email,
2. discovers and deduplicates opportunities,
3. evaluates each role against the candidate strategy,
4. filters noise,
5. prepares application packets for strong matches,
6. automatically submits only where the destination is explicitly approved and genuinely supported,
7. queues manual/assisted destinations for fast review,
8. records every application,
9. follows recruiter/company communications,
10. updates interviews/rejections/offers,
11. produces follow-up tasks,
12. keeps the user focused on decisions rather than clerical work.

## V2.0 characteristics

- real Gmail, not fixtures
- real profiles and job alerts
- real candidate/resume data
- real audit trail
- no invented candidate answers
- no fake application confirmations
- policy-gated automation
- idempotent application handling
- complete recruiting CRM
- recoverable database/backups
- dashboard-driven operation
- provider/model portability
- cross-IDE project continuity
- measurable job-search funnel
- human review for uncertainty

V2.0 should feel like a dependable personal recruiting operations team.

---

# V3.0 — Autonomous Career Agent Network

V3.0 expands from "job application automation" into a continuously improving personal career organization.

## Agent roles

A V3.0 deployment may include specialized agents such as:
- Market Scout — watches companies, roles, skills, compensation, hiring patterns.
- Opportunity Matcher — evaluates roles against long-term career goals, not only keywords.
- Resume Strategist — manages evidence-backed resume variants and experiments.
- Application Operator — handles approved application workflows.
- Recruiter CRM Agent — manages contacts, threads, follow-ups, and relationship history.
- Interview Agent — prepares company/role/recruiter briefs and interview practice.
- Networking Agent — identifies referral/networking opportunities and drafts outreach.
- Portfolio/Brand Agent — keeps GitHub, portfolio, LinkedIn, and public career material aligned.
- Policy/Safety Agent — prevents fabricated facts, duplicate submissions, and disallowed automation.
- Analytics Agent — learns from funnel outcomes and proposes strategy changes.

## V3.0 capabilities

- discovers roles beyond job-board alerts
- monitors target companies directly
- tracks recruiter relationships over months/years
- identifies referral paths
- maintains a career opportunity graph across companies, people, roles, skills, and projects
- prepares interview briefs automatically
- proposes portfolio projects/content that close skill gaps
- measures which resume positioning produces responses
- learns which sources/roles/companies are worth time
- recommends changes based on actual outcomes
- coordinates multiple specialized agents while maintaining one auditable source of truth
- operates locally/self-hosted where practical, with cloud models used selectively
- remains human-governed for consequential external actions

## V3.0 experience

The user should be able to say:

"Find me a better job."

The system should already know:
- the candidate's truthful career history,
- target compensation,
- preferred role families,
- what has already been applied to,
- who has responded,
- which resume works for which role,
- which recruiters are active,
- upcoming interviews,
- where follow-up is needed,
- what the market is doing,
- and what actions are allowed.

It then organizes the work, executes safe/approved tasks, asks only when a real decision or missing fact requires the user, and preserves a complete audit trail.

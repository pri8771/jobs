# First Real Application Plan

## Current strategic goal

Stop broad platform expansion.

The immediate product goal is:

**Jobs Automation can take the user's truthful candidate data and a real job opportunity through preparation and execute one genuine application workflow with external confirmation, without fabricating candidate facts or submission success.**

After this is demonstrated, pause and reassess before expanding into recruiter CRM, advanced dashboards, Temporal, multi-agent career intelligence, or other V2/V3 breadth.

## Definition of "real application"

A real application requires all of the following:

1. a real job opening
2. real candidate data
3. a real application destination
4. the correct resume/application packet
5. all required application answers known or explicitly reviewed by the user
6. actual external submission through an allowed workflow
7. externally observable evidence that the destination accepted the application

Valid evidence may include:
- actual confirmation page
- actual employer/ATS reference or receipt
- application-confirmation email
- employer/ATS account status showing submitted/applied

A locally generated receipt, fake URL, mock response, simulated event, or database state is not proof of application.

## Near-term milestone sequence

### V1.1 — Stabilization

Fix current implementation truth/safety:
- worker Gmail wiring
- no fixture fallback
- true dry-run
- no hard-coded candidate facts
- simulation != submission
- safe dashboard
- CI
- regression tests
- truthful project state

Exit:
Safe to use real data.

### V1.2 — Candidate + account onboarding

Required user/account setup:
- complete canonical candidate facts needed for applications
- add canonical resume source(s)
- create/verify LinkedIn profile
- create/verify Indeed profile
- create/verify ZipRecruiter profile
- create/verify Dice profile
- create Google Cloud project for Gmail OAuth
- connect Gmail read-only to Jobs Automation
- configure real job alerts

Do not fabricate missing facts.

Likely manual checkpoints:
- sign-up
- login
- MFA
- CAPTCHA
- phone verification
- profile confirmation

Exit:
System has real candidate data and real job alerts.

### V1.3 — Real job ingestion and selection

Deliver:
- process real alert emails
- dedupe real jobs
- normalize destination URLs
- identify source board vs actual application destination
- score/filter against candidate strategy
- manually review a sample for quality
- select one or more strong real jobs to use as application candidates

Exit:
At least one real strong-match job is selected with a known application URL.

### V1.4 — Real application packet

Deliver:
- choose correct base resume family
- tailor truthfully to selected real job
- produce exact resume artifact
- produce cover letter if needed
- prepare screening answers only from canonical facts
- block unresolved questions
- create packet manifest/hash
- user can inspect exact packet

Exit:
At least one real job has a complete, truthful, reviewable packet.

### V1.5 — Assisted real application

Deliver:
- dedicated browser profile/runner
- destination form inspection
- prefill known fields
- upload exact resume artifact
- stop at unknown questions/login/MFA/CAPTCHA
- preserve user review checkpoint
- capture real confirmation evidence after user submits

This milestone gives us a reliable fallback even if full automation is not allowed.

Exit:
One real application can be completed with automation assistance and correctly tracked.

### V1.6 — First genuine system-submitted application

Goal:
Prove Jobs Automation can perform an actual external submission for at least one approved destination.

Required:
- choose a real job whose destination permits the planned automation path
- current explicit policy approval for that destination/method
- validated application packet
- idempotency
- rate limit/safety guards
- unresolved-question stop
- user authorization before the consequential live submission
- execute actual submission
- detect/capture real external confirmation
- persist real APPLICATION_SUBMITTED only after external confirmation
- capture resulting confirmation email later if one arrives
- audit the complete attempt

If the selected job requires MFA/CAPTCHA/manual interaction:
- the system may use the assisted path instead,
- but that does not count as a fully automated submission.

Exit:
At least one genuine, externally confirmed application has been submitted through Jobs Automation.

## Stop point

After V1.6 is demonstrated:
- stop broad development,
- perform ChatGPT review,
- evaluate what worked/failed,
- decide whether next priority is higher application coverage, recruiter CRM, dashboard, research/market scouting, or the tentative V2/V3 architecture.

## User involvement required before live submission

The software may autonomously build/test up to the live boundary.

Before the first consequential real application:
- surface the exact job
- surface exact resume/document packet
- surface all screening answers
- surface submission method/policy
- surface unresolved risks
- obtain explicit authorization for that live application

Do not submit a random job merely to prove the system works.

The proof job should be one the user would actually want.

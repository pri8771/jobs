# Lead Future Work Backlog

Purpose: give ChatGPT useful, safe work to pull forward whenever the active milestone is blocked by Antigravity, CI, or a user-interactive boundary.

This is a preparation/review backlog, not permission to cross live-action boundaries.

## Pull-forward rule

When the highest-priority current milestone is waiting on another owner:
1. do not duplicate active implementation already assigned to Antigravity unless a lead-side patch is explicitly needed,
2. take the highest-value non-conflicting item below,
3. prefer work that reduces future critical-path time,
4. write results into Git so Antigravity can reuse them,
5. never weaken the active acceptance gate,
6. never connect accounts, grant OAuth, submit applications, message people, or perform other consequential external actions without the required user authorization.

## Tier A — accelerate the current first-real-application path

### A1. V1.4 adversarial review assets
- keep expanding edge-case tests/guidance for packet truthfulness,
- inspect new Antigravity commits immediately when they land,
- pre-identify migration/model/test hazards,
- verify exact resume attribution and artifact integrity.

### A2. V1.5 assisted-browser contract
Prepare/maintain:
- form-field classification contract,
- canonical field/provenance mapping schema,
- safe file-upload contract,
- manual-barrier classification,
- pre-submit review manifest,
- external confirmation evidence requirements,
- retry/resume behavior.

Current seed document:
- docs/V1_5_FAST_START.md

### A3. V1.6 controlled-submit acceptance contract
Prepare:
- policy decision requirements,
- user authorization receipt/record,
- idempotency key rules,
- duplicate-application detection,
- exact preflight checklist,
- external-confirmation rules,
- failure rollback/state machine,
- audit-log requirements.

No live submit until user authorizes the exact job/packet/method.

### A4. Proof-job selection criteria
Prepare a reusable proof-job checklist:
- actually desirable to the user,
- compensation fit,
- location/work-arrangement fit,
- role-family fit,
- live/current posting,
- application destination identified,
- application method compatible with project policy,
- no mandatory unknown qualifications that make it a poor test,
- not chosen merely because it is technically easy to automate.

Do not select/submit a live job without user review.

## Tier B — remove V1.2/V1.3 delays after V1.4

### B1. Candidate provenance contract
Design a private-safe provenance format:
- field path,
- value presence (not necessarily raw sensitive value in Git),
- provenance class: user_confirmed | source_document | inferred | unknown,
- source reference,
- verified_at,
- reviewer,
- allowed_for_application boolean.

No private candidate contents need to be committed.

### B2. Gmail OAuth/runbook
Prepare:
- Google Cloud project setup checklist,
- exact read-only scopes,
- local secret/token path conventions,
- credential validation,
- first harmless canary,
- revocation/recovery steps,
- no-mock proof requirements.

Do not authorize/connect Gmail without the user.

### B3. Job-board onboarding runbook
For LinkedIn, Indeed, ZipRecruiter, Dice:
- account/profile readiness fields,
- alert setup checklist,
- smallest manual login/MFA actions,
- expected email alert patterns,
- no password storage,
- platform-policy notes.

### B4. Real-ingestion canary acceptance
Prepare:
- exact test window,
- read-only mailbox query,
- expected evidence,
- parser/dedupe validation,
- rollback if parsing is wrong,
- proof that fixture/mock paths were not used.

### B5. Job matching benchmark
Prepare a small evaluation framework for:
- strong-fit,
- borderline,
- reject,
- duplicate,
- salary mismatch,
- location mismatch,
- seniority mismatch.

Use synthetic/public fixtures, not fabricated claims about the user's private profile.

## Tier C — measurement and learning foundations

### C1. Resume performance analytics design
Prepare SQL/query/service design for:
- applications by resume family,
- recruiter-response rate,
- screen rate,
- interview rate,
- final interview rate,
- offer rate,
- acceptance rate,
- time-to-stage,
- slicing by role family/source/company/compensation/work arrangement.

Respect sample-size/correlation caveats.

### C2. Application experiment framework
Design:
- experiment ID,
- hypothesis,
- target population,
- resume variant assignment,
- immutable treatment record,
- outcome metrics,
- minimum sample-size warnings.

No manipulative/fabricated resume claims.

### C3. Lifecycle evidence completeness
Audit whether current events can reconstruct:
- submitted,
- confirmed,
- recruiter response,
- screen,
- interview,
- final interview,
- offer,
- reject,
- withdraw,
- accept.

Prepare migration/event additions if gaps exist.

## Tier D — after first real application or when explicitly reprioritized

### D1. LinkedIn network growth design
Open-ended, non-spammy design for:
- recruiters,
- hiring managers,
- peers,
- alumni,
- former coworkers,
- referral paths,
- relationship history,
- connection suggestions,
- personalized drafts,
- outcome measurement.

No mass automation.

### D2. Recruiter CRM
Prepare data/UX contracts for:
- person/company/role relationships,
- contact timeline,
- follow-up states,
- multiple jobs per recruiter,
- evidence-grounded thread linking.

### D3. Interview agent
Prepare:
- trigger contract,
- company/role/recruiter research bundle,
- story/evidence mapping,
- question bank generation,
- calendar handoff requirements.

### D4. Future infrastructure decision records
Only when real scale/complexity justifies them, evaluate:
- Temporal,
- LangGraph,
- pgvector,
- MinIO,
- Jobs MCP,
- Tailscale,
- local model serving.

Do not introduce them merely because they appear in the long-term plan.

## Delegating pulled-forward work

When ChatGPT identifies future implementation work:
- prefer adding it to WORK_QUEUE for Antigravity instead of implementing it directly,
- assign a task ID and SP1-SP5 estimate,
- split anything >SP5,
- keep dependencies minimal,
- give Antigravity the bulk of SP1-SP3 implementation,
- retain lead ownership of architecture, hard debugging, and acceptance.

If ChatGPT produces a design/runbook/test plan, translate obvious follow-on implementation into bounded worker TODOs rather than leaving the next step implicit.

## Lead output standard

Any pulled-forward future work should end as one or more of:
- code audit,
- test plan,
- acceptance checklist,
- schema/migration proposal,
- runbook,
- design contract,
- benchmark,
- research note,
- bounded implementation patch when clearly non-conflicting.

Then:
- commit/push,
- mention it in AI_SYNC,
- keep the active milestone priority unchanged unless new evidence warrants reprioritization.

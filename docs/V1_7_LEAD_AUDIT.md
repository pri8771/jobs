# V1.7 Lead Brownfield Audit

Artifact scope:
- A-V17-CRM-EVIDENCE
- A-V17-INTERVIEW-FOLLOWUP

Baseline reviewed on main after commit 10fd61d.

## Executive conclusion

V1.7 is not greenfield. The repo already has useful CRM/lifecycle/interview/alert services and tests.

The correct path is:
- preserve working primitives,
- repair evidence/idempotency/ambiguity gaps,
- add missing lifecycle semantics,
- prove reconstruction from source evidence.

## Findings

### 1. Worker/lifecycle message processing is not idempotent

Current WorkerDaemon selects every non-JOB_ALERT message on every sweep and calls LifecycleEngine.process_message().

LifecycleEngine does not check whether an ApplicationEvent already exists for the same provider_message_id/event.

Impact:
- repeated worker sweeps can create duplicate lifecycle events,
- duplicate audit records,
- duplicate recruiter touch processing,
- duplicate interviews.

Required:
- durable processed/evidence key or source-reference idempotency check,
- repeated sweep must be a no-op for already-applied lifecycle evidence,
- test same message across two sweeps.

Recommended task:
- J17-04 / J17-06 acceptance expansion.

### 2. Interview extractor fabricates schedule data

InterviewExtractor.extract_from_message() currently defaults missing interview schedule to:
- received_at + 2 days + 2 hours,
- 45-minute duration,
- UTC.

This is fabricated candidate/recruiter operational data.

Required:
- never synthesize a meeting time as fact,
- parse explicit date/time/timezone when present,
- if schedule is absent/ambiguous, create review/unscheduled request rather than fake scheduled interview,
- preserve source message ID.

### 3. Reschedules create a new interview instead of updating/reconciling

record_interview() always inserts.

Impact:
- reschedule messages can create multiple simultaneously scheduled interviews,
- timeline becomes misleading.

Required:
- reconcile reschedule to prior interview when evidence is sufficient,
- preserve event history,
- ambiguity -> NEEDS_REVIEW.

### 4. Interview cancellation not modeled

No clear cancellation classification/transition exists.

Required:
- cancellation classification/event,
- update interview status without deleting historical evidence.

### 5. Lifecycle regression protection is incomplete

LifecycleEngine only special-cases REJECTED.

A later/duplicate lower-stage message may regress a more advanced application.

Required:
- explicit stage ordering/state-machine transition policy,
- terminal/reopen semantics,
- duplicate/out-of-order email tests.

### 6. Recruiter CRM identity is email-centric but relationship modeling is thin

RecruiterCRMService can dedupe a contact by email and create timelines through message links.

Missing for V1.7:
- explicit support for one contact across multiple applications/roles,
- safe correction/merge tools for contact/message links,
- relationship/timeline queries spanning contact -> company -> applications.

Do not overbuild a graph DB. Existing relational tables can support this with bounded additions.

### 7. New role in an existing thread needs explicit tests

Current linking/lifecycle behavior depends on MessageLinkModel.

Required:
- existing recruiter thread with a new requisition must not update the old application unless evidence/linking supports it,
- ambiguity -> review.

### 8. Follow-up task dedupe is mostly good but needs lifecycle-aware closure

UNANSWERED_RECRUITER dedupes by message ID and checks for outbound thread reply.

Need tests/repair for:
- repeated sweep after task created,
- reply arriving later should resolve/suppress stale pending task,
- recruiter sends two messages before reply,
- outbound message in same thread but before latest recruiter message does not count as reply.

### 9. Stale application logic is intentionally narrow

Current stale statuses are SUBMITTED and CONFIRMED.

Review whether SCREENING/INTERVIEWING should use a different follow-up strategy rather than the same stale rule.

Do not spam recruiter follow-ups automatically.

### 10. Lifecycle classes incomplete for V1.7 contract

Current transition map includes:
- confirmation
- recruiter outreach
- screening
- interview
- offer
- rejection

Need evidence-safe handling for:
- interview cancellation
- assessment
- background check
- onboarding
- withdrawal where sourced from real evidence

## Acceptance test pack

Lane B should add:
1. process same lifecycle message twice -> one event/audit/interview.
2. interview request with no explicit date -> no fabricated scheduled datetime.
3. explicit schedule parses correctly or routes unresolved.
4. reschedule updates/reconciles existing interview.
5. cancellation changes interview status and keeps history.
6. out-of-order lower-stage email does not regress offer/interview state.
7. one recruiter/contact across two applications.
8. existing thread + new role ambiguity -> review.
9. later candidate reply resolves/suppresses unanswered-recruiter task.
10. duplicate sweeps do not duplicate follow-up tasks.

## Lead direction

Repair these gaps within existing services. Do not rewrite CRM/lifecycle from scratch.

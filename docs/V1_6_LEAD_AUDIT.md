# V1.6 Controlled Submission — Lead Brownfield Audit

Artifact scope:
- A-V16-SUBMISSION-CONTRACT
- A-V16-FIRST-REAL-SUBMISSION

Baseline reviewed on current main.

## Executive conclusion

The current ControlledAutoApplicationEngine has useful policy/kill-switch/rate-limit/simulation scaffolding, but it is not live-submit safe.

The biggest gaps are not ATS-specific form filling. They are:
- exact authorization,
- exact packet binding,
- idempotency,
- ambiguous outcome handling,
- external confirmation truth,
- audit/task hygiene.

Keep transport/provider integration separate from submission-state truth.

## Findings

### 1. Implicit latest-packet selection is unsafe

If packet_id is omitted, execute_auto_apply() selects the latest packet for the job.

Required:
- real submission requires an explicit lead/user-approved packet ID,
- packet must belong to the job,
- packet hash/variant/artifact identity must match authorization/preflight.

Simulation/tests may use helper shortcuts, but real mode must not.

Maps to:
- J16-01
- J16-06

### 2. Explicit packet is not validated against selected job

A packet_id from another job can currently be loaded without an explicit packet.job_id == job_id guard.

Required:
- mismatch -> BLOCKED/NEEDS_REVIEW,
- adversarial test.

### 3. Packet/artifact integrity is not re-verified before submission

Adapter validation only checks basic candidate fields/unresolved questions.

Required immediately before consequential submit:
- exact packet hash,
- resume artifact exists,
- read-back hash matches packet/ResumeVariant record,
- cover letter artifact hash if applicable,
- no unresolved consequential question,
- generation/live-readiness state accepted.

### 4. No job/packet/method-specific user authorization record

AUTO_ALLOWED policy is not the same as user authorization.

Required:
- persist explicit authorization record described in docs/V1_6_SUBMISSION_CONTRACT.md,
- changed packet/method/job invalidates prior authorization,
- no blanket permission.

Maps to J16-01.

### 5. Idempotency is too weak

Current guard checks only:
- ApplicationModel with same job_id and status == SUBMITTED.

Gaps:
- APPLICATION_CONFIRMED should block duplicate.
- SUBMISSION_UNCONFIRMED must block blind retry.
- same requisition may be duplicated into more than one local JobModel.
- packet/job method should have stable idempotency key.

Maps to J16-02.

### 6. Retry loop can duplicate an application after ambiguous failure

The engine retries exceptions/RETRYABLE_ERROR automatically.

If the external submit reached the ATS but the response was lost, a retry may create a duplicate.

Required:
- distinguish definite pre-submit failure from ambiguous post-request failure,
- ambiguous -> SUBMISSION_UNCONFIRMED,
- check external confirmation/account/email evidence before retry,
- never blind-retry an ambiguous consequential request.

Maps to J16-03/J16-04.

### 7. Adapter success is treated as external confirmation

Current logic:
- if SubmissionResult.success and not SIMULATED -> Application status SUBMITTED + APPLICATION_SUBMITTED.

That is insufficient.

Required:
- adapter transport success may yield SUBMISSION_UNCONFIRMED,
- only an accepted external confirmation signal may create SUBMITTED/APPLICATION_SUBMITTED,
- confirmation page/reference/email/account status must be separately represented/evaluated.

Maps to J16-05.

### 8. Receipt semantics are underspecified

A receipt_id returned by the same submit call is not necessarily independent confirmation.

Required:
- receipt evidence type/source,
- confirmation confidence/type,
- external reference provenance,
- generic local strings never satisfy confirmation.

### 9. Pending-task completion is overbroad

_complete_tasks_for_job() marks every pending TaskModel for the job completed.

This can incorrectly close:
- unrelated NEEDS_REVIEW,
- follow-up,
- candidate decision,
- unresolved safety tasks.

Required:
- complete only tasks explicitly satisfied by successful confirmed submission,
- preserve unrelated tasks.

Add regression test.

Suggested J16-07 SP1.

### 10. Rate limiter records failed attempts as submissions

record_submission(domain) executes even when the adapter fails/NOT_IMPLEMENTED.

For pacing, an attempt timestamp may be reasonable, but the naming/telemetry is misleading.

Required:
- separate request-attempt pacing from confirmed submission metrics,
- do not let failed/NOT_IMPLEMENTED attempts inflate submission analytics.

Could be addressed as a small telemetry repair.

### 11. Current Greenhouse/Lever live transport is intentionally NOT_IMPLEMENTED

This is correct truthfulness.

Do not fake a direct ATS API.

For the first real submission, use only a transport that is actually implemented and policy-approved:
- assisted browser with explicit user final submit, or
- a future explicitly approved system-submit transport.

V2.0 does not require prohibited/fictional direct ATS auto-submit.

## Acceptance tests

1. no explicit packet ID in real mode -> blocked.
2. packet from another job -> blocked.
3. changed packet hash after authorization -> blocked.
4. missing/hash-mismatched resume artifact -> blocked.
5. missing/expired user authorization -> blocked.
6. duplicate requisition/local duplicate job -> blocked.
7. existing CONFIRMED/SUBMISSION_UNCONFIRMED -> no second submit.
8. ambiguous network outcome -> SUBMISSION_UNCONFIRMED, no blind retry.
9. transport success without external confirmation -> not SUBMITTED.
10. valid external confirmation -> SUBMITTED/APPLICATION_SUBMITTED.
11. simulation can never satisfy external confirmation.
12. unrelated pending review task remains pending after confirmed submission.
13. failed attempt does not count as successful submission analytics.

## Worker mapping

Existing:
- J16-01 SP2 authorization record
- J16-02 SP2 idempotency/duplicate guard
- J16-03 SP3 submission states
- J16-04 SP3 ambiguous recovery
- J16-05 SP2 external-confirmation gate
- J16-06 SP2 preflight/audit manifest

Add:
- J16-07 SP1 only complete submission-satisfied tasks; never blanket-complete job tasks
- J16-08 SP2 explicit packet-job/artifact integrity preflight
- J16-09 SP1 separate request-attempt pacing telemetry from successful submission metrics

## Lead direction

Do not implement a fake live Greenhouse/Lever API just to pass V1.6.

Build the authorization/idempotency/evidence state machine so any genuinely approved transport can plug into it.

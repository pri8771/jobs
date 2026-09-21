# V1.6 Submission Data Contracts

Artifacts:
- A-V16-SUBMISSION-CONTRACT
- A-V16-SUBMISSION-ENGINE-REPAIR

Purpose:
Constrain implementation-level data semantics before coding starts. Exact ORM/Pydantic names may adapt to the existing codebase, but these identities/invariants must remain.

## SubmissionAuthorization

Fields:
- id: UUID
- job_id
- application_id nullable until application record exists
- packet_id
- packet_hash
- candidate_profile_version
- resume_variant_id
- resume_artifact_sha256
- destination
- destination_provider/domain
- method
- action: SUBMIT_APPLICATION
- authorized_by
- authorization_source/reference
- policy_decision_id/version
- issued_at
- expires_at
- one_time_use: bool
- consumed_at nullable
- revoked_at nullable
- status: ACTIVE | CONSUMED | EXPIRED | REVOKED

Invariants:
- exact job + packet + method binding,
- changed packet/job/method invalidates reuse,
- expired/revoked/consumed record cannot authorize,
- no blanket "all jobs" submission authorization.

## SubmissionAttempt

Fields:
- id
- application_id
- job_id
- authorization_id
- idempotency_key
- destination
- method
- packet_id/hash
- attempt_number
- state
- started_at
- request_dispatched_at nullable
- response_received_at nullable
- completed_at nullable
- error_category nullable
- error_summary_redacted nullable
- external_confirmation_id nullable
- audit_ref

States:
- PREPARED
- AUTHORIZED
- PREFLIGHT_VALIDATED
- REQUEST_DISPATCHED
- SUBMISSION_UNCONFIRMED
- CONFIRMED
- DEFINITE_PRE_SUBMIT_FAILURE
- BLOCKED
- NEEDS_REVIEW
- CANCELLED

Do not collapse REQUEST_DISPATCHED into CONFIRMED.

## Idempotency key

Canonical logical inputs:
- canonical destination/provider/domain,
- external/public requisition/job identity,
- candidate identity/version,
- application identity when available.

Packet identity is audit-bound but should not permit a second application merely because a different packet was generated for the same requisition.

If the existing codebase uses a different stable logical identity, document and test equivalent semantics.

## DestinationPolicyDecision

Fields:
- id/version
- provider/domain/matcher
- capability: PREFILL | SUBMIT | MESSAGE etc.
- decision: MANUAL_ONLY | ASSISTED | AUTO_ALLOWED | BLOCKED
- source/evidence reference
- reviewed_at
- expires_at
- reviewer
- notes_safe

Rules:
- default absence = BLOCKED for auto-submit,
- expired AUTO_ALLOWED behaves non-authorized,
- LinkedIn/Indeed submit remains MANUAL_ONLY under current policy.

## PreSubmitManifest

Fields:
- manifest_id
- job/requisition identity
- destination/provider/domain
- policy decision/version
- authorization ID
- idempotency key
- candidate profile/version
- packet ID/hash
- resume variant ID/hash/artifact ID
- cover letter artifact ID/hash nullable
- form answers with provenance
- unresolved/manual fields
- prompt-injection warnings
- runtime barriers
- kill-switch state
- created_at
- code SHA

Any material mutation after manifest creation invalidates it.

## ExternalConfirmationEvidence

Fields:
- id
- attempt_id
- source_type:
  CONFIRMATION_PAGE | PROVIDER_REFERENCE | ACCOUNT_STATE | CONFIRMATION_EMAIL | OTHER_REVIEWED
- provider
- external_reference nullable
- observed_at
- evidence_hash/ref
- validation_method
- confidence/category
- independently_validated: bool
- redacted_summary

Rules:
- local adapter success is not confirmation,
- generated/random receipt ID is not confirmation,
- ambiguous evidence cannot mark CONFIRMED,
- simulation/mock evidence never confirms a real submission.

## Audit event minimum

Every consequential transition records:
- actor
- action
- entity IDs
- prior state
- new state
- permission/policy decision refs
- packet/artifact refs
- timestamp
- result/error category
- external evidence ref if any

## Task semantics

Confirmed submission may close only explicitly submission-satisfied tasks.

It must not blanket-complete:
- unrelated NEEDS_REVIEW,
- recruiter follow-up,
- candidate decision,
- missing-fact/safety tasks.

## Concurrency

The implementation must define one durable uniqueness/locking mechanism so two workers cannot dispatch the same logical application simultaneously.

Acceptable patterns:
- unique DB constraint on active idempotency key,
- transaction/row lock,
- equivalent durable lease.

In-memory locks alone are insufficient.

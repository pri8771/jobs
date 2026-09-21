# V1.6 Controlled Submission Contract

Artifact:
- A-V16-SUBMISSION-CONTRACT

## Purpose

Define the exact preconditions and evidence required before Jobs Automation may perform a genuine external application submit.

This document does not authorize a live submission.

## Preconditions

All required:
1. A-V14-PACKET-SAFETY ACCEPTED.
2. A-V15-ASSISTED-APPLICATION ACCEPTED.
3. A-PROOF-JOB-SELECTION ACCEPTED by the user.
4. Exact application packet is immutable and inspectable.
5. Every consequential answer is provenanced or explicitly resolved by the user.
6. Destination policy is current and explicitly permits the chosen method.
7. Duplicate/idempotency check passes.
8. User explicitly authorizes the exact job + exact packet + exact submission method.

## Authorization record

The system should persist:
- job ID / requisition
- company/title
- apply URL/destination
- packet ID/hash
- resume variant ID/hash
- policy decision/version
- authorization timestamp
- authorization actor
- method authorized
- unresolved/manual fields at authorization time
- expiration/scope of authorization

Authorization is job/packet/method-specific.

It is not blanket permission for future applications.

## Idempotency

Before submit:
- check existing active/submitted application for same normalized job/requisition,
- generate stable idempotency key from destination + requisition + candidate identity + packet,
- refuse duplicate submit unless an explicit override is authorized and audited.

## Preflight manifest

Must contain:
- job/company/title
- destination
- policy decision
- packet ID/hash
- resume variant/artifact/hash
- cover letter artifact/hash if any
- all form answers
- answer provenance
- manual/unknown fields
- upload file hashes
- authorization record ID
- idempotency key
- expected external confirmation signals

## Execution states

Recommended:
- PREPARED
- AUTHORIZED
- SUBMITTING
- SUBMISSION_UNCONFIRMED
- SUBMITTED
- FAILED
- NEEDS_REVIEW

Never jump directly from PREPARED to SUBMITTED based on a local adapter response.

## Confirmation

SUBMITTED requires external evidence.

Acceptable examples:
- confirmation page/reference,
- employer/ATS account state,
- application confirmation email,
- equivalent external receipt.

Page navigation alone is insufficient.

## Failure behavior

On transport/browser failure:
- do not retry blindly if the submit action may have reached the destination,
- enter SUBMISSION_UNCONFIRMED,
- search external evidence before retry,
- prevent duplicate second submits,
- surface manual review.

## Audit requirements

Record:
- actor
- method
- policy
- packet hash
- idempotency key
- started/finished timestamps
- result
- external reference/evidence
- screenshots/text receipts where appropriate
- error details without secrets

## Acceptance tests

- duplicate job blocked,
- expired/missing policy blocked,
- packet mismatch blocked,
- changed packet invalidates prior authorization,
- unprovenanced required answer blocked,
- ambiguous submit failure enters SUBMISSION_UNCONFIRMED,
- mock/local receipt cannot produce SUBMITTED,
- external confirmation can transition to SUBMITTED,
- second submit attempt with same idempotency key blocked.

## User boundary

The first real application requires explicit user authorization after seeing the exact preflight manifest.


## Implementation data contracts

Use:
- `docs/V1_6_DATA_CONTRACTS.md`
- `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`

These constrain authorization identity, attempt state, idempotency, policy expiry, confirmation evidence, concurrency, and audit semantics. Implementation names may adapt to existing code, but the invariants must not weaken.

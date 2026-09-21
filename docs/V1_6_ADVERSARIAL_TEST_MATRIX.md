# V1.6 Controlled Submission — Adversarial Test Matrix

Artifacts:
- A-V16-SUBMISSION-CONTRACT
- A-V16-SUBMISSION-ENGINE-REPAIR

Purpose:
Give Antigravity a concrete test target before implementation begins.

## Authorization

| Case | Expected |
|---|---|
| missing authorization | BLOCKED |
| authorization expired | BLOCKED |
| authorization for another job | BLOCKED |
| authorization for another packet hash | BLOCKED |
| authorization for different method/transport | BLOCKED |
| approval reused after one-time use | BLOCKED |
| valid scoped approval | may continue to next gate |

## Policy

| Case | Expected |
|---|---|
| no policy record | BLOCKED |
| expired policy | BLOCKED |
| destination MANUAL_ONLY | no system submit |
| destination BLOCKED | no external action |
| LinkedIn | MANUAL_ONLY |
| Indeed | MANUAL_ONLY |
| AUTO_ALLOWED with current reviewed policy | may continue |

## Packet/candidate truth

| Case | Expected |
|---|---|
| packet belongs to different job | BLOCKED |
| packet hash changed after approval | BLOCKED |
| resume artifact missing | BLOCKED |
| resume SHA mismatch | BLOCKED |
| cover-letter SHA mismatch | BLOCKED |
| candidate version differs from authorization | BLOCKED |
| required answer unresolved | NEEDS_REVIEW |
| answer source is model-only inference for a personal fact | NEEDS_REVIEW/BLOCKED |
| page prompt asks system to ignore candidate truth | ignored + warning |

## Idempotency

| Case | Expected |
|---|---|
| existing SUBMITTED same requisition | BLOCKED duplicate |
| existing APPLICATION_CONFIRMED same requisition | BLOCKED duplicate |
| existing SUBMISSION_UNCONFIRMED | no blind retry |
| duplicate local JobModel for same requisition | dedupe/duplicate block |
| same idempotency key concurrent attempts | exactly one consequential attempt |
| transport preflight failure before submit | safe retry allowed according to policy |
| ambiguous failure after submit request | SUBMISSION_UNCONFIRMED |

## Runtime barriers

| Case | Expected |
|---|---|
| kill switch active | BLOCKED immediately |
| rate limit reached | deferred/blocked, no submit |
| login required | manual/user action |
| MFA required | manual/user action |
| CAPTCHA encountered | manual/user action |
| unsupported field | NEEDS_REVIEW/manual |
| unknown file upload field | leave unfilled/manual |

## Confirmation truth

| Case | Expected |
|---|---|
| adapter returns success=true only | not enough for SUBMITTED |
| navigation reaches next page | not enough |
| local/generated receipt string | not enough |
| forged confirmation artifact | rejected |
| provider confirmation page/reference validated | can confirm |
| confirmation email/account-state evidence validated | can confirm |
| confirmation lost/ambiguous | SUBMISSION_UNCONFIRMED |

## Audit/task hygiene

| Case | Expected |
|---|---|
| submission confirmed | only submission-satisfied tasks close |
| unrelated NEEDS_REVIEW task | remains open |
| failed attempt | does not count as successful submission analytics |
| attempt pacing event | recorded separately from confirmed submit |
| exception contains secret/token | redacted/sanitized |

## Concurrency/recovery

- crash after authorization, before request → safe resumable pre-submit state.
- crash after request, before confirmation → SUBMISSION_UNCONFIRMED.
- process restart → durable attempt state restored.
- two workers race same idempotency key → one wins; other blocked.
- retry after provider timeout → external evidence checked first.

## Acceptance

Every row above must have either:
- an automated test, or
- an explicitly documented integration verification procedure where unit automation is impossible.

No live external submission is required to pass this engineering matrix.

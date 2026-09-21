# Authorization Gates

Purpose:
Separate engineering permission from live external-action authority.

No implementation prompt, roadmap entry, worker assignment, or heartbeat grants live-action authorization by itself.

## Safe without a new live-action authorization

- local code edits
- unit/integration/adversarial tests
- static analysis
- CI
- test/dev database migrations
- deterministic synthetic integration fixtures
- public read-only job revalidation
- plans/contracts/runbooks
- redacted verification over already-authorized local proof inputs

## Explicit scoped owner authorization required

### Private candidate/resume use in a genuine proof
Requires:
- accepted proof tooling for that milestone,
- owner-approved use of the local private inputs,
- private contents remain uncommitted.

### Gmail OAuth/mailbox read
Requires:
- explicit owner authorization,
- appropriate read-only scope,
- no token/secret contents committed or logged.

### Live browser application page
Requires:
- explicit owner authorization to use the real application page with real candidate/packet data.

### Real application submission
Requires all of:
1. explicit per-application owner authorization,
2. current destination policy = `AUTO_ALLOWED`,
3. LinkedIn and Indeed are not automated,
4. accepted submission engineering,
5. verified real packet,
6. no unresolved consequential candidate answers,
7. no CAPTCHA/MFA bypass,
8. kill switch available,
9. current pre-submit integrity validation,
10. external confirmation capture path.

A submit click without external confirmation does not establish `APPLICATION_SUBMITTED`.

### External recruiter/company message
Requires explicit owner authorization for sending.

Drafting alone is not sending.

### Calendar create/update/cancel
Requires explicit owner authorization for mutation.

### Spending
Requires explicit owner authorization for vendor/action/amount.

## Missing authorization behavior

If a required authorization is absent:
- do not improvise,
- do not simulate success,
- do not silently widen authority,
- report the exact blocker,
- continue safe non-conflicting engineering/preparation work.

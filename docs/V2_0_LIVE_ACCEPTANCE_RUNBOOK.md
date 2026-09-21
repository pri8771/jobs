# V2.0 Live Acceptance Runbook

Artifact:
- A-V20-INTEGRATED-OS

This runbook is preparation only. It does not authorize Gmail OAuth, mailbox access, browser submission, messaging, or other live external actions.

## Goal

Execute one bounded, reviewable live campaign that proves the integrated OS on real data without conflating engineering fixtures with live evidence.

## Preconditions

- V1.7 milestone accepted.
- V2.0 engineering artifacts accepted or explicitly included in the campaign.
- Gmail runtime readiness engineering accepted.
- real candidate/resume identity available locally.
- user explicitly authorizes read-only Gmail/live-data canary.
- any real browser/application action has separate scoped authorization.
- secrets/tokens remain local and uncommitted.

## Campaign 1 — read-only Gmail canary

1. verify token path/scopes without printing secrets,
2. perform harmless bounded profile/list call,
3. select narrow canary query/window,
4. ingest with real provider message IDs,
5. verify checkpoint/idempotency,
6. replay same window,
7. prove no duplicate/lost rows,
8. emit redacted canary report.

Failure:
- partial fetch/checkpoint anomaly = fail closed; do not advance.

## Campaign 2 — real opportunity

Using one genuinely relevant incoming job:
1. preserve public/source identity,
2. normalize/dedupe,
3. evaluate/hard-filter/score,
4. verify reason codes,
5. produce review state,
6. if strong/relevant, build truthful packet with exact genuine resume bytes.

No application submission is implied.

## Campaign 3 — real application lifecycle

Use an already-authorized real application path or real existing lifecycle evidence.

Must prove:
- application identity,
- exact packet/resume attribution,
- destination/policy classification,
- external confirmation truth if application is submitted,
- recruiter/company messages linked safely,
- interview/rejection/offer/follow-up events when available.

Do not fabricate stages that have not happened.

## Campaign 4 — operator/reliability

Validate against real runtime:
- dashboard state,
- worker last-run history,
- Gmail readiness/status,
- policy/kill switch,
- audit trail,
- backup/restore drill,
- recovery documentation.

## Campaign 5 — analytics

Run real/current-data queries:
- source,
- role family,
- resume variant,
- response/interview/offer,
- time-to-stage.

Display N/sample size and avoid causal claims.

## Evidence bundle

Commit only permitted redacted evidence:
- code SHA
- accepted artifact IDs
- canary run IDs
- provider message ID hashes/refs where safe
- job public identity/URL
- packet/resume fingerprints
- application/lifecycle IDs
- worker/health evidence
- backup drill result
- dashboard check summary
- analytics summary
- unresolved/user-gated items

Never commit:
- OAuth tokens,
- private resume/profile contents,
- full private email bodies unless explicitly intended/sanitized,
- passwords/cookies.

## Result

Possible lead outcomes:
- LIVE_ACCEPTED
- LIVE_BLOCKED_USER_AUTH
- LIVE_BLOCKED_PRIVATE_INPUT
- LIVE_BLOCKED_PROVIDER
- LIVE_FAILED_ENGINEERING
- LIVE_NEEDS_REVIEW

Only ChatGPT lead marks V2.0 live accepted.

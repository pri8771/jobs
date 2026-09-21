# Jobs Automation — V1.7 Live-Gap Audit

Date: 2026-09-21

Scope:
Audit current `main`, active worker branches, PRs, tests, and committed proof evidence to answer one question:

> Are we actually at V1.7 with genuine live evidence for the required checkpoints?

## Verdict

**No. We are behind the owner target.**

The repository contains substantial engineering through V1.7 and some V2.0 work, but the formal/live evidence chain is incomplete.

The decisive evidence:
- `coordination/proofs/` contains only the README and V1.4 schema on main; there is no committed redacted genuine proof candidate/receipt.
- V1.5 has no genuine live assisted-browser evidence bundle.
- V1.6 has no genuine externally confirmed system-submitted application evidence.
- V1.7 has no genuine mailbox/recruiter/interview lifecycle proof bundle.

Therefore engineering presence must not be confused with live checkpoint completion.

## V1.4

### Engineering

Active source:
- branch `worker/v14-real-proof`
- PR #8

Latest substantive rework audited:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

The latest verifier materially closes previous P0A gaps:
- candidate-only evidence type,
- structural-only cannot PASS,
- mandatory local/private SHA binding,
- failure receipt,
- profile file hashing/example rejection,
- fetched-at/canonical URL/question-file checks,
- canonical packet hash recomputation,
- DB packet/resume/artifact row validation.

Remaining audit concern:
- `verify_database_linkage()` validates JobModel.apply_url and packet/resume/artifact rows, but the current inspected code does not independently compare the persisted JobSource source attestation payload fields (provider/source kind/public ID/API URL/fetch timestamp/description/question SHAs) against the local attestation. This is now a small isolated proof-integrity repair, not a broad rewrite.

CI:
- previous PR CI was green before the latest rework,
- worker reports 168 tests + Ruff + format + mypy clean locally,
- hosted workflow runs after the latest rework are currently failing to start/run because the GitHub account reports a billing/spending-limit runner lock, not a code test failure.

### Live

**Missing.**

No redacted `REAL_PROOF_CANDIDATE` + verifier PASS receipt is committed.

V1.4 is not REAL_PROVEN / COMPLETE.

## V1.5

### Engineering

Existing code batches on `worker/v15-assisted-application`:
- `44f5fd9...` initial assisted application runtime,
- `3ef4002...` lead rework,
- `09f1852...` A-R15-06..09 residual safety repairs.

Code includes:
- inspect-before-write,
- field classification,
- page/field prompt-injection handling,
- consent/manual barriers,
- exact packet requirement,
- packet/provenance hash validation,
- resume/cover-letter field-specific upload mapping,
- unknown file inputs remain manual,
- external confirmation truth hardening.

Problem:
- PR #2 is old/diverged/non-mergeable against current main.
- It should not be repaired through another giant rebase. Port only the code commits into a fresh branch from current main.

### Live

**Missing.**

No genuine visible-browser assisted proof exists showing:
real job + real accepted packet + real form inspection/prefill + review boundary + redacted field/provenance/hash evidence.

V1.5 is not REAL_PROVEN / COMPLETE.

## V1.6

### Engineering

Current main contains useful scaffolding:
- ControlledAutoApplicationEngine,
- deny-by-default policy evaluator,
- kill switch,
- rate limiter,
- ATS adapter registry,
- Application/ApplicationEvent/Audit models,
- Greenhouse and Lever adapters that truthfully return NOT_IMPLEMENTED in live mode.

Current code is **not live-submit safe**.

Known gaps from code/lead audit:
- no scoped job/packet/method authorization record,
- weak idempotency,
- no durable submission-attempt state machine,
- blind retry risk after ambiguous external request,
- adapter success may be confused with confirmation,
- packet/artifact integrity needs stronger pre-submit gate,
- blanket pending-task completion,
- failed attempt telemetry can look like submission pacing/success,
- no implemented approved live system-submit transport.

### Live

**Missing.**

No exact-job authorization + real system submit + independent external confirmation evidence exists.

V1.6 is not ENGINEERING_ACCEPTED and not REAL_PROVEN.

## V1.7

### Engineering

This is the strongest area.

PR #3 was merged into main:
- merge `be765ea42856bc695fc1eece9c1da396b4f162d4`

Current code/tests already cover substantial V1.7 behavior:
- recruiter CRM,
- one recruiter across multiple roles/applications,
- thread-role divergence,
- ambiguity routing,
- manual message relink/unlink,
- contact merge,
- interview date/time/timezone,
- reschedule/cancel,
- duplicate sweep idempotency,
- unanswered recruiter/follow-up dedupe,
- lifecycle classes,
- rejection/offer/background/onboarding safety,
- stage-regression protection.

Artifact cards remain LEAD_REVIEW/BLOCKED and should be reconciled against current main after the earlier checkpoint chain is cleared.

### Live

**Missing.**

There is no genuine real recruiter/application/interview lifecycle evidence bundle.

Fastest live proof should not wait for a future recruiter response:
use a bounded historical read-only Gmail canary, select an existing real recruiting/application thread (or a small set of real threads), run it through the production ingestion/link/lifecycle path, and commit only redacted evidence.

This requires explicit owner authorization for Gmail read-only access.

## Current true position

Engineering maturity:
approximately V1.7/V2.0 components exist.

Formal live checkpoint maturity:
below V1.4 completion because the V1.4 genuine proof is absent.

## Recovery principle

Do not assign "finish V1.6" or "get to V1.7" as a worker task.

Every next unit must be:
- one artifact,
- SP1 or SP2 whenever possible,
- one narrow code surface,
- one explicit evidence bundle,
- one review boundary.

Live proof is always a separate artifact from engineering implementation.

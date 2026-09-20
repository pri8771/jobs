# Active Work Queue

ChatGPT owns priority/order unless the user explicitly overrides it.
Antigravity executes the highest-priority unblocked work, tests it, commits, pushes, and reports through coordination/AI_SYNC.md.

Last prioritized: 2026-09-20 15:46 ET

## Strategic finish line

Current scope ends when Jobs Automation demonstrates one genuine, externally confirmed application submitted through the system for a real job the user actually wants.

Path:
- V1.1 stabilization
- V1.2 real candidate/account/Gmail onboarding
- V1.3 real job ingestion/selection
- V1.4 real application packet with immutable resume attribution
- V1.5 assisted real application
- V1.6 first genuine system-submitted application

After V1.6, stop broad development and request strategy review.

## Current milestone

V1.1 lead-review repair, then V1.2 preparation.

Antigravity's commit `60a4c91` materially satisfies the V1.1 stabilization goals and current CI is green. Lead audit found one remaining scheduler correctness issue before V1.1 is accepted.

## P0 — V1.1 lead-review repair

### 1. Do not consume the daily reconciliation slot when ingestion fails

Current behavior in `WorkerDaemon.run_sweep()` sets `last_reconciliation_at` before Gmail ingestion is known to have succeeded. If the adapter is unavailable or polling returns an error, the worker can suppress another reconciliation attempt for roughly 24 hours even though no reconciliation succeeded.

Required:
- compute whether reconciliation is due without mutating `last_reconciliation_at`,
- update `last_reconciliation_at` only after a reconciliation ingestion sweep completes successfully,
- adapter-unavailable and polling-error paths must leave the reconciliation due state eligible for the next worker run,
- explicit `reconcile=True` failure must likewise not mark reconciliation successful,
- add regression tests for adapter-unavailable/polling-error retry behavior,
- preserve the 4-hour normal cadence and existing DB checkpoint safety.

Acceptance:
- pytest, ruff, mypy green,
- CI green on pushed commit,
- tests prove failed reconciliation does not consume the 24-hour reconciliation interval.

### 2. Correct project state after the repair

After the above passes:
- mark V1.1 ACCEPTED in state/CURRENT.md,
- update coordination/CONTEXT.md so the old V1.1 audit findings are no longer listed as unresolved,
- post `READY FOR V1.2` in AI_SYNC with commit and CI evidence.

## V1.2 — work authorized after P0 repair

Engineering preparation may continue without waiting for repeated prompts. Do not connect real accounts or OAuth without the user's required interactive action.

### P1 — unblocked engineering preparation

1. Candidate onboarding contract
- validate required canonical candidate fields,
- clearly distinguish required, optional, sensitive, and review-only facts,
- never invent missing values,
- support canonical resume source registration without committing private resume contents to Git.

2. Gmail OAuth readiness
- add exact runtime configuration validation and diagnostics,
- document Google Cloud project/OAuth setup,
- support read-only Gmail scopes first,
- provide a harmless connection/canary check that does not mutate mailbox state,
- fail closed when credentials are absent.

3. Source/account onboarding checklist
- LinkedIn, Indeed, ZipRecruiter, Dice profile/alert readiness,
- record profile/alert status without storing passwords,
- identify the smallest user actions required for login/MFA/verification.

4. Real-ingestion canary plan
- define how to run the first read-only Gmail sweep,
- exact evidence required to prove no fixture/mock path was used,
- exact rollback/recovery steps if parsing is wrong.

### User-blocked V1.2 actions

Do not fabricate or bypass these. Surface them only when engineering prep is complete:
- canonical private candidate facts that are still missing,
- canonical resume source files,
- Google Cloud OAuth consent/credentials,
- Gmail authorization,
- job-board login/MFA/phone/email verification as needed.

## Later milestones

### V1.3 — Real job ingestion/matching
- ingest real alerts,
- dedupe jobs,
- detect actual application destination,
- score/filter,
- choose strong proof-job candidates.

### V1.4 — Real application packet
- correct resume family,
- immutable exact resume variant/version/artifact/hash,
- truthful tailoring,
- screening answers,
- unresolved-question block,
- permanent application -> packet -> resume attribution for later response/interview/offer analytics.

### V1.5 — Assisted real application
- authenticated browser worker/profile,
- form inspection/prefill/upload,
- user review,
- real confirmation capture.

### V1.6 — First genuine system submission
- approved real destination/method,
- exact live application explicitly authorized by user,
- execute real external submission,
- capture external confirmation,
- only then record APPLICATION_SUBMITTED.

## Standing safety rules

- LinkedIn submission: MANUAL_ONLY.
- Indeed submission: MANUAL_ONLY.
- No CAPTCHA bypass or anti-bot evasion.
- No fabricated candidate facts.
- Simulation never equals submission.
- External confirmation is required for real submission state.
- V2/V3 remains tentative reference only until after the first-real-application proof.

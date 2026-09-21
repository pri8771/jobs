# Antigravity Kickoff — Artifact-First Recovery to V1.7

Repository:
`pri8771/jobs`

You are the single active implementation session.

## Objective

Reach V1.7 with genuine live evidence at every required checkpoint.

Do not optimize for version labels.
Optimize for accepted artifacts + live proof.

## Start

1. fetch latest origin/main,
2. read:
   - AGENTS.md
   - state/CURRENT.md
   - coordination/WORK_QUEUE.md
   - coordination/RECOVERY_QUEUE_V14_TO_V17.md
   - docs/AUDIT_V1_7_LIVE_GAP_20260921.md
   - docs/V1_4_TO_V1_7_RECOVERY_EXECUTION.md
   - docs/LIVE_CHECKPOINT_EVIDENCE_STANDARD_V14_V17.md
   - docs/AUTHORIZATION_GATES.md
3. inspect the live branch/PR before changing code.

## Work model

One artifact at a time.
One small task at a time.
Prefer SP1; maximum normal task here is SP2.

After each artifact:
- tests/checks,
- push,
- READY_FOR_LEAD_REVIEW,
- stop that artifact and wait for lead acceptance before crossing its gate.

Do not stack multiple unreviewed artifacts.

## Immediate work

Active artifact:
`A-V14-P0A-INTEGRITY`

Latest repair source:
`5e5058461d5371f292c93e0c53cb0b93caba7e44`

Immediate task:
`R14-P01 / SP1`

Inspect `verify_database_linkage()` and add strict comparison between the actual persisted Greenhouse JobSource/runtime import metadata and `local_data.source_attestation` for:
- provider
- source_kind
- public job ID
- API URL
- fetched_at_utc
- description SHA
- question-list SHA
- canonical apply URL

Do not trust a local bundle simply because its strings/hashes are well-formed.

Then:
- R14-P02 adversarial mismatch/omission tests,
- R14-P03 targeted proof tests + full pytest + Ruff + format check + mypy,
- R14-P04 exact-head CI if available.

If GitHub Actions cannot start solely because of the account billing/spending lock:
- record `CI_BLOCKED_ACCOUNT`,
- do not call it code failure,
- report exact head and local checks,
- request independent exact-head validation from lead.

Then set:
`READY_FOR_LEAD_REVIEW`

Do not run private profile/resume proof inputs until ChatGPT accepts A-V14-P0A-INTEGRITY.

## After acceptance

Follow `coordination/RECOVERY_QUEUE_V14_TO_V17.md` exactly.

Important branch rule:
old PR #8 and PR #2 are source/history branches.
For clean integration artifacts, create a fresh branch from current main and port only the necessary code commits—do not drag old heartbeat/history churn into new PRs.

## Live gates

Never self-authorize:
- private candidate/resume proof use,
- Gmail OAuth/mailbox access,
- real browser form action,
- application submission,
- recruiter messaging,
- calendar mutation,
- spending.

When a live gate is reached:
- state the exact requested authorization,
- do not simulate PASS,
- continue only safe work explicitly allowed by the plan.

## Heartbeat

One session, one watcher.

Epoch:
`FIVE_MIN_2026_09_21`

Every 5 minutes while active.

Use exactly one watcher for the current work branch.
Stop it before switching branches.

## Handoff format

Every artifact review handoff:
- artifact ID
- task IDs
- branch
- exact SHA
- files changed
- tests/checks
- CI or CI_BLOCKED_ACCOUNT evidence
- blockers
- live authorization status
- next artifact
- `READY_FOR_LEAD_REVIEW`

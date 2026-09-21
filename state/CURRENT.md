# Current State

Updated: 2026-09-21 15:50 ET

## Owner target / operating model

Exactly three implementation lanes are active in parallel:

1. Lane 1 — `worker/v14-real-proof` — P0 V1.4 proof-tool integrity and genuine real proof.
2. Lane 2 — `worker/v15-assisted-application` — V1.5 assisted-application safety.
3. Lane 3 — `worker/recruiting-ops` — recruiting/reliability verification and bounded regression repair.

Old Lane C, Lane D, and Scout are paused/superseded. `worker-pc` is independent bounded support infrastructure, not a fourth implementation lane.

A short-lived planning/doc update on main introduced "single implementation session" heartbeat wording. That wording conflicts with the explicit owner directive and `AGENTS.md`; the canonical heartbeat/session entry files have been corrected back to the three-lane model.

## Version truth

| Checkpoint | Engineering | Live evidence | Formal status |
|---|---|---|---|
| V1.4 | packet engineering accepted; P0A verifier remains in rework | no genuine candidate + separately bound verifier PASS receipt | **NOT COMPLETE** |
| V1.5 | accepted A-R15-01..05 preserved; A-R15-06..09 still require current-main validation | no real visible-browser assisted proof | NOT COMPLETE |
| V1.6 | scaffold/planning exists; live-submit safety gates remain | no real externally confirmed system submission | NOT COMPLETE |
| V1.7 | substantial recruiting code merged | no genuine live lifecycle proof | NOT COMPLETE |

Owner rule: no version is COMPLETE until one genuine non-mock production-path example passes its required live gate.

## P0 — Lane 1 / A-V14-P0A-INTEGRITY

Review source:
- branch `worker/v14-real-proof`
- draft PR #8
- latest substantive implementation still `5e5058461d5371f292c93e0c53cb0b93caba7e44`
- current branch head `f3a0c414f4da08e7fb92549f64cdff39cccb3186` is heartbeat #18 at `2026-09-21T19:18:36Z`
- compare from `5e505846...` to current head shows only heartbeat-file changes; no later production repair exists

Lead verdict remains **REWORK**. Two acceptance-critical gaps are directly verified in current code:

1. `verify_database_linkage()` still returns success when no `database_url` / `db_path` is supplied. REAL_PROOF_PASS therefore does not yet require persisted packet/resume/artifact linkage.
2. The verifier still does not bind source attestation to persisted Greenhouse `JobSource` evidence. A self-consistent local attestation/questions bundle is not independently proven against persisted import evidence.

Do **not** use private candidate/profile/resume inputs until ChatGPT lead-accepts P0A.

Independent support:
- reviewed tests-only branch `worker/jobs-v14-p0a-remaining-tests-20260921-1449` / `cffae70577b6719c92e7d7edc3ecd94d00db622d` remains support evidence only,
- new bounded worker-pc task `jobs-v14-p0a-remaining-fix-20260921-1545` was dispatched to implement only the two remaining verifier defects on an isolated support branch,
- remote workflow `35647203812` was in progress at this update; no result is accepted until the actual Jobs branch/diff/tests are reviewed.

## Lane 2

- branch `worker/v15-assisted-application`
- draft PR #2
- head `ddb4f848a97dec87033cfdef7ca33642480d99bc`
- latest comparison observed: 32 commits ahead / at least 151 behind main before the newest coordination commits
- accepted task scope A-R15-01..05 remains preserved
- current work: A-R15-06..09 only
- heartbeat is still obsolete `DAYWATCH_2026_09_21` / `WATCH_15M_24H`, last check-in `2026-09-21T17:39:16Z`

Required next action: stop/verify stopped any old watcher, synchronize with latest main, start exactly one `FIVE_MIN_2026_09_21` Lane 2 watcher, validate A-R15-06..09, and request lead review. No V1.6 work yet.

Known V1.4-proof eligibility blocker remains: the prior Lane 2 machine did not have a genuine file mapped to the selected `resume_ai_software_engineer` variant. Never substitute another resume.

## Lane 3

- branch `worker/recruiting-ops`
- PR #3 accepted batch is merged to main
- head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b`
- latest comparison observed: 0 commits ahead / at least 139 behind main before the newest coordination commits
- accepted behavior includes B-R17-03, B-R20-07, B-R20-08, B-R20-05/J20-14, B-R20-01, and B-R20-02
- heartbeat is still obsolete `DAYWATCH_2026_09_21`, last check-in `2026-09-21T16:44:37Z`

Required next action: synchronize to latest main, start exactly one current 5-minute watcher, run post-integration verification, and repair only a real evidence-backed regression. No new Lane 3 PR is needed while the branch remains 0 ahead.

## Heartbeat / visible progress

Canonical standard for **each** active lane:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one watcher per Lane 1/2/3
- no cadence transitions

Lane 1 emitted valid current-epoch heartbeats #1-18 from 17:54:00Z through 19:18:36Z, then stopped for more than 30 minutes. Verify the watcher process before restarting; do not create a duplicate.

Lane 2 and Lane 3 have not migrated from the superseded DAYWATCH epoch.

Issue #7 automated heartbeat comments stopped after the Lane 1 18:18:14Z comment while Lane 1 commits continued through 19:18:36Z. Latest heartbeat and ordinary main CI jobs fail before any steps start (`steps: []`, `runner_id: 0`). Treat this as `CI_BLOCKED_ACCOUNT` / GitHub Actions runner startup failure, not a heartbeat-code regression. Direct ChatGPT lead comments to issue #7 remain mandatory each lead run.

## Live proof inventory

`coordination/proofs/` still has no accepted genuine V1.4 runtime candidate + separately bound verifier PASS receipt. V1.4 remains **NOT COMPLETE**.

## Safety

No live Gmail OAuth/mailbox access, private candidate proof execution, browser application submission, external messaging, calendar mutation, spending, MFA/CAPTCHA handling, or fabricated candidate facts without explicit scoped owner authorization.
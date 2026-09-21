# Active Work Queue

Owner target:
**Reach V1.7 with genuine live evidence at every required checkpoint.**

Authoritative execution model:
- exactly three active implementation lanes,
- one current-epoch heartbeat watcher per active lane,
- fixed 5-minute cadence (`FIVE_MIN_2026_09_21` / `ACTIVE_5M`),
- `worker-pc` is bounded independent support infrastructure only,
- live proof is separate from engineering implementation,
- version completion requires genuine non-mock production-path evidence.

## Current live status

- V1.4 live proof: **MISSING — NOT COMPLETE**
- V1.5 live assisted proof: MISSING
- V1.6 real system submission: MISSING
- V1.7 real lifecycle proof: MISSING

## Lane 1 — P0 / A-V14-P0A-INTEGRITY

Branch:
- `worker/v14-real-proof`
- draft PR #8

Latest substantive repair reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Later branch commits through `9badcd32cdc848baa3f0c657ddb45c9858d8c977` are heartbeat-only.

Lead verdict:
- **REWORK**
- no private profile/resume proof execution yet

Remaining bounded work:

### R14-P01 / RP14-T7 — mandatory database linkage
REAL_PROOF_PASS must require a configured proof DB target and successful persisted-row validation. Omitting `database_url` / `db_path`, mismatching packet/resume/artifact rows, or presenting unrelated persisted rows must fail closed.

### R14-P02 / RP14-T3 — independently trusted source attestation
Load the corresponding persisted Greenhouse `JobSource`/`Job` evidence and bind at minimum:
- provider,
- source kind,
- public job ID,
- API URL,
- fetched_at_utc,
- description/content SHA,
- question-list SHA,
- canonical apply URL.

A self-consistent forged local `source_attestation` + locally authored questions file + fabricated description SHA must not pass.

### R14-P03 — adversarial verification
Add focused tests for:
- missing DB target,
- mismatched persisted packet/resume/artifact rows,
- forged self-consistent source attestation/questions,
- DB source metadata/hash mismatch,
- fabricated description/content SHA.

A bounded tests-only `worker-pc` task is running as support. Lane 1 does not wait for it and owns the production repair.

### R14-P04 — final validation / review boundary
- synchronize PR #8 to latest main without dragging unrelated historical churn,
- focused real-proof tests,
- full `pytest`,
- `ruff check .`,
- `mypy src tests`,
- exact-head CI when GitHub Actions runners are available,
- if Actions remain blocked before steps, record `CI_BLOCKED_ACCOUNT` and request independent exact-head validation,
- set `READY_FOR_LEAD_REVIEW` / `REVIEW` and stop implementation changes.

Gate:
**Do not use private profile/resume inputs until ChatGPT lead-accepts P0A.**

After P0A acceptance:
1. real private profile/resume mapping readiness,
2. genuine V1.4 packet proof,
3. runtime `REAL_PROOF_CANDIDATE`,
4. separately bound verifier PASS receipt,
5. lead review,
6. only then V1.4 may become COMPLETE.

## Lane 2 — V1.5 assisted application

Branch:
- `worker/v15-assisted-application`
- draft PR #2

Preserve:
- accepted A-R15-01..05

Current bounded scope:
- A-R15-06 — page-level prompt-injection warning semantics,
- A-R15-07 — field-specific cover-letter/file upload mapping,
- A-R15-08 — packet/provenance/artifact integrity revalidation immediately before browser use,
- A-R15-09 — unknown file inputs remain manual/unfilled.

Current branch evidence:
- head `ddb4f848a97dec87033cfdef7ca33642480d99bc`,
- 32 commits ahead / 140 behind current main,
- heartbeat still on obsolete `DAYWATCH_2026_09_21` / `WATCH_15M_24H`, last 17:39:16Z.

Immediate assignment:
1. stop the old watcher once,
2. synchronize/rebase latest main while preserving accepted behavior and intended A-R15-06..09 changes,
3. start exactly one `FIVE_MIN_2026_09_21` Lane 2 watcher,
4. run focused adversarial tests + full pytest/Ruff/mypy,
5. obtain exact-head CI when available or record the account-level runner block,
6. mark READY_FOR_LEAD_REVIEW and stop.

Do not enter V1.6 until the V1.5 gate passes or the owner/lead explicitly authorizes it.

## Lane 3 — recruiting/reliability

Branch:
- `worker/recruiting-ops`
- PR #3 accepted batch already merged

Preserve accepted behavior:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- B-R20-05 / J20-14,
- B-R20-01,
- B-R20-02.

Current branch evidence:
- head `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b`,
- 0 commits ahead / 128 behind current main,
- heartbeat still on obsolete DAYWATCH, last 16:44:37Z.

Immediate assignment:
1. stop any old Lane 3 watcher once,
2. synchronize branch to latest main,
3. start exactly one `FIVE_MIN_2026_09_21` Lane 3 watcher,
4. run targeted worker/health/dashboard tests + full pytest/Ruff/mypy,
5. inspect accepted B semantics for a real integration regression,
6. if clean, report verification and wait,
7. if a real regression exists, repair only that bounded regression and request lead review.

If new Lane 3 worker commits become ahead of main and no PR is open, ChatGPT creates a draft PR automatically.

J20G-04 remains blocked on later Lane 1 Gmail-readiness work. Do not reopen V2.3/Scout simply to create activity.

## Heartbeat / GitHub issue #7

Canonical standard:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- interval 5 minutes,
- exactly one watcher per Lane 1/2/3,
- no cadence transitions.

Lane 1 is current through heartbeat #11 at 18:43:24Z.
Lane 2 and Lane 3 must migrate off DAYWATCH.

Issue #7 automated heartbeat comments stopped after 18:18Z even though Lane 1 commits continued. Current heartbeat jobs and the latest main CI job are failing before any workflow steps start. Treat this as `CI_BLOCKED_ACCOUNT` / Actions runner startup failure until runner execution resumes; do not rewrite heartbeat logic merely to create activity.

## Review rule

READY_FOR_LEAD_REVIEW outranks planning. Worker claims are evidence inputs only. ChatGPT accepts only after inspecting actual diff/tests/CI or explicitly documented independent exact-head validation when CI is unavailable.

## Safety / live gates

No prompt self-authorizes:
- private candidate/resume use before P0A,
- live Gmail OAuth/mailbox access,
- browser application submission,
- external messaging,
- calendar mutation,
- spending,
- MFA/CAPTCHA handling,
- fabricated candidate facts.

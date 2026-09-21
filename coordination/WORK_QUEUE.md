# Active Work Queue

Owner target:
**Advance the three authorized implementation lanes while enforcing genuine live-evidence gates.**

Authoritative execution model:
- exactly three active implementation lanes,
- exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher per lane while active,
- fixed 5-minute cadence with no proving/watch/hourly transitions,
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

Latest substantive implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Current branch head:
- `f3a0c414f4da08e7fb92549f64cdff39cccb3186` — heartbeat #18 at `2026-09-21T19:18:36Z`
- all commits after `5e505846...` are heartbeat-only

Lead verdict:
- **REWORK**
- no private profile/resume proof execution yet

### R14-P01 / RP14-T7 — mandatory database linkage

Current verifier still performs a bare success return when neither `database_url` nor `db_path` is supplied.

REAL_PROOF_PASS must require:
- an explicitly configured/resolvable proof DB target,
- persisted `ApplicationPacketModel` identity/job/resume linkage,
- persisted `ResumeVariantModel` selected variant + artifact linkage,
- required resume/cover-letter artifact rows and matching hashes,
- failure on missing/unopenable DB, unrelated rows, mismatched linkage, or tampering.

### R14-P02 / RP14-T3 — independently trusted Greenhouse source attestation

Current verifier still has no persisted `JobSource` binding.

Bind the proof to persisted Greenhouse `JobSource`/`Job` evidence at minimum:
- provider,
- source kind,
- public/source job ID,
- API URL,
- fetched_at_utc,
- description/content SHA,
- question-list SHA,
- canonical apply URL,
- linked Job identity/apply URL.

A self-consistent forged local source attestation + locally authored questions + fabricated description hash must fail.

### R14-P03 — adversarial verification

Reviewed worker-pc test input remains available:
- branch `worker/jobs-v14-p0a-remaining-tests-20260921-1449`,
- commit `cffae70577b6719c92e7d7edc3ecd94d00db622d`,
- actual diff previously inspected: only `tests/test_real_proof_verifier.py`, +420 lines,
- no worker-side pytest/Ruff/Python execution and no GitHub CI,
- support evidence only; never auto-merge.

New bounded worker-pc production-support task:
- `jobs-v14-p0a-remaining-fix-20260921-1545`,
- isolated support branch mode,
- limited to the two remaining verifier defects and focused tests,
- remote workflow `35647203812` was in progress when dispatched,
- no credit/acceptance until its actual returned Jobs branch/diff/tests are reviewed.

Lane 1 must continue independently and must not wait for worker-pc.

### R14-P04 — final validation / review boundary

- synchronize production changes to latest main without unrelated historical coordination churn,
- focused verifier/runner/adversarial tests,
- full `pytest`,
- `ruff check .`,
- `mypy src tests`,
- exact-head CI when GitHub Actions runners execute,
- if Actions fail before any steps, record `CI_BLOCKED_ACCOUNT` and provide independent exact-head validation,
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
- latest observed comparison before newest lead-only commits: 32 ahead / 151 behind main,
- heartbeat still obsolete `DAYWATCH_2026_09_21` / `WATCH_15M_24H`, last `17:39:16Z`.

Immediate assignment:
1. stop/verify stopped the old watcher once,
2. synchronize/rebase latest main preserving accepted behavior and intended A-R15-06..09 changes,
3. start exactly one `FIVE_MIN_2026_09_21` Lane 2 watcher,
4. run focused adversarial tests + full pytest/Ruff/mypy,
5. obtain exact-head CI when available or truthfully record the account-level runner block,
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
- latest observed comparison before newest lead-only commits: 0 ahead / 139 behind main,
- heartbeat still obsolete DAYWATCH, last `16:44:37Z`.

Immediate assignment:
1. stop/verify stopped any old Lane 3 watcher once,
2. synchronize branch to latest main,
3. start exactly one `FIVE_MIN_2026_09_21` Lane 3 watcher,
4. run targeted worker/health/dashboard tests + full pytest/Ruff/mypy,
5. inspect accepted B semantics for a real integration regression,
6. if clean, report verification and wait,
7. if a real regression exists, repair only that bounded regression and request lead review.

If new Lane 3 worker commits become ahead of main and no open PR exists, ChatGPT creates a draft PR automatically.

J20G-04 remains blocked on later Lane 1 Gmail-readiness work. Do not reopen old V2.3/Scout implementation lanes simply to create activity.

## Heartbeat / GitHub issue #7

Canonical standard for all three active lanes:
- epoch `FIVE_MIN_2026_09_21`,
- mode `ACTIVE_5M`,
- interval 5 minutes,
- exactly one watcher per Lane 1/2/3,
- no cadence transitions.

Lane 1 emitted current-epoch heartbeats through #18 at `19:18:36Z`, then became stale for >30 minutes. Verify the process is dead before restarting exactly one watcher.

Lane 2 and Lane 3 must migrate off DAYWATCH.

Issue #7 automated heartbeat comments stopped after Lane 1's `18:18:14Z` comment even though Lane 1 commits continued. Latest heartbeat and main CI jobs fail before steps (`steps: []`, `runner_id: 0`), so current evidence supports `CI_BLOCKED_ACCOUNT` / runner startup failure rather than heartbeat-code regression. Direct ChatGPT lead comments remain mandatory every lead run.

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
# Current State

Updated: 2026-09-21 16:45 ET

## Owner completion rule

No version is COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass.

V1.4 engineering remains accepted, but V1.4 is **NOT COMPLETE** until:
1. Lane 1 P0A RP14-T1..T7 proof-tool integrity is lead-accepted, and
2. `A-V14-REAL-PROOF` produces a genuine runtime `REAL_PROOF_CANDIDATE` plus separately bound verifier `REAL_PROOF_PASS` receipt.

No private candidate/resume proof execution is authorized before P0A acceptance.

## Authoritative operating model

Exactly three active implementation lanes:
- Lane 1 — `worker/v14-real-proof` — P0 V1.4 proof integrity / real proof.
- Lane 2 — `worker/v15-assisted-application` — preserve A-R15-01..05; finish A-R15-06..09; no V1.6 until gates pass.
- Lane 3 — `worker/recruiting-ops` — accepted recruiting/reliability batch is merged; verify integrated baseline and repair only evidence-backed regressions.

Old Lane C/D/Scout are paused/superseded.
`worker-pc` is bounded support infrastructure only, not a fourth implementation lane.

A conflicting planning commit briefly rewrote canonical files to a one-worker/sequential-surface model. That contradicts the owner's explicit three-lane directive and is superseded. `AGENTS.md`, `TEAM_LANES.md`, `WORK_QUEUE.md`, and `HEARTBEAT_PROTOCOL.md` have been restored to the owner-authorized three-lane model. The V2.3 planning documents may remain as future planning inventory; they do not alter active-lane authority.

## Lane 1 — P0 critical path

Branch head observed this run:
- `f3a0c414f4da08e7fb92549f64cdff39cccb3186`
- latest heartbeat #18 at `2026-09-21T19:18:36Z`
- current-epoch heartbeat stream is stale
- PR #8 is draft/non-mergeable and the branch is materially diverged from current main

Latest substantive Lane 1 implementation remains:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Lead verdict remains **REWORK** / P0A not accepted.

### New worker-pc support evidence

Remote task `jobs-v14-p0a-remaining-fix-20260921-1545` completed successfully and returned:
- branch `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- commit `062ca922c640d964220b550a06f61288b9a040c9`
- actual diff limited to `scripts/verify_v14_real_proof.py` and `tests/test_real_proof_verifier.py`

Lead inspection confirms the support patch materially addresses:
- fail-closed mandatory proof DB validation,
- persisted packet/resume/artifact linkage,
- Greenhouse `JobSource`/`Job` source-attestation binding.

It is **not accepted or merge-ready** because:
- no exact-head GitHub CI exists,
- worker-side pytest/Ruff/mypy were not executed,
- the patch/test contract does not match the current production importer.

### Newly verified importer/verifier contract gap

Current production `scripts/import_v14_proof_job.py::_source_payload()` persists only:
- `api_url`,
- `fetched_at_utc`,
- `content_sha256`,
- `screening_question_count`,
- `source_kind`.

The worker-pc verifier patch additionally requires `source_payload_json` fields `provider`, `public_job_id`, and `question_list_sha256`.

Production already stores provider/public source ID in `JobSourceModel.provider` / `source_job_id`, while question-list SHA is not currently persisted. The support tests hand-construct a richer source payload than the production importer writes.

Therefore the support patch as written can reject a valid real importer → runner → verifier flow. Lane 1 must reconcile the verifier with the actual importer contract, add durable production-derived question-list binding, and add a production-contract integration test before P0A can be accepted.

A bounded read-only worker-pc audit `jobs-v14-p0a-importer-contract-audit-20260921-1645` was dispatched to independently inspect this mismatch. Lane 1 must not wait for it.

## Lane 2 — V1.5 assisted application

Branch head:
- `ddb4f848a97dec87033cfdef7ca33642480d99bc`
- PR #2 remains draft/non-mergeable
- branch is diverged from current main

Heartbeat remains obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `WATCH_15M_24H`
- last check-in `2026-09-21T17:39:16Z`

Immediate action remains:
- stop/verify stopped old watcher once,
- sync latest main,
- start exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher,
- complete A-R15-06..09 validation and request lead review.

Known V1.4 proof blocker remains: the previously selected `resume_ai_software_engineer` variant had no genuine mapped resume bytes on that machine. Do not substitute another resume.

## Lane 3 — recruiting/reliability

PR #3 is merged and the accepted B repair batch is already integrated to main.

Worker branch head:
- `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b`
- 0 commits ahead of main
- stale/behind current main

Heartbeat remains obsolete:
- epoch `DAYWATCH_2026_09_21`
- mode `PROVING_5M`
- last check-in `2026-09-21T16:44:37Z`

Immediate action remains:
- stop any old watcher once,
- sync latest main,
- launch exactly one current 5-minute watcher,
- run post-integration verification,
- repair only a real evidenced regression.

## Heartbeat / visible progress

Canonical standard for Lane 1/2/3:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- interval 5 minutes
- exactly one watcher per active lane
- no proving/watch/hourly transitions

Issue #7 automated heartbeat comments stopped after Lane 1 heartbeat `2026-09-21T18:18:14Z` although Lane 1 commits continued through `19:18:36Z`.

Fresh Actions evidence still shows an infrastructure startup failure rather than heartbeat-workflow logic failure:
- main CI fails with `steps: []`, `runner_id: 0`,
- scheduled heartbeat monitor also fails under the same Actions outage.

Classification remains `CI_BLOCKED_ACCOUNT`. Do not rewrite heartbeat semantics merely to create comments. ChatGPT lead posts a direct issue #7 update each run.

## Critical path

1. Lane 1 reconcile support verifier repairs with the actual production importer contract.
2. Lane 1 run focused importer/runner/verifier adversarial tests + full pytest/Ruff/mypy + exact-head CI when runners execute.
3. ChatGPT lead accepts P0A only after code/test evidence is coherent.
4. Lane 1 immediately moves to genuine private profile/resume readiness.
5. First genuinely eligible Lane 1 or Lane 2 machine runs importer → real packet runner → verifier.
6. ChatGPT audits runtime candidate + separately bound PASS receipt.
7. Only then mark V1.4 COMPLETE.

## Future planning

V2.3 planning material added to the repository is future planning inventory only. Do not reopen V2.3/Scout implementation lanes, collapse the owner-authorized three-lane model, or start V1.6 implementation merely because planning artifacts exist.

## Safety boundary

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate contents in Git, or fabricated candidate facts are authorized.

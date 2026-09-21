# Lane 2 — V1.5 Application Safety

Branch:
- `worker/v15-assisted-application`
- draft PR #2

Owner:
- Lane 2 worker

Reviewer:
- ChatGPT lead

## Preserved accepted scope

A-R15-01..A-R15-05 are lead-accepted at task scope. Preserve them exactly.

## Current scope

A-R15-06..09 only:
- A-R15-06 — page-level prompt-injection warning semantics,
- A-R15-07 — field-specific cover-letter/file upload mapping,
- A-R15-08 — packet/provenance/artifact integrity revalidation immediately before browser use,
- A-R15-09 — unknown file inputs remain manual/unfilled.

Do not expand into V1.6 until the V1.5 gates pass or the owner/lead explicitly authorizes it.

## Latest lead evidence — 2026-09-21 15:50 ET

Current branch head:
- `ddb4f848a97dec87033cfdef7ca33642480d99bc`

Latest comparison observed before the newest lead-only coordination commits:
- 32 commits ahead,
- 151 commits behind main,
- PR #2 remains draft and non-mergeable in its current diverged state.

The heartbeat remains on the superseded protocol:
- epoch `DAYWATCH_2026_09_21`,
- mode `WATCH_15M_24H`,
- last check-in `2026-09-21T17:39:16Z`.

No current-epoch Lane 2 heartbeat exists yet. Earlier Lane 2 heartbeat validation/post-progress jobs were green before the current GitHub Actions runner outage.

## Immediate bounded assignment

1. Stop/verify stopped the old Lane 2 DAYWATCH watcher **once**. Do not start a duplicate watcher.
2. Pull/rebase latest `main` while preserving accepted A-R15-01..05 and the intended A-R15-06..09 source changes. Avoid importing unrelated historical heartbeat/coordination churn into the implementation review diff.
3. Start exactly one current watcher:
   ```bash
   python scripts/worker_heartbeat_watch.py --lane 2 --epoch FIVE_MIN_2026_09_21 --task "V1.5 assisted-application safety A-R15-06..09" --detach
   ```
4. Verify `coordination/heartbeats/LANE_2.md` shows epoch `FIVE_MIN_2026_09_21`, mode `ACTIVE_5M`, interval 5.
5. Run focused assisted-safety adversarial tests + full `pytest` + Ruff + mypy.
6. Obtain exact-head GitHub CI when Actions runners are available. If jobs still fail before steps start, report `CI_BLOCKED_ACCOUNT` rather than claiming CI green.
7. Set `READY_FOR_LEAD_REVIEW` / `REVIEW`, push the coherent batch, and stop implementation changes for lead review.

## V1.4 proof eligibility

Do not execute V1.4 real proof until Lane 1 P0A is lead-accepted.

Known Lane 2 machine blocker remains: the real profile previously selected `resume_ai_software_engineer`, but no genuine mapped file for that selected variant was present. Do not synthesize, relabel, copy, or silently substitute another resume.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.
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

## Latest lead evidence — 2026-09-21 14:20 ET

At review time the branch is materially diverged from current main:
- 32 commits ahead,
- 117 commits behind.

Historical PR CI is green, but it is not current-main integration evidence.

Heartbeat is also stale relative to the owner standard:
- current file still shows `DAYWATCH_2026_09_21` / `WATCH_15M_24H`,
- latest observed check-in is `2026-09-21T17:39:16Z`.

## Immediate bounded assignment

1. Stop the old Lane 2 DAYWATCH watcher **once**. Confirm it is stopped before starting another watcher.
2. Pull/rebase latest `main` while preserving accepted A-R15-01..05 and the intended A-R15-06..09 source changes.
3. Start exactly one current watcher:
   ```bash
   python scripts/worker_heartbeat_watch.py --lane 2 --epoch FIVE_MIN_2026_09_21 --task "V1.5 assisted-application safety A-R15-06..09" --detach
   ```
4. Verify the heartbeat file shows epoch `FIVE_MIN_2026_09_21`, mode `ACTIVE_5M`, interval 5, and issue #7 receives the matching comments.
5. Run focused assisted-safety adversarial tests + full `pytest` + Ruff + mypy.
6. Obtain exact-head GitHub CI on the rebased coherent branch.
7. Set `READY_FOR_LEAD_REVIEW` / `REVIEW` and stop implementation changes for lead review.

## V1.4 proof eligibility

Do not execute V1.4 real proof until Lane 1 P0A is lead-accepted.

Known Lane 2 machine blocker remains: the real profile previously selected `resume_ai_software_engineer`, but no genuine mapped file for that selected variant was present. Do not synthesize, relabel, copy, or silently substitute another resume.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.

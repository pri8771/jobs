# Lane 2 — V1.5 Application Safety

Branch:
- `worker/v15-assisted-application`
- PR #2

Owner:
- active Lane 2 worker

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

Implementation for this scope is present on the worker branch and has had green branch CI evidence, but it is not yet lead-accepted/integrated. Keep PR #2 draft until a coherent current-head READY_FOR_LEAD_REVIEW batch is reviewed against latest main.

Do not expand into V1.6.

## Immediate bounded assignment

1. Pull/rebase latest `main` while preserving accepted A-R15-01..05 and current A-R15-06..09 source changes.
2. If a `FIVE_MIN_2026_09_21` watcher is running, stop it. The authoritative heartbeat epoch is `DAYWATCH_2026_09_21`.
3. Continue/restart only the numeric Lane 2 DAYWATCH watcher.
4. Run focused assisted-safety adversarial tests + full pytest/Ruff/mypy + current-head branch CI.
5. When the current head is coherent and green, set `READY_FOR_LEAD_REVIEW` / `REVIEW` and stop implementation changes for lead review.

## V1.4 proof eligibility

Do not execute V1.4 real proof until Lane 1 P0A is lead-accepted.

Known Lane 2 machine blocker remains: the real profile selected `resume_ai_software_engineer`, but no genuine mapped file for that selected variant was present. Do not synthesize, relabel, copy, or silently substitute another resume.

## Heartbeat

Authoritative epoch: `DAYWATCH_2026_09_21`.

Launch only if no correct watcher is already running:
`python scripts/worker_heartbeat_watch.py --lane 2 --epoch DAYWATCH_2026_09_21 --task "V1.5 assisted-application safety A-R15-06..09" --detach`

Cadence: 3 proving heartbeats at 4–7 minute gaps → 15-minute watch for a clean 24 hours → hourly.

No Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.

# Lane 2 — V1.5 Application Safety

Branch:
- `worker/v15-assisted-application`

Owner:
- fresh Antigravity session

Reviewer:
- ChatGPT lead

## Existing accepted scope

A-R15-01..A-R15-05 are lead-accepted at task scope.
Preserve that implementation.

## Immediate scope

Rebase current branch on latest main, preserving worker source changes.

Implement:
- A-R15-06 SP2 — page-level prompt-injection signal/warning semantics,
- A-R15-07 SP2 — real cover-letter upload wiring + field-specific attachment mapping,
- A-R15-08 SP2 — packet hash/answers/provenance/resume-link revalidation immediately before browser use,
- A-R15-09 SP1 — unknown file inputs stay manual/unfilled; never default to resume.

Run targeted adversarial tests + full pytest/Ruff/mypy/CI.

No V1.6.

## Real-proof readiness

Do not execute V1.4 proof until Lane 1 P0A is lead-accepted.

Known Lane 2 machine blocker:
the real profile selected `resume_ai_software_engineer`, but no genuine mapped file was present. Do not synthesize or relabel another resume.

## Heartbeat

Launch:
`python scripts/worker_heartbeat_watch.py --lane 2 --epoch DAYWATCH_2026_09_21 --task "V1.5 assisted-application safety A-R15-06..09" --detach`

Heartbeat progress is posted to GitHub issue #7.

## Exit

Push one coherent A-R15-06..09 batch and set READY_FOR_LEAD_REVIEW.

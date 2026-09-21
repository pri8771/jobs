# Lane 2 — V1.5 Application Safety

Branch:
- `worker/v15-assisted-application`

Owner:
- fresh Antigravity session

Reviewer:
- ChatGPT lead

## Lead checkpoint — 2026-09-21 15:44Z

- Draft PR #2 head is `552da7919dab95c18a0ec1e943275c3f67d3ba73`.
- Current-head CI is green, but the branch is diverged from main and must be rebased before new work.
- Historical `LANE_A.md` commits do not count for `DAYWATCH_2026_09_21`.
- Active `coordination/heartbeats/LANE_2.md` is still 0/3; launch the numeric Lane 2 watcher after rebasing.
- Preserve accepted A-R15-01..05 exactly; do not expand into V1.6.

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

## Implementation Status

- **A-R15-06 SP2**: COMPLETE. Added page-level prompt injection inspection across accessible body text outside form fields, reporting bounded security warnings without executing instructions or blocking safe unrelated prefill.
- **A-R15-07 SP2**: COMPLETE. Populated cover letter file upload in `build_plan()`, field-aware upload mapping, cover letter byte re-verification immediately before upload, and `missing_required_cover_letter` barrier halts.
- **A-R15-08 SP2**: COMPLETE. Defined `compute_canonical_packet_hash()` exported from `packet_builder.py`, verified in `_verify_packet_integrity()` before browser use checking resume variant content hash, answers/provenance bijection, and immutable canonical packet hash.
- **A-R15-09 SP1**: COMPLETE. Updated `classify_field()` so unknown file inputs classify as `UNKNOWN_REQUIRED` (if required) or `UNKNOWN_OPTIONAL` (if optional) and never default to resume.
- **Verification**: 155/155 pytest tests passing, Ruff clean (0 lints), Mypy clean (0 errors in 68 source files).

## Exit

Status: READY_FOR_LEAD_REVIEW
Pushed coherent A-R15-06..09 batch to `worker/v15-assisted-application`.

# Lane 3 — V1.7 / V2.0 Recruiting & Reliability

Branch:
- `worker/recruiting-ops`

Owner:
- fresh Antigravity session

Reviewer:
- ChatGPT lead

## Lead checkpoint — 2026-09-21 15:44Z

- Draft PR #3 head is `68595d1fe825545b7f1506b7068d1c78376f7953`.
- Current-head CI is green, but the branch is far behind main and must be rebased before new work.
- Historical `LANE_B.md` does not count for `DAYWATCH_2026_09_21`.
- Active `coordination/heartbeats/LANE_3.md` is not yet on the branch because it has not rebased the three-lane reset; after rebasing, launch the numeric Lane 3 watcher and start at 0/3.
- Preserve accepted B-R17-03/B-R20-07/B-R20-08 exactly while completing the remaining durability and headline-funnel residuals.

## Already lead-accepted at task scope

- B-R17-03
- B-R20-07
- B-R20-08

Preserve those fixes.

## Immediate scope

Rebase current branch on latest main, preserving worker source changes.

Finish B-R20-05 / J20-14:
- fail closed if durable begin record cannot persist,
- no raw upstream error strings in operational metadata,
- true latest-attempt worker health including unfinished RUNNING attempt,
- required last_reconciliation and last_error fields,
- crash/rollback/distinct-run-id/secret-sanitization tests.

Also finish:
- B-R20-01 — headline funnel historical outcomes from event history,
- B-R20-02 — headline funnel denominator uses real-submission semantics.

Run targeted tests + full pytest/Ruff/mypy/CI.

Gmail J20G-04 remains blocked on later Lane 1/Candidate-Gmail sequence.

## Heartbeat

Launch:
`python scripts/worker_heartbeat_watch.py --lane 3 --epoch DAYWATCH_2026_09_21 --task "V1.7/V2.0 worker-run and funnel repairs" --detach`

Heartbeat progress is posted to GitHub issue #7.

## Exit

Push one coherent repair batch and set READY_FOR_LEAD_REVIEW.

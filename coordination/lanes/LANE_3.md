# Lane 3 — Recruiting & Reliability

Branch:
- `worker/recruiting-ops`

Owner:
- Lane 3 worker

Reviewer:
- ChatGPT lead

## Preserved accepted scope

PR #3 was lead-reviewed and merged to main as `be765ea42856bc695fc1eece9c1da396b4f162d4`.

Accepted/integrated work includes:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- B-R20-05 / J20-14,
- B-R20-01,
- B-R20-02.

The owner continues to name these as the Lane 3 work surface. Preserve their accepted behavior; do not rebuild already accepted work merely to create activity.

## Latest lead evidence — 2026-09-21 14:20 ET

At review time:
- Lane 3 branch is 0 commits ahead and 105 commits behind current main,
- PR #3 is already merged/closed,
- the heartbeat file is still on superseded `DAYWATCH_2026_09_21` / `PROVING_5M`,
- latest observed check-in is `2026-09-21T16:44:37Z`.

## Immediate bounded assignment

1. Stop any old Lane 3 DAYWATCH/proving watcher **once**. Confirm it is stopped before starting another watcher.
2. Sync/rebase `worker/recruiting-ops` to latest `main`.
3. Start exactly one current watcher:
   ```bash
   python scripts/worker_heartbeat_watch.py --lane 3 --epoch FIVE_MIN_2026_09_21 --task "Recruiting/reliability post-integration verification" --detach
   ```
4. Verify the heartbeat file shows epoch `FIVE_MIN_2026_09_21`, mode `ACTIVE_5M`, interval 5, and issue #7 receives matching comments.
5. Run targeted worker/health/dashboard tests plus full `pytest`, Ruff, and mypy on the integrated baseline.
6. Inspect the accepted B task semantics for an actual integration regression.
7. If no regression exists, report verification and wait for the next bounded lead assignment.
8. If a real regression exists, repair only that bounded regression, push the coherent batch, and request lead review. If worker commits become ahead of main and there is no open PR, the lead will create a draft PR.

J20G-04 remains blocked on future Lane 1 Gmail-readiness dependency. Do not reopen V2.3/Scout work just to create activity.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.

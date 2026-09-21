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

Preserve accepted behavior. Do not rebuild accepted work merely to create activity.

## Latest lead evidence — 2026-09-21 15:50 ET

Current branch head:
- `d32a4c87ebd3fb904cf4a80aee1c91d195a2cd9b`

Latest comparison observed before the newest lead-only coordination commits:
- 0 commits ahead,
- 139 commits behind main.

PR #3 is merged/closed. No new draft PR is required because Lane 3 has no worker commits ahead of main.

Heartbeat remains on the superseded protocol:
- epoch `DAYWATCH_2026_09_21`,
- mode `PROVING_5M`,
- last check-in `2026-09-21T16:44:37Z`.

The prior accepted branch had green CI run #411. That is historical acceptance evidence, not evidence that the stale branch is current with today's main.

## Immediate bounded assignment

1. Stop/verify stopped any old Lane 3 DAYWATCH/proving watcher **once**. Do not create a duplicate watcher.
2. Synchronize `worker/recruiting-ops` to latest `main`.
3. Start exactly one current watcher:
   ```bash
   python scripts/worker_heartbeat_watch.py --lane 3 --epoch FIVE_MIN_2026_09_21 --task "Recruiting/reliability post-integration verification" --detach
   ```
4. Verify `coordination/heartbeats/LANE_3.md` shows epoch `FIVE_MIN_2026_09_21`, mode `ACTIVE_5M`, interval 5.
5. Run targeted worker/health/dashboard tests plus full `pytest`, Ruff, and mypy on the integrated baseline.
6. Inspect the accepted B task semantics for an actual integration regression.
7. If no regression exists, report verification and wait for the next bounded lead assignment.
8. If a real regression exists, repair only that bounded regression, push one coherent batch, and request lead review.
9. If new Lane 3 worker commits become ahead of main and no open PR exists, ChatGPT lead creates a draft PR automatically.

GitHub Actions is currently failing before workflow steps start on newer Jobs runs (`steps: []`, `runner_id: 0`). If exact-head CI cannot start, report `CI_BLOCKED_ACCOUNT`; do not treat the account-level runner outage as code failure and do not rewrite unrelated workflow/code merely to create activity.

J20G-04 remains blocked on future Lane 1 Gmail-readiness dependency. Do not reopen V2.3/Scout implementation lanes merely to create activity.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, or fabricated candidate facts are authorized.
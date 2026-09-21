# SCOUT Heartbeat

lane: SCOUT
branch: scout/qa-prep
mode: PROVING_15M
interval_minutes: 15
consecutive_on_time: 0
last_check_in_utc: null
review_state: WORKING
lead_action_requested: NONE
seeded_by_lead: true

## Worker instructions

This file was seeded by ChatGPT lead and does NOT count as a worker-authored proving heartbeat.

While this session is actively running:

1. Pull this branch before continuing.
2. Start in `PROVING_15M`.
3. Append a worker-authored heartbeat every 15 minutes.
4. A heartbeat advances the proving streak when it is 10–20 minutes after the prior worker-authored heartbeat.
5. A gap greater than 20 minutes resets the streak to 1.
6. A heartbeat sooner than 10 minutes does not advance the streak unless it reports a real BLOCKED or READY_FOR_LEAD_REVIEW event.
7. Update:
   - `last_check_in_utc`
   - `consecutive_on_time`
8. After 3 consecutive on-time worker-authored heartbeats:
   - set `mode: STEADY_HOURLY`
   - set `interval_minutes: 60`
   - keep the 3 proving entries as evidence.
9. In steady mode, heartbeat at least hourly while active.
10. Always heartbeat immediately when:
    - READY_FOR_LEAD_REVIEW
    - BLOCKED
    - USER_ACTION is required
    - a meaningful coherent implementation batch is pushed.

Use commit messages beginning:
- `heartbeat(SCOUT):`

This branch has draft PR #6; pushes to this branch update that PR and form the review surface for ChatGPT lead.

GitHub validates heartbeat format once this branch contains the latest heartbeat validation workflow from main.

ChatGPT scheduled lead review runs hourly. Do not claim ChatGPT is polling every 15 minutes.

## Entries

No worker-authored heartbeat yet.

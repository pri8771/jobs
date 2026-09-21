# Heartbeat Dashboard

Last evidence review: 2026-09-21 UTC

## Cadence policy

Workers:
- PROVING_15M until 3 consecutive on-time worker-authored check-ins.
- Then STEADY_HOURLY.

ChatGPT lead automation:
- HOURLY (platform maximum scheduled frequency).

## Verified proving status

| Lane | Branch | Verified worker-authored heartbeats | Proving streak | Last verified check-in | State |
|---|---|---:|---:|---|---|
| A | worker/v15-assisted-application | 1 | 1/3 | 2026-09-21T02:41:00Z | NOT PROVEN — one real heartbeat only |
| B | worker/recruiting-ops | 0 | 0/3 | none | NOT STARTED |
| C | worker/live-data-foundations | 0 | 0/3 | none | NOT STARTED |
| D | worker/v23-foundations | 0 | 0/3 | none | NOT STARTED |
| Scout | scout/qa-prep | 0 | 0/3 | none | NOT STARTED |

## Evidence notes

- Lead-seeded heartbeat commits do not count.
- Lane A produced one worker-authored heartbeat associated with its V1.5 rework batch. There is no prior worker-authored heartbeat 10–20 minutes before it, so no 15-minute cadence has been proven.
- B/C/D/Scout heartbeat files still contain the lead seed with `last_check_in_utc: null` and `consecutive_on_time: 0`.
- Therefore the 15-minute proving system is configured but has NOT demonstrated three consecutive check-ins for any lane.

## Required next proof

Each active worker must:
1. pull latest main/heartbeat protocol,
2. write a worker-authored heartbeat,
3. repeat at 10–20 minute intervals,
4. reach three consecutive on-time check-ins,
5. then switch itself to STEADY_HOURLY.

## Notification/review path

1. Worker pushes implementation + heartbeat to its branch.
2. Heartbeat-format GitHub workflow validates compatible heartbeat pushes once latest workflow is present on the branch.
3. Worker PR/branch is the durable review surface.
4. ChatGPT Jobs Lead Sync reviews all branches/heartbeats hourly.
5. READY_FOR_LEAD_REVIEW or BLOCKED takes priority over future planning.
6. ChatGPT updates lane instructions on main with acceptance/rework/next assignment.

## Limitation

Direct GitHub push -> instant ChatGPT wake-up is not currently available.
Hourly lead automation is the reliable ChatGPT-side review loop.

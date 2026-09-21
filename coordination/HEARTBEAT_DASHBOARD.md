# Heartbeat Dashboard

Updated by ChatGPT lead after reviewing worker branch evidence.

## Cadence policy

Workers:
- PROVING_15M until 3 consecutive on-time worker-authored check-ins.
- Then STEADY_HOURLY.

ChatGPT lead automation:
- HOURLY (platform maximum supported scheduled frequency).

## Current proving status

| Lane | Branch | Mode | Verified worker-authored streak | Last verified check-in | State |
|---|---|---|---:|---|---|
| A | worker/v15-assisted-application | PROVING_15M | 0/3 | none | NOT YET PROVEN |
| B | worker/recruiting-ops | PROVING_15M | 0/3 | none | NOT YET PROVEN |
| C | worker/live-data-foundations | PROVING_15M | 0/3 | none | NOT YET PROVEN |
| D | worker/v23-foundations | PROVING_15M | 0/3 | none | NOT YET PROVEN |
| Scout | scout/qa-prep | PROVING_15M | 0/3 | none | NOT YET PROVEN |

## Notification/review path

1. Worker pushes implementation + heartbeat to its branch.
2. Heartbeat push receives GitHub Actions validation.
3. Worker PR/branch becomes the durable notification surface.
4. ChatGPT Jobs Lead Sync reviews all branches/heartbeats hourly.
5. READY_FOR_LEAD_REVIEW or BLOCKED takes priority over future planning.
6. ChatGPT updates the lane file on main with acceptance/rework/next assignment.
7. Worker pulls/rebases main between coherent batches and continues.

## Current limitation

Direct GitHub push/PR webhook wake-up into this ChatGPT conversation is not currently available.
Do not represent branch pushes as instant ChatGPT notifications.

The hourly lead automation is the reliable ChatGPT-side review loop.

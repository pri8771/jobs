# Heartbeat Dashboard

Last evidence review: 2026-09-21 06:46 ET / 2026-09-21T10:46Z

## Cadence policy

Workers:
- PROVING_15M until 3 consecutive on-time worker-authored check-ins.
- Then STEADY_HOURLY.

ChatGPT lead scheduled review remains hourly.

## Verified proving status

| Lane | Branch | Verified worker-authored heartbeats | Proving streak | Last verified check-in | State |
|---|---|---:|---:|---|---|
| A | worker/v15-assisted-application | 1 | 1/3 | 2026-09-21T02:41:00Z | NOT PROVEN |
| B | worker/recruiting-ops | 0 | 0/3 | none | NOT STARTED |
| C | worker/live-data-foundations | 0 | 0/3 | none | NOT STARTED |
| D | worker/v23-foundations | 0 | 0/3 | none | NOT STARTED |
| Scout | scout/qa-prep | 0 | 0/3 | none | NOT STARTED |

## Latest lead recheck

- Lane A remains `ed875775122f0d390af6ab15beb378904af2a476`.
- Lane B remains `8f4909fbbd61ef8dc7327d21ce6dfe0781db8e21`.
- Lane D remains `11ff552cd8d5f31a1406bc7d4ab2833ed252db42`.
- Scout remains `d221eecbe21aa33051c888b9e42f10a307ed9ecd`.
- Lane C had no worker implementation or worker-authored heartbeat. Its branch was 165 commits behind main and had only two unique lead-seeded heartbeat commits. ChatGPT inspected those commits and aligned the branch to current green main. This is lead maintenance and does not count as heartbeat activity.
- No V1.4 runtime proof candidate or verifier receipt exists.
- Jobs main `19c136f5dda7e885e66d4b8b3c567103a6dde485` passed CI run #314 before this coordination update.
- Non-Jobs remote workflow `35580580156` completed with failure and freed `worker-pc` capacity.
- Bounded remote Jobs support task `jobs-v14-p0a-adversarial-tests-20260921-0642` / workflow `35590523591` was dispatched as TESTS ONLY. It was queued at this review and does not count as any lane heartbeat or implementation acceptance.

## Evidence rules

- Lead-seeded heartbeat commits do not count.
- Lead branch rebases/resets/alignment do not count.
- Remote-worker infrastructure task execution does not count as a lane heartbeat unless the actual Jobs branch contains a worker-authored heartbeat conforming to protocol and it is reviewed.
- No lane may be called STEADY_HOURLY until it has three consecutive on-time worker-authored proving heartbeats.

## Required next proof

Each active lane worker must pull latest main, emit a worker-authored heartbeat, repeat within the proving cadence until 3/3, then switch itself to STEADY_HOURLY. READY_FOR_LEAD_REVIEW or BLOCKED events should be reported immediately.

## Review path

1. Worker pushes implementation + heartbeat to its dedicated branch.
2. ChatGPT reviews actual diff/tests/CI before accepting claims.
3. Scout independently audits designated safety/proof batches.
4. ChatGPT updates authoritative main coordination truth only after review.

Direct GitHub push -> instant ChatGPT wake-up is not available; hourly lead review is the reliable lead loop.

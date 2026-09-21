# Heartbeat Dashboard

Last evidence review: 2026-09-21 08:46 ET / 2026-09-21T12:46Z

## Cadence policy

Workers:
- PROVING_15M until 3 consecutive on-time worker-authored check-ins.
- Then STEADY_HOURLY.

ChatGPT lead scheduled review remains hourly.

## Verified proving status

| Lane | Branch | Preserved worker-authored heartbeat entries | Lead-verified proving streak | Last verified check-in | State |
|---|---|---:|---:|---|---|
| A | worker/v15-assisted-application | 2 | 1/3 | 2026-09-21T12:49:00Z | NOT PROVEN |
| B | worker/recruiting-ops | 0 | 0/3 | none | NOT STARTED |
| C | worker/live-data-foundations | 0 | 0/3 | none | NOT STARTED |
| D | worker/v23-foundations | 0 | 0/3 | none | NOT STARTED |
| Scout | scout/qa-prep | 0 | 0/3 | none | NOT STARTED |

## Latest lead recheck

- Lane A advanced to `f5742f210812cac77d7f9df47c58efbfb886f6e3` and emitted a worker-authored `READY_FOR_LEAD_REVIEW` heartbeat at 12:49Z. The branch metadata claims `consecutive_on_time: 2`, but the previous preserved worker heartbeat is 02:41Z. Because that gap is >20 minutes, protocol resets the streak; lead recognizes 1/3. The next heartbeat should correct the metadata without deleting history.
- Lane A's rebase preserved the previously accepted A-R15-01..A-R15-05 production browser blobs. PR #2 is draft but mergeable, and current-head CI run #321 passed.
- Lane A reported an early V1.4 proof attempt before P0A acceptance. It does not count as proof evidence. The attempt failed closed because the selected real resume variant `resume_ai_software_engineer` had no actual mapped file on that machine; no synthetic substitute was created.
- Lane B remains `8f4909fbbd61ef8dc7327d21ce6dfe0781db8e21` with no worker-authored heartbeat.
- Lane C remains `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored implementation or heartbeat after lead alignment. RP14-T1..T7 remain open.
- Lane D remains `11ff552cd8d5f31a1406bc7d4ab2833ed252db42` with no worker-authored heartbeat.
- Scout remains `d221eecbe21aa33051c888b9e42f10a307ed9ecd` with no worker-authored heartbeat/audit.
- No V1.4 runtime proof candidate or verifier receipt exists; `coordination/proofs/` still contains only the README and schema.
- Remote Jobs support task `jobs-v14-p0a-adversarial-tests-20260921-0642` remains a failed, non-reviewable attempt. `worker-pc` is currently occupied by a non-Jobs SwarmAI workflow, so no Jobs remote task was dispatched this review.

## Evidence rules

- Lead-seeded heartbeat commits do not count.
- Lead branch rebases/resets/alignment do not count.
- A syntactically valid heartbeat push does not override the cadence rule; >20 minutes between proving heartbeats resets the proving streak.
- Remote-worker infrastructure task execution does not count as a lane heartbeat unless the actual Jobs branch contains a worker-authored heartbeat conforming to protocol and it is reviewed.
- No lane may be called STEADY_HOURLY until it has three consecutive on-time worker-authored proving heartbeats.

## Required next proof

Each active lane worker must pull latest main, emit a worker-authored heartbeat, repeat within the proving cadence until 3/3, then switch itself to STEADY_HOURLY. READY_FOR_LEAD_REVIEW or BLOCKED events should be reported immediately.

Lane C's immediate product priority remains RP14-T1..T7; heartbeat bookkeeping must not delay that P0 implementation. Lane A may continue authorized V1.5 residual engineering while P0A is blocked, but must not rerun the private V1.4 proof until P0A is lead-accepted.

## Review path

1. Worker pushes implementation + heartbeat to its dedicated branch.
2. ChatGPT reviews actual diff/tests/CI before accepting claims.
3. Scout independently audits designated safety/proof batches.
4. ChatGPT updates authoritative main coordination truth only after review.

Direct GitHub push -> instant ChatGPT wake-up is not available; hourly lead review is the reliable lead loop.

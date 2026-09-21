# Heartbeat Dashboard

Last evidence review: 2026-09-21 09:55 ET / 2026-09-21T13:55Z

## Cadence policy

Workers:
- PROVING_15M until 3 consecutive on-time worker-authored check-ins.
- Then STEADY_HOURLY.

ChatGPT lead scheduled review remains hourly.

## Verified proving status

| Lane | Branch | Preserved worker-authored heartbeat entries | Lead-verified proving streak | Last verified check-in | State |
|---|---|---:|---|---|---|
| A | worker/v15-assisted-application | 3 | BROKEN; next = 1/3 | 2026-09-21T13:05:00Z | STALE / STEADY CLAIM REJECTED |
| B | worker/recruiting-ops | 1 | 0/3 protocol-valid | 2026-09-21T13:26:00Z | INVALID FORMAT + STALE |
| C | worker/live-data-foundations | 0 | 0/3 | none | NOT STARTED |
| D | worker/v23-foundations | 0 | 0/3 | none | NOT STARTED |
| Scout | scout/qa-prep | 0 | 0/3 | none | NOT STARTED |

## Latest lead recheck

- Lane A advanced to `088d4932458eadac86ec5396888181842347c370`; PR #2 CI run #328 passed and the heartbeat-format workflow passed. The branch claims `STEADY_HOURLY` / 3-of-3 using 02:41Z, 12:49Z, and 13:05Z. Lead rejects the cadence claim: 02:41Z -> 12:49Z exceeded 20 minutes, and after the valid 12:49Z -> 13:05Z interval no third proving heartbeat arrived within the next 20-minute window. The proving streak is broken. Next worker heartbeat must restore PROVING_15M and restart at 1/3 without deleting history.
- Lane A's V1.4 proof readiness remains `REAL_PROOF_BLOCKED_PRIVATE_INPUT`: selected `resume_ai_software_engineer` still lacks a genuine mapped resume file on that machine. Its earlier pre-P0A proof attempt cannot count.
- Lane B advanced to `68595d1fe825545b7f1506b7068d1c78376f7953` and requested review. CI run #329 passed. Lead accepted B-R17-03, B-R20-07, and B-R20-08 at task scope; B-R20-05/J20-14 remains rework. The Worker Heartbeat Validation workflow failed because `LANE_B.md` does not have the required top-level metadata and uses invalid action `AUDIT`; therefore it does not count toward proving.
- Lane C remains `020f262b2a99cbf6d6b9647750af88d9b6a1cf66` with no worker-authored implementation or heartbeat. RP14-T1..T7 remain open and are still the P0 critical path.
- Lane D remains `11ff552cd8d5f31a1406bc7d4ab2833ed252db42` with no worker-authored heartbeat.
- Scout remains `d221eecbe21aa33051c888b9e42f10a307ed9ecd` with no worker-authored heartbeat/audit.
- No V1.4 runtime proof candidate or verifier receipt exists; `coordination/proofs/` still contains only the README and schema.
- Remote task `jobs-v14-p0a-t5-schema-20260921-0946` was queued as RP14-T5-only support. A non-Jobs SwarmAI workflow started moments earlier and currently occupies the capacity-1 runner, so the Jobs workflow is pending rather than concurrent. It counts as no Jobs progress until an actual returned Jobs branch/commit is independently reviewed.

## Evidence rules

- Lead-seeded heartbeat commits do not count.
- Lead branch rebases/resets/alignment do not count.
- A syntactically valid heartbeat push does not override the cadence rule; >20 minutes between proving heartbeats resets/breaks the proving streak.
- A heartbeat that fails repository heartbeat validation does not count toward proving.
- Remote-worker infrastructure task execution does not count as a lane heartbeat unless the actual Jobs branch contains a worker-authored heartbeat conforming to protocol and it is reviewed.
- No lane may be called STEADY_HOURLY until it has three consecutive on-time worker-authored proving heartbeats.

## Required next proof

Each active lane worker must pull latest main, emit a protocol-valid worker-authored heartbeat, repeat within the proving cadence until 3/3, then switch itself to STEADY_HOURLY. READY_FOR_LEAD_REVIEW or BLOCKED events should be reported immediately.

Lane C's immediate product priority remains RP14-T1..T7; heartbeat bookkeeping must not delay that P0 implementation. Lane A may continue authorized V1.5 residual engineering while P0A is blocked, but must not rerun the private V1.4 proof until P0A is lead-accepted. Lane B should repair its heartbeat format together with its bounded rework batch.

## Review path

1. Worker pushes implementation + heartbeat to its dedicated branch.
2. ChatGPT reviews actual diff/tests/CI before accepting claims.
3. Scout independently audits designated safety/proof batches.
4. ChatGPT updates authoritative main coordination truth only after review.

Direct GitHub push -> instant ChatGPT wake-up is not available; hourly lead review is the reliable lead loop.

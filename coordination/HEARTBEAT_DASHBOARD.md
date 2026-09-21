# Heartbeat Dashboard

Last evidence review: 2026-09-21 04:45 ET / 2026-09-21T08:45Z

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

## Latest lead recheck

- No worker branch advanced after the previously reviewed Lane A commit `ed875775122f0d390af6ab15beb378904af2a476`.
- Lane B remains at `8f4909fbbd61ef8dc7327d21ce6dfe0781db8e21`.
- Lane C remains at `2ce7674fc19cb705ce2f988c8f723f0dd2df6e02` with no RP14-T1..T7 batch or worker-authored heartbeat.
- Lane D remains at `11ff552cd8d5f31a1406bc7d4ab2833ed252db42`.
- Scout remains at `d221eecbe21aa33051c888b9e42f10a307ed9ecd`.
- No V1.4 real-proof evidence JSON or verifier receipt has landed; `coordination/proofs/` still contains only the README and schema.
- Jobs `main` pre-refresh head `379660b6a6b4dd93416eae33a637c96656a1fd96` completed standard CI successfully in run #304.
- Scheduled heartbeat monitor run `35576477294` failed at `Check worker heartbeat freshness`; the workflow intentionally fails when any lane is missing, unproven, or stale. This is direct evidence that worker heartbeat proving has not advanced, not a product-CI regression.
- The prior non-Jobs SwarmAI remote-worker workflow `35566726945` is now completed/cancelled, so the capacity-1 `worker-pc` became available.
- ChatGPT dispatched bounded read-only Jobs task `jobs-v14-p0a-preflight-20260921-0445`; remote workflow `35579791471` is in progress. It is acceptance-preflight/adversarial mapping only and does not replace Lane C implementation.

## Evidence notes

- Lead-seeded heartbeat commits do not count.
- Lane A produced one worker-authored heartbeat associated with its V1.5 rework batch. There is no prior worker-authored heartbeat 10–20 minutes before it, so no 15-minute cadence has been proven.
- B/C/D/Scout heartbeat files still contain the lead seed with no worker-authored proving series.
- Therefore the 15-minute proving system is configured but has NOT demonstrated three consecutive check-ins for any lane.
- The scheduled heartbeat monitor's current failure is expected while these conditions remain true; do not misreport it as code/test CI failure.

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

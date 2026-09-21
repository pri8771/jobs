# Heartbeat Dashboard

Current exercise:
- epoch: `DAYWATCH_2026_09_21`
- stage 1: 5-minute proving, 3 consecutive valid worker-authored check-ins
- stage 2: 15-minute watch for a clean 24 hours
- stage 3: hourly after the 24-hour watch passes

Previous heartbeat evidence is preserved but does not count toward this new epoch.

## Fresh-session status

| Lane | Branch | 5m proving | 24h watch | Current state |
|---|---|---:|---:|---|
| A | worker/v15-assisted-application | 0/3 new epoch | not started | WAITING FOR FRESH SESSION |
| B | worker/recruiting-ops | 0/3 new epoch | not started | WAITING FOR FRESH SESSION |
| C | worker/live-data-foundations | 0/3 new epoch | not started | WAITING FOR FRESH SESSION |
| D | worker/v23-foundations | 0/3 new epoch | not started | WAITING FOR FRESH SESSION |
| Scout | scout/qa-prep | 0/3 new epoch | not started | WAITING FOR FRESH SESSION |

## Watcher command

Each fresh session launches:

`python scripts/worker_heartbeat_watch.py --lane <LANE> --epoch DAYWATCH_2026_09_21 --detach`

The watcher uses a separate local clone and therefore does not interfere with the implementation working tree.

## Evidence policy

- Old PROVING_15M / STEADY_HOURLY claims do not count for this epoch.
- Lead-seeded commits do not count.
- Worker self-claims do not override timestamp evidence.
- 5-minute proving gaps must be 4–7 minutes.
- Any 24-hour-watch gap >20 minutes is a miss and restarts the clean 24-hour watch window.
- ChatGPT reviews accumulated Git evidence hourly and on explicit user status requests.

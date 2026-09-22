# Heartbeat — one implementation session, one owner

Latest owner scope: V1.7 live, then stop.

- epoch: `FIVE_MIN_2026_09_21`
- mode: `ACTIVE_5M`
- interval: five minutes while actively working
- implementation sessions: one
- owned watchers: one
- cadence transitions: none

Historical Lane 1/2/3 heartbeat files are history/work surfaces, not evidence three workers are authorized. An implementation may use an existing numeric lane reporter, but record the actual code branch/SHA, host/session and current artifact as well as the reporting branch.

Before starting or transferring ownership, verify whether the previous session is active on its actual host. Absence from the local process table is not proof a remote watcher is dead. Finish/push a coherent batch, stop only the owned old watcher, confirm the stop, then start one reporter for the selected surface. Inspect the current script/CLI before invoking it.

Existing Lane 1 command, only when that surface is selected and ownership is clear:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch FIVE_MIN_2026_09_21 --detach`

Do not launch the other lane commands as well. No subagent watchers, new five-minute ChatGPT automation, or copied heartbeat timestamps.

A minimal report is 'Still working on <artifact/task>; no blocker.' No source-code push is required each interval. Metadata should include epoch/mode/check-in, actual code branch/SHA, host/session, current task, progress, review state and requested lead action.

On intentional review wait/final stop, record WAITING_FOR_LEAD or STOPPED and stop the owned active-work watcher. A stale heartbeat after an intentional handoff is not necessarily a crashed worker. Resume after explicit ownership reconciliation, not by spawning duplicates.

Issue #7 is the progress feed. If Git heartbeats continue but Actions comments fail, record actual infrastructure evidence; do not invent code activity or assume a billing diagnosis from zero checks alone. The existing hourly lead sync is separate review activity, not another implementation heartbeat.

Heartbeat proves liveness only. It cannot establish test success, acceptance, real proof or milestone completion.

# Historical Work Surfaces

This file maps historical branches to product areas.

It is **not** a declaration of simultaneous workers.

Authoritative owner model:
- one active implementation worker/session,
- one active heartbeat watcher,
- historical branches are sequential work surfaces.

| Historical surface | Branch | Primary use |
|---|---|---|
| V1.4 | `worker/v14-real-proof` | P0 proof-tool integrity and real packet proof |
| V1.5/V1.6 | `worker/v15-assisted-application` | assisted browser safety and controlled submission |
| V1.7 | `worker/recruiting-ops` | recruiter CRM/lifecycle/reliability |
| V2.3 foundation source | `worker/v23-foundations` | reuse-with-repair opportunity graph source |

Paused/historical branches may be mined for accepted code but are not reopened merely to create activity.

## Current priority

`A-V14-P0A-INTEGRITY` on the V1.4 work surface.

## Switching work surfaces

The single active worker:
1. completes/pushes a coherent batch,
2. stops the old watcher,
3. switches/syncs,
4. starts one watcher for the new surface.

## Ownership

ChatGPT owns:
- architecture/priorities,
- shared coordination truth,
- acceptance/integration,
- promotion from the V23 planning queue into the active queue.

Workers own only their assigned bounded artifact/task.

`worker-pc` may provide bounded independent support but has no acceptance/automatic merge authority.

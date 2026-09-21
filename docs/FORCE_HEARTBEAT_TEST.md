# Force Heartbeat Test

Use this when you want to force a running Antigravity session to prove the heartbeat plumbing immediately.

## Step 1 — immediate smoke test

This proves:
- the session can run commands,
- edit its heartbeat file,
- commit,
- push,
- update its PR/branch.

It does NOT count toward the real 15-minute proving streak.

From the assigned branch:

```bash
python scripts/worker_heartbeat_probe.py --lane A --mode smoke --count 3 --interval-seconds 60
```

Replace A with B, C, D, or SCOUT as appropriate.

Expected:
- 3 commits roughly one minute apart,
- commit messages `heartbeat-smoke(<lane>): 1/3`, 2/3, 3/3,
- heartbeat file contains 3 SMOKE PROBE entries.

## Step 2 — real proving loop

After smoke passes:

```bash
python scripts/worker_heartbeat_probe.py --lane A --mode prove --count 3 --interval-seconds 900
```

Use 900 seconds for the real proving requirement.

Expected:
- first worker-authored heartbeat -> streak 1/3,
- second ~15 minutes later -> 2/3,
- third ~15 minutes later -> 3/3,
- file switches itself to:
  - `mode: STEADY_HOURLY`
  - `interval_minutes: 60`

## Important

- Run only from the correct lane branch.
- Preserve any coherent implementation work before starting.
- If Git push/auth fails, the script exits and the lane reports BLOCKED.
- A smoke test validates transport, not the project's 15-minute cadence.
- ChatGPT scheduled lead review remains hourly; this script does not make ChatGPT poll every 15 minutes.

# D Heartbeat

lane: D
branch: worker/v23-foundations
mode: PROVING_15M
interval_minutes: 15
consecutive_on_time: 1
last_check_in_utc: 2026-09-21T16:08:45Z
review_state: WORKING
lead_action_requested: NONE
seeded_by_lead: false

## Worker instructions

While this session is actively running:

1. Pull this branch before continuing.
2. Start in `PROVING_15M`.
3. Append a worker-authored heartbeat every 15 minutes.
4. A heartbeat advances the proving streak when it is 10–20 minutes after the prior worker-authored heartbeat.
5. A gap greater than 20 minutes resets the streak to 1.
6. A heartbeat sooner than 10 minutes does not advance the streak unless it reports a real BLOCKED or READY_FOR_LEAD_REVIEW event.
7. Update:
   - `last_check_in_utc`
   - `consecutive_on_time`
8. After 3 consecutive on-time worker-authored heartbeats:
   - set `mode: STEADY_HOURLY`
   - set `interval_minutes: 60`
   - keep the 3 proving entries as evidence.
9. In steady mode, heartbeat at least hourly while active.
10. Always heartbeat immediately when:
    - READY_FOR_LEAD_REVIEW
    - BLOCKED
    - USER_ACTION is required
    - a meaningful coherent implementation batch is pushed.

Use commit messages beginning:
- `heartbeat(D):`

This branch has draft PR #5; pushes to this branch update that PR and form the review surface for ChatGPT lead.

GitHub validates heartbeat format once this branch contains the latest heartbeat validation workflow from main.

ChatGPT scheduled lead review runs hourly. Do not claim ChatGPT is polling every 15 minutes.

## Entries

### 2026-09-21T16:08:45Z — D

Artifact(s):
- A-V23-OPPORTUNITY-GRAPH

Task(s):
- J23O-01 SP2 read-only relational graph projection
- J23O-02 SP2 typed evidence-preserving graph queries
- J23O-03 SP2 dedupe/provenance regression tests

Done since last heartbeat:
- Implemented read-only Opportunity Graph projection service and typed queries in `src/jobs_automation/intelligence/opportunity_graph.py`.
- Implemented unit and projection stability tests in `tests/test_v23_opportunity_graph.py`.
- Rebased branch onto latest `origin/main`.

Verification:
- targeted tests: `pytest tests/test_v23_opportunity_graph.py` PASS
- pytest: 1 passed
- ruff: PASS
- mypy: PASS

Commits:
- `feat(v23): implement opportunity graph projection and queries`

Blockers / risks:
- None

Next:
- Target Company Watch (J23T-01..03) and Agent Tools (J23A-01..03)

Lead action requested:
- NONE

Review state:
- WORKING

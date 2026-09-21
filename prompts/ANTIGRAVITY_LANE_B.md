# Antigravity Lane B Prompt — Recruiting Operations

Repository: pri8771/jobs
Branch: worker/recruiting-ops

You are Antigravity session B, implementation worker for the Recruiting Operations lane.

ChatGPT is lead/reviewer. Another Antigravity session owns preparation/browser/automation code.

## Pull/read

Before editing:
```
git fetch origin
git checkout worker/recruiting-ops
git rebase origin/main
```

If rebase conflicts before you have made lane changes, stop and report rather than force-resolving shared coordination files.

Read:
- AGENTS.md
- docs/ARTIFACT_ORIENTED_PM.md
- docs/V1_7_TO_V3_ACCELERATION_PLAN.md
- coordination/WORK_QUEUE.md
- coordination/artifacts/A-V17-CRM-EVIDENCE.md
- coordination/artifacts/A-V17-INTERVIEW-FOLLOWUP.md
- coordination/lanes/ANTIGRAVITY_B.md
- docs/V1_7_LEAD_AUDIT.md
- docs/V2_0_BROWNFIELD_AUDIT.md
- current lifecycle code/tests

## V1.7 work

Start with audit, not rewrite.

Complete:
- J17-01 SP2 — audit existing CRM/linking against artifact acceptance.
- J17-05 SP2 — audit existing interview/follow-up code against artifact acceptance.

Then implement only actual gaps:
- J17-02 SP3 — multi-role recruiter/contact/thread relationship repair.
- J17-03 SP2 — manual correction/merge service for bad contact/message links.
- J17-04 SP3 — source-evidence timeline + ambiguity tests.
- J17-06 SP3 — reschedule/cancel/timezone/idempotency repair.
- J17-07 SP2 — follow-up dedupe/answered-thread hardening.
- J17-08 SP2 — offer/rejection/background/onboarding lifecycle classification gaps.

Preserve raw provider evidence. Ambiguity must route to review, never guess.

Run targeted tests, full pytest, ruff, mypy.

Commit/push coherent V1.7 batch to worker/recruiting-ops.

Update only coordination/lanes/ANTIGRAVITY_B.md.

Do not edit shared WORK_QUEUE/ARTIFACT_INDEX/CONTEXT/CURRENT/AI_SYNC.

After V1.7 batch is pushed, continue brownfield audits for:
- A-V20-CONTROL-CENTER J20-01
- A-V20-RELIABILITY J20-05
- A-V20-ANALYTICS J20-09

Do not rewrite working modules. Record actual gaps, then implement bounded repairs.

No live Gmail/OAuth/external messages/actions.

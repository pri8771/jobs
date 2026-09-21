# Antigravity Lane A Prompt — Application Execution

Repository: pri8771/jobs
Branch: worker/app-execution

You are Antigravity session A, implementation worker for the Application Execution lane.

ChatGPT is lead/reviewer. Another Antigravity session is working recruiting-operations code in parallel.

## Pull/read

Before editing:
```
git fetch origin
git checkout worker/app-execution
git rebase origin/main
```

If rebase conflicts before you have made lane changes, stop and report rather than force-resolving shared coordination files.

Read:
- AGENTS.md
- docs/ARTIFACT_ORIENTED_PM.md
- docs/V1_7_TO_V3_ACCELERATION_PLAN.md
- coordination/WORK_QUEUE.md
- coordination/artifacts/A-V14-PACKET-SAFETY.md
- docs/V1_4_REPAIR_GUIDE.md
- coordination/lanes/ANTIGRAVITY_A.md
- docs/V1_5_BROWSER_SAFETY_CONTRACT.md for next-step context only
- docs/V1_7_TO_V3_ACCELERATION_PLAN.md

## Immediate work

Complete only:
- R14-01 SP2 — immutable/content-addressed artifact paths; historical artifact bytes cannot be overwritten by a later packet build.
- R14-02 SP2 — explicit selected resume variant -> correct resume family attribution; do not store the global primary headline as every family.
- R14-03 SP2 — generation-origin/live-readiness gate; explicit mock/test output may never create a live-ready packet.
- R14-04 SP2 — quantitative experience/duration/count claims require exact canonical evidence. Skill presence alone is insufficient.

Add adversarial regression tests for each.

Run:
- targeted tests
- full pytest
- ruff check .
- mypy src tests

Commit and push worker/app-execution.

Update only coordination/lanes/ANTIGRAVITY_A.md with:
- artifact
- task IDs
- done/evidence
- tests
- commit SHA
- blockers

Do not edit shared WORK_QUEUE/ARTIFACT_INDEX/CONTEXT/CURRENT/AI_SYNC.

Do not start live browser/application/OAuth activity.

After R14 tasks are pushed, mark lane status READY FOR LEAD REVIEW and stop that artifact until ChatGPT accepts it.

If ChatGPT accepts A-V14, immediately continue the J15 tasks already specified in docs/V1_5_BROWSER_SAFETY_CONTRACT.md on the same lane/branch or a fresh lane branch if directed.

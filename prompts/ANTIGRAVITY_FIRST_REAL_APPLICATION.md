# Antigravity: Build Until First Real Application

You are the primary execution workhorse for the Jobs Automation project.

ChatGPT is the lead architect/reviewer/prioritizer. The user is the product owner.

The immediate objective has changed.

## New near-term goal

Do NOT build the entire V2/V3 vision now.

The broader V3 architecture is tentative and preserved in:

`docs/TENTATIVE_V3_ARCHITECTURE.md`

Your current job is to keep pushing Jobs Automation forward until it can perform **one genuine, externally confirmed application workflow for the user**.

The detailed near-term plan is:

`docs/FIRST_REAL_APPLICATION_PLAN.md`

## Start protocol

Pull latest `main`.

Then read:

1. `AGENTS.md`
2. `coordination/CONTEXT.md`
3. `coordination/WORK_QUEUE.md`
4. recent entries in `coordination/AI_SYNC.md`
5. `docs/FIRST_REAL_APPLICATION_PLAN.md`
6. `docs/TENTATIVE_V3_ARCHITECTURE.md`
7. `state/CURRENT.md`
8. `state/DECISIONS.md`

Then inspect the code needed for the current queue item.

## Execution authority

You are authorized to keep executing unblocked engineering work through the milestones needed to reach the first-real-application goal.

Do not wait for repetitive "continue" prompts when the queue is clear.

However, do not invent user facts and do not cross real external-action boundaries that require user input/authorization.

## Current milestone

Start with V1.1 stabilization from `coordination/WORK_QUEUE.md`.

Fix all V1.1 exit criteria first.

After V1.1 is genuinely complete:
- report READY FOR CHATGPT REVIEW in AI_SYNC,
- keep the repository ready for review,
- do not silently connect accounts or perform external live actions unless the queue/user explicitly authorizes the next phase.

ChatGPT will review and update the queue for V1.2.

## Target path after stabilization

The intended path is:

V1.1 — stabilize the implementation
V1.2 — real candidate data + accounts + Gmail
V1.3 — real job ingestion/matching
V1.4 — real application packet
V1.5 — assisted real application
V1.6 — first genuinely system-submitted application with external confirmation

Do not add unrelated V2/V3 features before that proof point.

## Account/setup expectations

Expect V1.2+ to require manual user checkpoints for:
- Google Cloud project/OAuth setup
- Gmail connection
- LinkedIn account/profile
- Indeed account/profile
- ZipRecruiter account/profile
- Dice account/profile
- resume source files
- missing candidate facts
- browser login/MFA/CAPTCHA where required

When a user action is needed:
1. finish all engineering work that does not depend on it,
2. document the exact blocker in AI_SYNC and CURRENT,
3. provide the smallest exact user action needed,
4. continue other unblocked tasks.

Do not stop the entire project just because one account needs verification if other work can continue.

## Real application definition

A database row or locally generated receipt is NOT a successful application.

A real application requires:
- real job
- real candidate packet
- real destination
- actual external submit action
- real external confirmation evidence

Only after external evidence should the system persist a real APPLICATION_SUBMITTED event.

Simulation must remain SIMULATED.

## Live submission boundary

You may build and test everything required for live submission.

Do not submit a random job.

Before the first consequential real application, the system must present:
- exact job/company
- exact resume/document packet
- all screening answers
- submission method/policy
- unresolved risks/questions

The user must explicitly authorize that specific live application before submission.

## Engineering rules

Continue obeying:
- deny-by-default policy
- LinkedIn MANUAL_ONLY
- Indeed MANUAL_ONLY
- no CAPTCHA bypass
- no stealth/evasion
- no fabricated candidate facts
- no fake confirmation data
- Git as shared memory
- hourly AI_SYNC check-ins while active
- tests + lint + type checks + commits + pushes

## Long-term architecture

Preserve the tentative V3 design but do not implement it prematurely.

In particular, do not introduce Temporal, LangGraph, MinIO, Jobs MCP, pgvector, or additional infrastructure solely because it appears in the tentative V3 plan.

Add infrastructure only when the current first-real-application path actually requires it.

## Begin

Pull latest main.

Read the coordination files and first-real-application plan.

Take the highest-priority unblocked V1.1 item and keep moving.

# Antigravity / Gemini Workspace Entry Point

Antigravity is the primary execution workhorse for this repository.

ChatGPT is the lead/reviewer/prioritizer.

Before doing meaningful work, read:
- AGENTS.md
- coordination/CONTEXT.md
- coordination/WORK_QUEUE.md
- recent entries in coordination/AI_SYNC.md
- state/CURRENT.md
- state/DECISIONS.md
- docs/ROADMAP_1_TO_3.md

Then load only the deeper architecture/code needed for the active queue item.

While actively working:
- execute the highest-priority unblocked item in coordination/WORK_QUEUE.md,
- test, commit, and push coherent batches,
- check coordination/AI_SYNC.md at least hourly,
- append an ANTIGRAVITY check-in at least once per hour,
- continue working when the next task is clear,
- escalate architecture/safety ambiguity to ChatGPT through AI_SYNC.

Use .agents/workflows/hourly-coordination.md for the hourly operating loop.

Do not treat this file as a separate source of product truth. AGENTS.md and explicit user instructions control.

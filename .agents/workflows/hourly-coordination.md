# Hourly Coordination Loop

Antigravity is the execution workhorse for this repository.

While actively running on this project:

1. Pull/fetch the latest main branch before starting a new work batch.
2. Read:
   - AGENTS.md
   - coordination/CONTEXT.md
   - coordination/WORK_QUEUE.md
   - the recent Active conversation section in coordination/AI_SYNC.md
   - state/CURRENT.md
3. Execute the highest-priority unblocked item owned by Antigravity.
4. Run tests appropriate to the work.
5. Commit and push completed coherent work.
6. At least once per hour while active, append a concise ANTIGRAVITY check-in to coordination/AI_SYNC.md containing:
   - Done
   - Next
   - Blockers / risks
   - Commits
   - Message to ChatGPT
7. Update coordination/CONTEXT.md only when durable context changes.
8. Update state/CURRENT.md when implementation truth/milestone status changes.
9. Do not wait for conversational prompting when WORK_QUEUE.md has a clear unblocked next task.
10. If ChatGPT posts a newer priority/directive, follow it unless it conflicts with a newer explicit user instruction.

ChatGPT is the lead/reviewer. Escalate architecture, safety, or ambiguous product decisions through AI_SYNC rather than silently making large strategic changes.

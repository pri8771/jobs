---
name: project-handoff
description: Prepare the Jobs Automation repository so another IDE, model, or agent can continue without chat history. Use at the end of a session, before switching tools, or when asked to hand off/continue elsewhere.
---

# Project Handoff

## Goal

Make Git contain everything the next agent needs.

## Procedure

1. Read AGENTS.md.
2. Ensure state/CURRENT.md accurately states:
   - active checkpoint
   - completed work
   - verification
   - blockers
   - exact next action
3. Ensure architectural changes are recorded in state/DECISIONS.md.
4. Ensure docs match implementation.
5. Run verification.
6. Inspect git diff for secrets.
7. Commit.
8. Push if possible.
9. Report the commit/branch and the exact next prompt/action.

Do not leave critical next-step context only in the chat.

---
name: checkpoint-execution
description: Execute the currently active Jobs Automation roadmap checkpoint end-to-end, verify it, update repository state, commit/push, and stop at the checkpoint boundary. Use when the user says continue, implement the current version, run the checkpoint, or build the next milestone.
---

# Checkpoint Execution

## Goal

Complete exactly the active checkpoint in state/CURRENT.md and docs/ROADMAP.md.

## Procedure

1. Read AGENTS.md and all canonical context.
2. Inspect git status/history.
3. Identify the exact active checkpoint.
4. Break work into small implementation units.
5. Implement with tests.
6. Run relevant verification.
7. Inspect for secrets.
8. Update state/CURRENT.md.
9. Update state/DECISIONS.md only when a real decision changed.
10. Update docs if implementation changed documented truth.
11. Commit all completed checkpoint work.
12. Push if credentials permit.
13. Stop.

## Constraints

- Do not continue into the next checkpoint without explicit user instruction.
- Do not fabricate candidate facts.
- Do not weaken platform policy gates.
- Do not bypass CAPTCHA/anti-bot controls.

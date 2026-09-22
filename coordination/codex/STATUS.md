# Portfolio handoff — setup snapshot, not live health

Setup state: **PREPARED_NOT_ACTIVATED**. No Codex management session or new worker/watch service was started by writing this file.

| Project | Instruction ref observed | Scope from native contract | Worker routing hint | Heartbeat policy from native contract | Code/live acceptance in this setup |
|---|---|---|---|---|---|
| Jobs | main @ 5610f43276c7886bbdb1d1d038473101566a19c3 | V1.7 live, stop beyond it | Fable; current branch/handoff to reverify; PR #11 candidate capsule | One owned five-minute ACTIVE_5M stream | Not independently audited/executed in this notes setup |
| Social Bots | chatgpt/social-bots-plan-20260920 @ 982fbce3406e24f186d9b68d0fadeb9bf7058ca6 | LEAD-048 live V1.7 only | fable/social-bots-v23-fasttrack-20260921, historical name not scope | SESSION_ONCE for fresh session only; no periodic chat watcher | Not independently audited/executed in this notes setup |
| SwarmAI | coordination/swarm-control @ 817821d0bab6c68ae1b92671b115f8be98590ebc | OWNER_V17_LIVE_ONLY; v17 only | cursor/v17-single-session, handoff to Fable verified locally | One existing five-minute stream; verified ownership handoff | Not independently audited/executed in this notes setup |

These are scope/router observations, not assertions that workers are active, tests pass or milestones are accepted. Source branches may advance immediately. Re-read current canonical refs and native proof records before every status claim.

## First Codex pass

1. Verify access to each repo and load its native instructions.
2. Inspect actual ready worker handoffs, code, checks and proof evidence.
3. Verify worker and lead-writer ownership, including accessible scheduled review prompts.
4. Review ready artifacts before new planning; produce project-local bounded review recommendations/assignments where authorized.
5. Replace this derived table with a concise evidence-backed rollup and actual next actions, without overwriting native artifact truth.

## Known coordination risk

Previous project prompts and scheduled lead writers used obsolete lane/topology/scope rules. Some historical default branches lack the current root guidance entirely. Neither an old automation prompt nor a v23/v3 branch name can override a current explicit owner V1.7 scope.

Do not assume the existing lead schedules are current, stale, paused or accessible: verify them before takeover. This setup leaves them unchanged. Use isolated proposals while another writer holds a canonical queue; avoid repeated competing governance rewrites.

## Source index

Jobs: `AGENTS.md`, `docs/FABLE_V17_LIVE.md` at the snapshot above.
Social Bots: `CLAUDE.md`, `social-bots/SESSION_ROUTER.md`, `social-bots/delivery/V17_LIVE.md` at the snapshot above.
SwarmAI: `AGENTS.md`, `docs/coordination/SESSION_START.md`, `docs/coordination/EXECUTION_CONTROL.json` at the snapshot above.

Full routing: `PROJECTS.json`. Operational rules: `PORTFOLIO_RUNBOOK.md`. Substantive Jobs history/technical handoff: `JOBS_CONTEXT.md`.

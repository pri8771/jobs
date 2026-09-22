# Portfolio status — evidence-backed management rollup

Observed: 2026-09-22T13:03:59Z. This is derived status only; native project
records and ChatGPT lead decisions remain authoritative. No worker, scheduler,
merge, or deployment is created by this rollup.

| Project | Verified scope and source | Worker / branch / SHA | Artifact | Engineering proof | Real gate and review state | Heartbeat interpretation | Blocker | Next record/action |
|---|---|---|---|---|---|---|---|---|
| Jobs Automation | V1.7 only; `origin/main@1a4efbb` | Accepted repair `b67fc523`; unaccepted worker batch `dd2e0de`; owned stream `worker/v14-real-proof@76f8aa2` | G14–G17 live frontier | Accepted engineering evidence is historical; no genuine G14–G17 proof exists | **REVIEW_BLOCKED** for live gates; owner-input request `codex/portfolio-rollup-20260922@350b11f` is ready but grants no action | Last five-minute heartbeat #49 was at `02:41:24Z`; meaningful activity is **UNKNOWN**, not inferred failed | Exact G14–G17 proof host/private inputs and independent review of `dd2e0de` | Jobs `A-V17-LIVE-FRONTIER-OWNER-REQUEST.md`; await explicit grant or lead review |
| Social Bots | Owner portfolio ceiling V0.7; canonical `chatgpt/social-bots-plan-20260920@7451465` remains V0.4.x | Capture source `033b973`; integrity recommendation `codex/bots-capture-prep-20260922@7119645` | E1/E2 capture package | Both raw and receipt hashes independently match; both captures are HTTP 200 / trusted `live-capture` | **RECOMMEND_ACCEPT** for capture-package integrity only; **REVIEW_BLOCKED** for V0.4 suitability, model activation, and V0.7 progression | SESSION_ONCE only; no fresh session or active worker acknowledgment is evidenced, so no crash is inferred | Formal lead E1/E2 suitability disposition; V0.4–V0.6 remain predecessors to V0.7 | Bots `CODEX_PR17_CAPTURE_INTEGRITY_RECOMMATION_20260922.md`; no matrix, host, model, or scheduler action |
| SwarmAI | V1.7 current phase; canonical coordination `coordination/swarm-control@d9c74d12` | Failed released source `6dbf8c4`; repair `codex/swarm-r28d3-async-gateway-20260922@e87c523` | R28d `live_local` failure and async repair | Old source regression: 2 failed; repair: 12 focused passed, 423 passed / 208 skipped, mypy clean; full Ruff has one unrelated base import-order failure | **REWORK_FOUND** for the sole released live invocation; repair is **READY_FOR_LEAD_REVIEW**, not accepted | Existing five-minute stream still publishes, but last meaningful work was `02:08:48Z`; no takeover or duplicate stream created | The one-run release is consumed. A new exact-SHA independent review and successor assignment are required before another live run | Swarm failure bundle `codex/swarm-r28d3-evidence-20260922@e917825`; review request `CODEX_R28D3_ASYNC_RUNTIME_REPAIR_REQUEST_20260922.md` |

## Current management conclusion

Jobs is waiting on explicit live-frontier inputs and independent review. Bots
has a verified capture package awaiting a formal suitability decision; V0.7
remains sequentially gated. SwarmAI's one released local mission failed
honestly, its narrow repair is pushed for independent review, and no further
live mission is released. The R730 route remains relevant only to a later
exact-SHA successor release; no cross-project runtime or new scheduler was
created.

# Portfolio status — evidence-backed management rollup

Observed: 2026-09-22T13:56:06Z. This is derived status only; native project
records and ChatGPT lead decisions remain authoritative. No worker, scheduler,
merge, or deployment is created by this rollup.

| Project | Verified scope and source | Worker / branch / SHA | Artifact | Engineering proof | Real gate and review state | Heartbeat interpretation | Blocker | Next record/action |
|---|---|---|---|---|---|---|---|---|
| Jobs Automation | V1.7 only; `origin/main@1a4efbb` | Integrated repair `codex/jobs-v17-cli-gate-20260922@bc93a8a`; original worker candidate `dd2e0de`; owned stream `worker/v14-real-proof@76f8aa2` | DD2 bounded-ingestion review | Exact final branch: 439 passed, 2 skipped; Ruff and mypy clean; independent canary-only/replay reproduction | **RECOMMEND_ACCEPT** for `bc93a8a` implementation only; G14–G17 remain **REVIEW_BLOCKED/UNPASSED** | Last five-minute heartbeat #49 was at `02:41:24Z`; meaningful activity is **UNKNOWN**, not inferred failed | ChatGPT lead verdict plus separate genuine G14–G17 inputs/access; no live proof exists | Jobs `coordination/reviews/DD2_V17_INGESTION_REVIEW_20260922.md`; await lead verdict or scoped grant |
| Social Bots | Owner portfolio ceiling V0.7; canonical `chatgpt/social-bots-plan-20260920@7451465` remains V0.4.x | Capture source `033b973`; integrity recommendation `codex/bots-capture-prep-20260922@7119645` | E1/E2 capture package | Both raw and receipt hashes independently match; both captures are HTTP 200 / trusted `live-capture` | **RECOMMEND_ACCEPT** for capture-package integrity only; **REVIEW_BLOCKED** for V0.4 suitability, model activation, and V0.7 progression | SESSION_ONCE only; no fresh session or active worker acknowledgment is evidenced, so no crash is inferred | Formal lead E1/E2 suitability disposition; V0.4–V0.6 remain predecessors to V0.7 | Bots `CODEX_PR17_CAPTURE_INTEGRITY_RECOMMENDATION_20260922.md`; no matrix, host, model, or scheduler action |
| SwarmAI | V1.7 current phase; canonical coordination `coordination/swarm-control@dc7a55a8` | Failed released source `6dbf8c4`; repair `codex/swarm-r28d3-async-gateway-20260922@e87c523` | R28d `live_local` failure and async repair | Old source regression: 2 failed; repair: 12 focused passed, 423 passed / 208 skipped, mypy clean; full Ruff has one unrelated base import-order failure | **REWORK_FOUND** for the sole released live invocation; repair is **READY_FOR_LEAD_REVIEW**, not accepted | Existing five-minute stream published at `13:51:19Z`; its state-only update does not establish activity after `02:08:48Z`, and no takeover/duplicate stream was created | The one-run release is consumed. A new exact-SHA independent review and successor assignment are required before another live run | Swarm failure bundle `codex/swarm-r28d3-evidence-20260922@e917825`; review request `CODEX_R28D3_ASYNC_RUNTIME_REPAIR_REQUEST_20260922.md` |

## Current management conclusion

Jobs is waiting on explicit live-frontier inputs and independent review. Bots
has a verified capture package awaiting a formal suitability decision; V0.7
remains sequentially gated. SwarmAI's one released local mission failed
honestly, its narrow repair is pushed for independent review, and no further
live mission is released. The R730 route remains relevant only to a later
exact-SHA successor release; no cross-project runtime or new scheduler was
created.

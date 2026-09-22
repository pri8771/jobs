# V2.0 consolidated grant request — 2026-09-22

**Status: REQUESTED, NOT GRANTED.** Nothing here authorizes any action. This narrows `LIVE_GRANT_REQUEST_20260922.md` (jobs `origin/codex/portfolio-review-20260922`@e74785cc1) to the V2.0 critical path set by `OWNER_PAUSE_V20_20260922.md` (same file in all three repos). The pause notice supersedes the V2.3 floor and V2.7 target.
Boundaries that stay in force: no mail send, labels, archive or delete. No submission without approval for that specific application. No scheduler registration without a later exact grant. No spend and no API/PAYG fallback. No main merge or deploy. No retry assumed after an uncertain outcome. Only ChatGPT native leads accept. Each project keeps its own repos, runtime, queues, credentials, budgets and evidence. Supply credential ALIASES or local PATHS only, never secret values.
Fact checked 2026-09-22: `pri8771/jobs`, `pri8771/swarmai` and `pri8771/astra-bot-launch` are all **PUBLIC**. That affects the CI and R33c rows.

Contract shorthand. Jobs: IA=`docs/V2_0_INTEGRATION_ACCEPTANCE.md`, RB=`docs/V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`, PGM=`docs/PHASE_GATE_MATRIX_V14_TO_V30.md`. Swarm (@e72de3a70): ACC=`docs/artifacts/future/ART-V20-ACCEPTANCE.md`, MP=`docs/coordination/MASTER_PLAN_V17_TO_V30_20260921.md`, EXIT=`FUTURE_VERSION_EXIT_CHECKLISTS_20260921.md`, REL=`ART-V20-RELIABILITY_PROTOCOL.md`, CPP=`V17_LIVE_CHECKPOINT_PROTOCOL.md`, CPL=`V17_TO_V23_LIVE_CHECKPOINTS.md`. Bots (@63ce2a5d5, canonical plan 7451465a7): DE=`social-bots/DETAILED_EXECUTION_V18_TO_V30.md`, GJ=`social-bots/delivery/GATES.json`, OG=`delivery/OWNER_GATES.md`, SB4=`artifact-packets/SB-V20-004.md`.

## Jobs Automation

| Gate | Needed for V2.0? | Exact bounded scope (caps, window, stop-before) | Owner must supply (ALIAS/PATH only) | Prereq/order |
|---|---|---|---|---|
| G14 runtime identity | YES: IA Gate 1; PGM G14B; RB Campaign 2 | One importer run, one production packet, one independent verifier PASS receipt. Inputs stay local; only sanitized hashes and provenance are committed. Stop before any browser or network effect. | Local path to the genuine profile, exact resume file path, one real job URL, consent for private use | Needs the integrated source (b2688ee + b67fc523 + PR27 reference) composed and accepted. **Order 1.** |
| Gmail canary (G17/G20B) | YES: IA Gate 2 and Gate 5; RB Campaign 1; PGM G20B | Dry run first, then one persisted canary: 24h UTC window, at most 5 messages, then replay of the same window (no duplicate or lost rows). Genuine recruiting ingestion is a separate request: named query, at most 7 days and 25 messages, same-window replay. Read-only scope. No send, labels, archive, delete or scheduling. Persistence needs its own approval after the dry run is inspected. | Mailbox alias; path to local read-only OAuth token; exact query, window and cap; canary alias | Integrated Gmail readiness accepted. Can run in parallel with G14. **Order 2.** |
| G16B, or an owner-manual application lifecycle | YES, one of the two: IA Gate 4 needs one real application lifecycle with external evidence; RB Campaign 3 allows "already-authorized real application path or real existing lifecycle evidence"; PGM G16B | Option A: one AUTO_ALLOWED destination, per-application approval of the exact job, packet hash and method, external confirmation required, an unknown outcome is reconciled rather than retried. Option B: the owner applies manually and the system only ingests and links the confirmation. LinkedIn and Indeed stay manual-only. | For A: job, account alias, packet hash, method and a separate approval. For B: reference to the confirmation message or page. | G14 accepted, plus the G16A engineering acceptance. Option B also needs the Gmail canary. |
| Recovery drill | YES: IA Gate 6; PGM G20B "backup/recovery drill" | Back up the approved runtime DB, restore into a separate disposable DB, read back, clean up. Never restore over production. | Runtime DB identity alias, backup directory path, consent for private-data use | Any time after composition |
| Ops and analytics on real data | YES: IA Gates 6 and 7; RB Campaigns 4 and 5 | Local dashboard, health, one-shot worker runs and analytics over data already granted. No scheduler registration. Report N and make no causal claims. | Nothing new beyond the grants above | Runs last, over G14, Gmail and application data |
| CI | YES: IA evidence bundle "CI"; PGM G14A "current-head CI green" | Hosted Actions on the now-public repo. No billing or spending-limit change. | Confirm that public visibility is the intended zero-cost CI route | **Order 0** (all projects) |

## SwarmAI

| Gate | Needed for V2.0? | Exact bounded scope (caps, window, stop-before) | Owner must supply (ALIAS/PATH only) | Prereq/order |
|---|---|---|---|---|
| CI (EXT-ACTIONS-BILLING) | YES: EXIT V2.0 "configured deterministic CI green"; CPP CP0 | Exact-tip checks only. **OPS-CI-01 heartbeat throttle first**: MP §0.4 records about 1,000 runs/day from heartbeat commits. | Confirm public-repo Actions as the CI disposition; no billing change | OPS-CI-01 lands first. **Order 0.** |
| CP2: G12 routes + G13 | YES: MP §0.4 V1.4 path; WC-LIVE142-24H depends on G12+G13; ACC requires lower-version acceptance | At least 2 zero-charge remote providers plus a local fallback, on named routes with call and token caps. G13 needs either the HOST-WIN-DEV verifier or a lead ruling that verification is platform-neutral, plus a sealed digest. | Provider credential aliases and quota facts; Windows host alias, or a request for the lead ruling | MP calls this "the earliest lever". It starts the 24h V1.4 clock. **Order 3.** |
| CP1 (V1.4 real mission) | YES: CPP CP1; MP EXT-V14-LEAD-REVIEW | New preregistration. 2 of 2 attempts are used and 0 remain, so the attempt-limit disposition must be explicit. Brokered local inference on an unfamiliar target. No auto-apply. | Explicit disposition of the attempt limit (owner and lead) | R02a→R02b, then G12/G13 |
| R28d successor (single run) | YES: MP §0.3 V1.7 critical path | One local, private mission on a named host, model, route and throwaway target. Explicit caps on calls, tokens and time, plus an expiry. $0 incremental. Receipt, readback and cleanup required. No retry of the failed e9178259 run. | Host and route aliases; path to the throwaway target | The repair must pass engineering acceptance first |
| CP3 second host (EXT-V15-SECOND-HOST) | YES: MP §0.4 R18; CPP CP3 | Isolated worker kill, restart, expiry, cancel and race tests. No disruption of production processes. | Alias for an owned second physical host; confirmation that PG, Git and Python are reachable | R17a wiring |
| CP4 / CP5 (V1.7) | YES: CPP CP4, CP5, CP6 | CP4: real A/B missions over local knowledge with bounded brokered inference. CP5: exact local, API and browser-session targets, each approved individually. | Knowledge-scope path; target aliases | R25b, R33b |
| R33c real GitHub effect | YES: CPP CP5-REALWORLD; MP "V1.7 adds R33c" | One `[SwarmAI LIVE TEST]` issue, one comment and a close for cleanup, each independently read back. **Re-scope needed**: `pri8771/swarmai` is now PUBLIC, so this is a public effect. Either name a private throwaway repo or approve the public test issue. | Target repo alias and a separate gateway action grant | CP5 fixtures pass |
| CP18 recovery (EXT-D18-01/02) | YES: MP V1.8 exit; CPL CP18 | Isolated outage, backup, restore and fencing run. Record RPO/RTO and the duplicate-effect count. | Alias for the approved host/storage and the outage scope | V1.8 build complete |
| CP19 (EXT-V19-FRESH-ENVIRONMENTS / WINDOWS-HOST) | YES: MP §0.4 19-09/19-10; CPL CP19 | Clean install and upgrade/rollback in a fresh environment; one bounded self-development PR candidate with no self-merge. | Fresh-environment and Windows host aliases | V1.9 build complete. *New row, not in the old request.* |
| WC-V20-RELIABILITY-168H | YES: REL "7 consecutive wall-clock days"; ACC | Frozen CandidateManifest running for at least 168 real hours, with a checkpoint at least every 24h. Starting any process or timer needs a later exact grant. | Persistent host alias; sleep and reboot facts | CP20 freeze (20-08a) |

## Social Bots (all predecessor gates apply: DE "Version completion philosophy"; SB4 dependencies)

| Gate | Needed for V2.0? | Exact bounded scope (caps, window, stop-before) | Owner must supply (ALIAS/PATH only) | Prereq/order |
|---|---|---|---|---|
| G-MODEL-V04 | YES: GJ V0.4 | At most 5 Claude Code subscription calls (P0, P1, P2, P3, E0). No retries, fail fast, no spend or API fallback, API key absent. Expires 2h after lead activation. The old dormant pin cannot be reused. | Owner approval bound to source, tree and matrix | PR17 da5315970 suitability verdict, then a prepare-only matrix release. **Order 4.** |
| G-MODEL-RUNS | YES: GJ V0.5, V0.6, V1.0, V1.6–V1.9; OG | Separate caps for generation, review and unattended development calls. Subscription only, no PAYG. | Budget number per artifact | After V0.4 |
| G-CULTURAL | YES: GJ V0.5, V1.8; DE V1.8 LIVE | Attributable review event over the exact final content hash. Automated review cannot claim human endorsement. | Named reviewer alias or review method | V0.5 and V1.8 candidates |
| G-HOST + G-LEAD-LOOP | YES: GJ V0.7, V1.0, V1.1, V1.9 | Preparation only: capability receipt and an install proposal. Registration needs a later exact grant. Later windows: 3 genuine firings across 2 intervals (V0.7), 24h (V1.0), 72h unattended (V1.9). SB-R07-073/074 are still planned. | Persistent host alias and path; existing scheduler identity; sleep, reboot and auth facts; lead write route | C09→C10→C11 |
| G-ACCOUNTS | YES: GJ V0.8, V1.2, V1.7 | Readiness and account setup only. Reuse existing accounts first. MFA and consent are owner actions. | Account and credential aliases per route (X, IG, TikTok, Reddit, FB) | After V0.7 |
| G-PUBLISH + G-MEASURE | YES: GJ V0.9, V1.0, V1.3–V1.5, V2.0; DE V2.0 LIVE | 3 canaries, one per general persona, each scoped individually. Permalink readback. Named measurement windows. An uncertain outcome is reconciled before any resend. | Exact content hash, persona and account alias for each canary; permission to read metrics | G-ACCOUNTS |
| Recovery drill | YES: GJ V1.1, V1.9 | Isolated test state only. Fault injection and backup/restore with no external duplicate attempts. | Isolated state path | G-HOST |

## Dropped as V2.3+/deferred (from the old request)

- **Swarm CP23 half of "recovery/CP23"**: CPL CP23 and EXIT define it as V2.3 (2 physical nodes plus a real external interaction). The CP18 half stays.
- **Swarm EXT-D23-FAIRNESS**: MP §0.4 ties it to 23-12, which is V2.3.
- **Bots specialist budgets** (from the "later gates" row): specialist workers are DE V2.3 (SB-V23-001..003). Cultural review and generation/review budgets stay.
- **Bots SB-V23 and SB-V27 mapping**: the pause notice says V2.3/V2.7 are deferred.
- **Jobs V2.3 Career Intelligence, and the V2.7 definition proposals for all three projects**: deferred by the pause notice; PGM G23 comes after G20B.
- **Jobs G15 live assisted prefill**: PGM G15 lists it under "Optional real proof". V2.0 needs only the engineering acceptance of A-V15. Keep it available as an option; it is not on the critical path.

## Minimum first grants to unblock the most work

1. **CI disposition.** The repos are now public, so confirm public-repo Actions as the zero-cost CI route with no billing change. Swarm lands OPS-CI-01 first. This unblocks exact-tip CI, which every acceptance in all three repos requires.
2. **Jobs G14 local inputs**: profile path, resume path and one real job URL. There is no external effect, and it unblocks IA Gates 1, 3 and 4 plus downstream analytics.
3. **Jobs Gmail read-only dry-run canary** (24h, at most 5 messages; alias and token path). Unblocks IA Gates 2, 5 and 6 (health).
4. **Swarm G12**: aliases for at least 2 zero-charge providers, plus a request for the G13 platform-neutral ruling. This starts the V1.4 24h clock, the longest external lever (MP §0.4).
5. **Bots G-MODEL-V04**: five-call approval that takes effect only once lead release binds PR17 and the matrix. Supply the G-HOST facts at the same time; they are information only and do not register anything. This unblocks the whole Bots ladder from V0.4.

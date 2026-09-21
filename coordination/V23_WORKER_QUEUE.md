# V2.3 Master Worker Queue — PROPOSED

Status: **PLANNING PACKAGE LEAD-ACCEPTED WITH CORRECTIONS**. Rows remain inactive until ChatGPT promotes a bounded task/artifact into `coordination/WORK_QUEUE.md`. Read `docs/V23_LEAD_REVIEW_20260921.md` first.
This file is subordinate to `docs/V23_LEAD_REVIEW_20260921.md`, `AGENTS.md`, and the active `WORK_QUEUE.md`. There is one active implementation worker/session and one five-minute heartbeat watcher. The lane/group names below identify historical work surfaces and dependency groups, not simultaneous implementation workers.

Source of task detail (every ID below is fully specified there):
- `docs/V23_TASK_GRAPH_RECOVERY.md` (R14-*, R15-*, A-R15-*, R16-*, R17-*)
- `docs/V23_TASK_GRAPH_V20.md` (J20-*, J20G-*, J20I-*, G-*, C*)
- `docs/V23_TASK_GRAPH_V23.md` (V23-F/OG/SL/TW/II/TL/CB/AC)
- decisions D1–D9 and gates: `docs/V23_MASTER_PLAN.md` §11–§13

Promotion rule: a row may be promoted only when its dependency is open, its lead decision (if any) is taken, it does not conflict with the active branch batch, and it implies no live-action authority.

## 0. Immediately executable after lead review (first five)

| # | Task(s) | Lane / group | SP | Model | Blocked by |
|---|---|---|---|---|---|
| 1 | R14-P01 + R14-P02 (then R14-P03, R14-P04) | Lane 1 | 1+1 (+1+1) | Sonnet high | none (already assigned) |
| 2 | R14-P03 proof-integrity adversarial suite | active V1.4 surface | 1 | Sonnet medium | R14-P01/P02 |
| 3 | R14-P04 exact-head independent validation | active V1.4 surface | 1 | Sonnet low | R14-P03 |
| 4 | R14-I01..I05 clean current-main proof integration | next V1.4 surface | 5 × 1 | Sonnet/Haiku | P0A lead acceptance |
| 5 | next unblocked artifact: V1.4 live proof if gate open, otherwise V1.5 clean integration | single active worker | bounded SP1/SP2 | Sonnet | current gate truth |

## 1. PG1 — V1.4 dependency group (`worker/v14-real-proof` → `worker/v14-clean-integration`)

Order: R14-P01, R14-P02, R14-P03, R14-P04 → `LEAD_GATE` P0A → R14-I01..I05 → `LEAD_GATE` → `USER_GATE` private inputs → R14-L01..L07 → (after lead assignment) J20G-01, J20G-02, J20G-03, J20G-04 → `USER_GATE` OAuth → G-01..G-05 → R17-L01..L09.
SP: 4 + 5 + (5 SP1 + 2 LIVE) + 8 + (1 SP1 + 3 LIVE) + (5 SP1 + 4 LIVE).

## 2. PG2 — V1.5/V1.6 dependency group (`worker/v15-assisted-application` → `worker/v15-clean-integration` when active)

Order: R15-I01..I04 → A-R15-09, A-R15-08, A-R15-06 (lands `core/untrusted_text.py` if V23-F02 has not), A-R15-07, R15-V01 → `LEAD_GATE` V1.5 engineering → mandatory-for-completion `USER_GATE` R15-L01..L07 (may be scheduled when gate opens while safe engineering continues) → (lead advancement) R16-A01..A04 → R16-I01..I05 → R16-P01..P07 → R16-C01..C05 → R16-H01..H04 → R16-T01, R16-T02 → implement the first compliant supported transport when one is identified (R16-T03..T05) → `USER_GATE` R16-L01..L06. Engineering may continue elsewhere while a transport/user gate is blocked, but V1.6 live proof remains mandatory before V2.0/V2.3 completion.
Schema window: migration `004_v16_submission_truth` (R16-A01 + R16-I02) lands before PG4's `005_v23_intelligence_foundation` (lead-corrected D4).

## 3. PG3 — V1.7/V2.0 dependency group (historical `worker/recruiting-ops`; execute only when this is the active work surface)

Order: R17-E01, R17-E02, R17-E03, R17-E03b (optional), R17-E04, R17-E05 → J20-12, J20-15, J20-16 → J20-01, J20-02, J20-03, J20-04 → J20-05, J20-06a, J20-06b, J20-08 → J20-17, J20-19, J20-20 → J20-09, J20-10 → J20I-01, J20I-02, J20I-03 → (after V23-F04) J20-11 → V23-SL-01..07 → V23-CB-01..05 → (optional) J20-18.

## 4. PG4 — V2.3 intelligence dependency group (`worker/v23-intelligence` when this becomes the single active work surface)

Order: V23-F01, V23-F02, V23-F03 (schema window 004), V23-F04, V23-F05 → V23-OG-01, OG-02, OG-03, OG-04, OG-08, OG-05, OG-06, OG-07, OG-09, OG-10 → V23-TW-01, TW-02, TW-03, TW-04, TW-05, TW-06, TW-07 → V23-II-01, II-02, II-03, II-04, II-05, II-06, II-07 → V23-TL-01, TL-02, TL-03 (Opus review), TL-04, TL-05, TL-06, TL-07, TL-08 (needs J20-15, J20-17), TL-09 (needs V1.5 clean port), TL-10, TL-11 → V23-AC-01 (needs J20I-01, CB-02), AC-02, AC-03 → `USER_GATE` inputs → V23-AC-04 LIVE → `LEAD_GATE` A-V23-CAREER-INTELLIGENCE.

Parallelism inside PG4 means dependency-level/subagent parallelizability only. With the one-worker rule, the parent implementation session owns integration and commits sequential coherent batches. Lower-cost subagents may independently analyze/test non-overlapping surfaces. TL follows the services it wraps; CB follows OG/SL/TW/II; AC is last.

## 5. Gates that block only their own action

| Gate | Blocks | Does not block |
|---|---|---|
| `USER_GATE` private inputs | R14-L05..L07, live V2.0/V2.3 campaigns | all engineering |
| `USER_GATE` Gmail OAuth | G-03..05, R17-L04..L07, live campaigns | J20G engineering, fixtures |
| `USER_GATE` visible browser | R15-L03..L06 | V1.5 engineering, V1.6 engineering |
| `USER_GATE` per-application submit + eligible transport | R16-L* (deferred) | everything |
| `USER_GATE` target list / manual application reports | V23-AC-04 inputs | V2.3 engineering; any reported submission stays unconfirmed until external evidence |
| `LEAD_GATE` P0A | R14-I, R14-L | Lane 2/3/PG4 work |
| `CI_BLOCKED_ACCOUNT` | CI-green evidence | `INDEPENDENT_SANDBOX_VALIDATION` (D6) |

## 6. Review rule (unchanged)

Workers push coherent tested batches, set `READY_FOR_LEAD_REVIEW`, and stop at the review boundary. ChatGPT reviews actual diff/tests/validation records, accepts or issues one bounded rework, integrates, and writes the next bounded assignment into the lane file. Worker claims are evidence inputs only.

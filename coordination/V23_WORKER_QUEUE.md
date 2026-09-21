# V2.3 Master Worker Queue — PROPOSED

Status: **PROPOSED by the Fable planning pass; not active until ChatGPT promotes rows into `coordination/WORK_QUEUE.md`.**
This file does not change lane assignments, heartbeat rules, phase gates, or live/user gates. `WORK_QUEUE.md` and the lane files remain authoritative.

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
| 2 | R15-I01..I04 clean port of 8 browser files | Lane 2 | 4 × 1 | Sonnet medium | D2 |
| 3 | R17-E01..E05 V1.7 reconciliation with sandbox validation | Lane 3 | 5–6 × 1 | Sonnet/Haiku | D6 |
| 4 | J20-12 local CI parity + J20-15 record-manual-application | Lane 3 | 1 + 2 | Sonnet | D5, D6 |
| 5 | V23-F01 envelope + V23-OG-01 port Lane D graph module | PG4 (V2.3 surface) | 1 + 1 | Sonnet | D3, D8 |

## 1. PG1 — Lane 1 (`worker/v14-real-proof` → `worker/v14-clean-integration`)

Order: R14-P01, R14-P02, R14-P03, R14-P04 → `LEAD_GATE` P0A → R14-I01..I05 → `LEAD_GATE` → `USER_GATE` private inputs → R14-L01..L07 → (after lead assignment) J20G-01, J20G-02, J20G-03, J20G-04 → `USER_GATE` OAuth → G-01..G-05 → R17-L01..L09.
SP: 4 + 5 + (5 SP1 + 2 LIVE) + 8 + (1 SP1 + 3 LIVE) + (5 SP1 + 4 LIVE).

## 2. PG2 — Lane 2 (`worker/v15-assisted-application` → `worker/v15-clean-integration`)

Order: R15-I01..I04 → A-R15-09, A-R15-08, A-R15-06 (lands `core/untrusted_text.py` if V23-F02 has not), A-R15-07, R15-V01 → `LEAD_GATE` V1.5 engineering → optional `USER_GATE` R15-L01..L07 → (lead advancement) R16-A01..A04 → R16-I01..I05 → R16-P01..P07 → R16-C01..C05 → R16-H01..H04 → R16-T01, R16-T02 → stop (R16-T03..T05, R16-L deferred after V2.3 per D1).
Schema window: migration `005_v16_submission_truth` (R16-A01 + R16-I02) coordinated with PG4's 004 (D4).

## 3. PG3 — Lane 3 (`worker/recruiting-ops` synced to main)

Order: R17-E01, R17-E02, R17-E03, R17-E03b (optional), R17-E04, R17-E05 → J20-12, J20-15, J20-16 → J20-01, J20-02, J20-03, J20-04 → J20-05, J20-06a, J20-06b, J20-08 → J20-17, J20-19, J20-20 → J20-09, J20-10 → J20I-01, J20I-02, J20I-03 → (after V23-F04) J20-11 → V23-SL-01..07 → V23-CB-01..05 → (optional) J20-18.

## 4. PG4 — V2.3 intelligence surface (`worker/v23-intelligence`, owner per D3)

Order: V23-F01, V23-F02, V23-F03 (schema window 004), V23-F04, V23-F05 → V23-OG-01, OG-02, OG-03, OG-04, OG-08, OG-05, OG-06, OG-07, OG-09, OG-10 → V23-TW-01, TW-02, TW-03, TW-04, TW-05, TW-06, TW-07 → V23-II-01, II-02, II-03, II-04, II-05, II-06, II-07 → V23-TL-01, TL-02, TL-03 (Opus review), TL-04, TL-05, TL-06, TL-07, TL-08 (needs J20-15, J20-17), TL-09 (needs V1.5 clean port), TL-10, TL-11 → V23-AC-01 (needs J20I-01, CB-02), AC-02, AC-03 → `USER_GATE` inputs → V23-AC-04 LIVE → `LEAD_GATE` A-V23-CAREER-INTELLIGENCE.

Parallelism inside PG4: OG, TW and II may run concurrently (separate files) once F01–F05 exist; TL after the services it wraps; CB after OG/SL/TW/II; AC last.

## 5. Gates that block only their own action

| Gate | Blocks | Does not block |
|---|---|---|
| `USER_GATE` private inputs | R14-L05..L07, live V2.0/V2.3 campaigns | all engineering |
| `USER_GATE` Gmail OAuth | G-03..05, R17-L04..L07, live campaigns | J20G engineering, fixtures |
| `USER_GATE` visible browser | R15-L03..L06 | V1.5 engineering, V1.6 engineering |
| `USER_GATE` per-application submit + eligible transport | R16-L* (deferred) | everything |
| `USER_GATE` target list / manual application attestations | V23-AC-04 | V2.3 engineering |
| `LEAD_GATE` P0A | R14-I, R14-L | Lane 2/3/PG4 work |
| `CI_BLOCKED_ACCOUNT` | CI-green evidence | `INDEPENDENT_SANDBOX_VALIDATION` (D6) |

## 6. Review rule (unchanged)

Workers push coherent tested batches, set `READY_FOR_LEAD_REVIEW`, and stop at the review boundary. ChatGPT reviews actual diff/tests/validation records, accepts or issues one bounded rework, integrates, and writes the next bounded assignment into the lane file. Worker claims are evidence inputs only.

# Test / Adversarial Matrix by Artifact (V1.4 → V2.3)

- Status: PROPOSED (companion to `docs/V23_MASTER_PLAN.md`)
- Rule: every row maps to a task ID in the task graphs and to a test file. Existing matrices are referenced, not copied: `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`, `docs/V2_3_ACCEPTANCE_MATRIX.md`, `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`, `docs/LANE_A_REAUDIT_2.md`.
- Baseline on main `e84da8d`: 151 tests, 22 files (largest: `test_lifecycle.py` 22, `test_ingestion_engine.py` 15, `test_worker.py` 12, `test_dashboard.py` 10, `test_health.py` 10). Mocks/fixtures never count as live proof.

## A-V14-P0A-INTEGRITY / A-V14-CLEAN-INTEGRATION

| Case | Expected | Task | Test file |
|---|---|---|---|
| no DB target configured | FAIL `DB_TARGET_MISSING` | R14-P01 | `tests/test_real_proof_verifier.py` (worker-pc suite, un-xfailed) |
| persisted packet row absent / hash / origin / resume sha / variant family / variant name mismatch (6 params) | FAIL naming field | R14-P01 | same |
| JobSource provider / source kind / public id / api url / fetched_at / description sha / question sha divergence (7 params) | FAIL naming field | R14-P02 | same |
| self-consistent forged questions + description sha (with and without DB target) | FAIL | R14-P02 | same |
| valid bundle with configured DB | PASS receipt bound to candidate bundle | R14-P01/P02 | `test_persisted_source_baseline_passes_so_adversarial_variants_are_isolated` |
| packet-hash helper backward compatibility | identical hash to inline formula | R14-I03 | `tests/test_preparation.py` |
| overlay regression | ≥168 tests green | R14-I04 | full suite |

## A-V15-* (clean port + residuals)

| Case | Expected | Task | Test file |
|---|---|---|---|
| A-R15-01..05 accepted behaviors | preserved (27 targeted tests) | R15-I02 | `tests/test_assisted_safety_adversarial.py` |
| page-level injection outside labels | security signal, no instruction execution | A-R15-06 | same |
| optional page injection + safe form | safe fields prepared, warning retained | A-R15-06 | same |
| required field with injection text | manual / policy block | A-R15-06 | same |
| page text sets live-ready/submitted/authorization | impossible | A-R15-06 | same |
| resume + cover letter distinct uploads | distinct paths/bytes/hashes | A-R15-07 | same |
| required cover letter missing / tampered | no prefill / blocked | A-R15-07 | same |
| two file inputs cross-attach | impossible | A-R15-07 | same |
| answers / provenance / variant mutated after packet hash | blocked before browser write | A-R15-08 | same |
| unknown required / optional file input | manual block / unfilled | A-R15-09 | same |
| mock runner default, `file://` URI, review-required audit | safe defaults, path conversion, audit row | R15-V01 | `tests/test_assisted_application.py` |

## A-V17-ENGINEERING-RECONCILIATION

| Case | Expected | Task | Test file |
|---|---|---|---|
| all card criteria mapped to existing tests | checklist in card | R17-E01/E02 | existing `tests/test_lifecycle.py` |
| contact without parseable email | deterministic dedupe by (company, normalized name) | R17-E03 | `tests/test_lifecycle.py` |
| plaintext parser fallback per board | parsed | R17-E03 | `tests/test_parsers.py` |
| follow-up task draft inputs (optional) | structured payload, no send | R17-E03b | `tests/test_lifecycle.py` |
| offer accept/decline/withdraw | reachable only via user decision; terminal protection intact | J20-16 | `tests/test_lifecycle.py` |

## A-V16-* (engineering; not on the V2.3 critical path)

All rows of `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md` are owned as follows: Authorization → R16-A04; Policy → existing `tests/test_policy.py` + R16-P07; Packet/candidate truth → R16-P07; Idempotency → R16-I05 (+ R16-I03 concurrency); Runtime barriers → R16-P07 / existing `tests/test_auto_application.py`; Confirmation truth → R16-C05; Audit/task hygiene and Concurrency/recovery → R16-H04. New files: `tests/test_submission_authorization.py`, `tests/test_submission_attempts.py`, `tests/test_submission_confirmation.py`.

## A-V20-GMAIL-RUNTIME-READINESS

| Case | Expected | Task | Test file |
|---|---|---|---|
| 3 listed, second fetch fails | error, 0 rows, checkpoint unchanged; next run ingests 3 once | J20G-01 | `tests/test_ingestion_engine.py` |
| failure on last message | full rollback | J20G-01 | same |
| diagnostic output | no `ya29`/`refresh_token`/`client_secret`; interactive flow never called | J20G-03 | `tests/test_gmail_diagnostic.py` |
| scope mismatch | `SCOPE_MISMATCH` | J20G-03 | same |
| registered/mock adapter | never `gmail_mode == REAL` | J20G-04 | `tests/test_health.py` |
| dashboard exposes readiness | fields present, no secrets | J20G-04 | `tests/test_dashboard.py` |

## A-V20-CONTROL-CENTER / RELIABILITY / ANALYTICS

| Case | Expected | Task | Test file |
|---|---|---|---|
| all GET endpoints | 200 JSON | J20-04 | `tests/test_dashboard.py` |
| POST resolve 404 / 400 / 403 no token / 403 wrong token / 200 | as listed | J20-04 | same |
| `/api/config` | allowlist keys only; denylist regex clean | J20-02 | same |
| manual application reported | application row + `SUBMISSION_UNCONFIRMED`; duplicate refused; no variant guess; confirmed-submission denominator unchanged until external confirmation | J20-15 | `tests/test_manual_application.py`, `tests/test_dashboard.py` |
| restore without checksum | exit 2 unless explicit override | J20-06a | `tests/test_scripts.py` |
| backup without credential | exit 2, no echo | J20-06b | same |
| gateway factory | null → deterministic; configured w/o litellm → error; mock forbidden in production | J20-17 | `tests/test_deterministic_gateway.py` |
| freshness | old posting scores lower; fixtures keep decisions | J20-19 | `tests/test_evaluation.py` |
| window_days | all-time default unchanged; windowed N | J20-10 | `tests/test_dashboard.py` |
| golden scenario 17 steps + replay/out-of-order | pass; report schema | J20I-01..03 | `tests/integration/test_v20_golden_scenario.py` |

## A-V23-OPPORTUNITY-GRAPH

| Acceptance-matrix case | Expected | Task | Test file |
|---|---|---|---|
| model proposes nonexistent recruiter relation | `REVIEW_REQUIRED`, `inferred=True`; cannot self-assert | V23-OG-06 | `tests/test_v23_edges.py` |
| same contact under multiple emails | merge via CRM `merge_contacts`; edges follow primary; no duplicate edge | V23-OG-04/05 | `tests/test_v23_opportunity_graph.py` |
| stale target-company observation | excluded by `as_of`; `stale` flag | V23-OG-07 / TW-04 | graph + watch tests |
| source evidence invalidated | edge hidden; audit row | V23-OG-06/07 | `tests/test_v23_edges.py` |
| duplicate public role | one job (tier-3 dedupe); one `HAS_JOB` edge | V23-TW-04 | `tests/test_v23_target_watch_adversarial.py` |
| rebuild from fixtures stable | byte-identical JSON for fixed `as_of` | V23-OG-07 | `tests/test_v23_opportunity_graph.py` |
| same evidence twice | one edge | V23-OG-04/06 | same |
| user-confirmed → ASSERTED | via `confirm` by non-system actor | V23-OG-06 | `tests/test_v23_edges.py` |
| queries preserve source refs | every result carries `EvidenceRef`s | V23-OG-02/04 | graph tests |
| exact vs substring email | `an@` ≠ `jordan@` | V23-OG-03 | graph tests |
| multi-company isolation | no cross-company edges | V23-OG-04 | graph tests |
| N+1 | ≤5 queries for 20 jobs | V23-OG-08 | graph tests |

## A-V23-STRATEGY-LEARNING

| Case | Expected | Task | Test file |
|---|---|---|---|
| one success from N=1 | `GATHER_MORE_DATA`, LOW | V23-SL-03/06 | `tests/test_v23_strategy_adversarial.py` |
| Simpson/confounding segments | `SEGMENT_DIRECTION_REVERSAL` warning | V23-SL-05/06 | same |
| stale outcomes | n=0 in window, `stale` warning | V23-SL-02/06 | same |
| treatment assignment missing | observational only; never `EXPERIMENTAL` | V23-SL-04/06 | same |
| resume versions collapsed incorrectly | rollup only when requested and labeled | V23-SL-02/05 | same |
| late experiment assignment | `AssignmentTooLateError` | V23-SL-04 | `tests/test_v23_strategy.py` |
| every rate has N and window | validator | V23-F01 | `tests/test_v23_envelope.py` |

## A-V23-TARGET-COMPANY-WATCH

| Case | Expected | Task | Test file |
|---|---|---|---|
| career page temporarily unavailable | `SOURCE_UNAVAILABLE` observation; no closures | V23-TW-04/07 | `tests/test_v23_target_watch_adversarial.py` |
| role URL changes, requisition same | no duplicate job, no `NEW_ROLE` | V23-TW-04/07 | same |
| recruiter relation inferred from text only | `RECRUITER_SIGNAL` observation; edge stays `REVIEW_REQUIRED` | V23-TW-07 | same |
| duplicate role across ATS/public page | one job | V23-TW-07 | same |
| paused company | no observations/tasks | V23-TW-05 | `tests/test_v23_target_watch.py` |
| already-applied role | `SUPPRESSED` | V23-TW-05 | same |
| repeated identical fetch | zero new observations | V23-TW-04 | same |
| rate-limited / malformed source | status set, no postings, no exception | V23-TW-01/02 | `tests/test_public_sources.py` |

## A-V23-INTERVIEW-INTELLIGENCE

| Contract case | Expected | Task | Test file |
|---|---|---|---|
| ambiguous interviewer identity | review item | V23-II-03/06 | `tests/test_v23_interview_adversarial.py` |
| rescheduled interview | stage/schedule from `InterviewModel`; conflict noted | V23-II-06 | same |
| timezone conflict | conflict listed | V23-II-06 | same |
| stale job description | staleness from `job_description_hash` vs packet metadata | V23-II-03/06, J20-20 | same |
| role changed between application and interview | warning | V23-II-06 | same |
| resume variant differs from another role | brief cites packet variant only | V23-II-06 | same |
| unsupported quantitative achievement | `unsupported_claims_to_avoid` | V23-II-04/06 | same |
| prompt injection in public content | `security_signals`; never in allowed claims | V23-F02, II-03/04/06 | same |
| duplicate calendar/interview evidence | conflict | V23-II-06 | same |
| interview cancelled after brief | `stale=True` on rebuild | V23-II-06 | same |
| `send_performed` | always False | V23-II-01/05 | `tests/test_v23_interview.py` |

## A-V23-AGENT-TOOLS

| Acceptance-matrix case | Expected | Task | Test file |
|---|---|---|---|
| caller omits permission context for consequential tool | P2/P3 → NEEDS_REVIEW (REQUIRE_APPROVAL) without handler call | V23-TL-03/11 | `tests/test_v23_tools_adversarial.py` |
| stale entity ID | `NOT_FOUND`, never partial success | V23-TL-05/11 | same |
| duplicate request ID / idempotency key | replay (same hash) or `DUPLICATE_REQUEST` (different hash) | V23-TL-05/11 | same |
| tool partially fails | `PARTIAL` preserved with warnings | V23-TL-05/11 | same |
| transport wrapper bypasses service policy | impossible: handlers not exported; only `ToolRuntime` public | V23-TL-11 | same |
| P4 tool | always DENY | V23-TL-03 | `tests/test_v23_permission_gate.py` |
| class above caller ceiling | DENY (`min()` rule) | V23-TL-03 | same |
| approval mismatch (hash/target/method/expired/consumed) | DENY with reason | V23-TL-03 | same |
| simulated handler result | `simulated=True` enforced; can never set `SUBMITTED` | V23-TL-05/09 | `tests/test_v23_tools.py` |
| no agent-framework import under `tools/` | AST scan clean | V23-TL-11 | adversarial file |
| health tool output | no secrets/paths | V23-TL-07 | `tests/test_v23_tools.py` |

## A-V23-CAREER-BRIEFING / A-V23-ACCEPTANCE-CAMPAIGN

| Case | Expected | Task | Test file |
|---|---|---|---|
| empty DB | briefing with data gaps only | V23-CB-02/05 | `tests/test_v23_briefing.py` |
| fixture DB, fixed `as_of` | deterministic JSON | V23-CB-02 | same |
| MANUAL_ONLY destination | `next_action` never `AWAIT_APPROVAL` | V23-CB-05 | same |
| simulated rows present | `simulated=True` on briefing | V23-CB-02 | same |
| schema drift | test regenerates `docs/schemas/career_briefing.schema.json` and fails on diff | V23-CB-01 | same |
| engineering campaign | all assertions pass; report `simulated=True` | V23-AC-01 | `tests/integration/test_v23_campaign.py` |
| forged live report (fixture marker / stale sha / missing DB target) | `V23_CAMPAIGN_FAIL` | V23-AC-02 | `tests/test_verify_v23_campaign.py` |

## Coverage gaps closed by this plan (from the inventories)

- CLI `auto-apply`/`assisted-apply` untested end-to-end → covered indirectly by V23-TL-09 tool wrappers and R15-V01; explicit CLI tests remain a documented gap.
- Dashboard GET endpoints unauthenticated → documented by design (J20-04), not changed in V2.3.
- `GmailAdapter` real path untested → J20G-01/03 fake-client tests.
- `OFFER_ACCEPTED/DECLINED` unreachable → J20-16.
- Per-dimension scoring reasons not persisted → recomputed at query time (V23-TL-06, CB-02), labeled.

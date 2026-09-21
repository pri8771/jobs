# V2.3 Acceptance Campaign — Engineering Scenario and Live Overlay

- Artifact: A-V23-ACCEPTANCE-CAMPAIGN (evidence artifact for A-V23-CAREER-INTELLIGENCE)
- Status: PROPOSED (procedure; nothing here authorizes a live action)
- Tasks: V23-AC-01..04 in `docs/V23_TASK_GRAPH_V23.md`
- Requirements source: `docs/V2_3_ACCEPTANCE_MATRIX.md`; evidence standard: `docs/LIVE_CHECKPOINT_EVIDENCE_STANDARD_V14_V17.md`; real-proof policy: `docs/REAL_PROOF_ACCEPTANCE_POLICY.md`

## 1. Purpose

Turn "V2.3 works" into two machine-verifiable reports:
- an **engineering campaign report** produced by a deterministic fixture (regression evidence, explicitly `simulated=true`), and
- a **live campaign report** produced over the owner's real data after the user gates open (the only evidence that can make V2.3 `REAL_PROVEN`).

Both are checked by `scripts/verify_v23_campaign.py`, which fails closed (no DB target → FAIL; fixture markers in live mode → FAIL; stale code SHA → FAIL). Only ChatGPT marks the result accepted.

## 2. Engineering campaign (fixture; `tests/integration/test_v23_campaign.py`)

Extends the V2.0 golden scenario (J20I-01) after its step 17. All inputs synthetic and internally consistent; the public-source client uses an injected fake transport with a captured JSON payload labeled `fixture`.

| Step | Action | Assertion |
|---|---|---|
| 18 | add target company for the fixture company with `greenhouse_board_token`; activate | row `watch_status == ACTIVE`; default before activation was `PAUSED` |
| 19 | `WatchRunner.run()` with fixture transport (3 postings; one equals the already-known job) | 2 `NEW_ROLE` observations, 0 for the known job (dedupe), fit scores attached; second run → 0 new observations |
| 20 | fixture transport returns 429 | 1 `SOURCE_UNAVAILABLE`, no `ROLE_CLOSED` |
| 21 | propose recruiter→company edge from message evidence; user confirms | `REVIEW_REQUIRED` → `ASSERTED`; audit rows; projection shows edge `inferred=false` |
| 22 | invalidate one message-derived edge | absent from `project_graph(as_of=now)` |
| 23 | record manual application (J20-15) for a second job with explicit resume variant | application `manual/SUBMITTED`; funnel counts it |
| 24 | strategy over fixture outcomes (window 90 d) | every rate has `n`; all recommendations `GATHER_MORE_DATA` with `low_n=true` (fixture N < 5) |
| 25 | create experiment, assign variant to an unapplied job, then apply (fixture) | assignment immutable; late assignment on an already-applied job raises |
| 26 | interview brief for the fixture application with a scheduled interview | people carry evidence refs; requirements cite `description_hash`; story map has one unsupported quantitative requirement; injected JD phrase appears only in `security_signals` |
| 27 | followup package | `send_performed == false`; unresolved facts listed |
| 28 | briefing (`limit=5`, fixed `as_of`) | deterministic JSON; top card has reasons, relationship signal, resume recommendation with rates, `next_action`; `data_gaps` non-empty |
| 29 | invoke each step's tool through `ToolRuntime` (read + prep tools; P2 without flag; P3 without approval) | statuses `SUCCEEDED / NEEDS_REVIEW / NEEDS_REVIEW`; audit rows with `request_id`, `input_hash`; replay with same key → `REPLAYED` warning |
| 30 | emit report | `artifacts/reports/v23_engineering_campaign_report.json` validates against the schema below |

Engineering report schema (JSON): `trace_id, mode:"engineering", simulated:true, code_sha, fixture_version, generated_at, entity_ids{jobs[],applications[],contacts[],interviews[],target_companies[],observations[],edges[],experiments[]}, assertions[{step,name,pass,detail}], tool_audit_refs[], rates[{subject,numerator,denominator,n,low_n}], briefing_hash, warnings[]`.

## 3. Live overlay (after gates; owner data)

### Preconditions (all must hold; each is a separate gate)
1. V1.4 `A-V14-REAL-PROOF` accepted (real resume identity in `resume_variant`) — `USER_GATE` private inputs.
2. Gmail read-only OAuth completed by the owner; `gmail-diagnose` reports `mode=REAL`, canary ok — `USER_GATE`.
3. At least one bounded persisted Gmail canary and idempotent rerun accepted (A-V20-LIVE-INGESTION), plus V1.7 real lifecycle proof accepted.
4. At least one real application with accepted **external confirmation evidence**. The record may originate from an assisted/manual or system-submit flow, but user attestation alone is not sufficient to claim submitted/confirmed truth.
5. Owner supplies a target-company list (≥1 ACTIVE target with a public ATS token) — `USER_GATE` input, no outreach implied.
6. V1.4, V1.5, V1.6, V1.7 and V2.0 required live checkpoints accepted; V2.3 engineering artifacts accepted on the engineering campaign.

### Commands (from a machine holding the private profile, resume bytes, Gmail token; no secrets committed)
```
scripts/local_ci.sh                                   # exact-head validation record
jobs-automation gmail-diagnose --json                 # mode=REAL, no secrets
jobs-automation worker --once                         # real ingestion sweep (already authorized canary scope)
jobs-automation intel targets run-watch               # real public API fetch for ACTIVE targets
jobs-automation intel graph company <real_company_id> --json
jobs-automation intel strategy --window-days 90 --json
jobs-automation intel interview-brief <real_application_id> --json     # or record "no interview evidence" truthfully
jobs-automation briefing --json > artifacts/reports/v23_live_campaign_report.json
python scripts/verify_v23_campaign.py --report artifacts/reports/v23_live_campaign_report.json --mode live --database-url "$DATABASE_URL"
```

### Live report content (before redaction)
`trace_id, mode:"live", simulated:false, code_sha, generated_at, gmail_mode:"REAL", data_freshness, real_jobs[{job_id, public_url, provider}], real_applications[{application_id, mode, status, resume_variant_id}], contacts_count, messages_count, interviews_count, target_companies[{id, source_provider, fetch_status, observations_count}], edges{asserted, review_required, invalidated}, rates[...], briefing_hash, data_gaps[], unresolved_user_gates[]`.

### Redaction allowlist for the committed copy (`coordination/proofs/v23_live_campaign_report.redacted.json`)
Allowed: code SHA, run ids, public job URLs, entity UUIDs, provider names, counts, rates with N, `briefing_hash`, hashed email fingerprints, timestamps, verifier receipt. Forbidden: message bodies, contact names/emails, resume/profile contents, tokens, local paths, briefing prose fields other than `next_action`/`decision` enums.

### Verifier checks (live mode)
- report schema valid; `simulated == false`; `gmail_mode == "REAL"`;
- no fixture markers (`FORBIDDEN_TOKENS` approach shared with the V1.4 verifier: `fixture`, `mock`, `example.yaml`, `SIM-GH`, `SIM-LEVER`, `MockEmailAdapter`, `MockBrowserRunner`, `MockModelGateway`);
- every listed entity id resolves in the configured DB; every `rate` internally consistent (`numerator ≤ denominator`, `n == denominator`, `low_n` matches guardrails);
- `code_sha == git rev-parse HEAD`; the report hash is bound into `v23_campaign_receipt.json` with `result: V23_CAMPAIGN_PASS | V23_CAMPAIGN_FAIL`;
- missing `--database-url` → FAIL (never a bare success).

### Result vocabulary
`V23_CAMPAIGN_PASS | V23_CAMPAIGN_FAIL | LIVE_PROOF_BLOCKED_USER_AUTH | LIVE_PROOF_BLOCKED_PRIVATE_INPUT | LIVE_PROOF_BLOCKED_PROVIDER | LIVE_PROOF_BLOCKED_OTHER`. Blocked/fail never becomes pass.

## 4. Stop conditions (any one blocks V2.3 REAL_PROVEN)

- fixture/mock evidence presented as live; `gmail_mode != REAL`;
- a relationship shown as `ASSERTED` without a `USER_CONFIRMATION` or FK/message evidence row;
- a recommendation with `confidence != LOW` at `n < min_n`;
- a brief claim not traceable to a candidate profile field;
- any unauthorized external side effect (message, submission, calendar) performed by the campaign; the campaign may read already-confirmed application state but does not create a new external submission itself;
- unresolvable entity ids in the report.

## 5. Acceptance ownership

Workers run and report. `worker-pc` may independently re-run the verifier. Only ChatGPT marks A-V23-ACCEPTANCE-CAMPAIGN accepted and A-V23-CAREER-INTELLIGENCE `ENGINEERING_ACCEPTED` / `REAL_PROVEN`. Low N with honest `GATHER_MORE_DATA` outputs is an acceptable PASS state; fabricated certainty is not.

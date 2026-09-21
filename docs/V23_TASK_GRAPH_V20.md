# Task Graph — V2.0 Integrated OS (Gmail runtime, control center, reliability, analytics, integration fixture, live campaign)

- Status: PROPOSED (lead review required)
- Parent plan: `docs/V23_MASTER_PLAN.md`
- Contracts: `docs/V2_0_GMAIL_RUNTIME_READINESS.md`, `V2_0_INTEGRATION_FIXTURE.md`, `V2_0_INTEGRATION_ACCEPTANCE.md`, `V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`, `V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`, `V2_0_BROWNFIELD_AUDIT.md`, `GMAIL_CANARY_RUNBOOK.md`
- Brownfield truth used (master plan §2.3): the dashboard already serves funnel, sources, kanban, jobs, reviews, interviews, contacts, audit, health, followups, analytics/{sources,roles,resumes,time-to-stage}, timeline, offers-rejections, policies, worker; analytics already reports N and low-sample flags; worker run history is accepted; `health.check_gmail` is a placeholder awaiting a typed readiness report.

Conventions: `docs/V23_TASK_GRAPH_V23.md` §0. Card task IDs (J20-*, J20G-*, J20I-*) are canonical; legacy `V20-*` rows in `PREP_QUEUE_V16_TO_V30.md` map onto them in §7.

Lane suggestion: J20G-* → Lane 1 after the V1.4 proof (or Lane 3 by lead reassignment); everything else → Lane 3 (PG3).

---

## 1. A-V20-GMAIL-RUNTIME-READINESS

### J20G-01 — Fail closed on partial Gmail fetch
- SP2 · Parallel: yes · Model: Sonnet · Effort: high
- Objective: `GmailAdapter.poll_messages()` must not silently omit a listed message.
- Why: `get_message()` swallows exceptions and returns `None`; a sweep can advance the checkpoint past a lost message.
- Depends on: none.
- Code: `adapters/gmail.py`, `ingestion/engine.py` (reuse the existing rollback boundary in `run_sweep`), `worker.py` error categorization; tests `tests/test_ingestion_engine.py`, `tests/test_worker.py`.
- Required behavior: when any listed id fails to fetch, raise `PartialFetchError(listed: int, fetched: int, failed_ids: list[str])`; `run_sweep` catches it, rolls back, returns `status="FAILED"`, `error_category="GMAIL_PARTIAL_FETCH"`, checkpoint unchanged; worker finalizes `FAILED` with the category; next run re-polls through the overlap window.
- Non-goals: no retries inside the adapter beyond one immediate retry per message; no fixture fallback.
- Tests: list returns 3 ids, second fetch fails → error, zero committed rows, checkpoint unchanged; subsequent success ingests all 3 once; `MockEmailAdapter` unaffected.
- Adversarial: failure on the last message still rolls back everything.
- Failure behavior: as above; never partial commit.

### J20G-02 — Runtime OAuth token wiring
- SP2 · Parallel: yes · Model: Sonnet · Effort: medium
- Objective: documented, secret-free container/runtime token path.
- Code: `docker-compose.yml` (worker service: `GMAIL_TOKEN_PATH=/app/.local/gmail_token.json`, volume `./.local:/app/.local` read-write for the worker only; dashboard gets no token mount), `.env.example` (comment only), `docs/GMAIL_CANARY_RUNBOOK.md` "Runtime wiring" section, `config/README.md`.
- Required behavior: `AppSettings.gmail_token_path` honors the env var; nothing under `.local/` is committed (`.gitignore` already covers it); client id/secret via env/secret store only.
- Tests: settings resolution from env; YAML parse test of compose file asserting the dashboard service has no `.local` mount.
- Failure behavior: missing token → adapter fails closed (existing `RuntimeError`), diagnostic reports `token_present=false`.

### J20G-03 — Gmail diagnostic service + typed secret-free readiness report
- SP2 · Parallel: after J20G-02 · Model: Sonnet · Effort: high
- Objective: `adapters/gmail_diagnostic.py::GmailDiagnosticService(settings, client_factory=None).check() -> GmailReadinessReport` and CLI `gmail-diagnose [--json]`.
- Required behavior: `GmailReadinessReport(mode: Literal["REAL"], configured: bool, token_path: str (safe path only), token_present: bool, credentials_parseable: bool, refresh_ok: bool, api_canary_ok: bool, scopes: list[str], error_category: str | None, checked_at: datetime)`; non-interactive always (never `run_local_server`); canary = `users().getProfile(userId="me")` or `labels().list(maxResults=1)`; no token contents, no message bodies, no client secret anywhere in output or logs; `scopes` must equal the read-only scope or `error_category="SCOPE_MISMATCH"`.
- Tests: fake client for each outcome; output serialization contains no `ya29`, `refresh_token`, `client_secret` substrings (denylist assertion); interactive flow never invoked (spy).
- Failure behavior: every exception becomes a stable `error_category` (`TOKEN_MISSING|TOKEN_UNPARSEABLE|REFRESH_FAILED|API_CANARY_FAILED|SCOPE_MISMATCH|NOT_CONFIGURED`).

### J20G-04 — Health / worker / dashboard consume the readiness boundary
- SP2 · Parallel: after J20G-03 · Model: Sonnet · Effort: medium
- Objective: `HealthCheckService.check_gmail()` calls the diagnostic (injectable) and maps: REAL + all ok → HEALTHY; configured but failing → DEGRADED with category; not configured → DEGRADED `NOT_CONFIGURED`; worker finalize metadata records `gmail_mode` (`REAL|MOCK|UNAVAILABLE`), `last_real_ingestion_at`, `last_reconciliation_at`, `last_error_category`; `/api/health` and `/api/worker` expose them.
- Required behavior: registered/mock adapters never produce `gmail_mode == "REAL"`; health never reads token values; scheduled runs never trigger OAuth.
- Tests: mock adapter → `MOCK`; injected failing report → DEGRADED; dashboard JSON includes the fields; no secret substrings.

## 2. A-V20-CONTROL-CENTER (Lane 3)

### J20-01 — Endpoint inventory reconciliation
- SP1 · Model: Haiku · Effort: low
- Objective: record in the card the mapping acceptance item → existing endpoint (new jobs/shortlist/review queue → `/api/jobs`, `/api/reviews`; pipeline → `/api/kanban`; communication timeline → `/api/timeline`; interviews → `/api/interviews`; follow-ups → `/api/followups`; offers/rejections → `/api/offers-rejections`; audit → `/api/audit`; Gmail/source/worker health → `/api/health`, `/api/worker` (Gmail after J20G-04); policy + kill switch → `/api/policies`, `/api/health`; safe config → **missing** → J20-02). Output: gap list of exactly the missing items.

### J20-02 — Safe non-secret config view
- SP1 · Model: Sonnet · Effort: medium
- Objective: GET `/api/config` returning an allowlisted view: job-search thresholds/weights, polling cadence, policy registry summary (platform/decision/review_due_at), model-routing task names with `configured: bool` (never model keys/URLs), kill-switch env presence booleans, dashboard write-gate mode (`token|loopback`), `environment`. Never paths, secrets, or token indicators beyond booleans.
- Tests: denylist regex on the response (`secret|token|password|/home/|\.local`) ; allowlist keys exact.

### J20-03 — Source/worker/policy status completeness
- SP1 · Model: Sonnet · Effort: low
- Objective: `/api/worker` adds `last_reconciliation_at`, `last_error_category`, `last_gmail_mode` (from J20G-04 metadata when present); `/api/policies` adds `expired: bool` per row.
- Tests: fields present; expired computed against `review_due_at`.

### J20-04 — Operator-flow regression tests
- SP1 · Model: Haiku/Sonnet · Effort: low
- Objective: parametrized smoke test over all GET endpoints (200 + JSON); POST resolve: 404 unknown task, 400 invalid UUID, 403 non-loopback without token, 403 wrong token, 200 with token; document in the test that GET endpoints are unauthenticated by design (loopback binding).

### J20-15 — Record a manually submitted application (user attestation)
- SP2 · Model: Sonnet · Effort: high · Pending lead decision D5
- Objective: `lifecycle/manual_application.py::ManualApplicationService(session).record(job_id, *, resume_variant_id=None, packet_id=None, submitted_at, destination_domain=None, attestation_note, actor, allow_duplicate=False) -> ApplicationModel` and CLI `record-manual-application --job-id ... (--resume-variant-id | --packet-id) --submitted-at ISO --note "..."`.
- Why: MANUAL_ONLY destinations (LinkedIn/Indeed) and any application the user submits by hand currently leave no lifecycle record, so V2.0/V2.3 cannot attribute outcomes without V1.6.
- Required behavior: exactly one of `resume_variant_id`/`packet_id` (packet supplies the variant; never guess a variant); destination from argument or `job.apply_url` domain; `policy_decision`/`policy_version` from `PolicyEvaluator`; `ApplicationModel(application_mode="manual", status="SUBMITTED", applied_at=submitted_at, last_activity_at=submitted_at)`; `ApplicationEventModel(event_type="APPLICATION_SUBMITTED_USER_ATTESTED", source="user_attestation", source_reference=f"user:{actor}:{submitted_at.isoformat()}", payload_json={"attestation_note": note[:500], "resume_variant_id": ..., "packet_id": ...}, actor=actor)`; `AuditLogModel(action_type="manual_application_recorded", ...)`; an existing non-terminal application for the job → `DuplicateApplicationError` unless `allow_duplicate=True` (then audited with reason); later `APPLICATION_CONFIRMATION` email may move it to `CONFIRMED` through the existing lifecycle path.
- Non-goals: no external action; no status beyond SUBMITTED; no inference of resume used.
- Tests: rows created; analytics funnel counts it as a real submission (`_is_real_submission` true for mode `manual`); duplicate refused; both/none of variant/packet → error; confirmation email later transitions to CONFIRMED idempotently.
- Failure behavior: validation errors raise; nothing written.

### J20-16 — Offer decision / withdrawal recording
- SP1 · Model: Sonnet · Effort: medium
- Objective: `LifecycleEngine.record_user_decision(application_id, decision: Literal["ACCEPT","DECLINE","WITHDRAW"], actor, note=None)` and CLI `lifecycle-decide`.
- Required behavior: ACCEPT/DECLINE only from `OFFER_RECEIVED` → `OFFER_ACCEPTED`/`OFFER_DECLINED`; WITHDRAW from any non-terminal → `WITHDRAWN`; event `source="user_decision"`, `source_reference=f"user:{actor}:{now}"`; audit; terminal protection unchanged; `closed_at` set.
- Tests: allowed/disallowed transitions; subsequent rejection email on an accepted offer still routes to review (existing behavior).

## 3. A-V20-RELIABILITY (Lane 3)

### J20-05 — Gap audit record · SP1 · Haiku — record in the card: restore proceeds without checksum; backup default password; no FK indexes; reconciliation timestamp in memory; single-worker assumption (no lock) accepted as design with compose evidence.
### J20-06a — Restore checksum fails closed · SP1 · Sonnet — `scripts/restore_db.sh`: missing/invalid `.sha256` → exit 2 unless `--allow-missing-checksum` (prints an audit line to stderr); `docs/RECOVERY.md` drill steps; shell test via `bash -n` + a bats-free pytest that runs the script against a temp file.
### J20-06b — No default DB credential in backup/restore · SP1 · Sonnet — require `DATABASE_URL` or `DB_PASSWORD`; exit 2 otherwise; never echo values.
### J20-08 — Health/recovery regression coverage · SP1 · Sonnet — tests for per-platform kill switch env vars, `check_gmail` with injected reports (J20G-04), `WORKER_STALE_RUN_THRESHOLD_SECONDS` override, degraded aggregation order.
### J20-12 — Local CI parity script
- SP1 · Model: Sonnet · Effort: low · Pending lead decision D6
- Objective: `scripts/local_ci.sh` runs exactly the CI steps: `ruff check .`, `mypy src tests`, `bash scripts/verify_migrations.sh` if `DATABASE_URL` is set else prints `migrations=SKIPPED_NO_DATABASE_URL`, `pytest -q`; prints one summary line `INDEPENDENT_SANDBOX_VALIDATION sha=<git rev-parse HEAD> python=<x.y.z> ruff=PASS|FAIL mypy=PASS|FAIL migrations=PASS|FAIL|SKIPPED pytest=<n passed>`; non-zero exit on any failure; documented in `docs/RECOVERY.md` and referenced by lane handoffs when `CI_BLOCKED_ACCOUNT`.
### J20-17 — Fail-closed model gateway factory
- SP2 · Model: Sonnet · Effort: high
- Objective: `adapters/models.py::build_model_gateway(routing: ModelRoutingConfig, settings: AppSettings, *, mode: Literal["production","test"]) -> ModelGateway`.
- Required behavior: production: if any task has a non-null model and gateway credentials exist → `LiteLLMModelGateway` (lazy import; missing `litellm` or credentials → `ModelGatewayUnavailableError`, **no silent fallback**); if no task configured → `DeterministicModelGateway`; `MockModelGateway` only when `mode="test"`; `prepare-packets` CLI uses the factory (`--allow-mock` flag only sets `mode="test"` and prints a MOCK banner); generation metadata records `model_provider`/`model_name`/`model_origin ∈ {deterministic, real, mock}` truthfully.
- Tests: null config → deterministic; configured without litellm → error; mock forbidden in production; CLI default never mock.
### J20-18 — Existing FK indexes (optional) · SP1 · Sonnet — migration `006_existing_fk_indexes` adding indexes on every FK column of the 19 pre-existing tables; downgrade drops them; no model behavior change.
### J20-19 — Real freshness dimension · SP1 · Sonnet — `SemanticScorer` freshness `raw_score = clamp(1 - age_days/30, 0, 1)` from `posted_at or first_seen_at`; adjust fixtures so existing shortlist/reject tests keep their decisions; new test for old postings.
### J20-20 — Job snapshot in packet metadata · SP1 · Sonnet — `ApplicationPacketBuilder` writes `generation_metadata_json["job_description_hash"]`, `["job_title_snapshot"]`, `["apply_url_snapshot"]`; no migration; test asserts presence; consumed by V23-II-03 staleness.

## 4. A-V20-ANALYTICS (Lane 3)

### J20-09 — Analytics reconciliation · SP1 · Haiku — record in the card: implemented (source, role family, resume variant, response/screen/interview/final/offer/acceptance rates, time-to-stage, N and low-sample notes, descriptive wording, simulation exclusion); gaps: recency window (J20-10), shared role-family definition (J20-11), family rollup (V23-SL-02).
### J20-10 — Recency windows · SP1 · Sonnet — `window_days: int | None = None` on the five performance methods and the funnel; outputs gain `window_start/window_end`; default preserves current all-time behavior and tests.
### J20-11 — Adopt `RoleFamilyClassifier` · SP1 · Sonnet — after V23-F04; `get_role_family_performance` groups by classifier output; update tests; wording unchanged.

## 5. A-V20-INTEGRATION-FIXTURE

### J20I-01 — Golden engineering scenario
- SP2 · Model: Sonnet · Effort: high
- Objective: `tests/integration/test_v20_golden_scenario.py` implementing steps 1–17 of `V2_0_INTEGRATION_FIXTURE.md` with `MockEmailAdapter` fixtures, `MockBrowserRunner` (labeled simulation), deterministic gateway, SQLite; trace id per run; assertions per step (dedupe replay, packet hash/immutability, unresolved EEO, application in manual/assisted test mode, confirmation link, recruiter contact, interview with explicit timestamp, duplicate replay no-op, outbound reply resolves task, rejection/offer without regression, dashboard JSON for job/application/contact/interview/review/audit, analytics funnel + resume variant, health with last run + policy/kill switch).
- Tests: the scenario itself; runtime < 30 s.

### J20I-02 — Machine-readable integration report · SP1 · Sonnet — `artifacts/reports/v20_engineering_campaign_report.json` (gitignored path) with `trace_id, fixture_version, code_sha, entities, source_refs, idempotency_assertions, packet_hashes, lifecycle_events, dashboard_checks, analytics_checks, health_checks, result, simulated=True`; schema test.
### J20I-03 — Replay and out-of-order cases · SP1 · Sonnet — same-message replay; interview email before confirmation email (regression prevention); duplicate recruiter thread; late rejection after offer (review routing).

## 6. Live items (`USER_GATE`; never self-authorized)

- G-01 USER_GATE owner performs OAuth consent per `GMAIL_CANARY_RUNBOOK.md` (token in `.local/`, never committed).
- G-02 SP1 `gmail-diagnose` then `poll-emails --dry-run` bounded window; evidence: counts, classifications, checkpoint unchanged, `mock_fixtures=false`.
- G-03 LIVE bounded persisted canary; provider ids preserved.
- G-04 LIVE rerun same window; prove idempotency (no duplicates/no losses).
- G-05 SP1 redacted canary report → A-V12-GMAIL-CANARY / A-V20-LIVE-INGESTION lead review.
- C1..C5 LIVE campaigns per `V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`; Campaign 3 uses the assisted path (after V1.5 acceptance + browser gate) **or** a user-attested manual application (J20-15) — no system submission required (master plan D1/D9).
- Labels: `ENGINEERING_READY` when all J20/J20G/J20I engineering is accepted; `LIVE_ACCEPTED` only by ChatGPT after the campaigns.

## 7. Mapping from legacy V20-* prep rows

| Legacy | Canonical |
|---|---|
| V20-CC01..CC06 | J20-01, J20-04, (J20-02 for CC06); CC02–CC05 already exist on main → verified by J20-01 |
| V20-R01 migration verification | `scripts/verify_migrations.sh` exists; J20-12 wires it into local parity |
| V20-R02 backup/restore drill | J20-06a/06b |
| V20-R03 parser regression corpus | R17-E03 (plaintext fallbacks); broader corpus deferred |
| V20-R04 model/provider fail-closed | J20-17 |
| V20-R05 policy expiry reminders | J20-03 (`expired` flag) + existing health check |
| V20-R06 recovery runbooks | `docs/RECOVERY.md` updates in J20-06a/J20-12 |
| V20-A01..A05 | J20-09, J20-10, J20-11, V23-SL-02 |
| V20-G01..G03 | J20G-03, J20G-01, J20G-04 |
| V20-X01..X03 | J20I-01..03 |

Totals: 25 engineering tasks ≈ 32 SP (SP2: J20G-01..04, J20-15, J20-17, J20I-01; the rest SP1); live items G-01..05, C1..C5.

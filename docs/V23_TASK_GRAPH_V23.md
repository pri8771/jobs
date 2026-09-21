# V2.3 Task Graph — Intelligence Layer, Tool Layer, Briefing, Campaign

- Status: PROPOSED (lead review required before promotion into `coordination/WORK_QUEUE.md`)
- Parent plan: `docs/V23_MASTER_PLAN.md`
- Contracts: `docs/V2_3_SPEC.md`, `V2_3_ACCEPTANCE_MATRIX.md`, `V2_3_OPPORTUNITY_GRAPH_SCHEMA.md`, `V2_3_OPPORTUNITY_GRAPH_CONTRACT.md`, `V2_3_STRATEGY_LEARNING_CONTRACT.md`, `V2_3_TARGET_COMPANY_WATCH.md`, `V2_3_INTERVIEW_INTELLIGENCE_CONTRACT.md`, `V2_3_AGENT_TOOL_LAYER.md`, `V3_TOOL_PERMISSION_MATRIX.md`, `V3_RUNTIME_DATA_CONTRACTS.md`
- Supersedes the coarse SP3–SP5 rows V23-G0x/S0x/T0x/I0x/TL0x in `coordination/PREP_QUEUE_V16_TO_V30.md` (mapping in §9)

## 0. Conventions every task in this file shares

- Branch: one V2.3 work surface (proposed `worker/v23-intelligence`, created from current `main`; lead decides lane per D3). Heartbeat per `coordination/HEARTBEAT_PROTOCOL.md`.
- Python 3.12, Pydantic v2 models with `model_config = ConfigDict(extra="forbid")`, SQLAlchemy 2.0 typed mappings, `UTCDateTime` from `db/base.py`, UUID PKs via `generate_uuid()`, `JSONType` variant as in `db/models.py`.
- Quality gate for every task: `ruff check .`, `mypy src tests` (strict), `pytest -q` all green; new tests use SQLite in-memory + `Base.metadata.create_all()` like existing tests; no network in tests (public-source clients are exercised through injected fake transports).
- No LLM calls. No external side effects. No mock result may be labeled real; every derived object carries `simulated`/`origin` labels where relevant.
- Every derived output inherits `DerivedArtifactEnvelope` (V23-F01). Every persisted V2.3 row that represents a relationship or observation carries `source_type`, `source_reference`, `observed_at`.
- CLI commands added by this graph live in a new `src/jobs_automation/cli/intelligence_cli.py` (click group `intel`, plus top-level aliases) registered with a single `cli.add_command(...)` line in `cli/main.py`.
- Dashboard endpoints added by this graph are read-only GET handlers in `dashboard/server.py` following the existing `_send_json` pattern; no new write endpoints.
- "Model" = minimum recommended worker model; "Effort" = suggested reasoning effort. "Parallel" = may run concurrently with other tasks whose write surfaces do not overlap.
- Acceptance evidence for every task: commit SHA on the V2.3 branch, focused test names, full-suite counts, `INDEPENDENT_SANDBOX_VALIDATION` or CI result, `READY_FOR_LEAD_REVIEW` in the heartbeat. Workers never self-accept.

Task ordering (dependency-respecting): F01 → F02 → F03 → F04 → F05 → OG-01..10 → SL-01..07 → TW-01..07 → II-01..07 → TL-01..11 → CB-01..05 → AC-01..04. Groups OG/SL/TW/II are mutually parallel once F01–F05 exist; TL depends on the services it wraps; CB depends on OG/SL/TW/II; AC depends on CB.

---

## 1. Foundation (shared helpers; land first)

### V23-F01 — Derived-artifact envelope and shared value types
- Artifact: all A-V23-* · SP1 · Parallel: no (first) · Model: Sonnet · Effort: medium
- Objective: create `src/jobs_automation/intelligence/__init__.py` (if absent) and `src/jobs_automation/intelligence/envelope.py` with the shared typed base classes used by every V2.3 output.
- Why: V3 shared-memory contract requires derived summaries to be recomputable/invalidatable with source refs; strategy contract requires N with every rate. One base prevents five divergent shapes.
- Depends on: none.
- Code: new `intelligence/envelope.py`; tests `tests/test_v23_envelope.py`.
- Required behavior:
  - `EvidenceRef(ref_type: Literal["job","job_source","application","application_event","message","message_link","contact","company","interview","task","artifact","packet","resume_variant","evaluation","edge","observation","experiment","audit","public_source","candidate_field"], ref_id: str, note: str | None = None)`.
  - `ConfidenceLabel = Literal["LOW","MEDIUM","HIGH"]`.
  - `DerivedArtifactEnvelope(BaseModel)`: `artifact_type: str`, `generated_at: datetime` (tz-aware UTC), `generator: str` (module.Class), `generator_version: str` (semver string constant per service), `code_sha: str | None` (from `JOBS_AUTOMATION_CODE_SHA` env or `git rev-parse HEAD` best effort, else None), `source_refs: list[EvidenceRef]`, `confidence: ConfidenceLabel | None`, `warnings: list[str]`, `review_items: list[str]`, `valid_until: datetime | None`, `supersedes: str | None`, `stale: bool = False`, `simulated: bool = False`.
  - `RateWithN(BaseModel)`: `numerator: int`, `denominator: int`, `rate: float | None` (None when denominator == 0), `n: int` (= denominator), `min_n: int`, `low_n: bool` (= n < min_n), `window_days: int | None`, `window_start: datetime | None`, `window_end: datetime | None`, `evidence_class: Literal["DESCRIPTIVE","EXPERIMENTAL"] = "DESCRIPTIVE"`. Validator: `rate` must equal `numerator/denominator` rounded to 4 dp when denominator > 0; numerator ≤ denominator.
  - Helper `utc_now()` and `canonical_json_hash(obj) -> str` (sha256 of `json.dumps(sort_keys=True, separators=(",",":"), default=str)`).
- Non-goals: no persistence, no memory table, no LLM.
- Tests: envelope round-trip JSON; `RateWithN` zero-denominator → `rate None`, `low_n True`; validator rejects numerator > denominator; `canonical_json_hash` stable across key order.
- Failure behavior: validation errors raise `pydantic.ValidationError`; never coerce invalid rates.
- Output: module + tests.
- Acceptance evidence: tests pass; mypy strict clean.

### V23-F02 — Shared untrusted-text signal detector
- Artifact: A-V23-INTERVIEW-INTELLIGENCE, A-V15 (shared) · SP1 · Parallel: yes · Model: Sonnet · Effort: medium
- Objective: `src/jobs_automation/core/untrusted_text.py` exposing `detect_prompt_injection_signals(text: str, *, context: str) -> list[InjectionSignal]` with `InjectionSignal(pattern_id: str, excerpt: str (≤120 chars), severity: Literal["LOW","HIGH"], context: str)`.
- Why: page text, job descriptions, and public company content are attacker-controlled. V1.5 A-R15-06 and V2.3 interview intelligence need the same detector; one module prevents drift.
- Depends on: none. Coordination note: when Lane 2 ports A-R15-06 it must import this module instead of a private pattern list (see `V23_TASK_GRAPH_RECOVERY.md` A-R15-06).
- Code: new `core/untrusted_text.py`; tests `tests/test_untrusted_text.py`.
- Required behavior: case-insensitive regex families: instruction override ("ignore (all )?(previous|prior|above) instructions", "disregard .* rules"), role hijack ("you are (now )?an? (ai|assistant|agent)"), data exfil ("print|reveal|send .* (token|password|secret|api key)"), authority claims ("(mark|set|treat) .* as (submitted|approved|authorized|verified)"), hidden-instruction markers ("<!--.*(instruction|assistant).*-->", "system:"). HIGH for override/authority/exfil; LOW otherwise. Pure function, no I/O. Excerpts are truncated and never re-emitted as instructions.
- Non-goals: no ML classifier; no blocking policy here (callers decide).
- Tests: each family detected; benign JD text produces no signal; excerpt truncation; multiple signals ordered by position.
- Failure behavior: none (pure); empty string → `[]`.
- Output: module + tests.
- Acceptance evidence: tests pass.

### V23-F03 — Migration `005_v23_intelligence_foundation` + ORM models
- Artifact: A-V23-OPPORTUNITY-GRAPH, A-V23-TARGET-COMPANY-WATCH, A-V23-STRATEGY-LEARNING · SP2 · Parallel: no (schema window) · Model: Sonnet (Opus review of constraints recommended) · Effort: high
- Objective: add the additive V2.3 tables and one column, with real downgrade, mirrored in `db/models.py`.
- Why: persisted user-confirmed/invalidated edges, watch lists, observations and immutable experiment assignments have no home in the current schema; everything else V2.3 needs already exists.
- Depends on: V23-F01 (for shared literal vocabularies; enums stay strings in DB per project convention).
- Code: `migrations/versions/005_v23_intelligence_foundation.py` (`down_revision = "004_v16_submission_truth"`), `db/models.py`, `db/__init__.py` exports, `docs/DATA_MODEL.md` section, tests `tests/test_v23_schema.py`.
- Required behavior (exact columns; all timestamps `UTCDateTime`, all ids UUID):
  - `opportunity_edge`: `id` PK; `subject_type` String(32) NOT NULL; `subject_id` UUID NOT NULL; `predicate` String(64) NOT NULL; `object_type` String(32) NOT NULL; `object_id` UUID NOT NULL; `source_type` String(32) NOT NULL (vocabulary: `USER_CONFIRMATION|MESSAGE|APPLICATION|JOB_SOURCE|PUBLIC_SOURCE|IMPORTED_CONTACT|MODEL_INFERENCE`); `source_reference` String(512) NOT NULL; `method` String(64) NOT NULL; `confidence` Float NOT NULL; `inferred` Boolean NOT NULL server_default true; `evidence_hash` String(64) NULL; `observed_at` NOT NULL; `valid_from` NOT NULL; `valid_to` NULL; `status` String(32) NOT NULL server_default `'REVIEW_REQUIRED'` (vocabulary `ASSERTED|REVIEW_REQUIRED|INVALIDATED`); `invalidated_reason` String(255) NULL; `created_by` String(64) NOT NULL; `created_at` NOT NULL; `updated_at` NOT NULL. Unique `(subject_type, subject_id, predicate, object_type, object_id, source_type, source_reference)` named `uq_opportunity_edge_evidence`. Indexes: `(subject_type, subject_id)`, `(object_type, object_id)`, `(predicate, status)`, `source_reference`.
  - `message_link.contact_id`: UUID NULL FK `contact.id`, index `ix_message_link_contact_id`. ORM: `MessageLinkModel.contact_id` + relationship `contact`.
  - `target_company`: `id`; `company_id` UUID NULL FK `company.id`; `canonical_name` String(255) NOT NULL UNIQUE; `domain` String(255) NULL; `priority` Integer NOT NULL server_default 3; `reason` Text NULL; `target_role_families` JSON NOT NULL default `[]`; `compensation_floor` Numeric(12,2) NULL; `location_constraints` JSON NOT NULL default `{}`; `watch_status` String(16) NOT NULL server_default `'PAUSED'` (`ACTIVE|PAUSED|ARCHIVED`); `source_config` JSON NOT NULL default `{}` (keys: `greenhouse_board_token`, `lever_site`); `created_at`, `updated_at`. Index `watch_status`.
  - `target_company_observation`: `id`; `target_company_id` FK NOT NULL; `observation_type` String(32) NOT NULL (`NEW_ROLE|ROLE_CLOSED|ROLE_CHANGED|RECRUITER_SIGNAL|CAREER_PAGE_UPDATE|USER_NOTE|SOURCE_UNAVAILABLE`); `source_type` String(32) NOT NULL; `source_reference` String(512) NOT NULL; `observed_at` NOT NULL; `confidence` Float NOT NULL; `normalized_payload` JSON NOT NULL default `{}`; `dedupe_key` String(128) NOT NULL; `job_id` UUID NULL FK `job.id`; `status` String(16) NOT NULL server_default `'NEW'` (`NEW|ACKNOWLEDGED|SUPPRESSED`); `created_at`. Unique `(target_company_id, dedupe_key)`; index `(target_company_id, observed_at)`, `job_id`.
  - `strategy_experiment`: `id`; `name` String(128) NOT NULL UNIQUE; `hypothesis` Text NOT NULL; `target_population_json` JSON NOT NULL default `{}`; `metric_definition_json` JSON NOT NULL default `{}`; `status` String(16) NOT NULL server_default `'DRAFT'` (`DRAFT|ACTIVE|ENDED`); `created_by` String(64) NOT NULL; `created_at`; `started_at` NULL; `ended_at` NULL.
  - `strategy_experiment_assignment`: `id`; `experiment_id` FK NOT NULL; `job_id` FK `job.id` NOT NULL; `application_id` FK `application.id` NULL; `treatment_type` String(64) NOT NULL; `resume_variant_id` FK `resume_variant.id` NULL; `treatment_payload_json` JSON NOT NULL default `{}`; `treatment_hash` String(64) NOT NULL; `assigned_at` NOT NULL. Unique `(experiment_id, job_id)`; index `application_id`.
  - Downgrade drops the five tables and the column/index in reverse order.
- Non-goals: no FK indexes on pre-existing tables (that is J20-18); no enum types; no data backfill.
- Tests: `create_all` includes the new tables; unique constraints raise `IntegrityError` (edge evidence duplicate; observation dedupe duplicate; assignment duplicate); server defaults observed on insert (`status == "REVIEW_REQUIRED"`, `inferred is True`, `watch_status == "PAUSED"`); Alembic script compiles (`alembic heads` includes `005_v23_intelligence_foundation` as the single head after 004 via `scripts/verify_migrations.sh` when Postgres is available; document `CI_BLOCKED_ACCOUNT`/no-Postgres fallback).
- Adversarial: inserting an edge without `source_reference` fails (NOT NULL); inserting a target company without `canonical_name` fails.
- Failure behavior: migration errors abort; no partial state (single Alembic transaction on Postgres).
- Output: migration, models, doc section, tests.
- Acceptance evidence: tests; `scripts/verify_migrations.sh` output when Postgres available; lead review of column list against this spec.

### V23-F04 — Shared role-family classifier
- Artifact: A-V23-STRATEGY-LEARNING, A-V20-ANALYTICS · SP1 · Parallel: yes · Model: Sonnet · Effort: medium
- Objective: `intelligence/role_family.py::RoleFamilyClassifier` with `classify(title: str) -> str` and `families() -> list[str]`, sourced from the same keyword tables `preparation/tailoring.py::ResumeVariantSelector` uses plus the candidate profile's target titles; then make `dashboard/analytics.py::get_role_family_performance` use it (behavior-preserving default: unknown → `"other"`).
- Why: strategy learning, watch matching and analytics must agree on what a "role family" is; today analytics groups differently from the resume selector.
- Depends on: none (coordinate with PG3 owner of `analytics.py`; if PG3 is mid-change, land the classifier first and let PG3 adopt it under J20-11).
- Code: new `intelligence/role_family.py`; `preparation/tailoring.py` (expose the keyword table as a module constant, no behavior change); `dashboard/analytics.py` (J20-11); tests `tests/test_role_family.py`.
- Required behavior: deterministic, case-insensitive keyword→family mapping; longest-match wins; optional `overrides: dict[str,str]` loaded from `config/job_search.yaml` key `role_family_overrides` (additive, optional).
- Non-goals: no ML; no title normalization beyond lowercase/punctuation strip (reuse `ingestion/deduplication.normalize_string`).
- Tests: known titles map; unknown → `other`; override wins; selector and classifier agree on the five canned variant families.
- Failure behavior: never raises on odd input; empty title → `other`.
- Output: module + adoption diff + tests.

### V23-F05 — Candidate evidence service (A-V12-CANDIDATE-PROVENANCE minimal)
- Artifact: A-V12-CANDIDATE-PROVENANCE, A-V23-INTERVIEW-INTELLIGENCE, A-V23-OPPORTUNITY-GRAPH · SP2 · Parallel: yes · Model: Sonnet · Effort: high
- Objective: `intelligence/candidate_evidence.py::CandidateEvidenceService(profile: CandidateProfileConfig)` producing typed, private-safe evidence refs for skills, employment, projects, education and target preferences, each with a provenance class and `allowed_for_application`.
- Why: story maps and "skills evidenced by projects" must never exceed canonical candidate truth; A-V12 defines the record shape and has no implementation.
- Depends on: V23-F01.
- Code: new `intelligence/candidate_evidence.py`; optional additive `provenance:` section support in `core/candidate_profile.py` (per-field `provenance_class`, `source_reference`, `verified_at`, `reviewer`); tests `tests/test_candidate_evidence.py` using `config/candidate_profile.example.yaml` **only as a test fixture** (never as truth in runtime paths).
- Required behavior:
  - `CandidateEvidenceRef(field_path: str, present: bool, provenance_class: Literal["user_confirmed","source_document","inferred","unknown"], source_reference: str | None, verified_at: datetime | None, reviewer: str | None, allowed_for_application: bool, value_fingerprint: str | None)` — `value_fingerprint` = sha256 of the value, never the raw value.
  - Defaults: field present in the private profile → `user_confirmed`, `allowed_for_application=True`; absent → `unknown`, False; demographic/EEO field paths → always `allowed_for_application=False`; anything the caller marks model-derived → `inferred`, False.
  - Methods: `skills() -> list[SkillEvidence(skill, evidence_refs, projects: list[str], employers: list[str])]`, `projects() -> list[ProjectEvidence(name, skills, evidence_ref)]`, `evidence_for_requirement(text) -> list[CandidateEvidenceRef]` (keyword match against skills/projects; deterministic), `allowed_claims_for(field_paths) -> list[str]` returning only literal profile values marked allowed (raw values are returned in-process only, never persisted or logged by this service).
- Non-goals: no persistence; no Git-committed private values; no inference of new facts.
- Tests: example profile → refs with fingerprints and no raw values in serialized output of refs; EEO paths never allowed; `evidence_for_requirement("kubernetes")` returns matching skill refs only; unknown requirement → empty list.
- Adversarial: requirement text containing injection phrases produces no evidence and no exception.
- Failure behavior: missing profile → raises `FileNotFoundError` from the existing loader (fail closed); never substitutes the example profile at runtime.
- Output: module + tests.

---

## 2. A-V23-OPPORTUNITY-GRAPH

Base: Lane D `origin/worker/v23-foundations:src/jobs_automation/intelligence/opportunity_graph.py` and `tests/test_v23_opportunity_graph.py` (audit verdict `REUSE_WITH_REPAIR`; runs green on current main).

### V23-OG-01 — Port Lane D module verbatim
- SP1 · Parallel: no (base for OG-02..10) · Model: Sonnet · Effort: low
- Objective: copy the two files onto the V2.3 branch unchanged except import path fixes; add `intelligence/__init__.py` exports.
- Why: 933 LOC of contract-aligned projection already exists and passes on main.
- Depends on: V23-F01.
- Code: `git show origin/worker/v23-foundations:<path>` for the three files; commit message cites source commit `d99e774`.
- Required behavior: `pytest tests/test_v23_opportunity_graph.py` passes; ruff/mypy clean; no functional edits in this task.
- Tests: existing single test.
- Acceptance evidence: diff shows only the three files plus `__init__` exports.

### V23-OG-02 — Edge evidence fields
- SP1 · Parallel: after OG-01 · Model: Sonnet · Effort: medium
- Objective: add `observed_at: datetime`, `method: str`, `inferred: bool` to `OpportunityEdge`; populate from `MessageLinkModel.method`/`confidence`/`created_at` for message-derived edges and from FK semantics (`method="fk_projection"`, `inferred=False`, `observed_at=<row created/first_seen>`) for structural edges.
- Why: contract §"Evidence fields on derived edges" requires all six; Lane D has three.
- Code: `intelligence/opportunity_graph.py`; tests.
- Required behavior: every edge in `project_graph()` has the six fields; FK-derived edges are `ASSERTED`, `inferred=False`; message-derived edges with `confidence < 0.8` are `REVIEW_REQUIRED` and `inferred=True`.
- Tests: assert fields on `HAS_JOB`, `USED_RESUME`, `CONTACT_TOUCHED_APPLICATION`; a link with `confidence=0.6` yields `REVIEW_REQUIRED`.
- Failure behavior: missing timestamps fall back to the projection `as_of` parameter (OG-07), never wall-clock inside loops.

### V23-OG-03 — Job status vocabulary and exact contact matching
- SP1 · Parallel: after OG-01 · Model: Sonnet · Effort: medium
- Objective: replace the `("discovered","evaluated","shortlisted")` filter with the real open set `{"discovered","needs_review","shortlisted","packet_prepared","packet_prepared_review_needed"}` exposed as `OPEN_JOB_STATUSES` in `evaluation/engine.py` (single source of truth, importable); replace substring email matching with exact normalized address comparison using `lifecycle/crm.py::RecruiterCRMService.parse_sender`; any contact→application edge produced by address matching (not by `message_link.contact_id`) is `inferred=True`, `method="sender_address_match"`.
- Why: audit found a dead status branch and a false-positive substring heuristic.
- Code: `intelligence/opportunity_graph.py`, `evaluation/engine.py` (constant only), tests.
- Tests: `an@acme.com` does not match `jordan@acme.com`; `needs_review` job appears in open opportunities; `evaluated` no longer referenced.
- Adversarial: uppercase/whitespace variants of the same address match; display-name-only sender yields no edge.

### V23-OG-04 — Contract naming and isolation tests
- SP1 · Parallel: after OG-02 · Model: Haiku/Sonnet · Effort: low
- Objective: rename `applications_for_contact` → `applications_with_contact` (keep a deprecated alias for one release); add tests: multi-company isolation (edges never cross companies), same evidence twice → one edge, `REVIEW_REQUIRED` path, `resume_outcomes_for_role_family` with zero matches returns empty typed list, "screenings" metric counts only `SCREENING` reached (use `ApplicationEventModel` history, not current status).
- Code: `intelligence/opportunity_graph.py`, tests.

### V23-OG-05 — `message_link.contact_id` writes and backfill
- SP2 · Parallel: after F03 · Model: Sonnet · Effort: high
- Objective: populate the new `message_link.contact_id` (a) going forward in `lifecycle/engine.py` where recruiting messages are linked (use `RecruiterCRMService.get_or_create_contact` result), (b) via a one-off idempotent backfill service `intelligence/edges.py::backfill_message_link_contacts(session) -> BackfillReport` (match by exact sender address to existing contacts only; never create contacts during backfill), and (c) CLI `intel backfill-contact-links [--dry-run]`.
- Why: removes the need for sender-string heuristics; makes `contact TOUCHED application` an FK-backed, `inferred=False` edge.
- Depends on: V23-F03.
- Code: `lifecycle/engine.py` (minimal additive change; coordinate with PG3), `intelligence/edges.py`, `cli/intelligence_cli.py`, tests in `tests/test_lifecycle.py` (one new test) and `tests/test_v23_edges.py`.
- Required behavior: forward path sets `contact_id` when the message sender resolves to a contact; backfill is idempotent (second run reports 0 changes); dry-run writes nothing.
- Tests: new lifecycle test asserts `contact_id` set; backfill idempotency; ambiguous sender (two contacts same email — should not exist, but guard) → skipped with report entry.
- Failure behavior: unresolved sender → `contact_id` stays NULL; never guesses.

### V23-OG-06 — OpportunityEdgeService (persisted evidence edges)
- SP2 · Parallel: after F03 · Model: Sonnet (Opus review) · Effort: high
- Objective: `intelligence/edges.py::OpportunityEdgeService(session)` with `propose(edge: EdgeProposal) -> OpportunityEdgeModel` (always `REVIEW_REQUIRED`, `inferred=True` unless `source_type == "USER_CONFIRMATION"`), `confirm(edge_id, actor) -> ...` (sets `ASSERTED`, `inferred=False`, `source_type="USER_CONFIRMATION"` evidence row added, audit log), `invalidate(edge_id, reason, actor)` (sets `INVALIDATED`, `valid_to=now`, audit), `active_edges(subject|object filters)`.
- Why: contract requires user-confirmed relationships to become truth and invalidated evidence to disappear; a stateless projection cannot remember either.
- Depends on: V23-F03, F01.
- Code: `intelligence/edges.py`; tests `tests/test_v23_edges.py`.
- Required behavior: provenance mandatory (`source_type`, `source_reference`, `method`, `observed_at`); duplicate evidence (same unique key) returns the existing row (no IntegrityError leak); `MODEL_INFERENCE` can never be confirmed without a `USER_CONFIRMATION` evidence row; every state change writes `AuditLogModel(action_type="opportunity_edge_" + verb, entity_type="opportunity_edge", entity_id=edge.id, actor=..., metadata_json={prior_status,new_status,reason})`.
- Tests: propose→confirm→invalidate lifecycle; duplicate proposal idempotent; model inference cannot self-assert; audit rows present.
- Adversarial: `confirm` with `actor="system"` rejected (must be a user actor string not equal to `system`); invalidated edge cannot be re-confirmed without a new proposal.
- Failure behavior: raises `EdgeStateError`; no partial writes (single transaction).

### V23-OG-07 — Projection merges persisted edges; deterministic rebuild
- SP1 · Parallel: after OG-06 · Model: Sonnet · Effort: medium
- Objective: `OpportunityGraphService.project_graph(as_of: datetime | None = None)` unions FK-derived edges with `opportunity_edge` rows where `status != INVALIDATED` and `valid_from <= as_of < coalesce(valid_to, ∞)`; persisted edges override derived ones with the same `(subject,predicate,object)` when `ASSERTED`; `as_of` replaces every `now()` fallback so two rebuilds with the same `as_of` are byte-identical.
- Tests: rebuild equality on full JSON dump; invalidated edge absent; confirmed edge present as `ASSERTED`; `as_of` in the past excludes later edges.

### V23-OG-08 — Remove N+1 queries
- SP1 · Parallel: after OG-01 · Model: Sonnet · Effort: medium
- Objective: batch the per-variant and per-job queries in `resume_outcomes_for_role_family` and `open_opportunities_with_relationship_signal` into ≤3 queries each (prefetch applications by variant ids; prefetch contacts/prior applications by company ids).
- Tests: existing behavior unchanged; add a query-count assertion using SQLAlchemy `event.listen(engine, "before_cursor_execute")` ≤ 5 for a 20-job fixture.

### V23-OG-09 — Skill/project evidence nodes
- SP1 · Parallel: after F05 · Model: Sonnet · Effort: medium
- Objective: add node types `skill`, `project`, `candidate_evidence` and predicates `EVIDENCES` (project→skill) and `REQUIRES` (job→skill via `SemanticScorer` keyword extraction, `inferred=True`, `method="keyword_match"`, source = job description hash); implement `skills_evidenced_by_projects()` from `CandidateEvidenceService`. No persistence.
- Tests: fixture profile projects → `EVIDENCES` edges; job requiring an unevidenced skill shows as a gap in `open_opportunities_with_relationship_signal` output field `skill_gaps`.

### V23-OG-10 — Graph CLI
- SP1 · Parallel: after OG-07 · Model: Sonnet · Effort: low
- Objective: `intel graph company <id> [--json]`, `intel graph contact <id> [--json]`, `intel edges propose|confirm|invalidate ...` (user actions), printing typed JSON with evidence refs.
- Tests: click runner smoke tests with SQLite fixture.

---

## 3. A-V23-STRATEGY-LEARNING

### V23-SL-01 — Strategy guardrails config
- SP1 · Parallel: yes · Model: Sonnet · Effort: low
- Objective: `StrategyGuardrails(BaseModel)` in `intelligence/strategy.py`: `min_n_descriptive=5`, `min_n_comparison=10`, `min_n_per_arm=5`, `default_window_days=90`, `stale_after_days=180`; optional additive section `strategy_guardrails:` in `config/job_search.yaml` (`core/job_search.py`), defaults when absent.
- Tests: defaults; override from YAML; negative values rejected.

### V23-SL-02 — StrategyLearningService rates with N and windows
- SP2 · Parallel: after SL-01, F04 · Model: Sonnet · Effort: high
- Objective: `StrategyLearningService(session, guardrails, role_family_classifier)` returning typed `RateWithN` sets: `resume_strategy(window_days) -> list[ResumeStrategyRow(resume_family, resume_variant_id|None (None = family rollup, explicitly labeled), version, response, screen, interview, offer: RateWithN, similar_role_family: str|None)]`, `source_strategy(window_days)`, `role_strategy(window_days)` (funnel + compensation distribution min/median/max from `job.compensation_*` + location/remote outcomes + top reject reason codes from `job_evaluation.reason_codes_json`), `company_strategy(window_days)` (median hours to first inbound response computed from `application.applied_at` → first linked inbound message `received_at`; recruiter engagement = distinct contacts with `message_link.contact_id`; repeat role patterns = count of jobs per company in window).
- Why: contract outputs; reuse `FunnelAnalyticsService` real-submission filters and historical-outcome logic (import and call; do not duplicate).
- Code: `intelligence/strategy.py`; `dashboard/analytics.py` gains `window_days: int | None` parameters (J20-10, coordinate with PG3); tests `tests/test_v23_strategy.py`.
- Required behavior: every rate is a `RateWithN` with `window_*` set; variants are never merged across `version` unless the caller requests family rollup and the row is labeled `rollup=True`; applications with simulation modes excluded (reuse `_is_real_submission`).
- Tests: fixture with 3 variants across 2 families; window excludes old applications; rollup labeled; no rate without N.
- Failure behavior: empty data → rows with `n=0`, `rate=None`; never raises for sparse data.

### V23-SL-03 — StrategyRecommendation object and rule engine
- SP1 · Parallel: after SL-02 · Model: Sonnet · Effort: medium
- Objective: `StrategyRecommendation(DerivedArtifactEnvelope)`: `subject_type: Literal["resume_family","resume_variant","source","role_family","company"]`, `subject_id: str`, `action: Literal["PREFER","DEPRIORITIZE","CONTINUE","GATHER_MORE_DATA"]`, `rationale: str` (templated, cites numbers), `rates: list[RateWithN]`, `comparison_to: str | None`, `reversible: bool = True`; rule: any `low_n` → `GATHER_MORE_DATA`, `confidence="LOW"`; comparison requires both arms ≥ `min_n_per_arm` and total ≥ `min_n_comparison`; difference in interview rate ≥ 0.15 absolute → `PREFER`/`DEPRIORITIZE` with `confidence="MEDIUM"` (never HIGH for `DESCRIPTIVE`); `EXPERIMENTAL` rows may reach `HIGH` only when experiment status `ENDED` and arms meet thresholds.
- Tests: N=1 success → `GATHER_MORE_DATA`; balanced arms → `CONTINUE`; large gap → `PREFER` MEDIUM; descriptive never HIGH.

### V23-SL-04 — Experiments service
- SP2 · Parallel: after F03 · Model: Sonnet · Effort: high
- Objective: `ExperimentService(session)`: `create(name, hypothesis, population, metric) -> DRAFT`, `start(id)`, `end(id)`, `assign(experiment_id, job_id, treatment_type, resume_variant_id, payload) -> assignment` (insert-only; `treatment_hash = canonical_json_hash(payload+variant)`; duplicate `(experiment, job)` returns existing; assignment must precede any `application.applied_at` for that job — otherwise `AssignmentTooLateError`), `summary(experiment_id) -> list[RateWithN]` grouped by `treatment_type` with `evidence_class="EXPERIMENTAL"`.
- Why: contract forbids retroactive treatment inference and requires experiments separate from observational comparisons.
- Tests: assignment immutability (no update API; direct update attempt not offered); late assignment rejected; summary arms with N; DRAFT experiment cannot assign.

### V23-SL-05 — Confounding and version-collapse guards
- SP1 · Parallel: after SL-03 · Model: Sonnet · Effort: medium
- Objective: `segment_consistency_check(overall: RateWithN, segments: dict[str, RateWithN]) -> list[str]` returning warning `SEGMENT_DIRECTION_REVERSAL` when ≥2 segments each meeting `min_n_per_arm` disagree in direction with the overall comparison (Simpson-like); `StrategyLearningService` attaches warnings to recommendations; `resume_strategy` refuses to collapse versions silently (rollup only when requested).
- Tests: constructed reversal fixture triggers warning; non-reversal does not.

### V23-SL-06 — Adversarial strategy tests
- SP1 · Parallel: after SL-05 · Model: Haiku/Sonnet · Effort: low
- Objective: encode acceptance-matrix adversarial rows: one success from N=1; Simpson-like segments; stale outcomes (all outside window → n=0, `stale` warning); treatment assignment missing (observational only, `EXPERIMENTAL` never emitted); different resume versions collapsed incorrectly (rollup unlabeled → test fails).
- Code: `tests/test_v23_strategy_adversarial.py`.

### V23-SL-07 — Strategy CLI and endpoint
- SP1 · Parallel: after SL-03 · Model: Sonnet · Effort: low
- Objective: `intel strategy [--window-days N] [--json]` and GET `/api/strategy?window_days=N` returning recommendations + rows; dashboard handler read-only.
- Tests: click smoke; endpoint JSON contains `n` for every rate; sample-size note present.

---

## 4. A-V23-TARGET-COMPANY-WATCH

### V23-TW-01 — Public job source protocol + Greenhouse board client extraction
- SP2 · Parallel: yes · Model: Sonnet · Effort: high
- Objective: `ingestion/sources/base.py`: `PublicPosting(provider, source_job_id, title, absolute_url, location_text|None, updated_at|None, content_sha256, raw_payload_hash)`, `SourceFetchResult(provider, source_key, api_url, fetched_at_utc, status: Literal["OK","UNAVAILABLE","RATE_LIMITED","INVALID"], http_status|None, postings: list[PublicPosting], error_category|None)`, `PublicJobSource` protocol `fetch(source_key: str) -> SourceFetchResult`, and a `Transport` protocol (`get(url, timeout) -> (status, body)`) so tests inject a fake. `ingestion/sources/greenhouse_board.py::GreenhouseBoardSource` calls `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`; `scripts/import_v14_proof_job.py` is refactored to import this client for its single-job fetch (`.../jobs/{id}?questions=true`) **without changing the proof script's assertions or outputs**.
- Why: reuse the only existing public ATS fetch; approved read-only JSON API; no HTML scraping.
- Required behavior: one request per fetch; explicit `User-Agent: jobs-automation/<version>`; timeout 20 s; no retries beyond one on connection error; HTTP 429/5xx → `UNAVAILABLE`/`RATE_LIMITED` with no postings (never partial); JSON schema errors → `INVALID`.
- Tests: fake transport fixtures (captured JSON shape); 429 → `RATE_LIMITED`; malformed → `INVALID`; proof script tests still pass (`tests/test_proof_job_importer.py`).
- Failure behavior: never raises to callers; status carries the failure.

### V23-TW-02 — Lever postings client
- SP1 · Parallel: after TW-01 · Model: Sonnet · Effort: medium
- Objective: `ingestion/sources/lever_postings.py::LeverPostingsSource` for `https://api.lever.co/v0/postings/{site}?mode=json`; same protocol/semantics; registry `ingestion/sources/__init__.py::get_source(provider)`.
- Tests: fake transport; unknown provider → `KeyError` at registry level (caller validates config).

### V23-TW-03 — TargetCompanyService and relationship signal
- SP2 · Parallel: after F03 · Model: Sonnet · Effort: high
- Objective: `intelligence/target_companies.py::TargetCompanyService(session)`: `add(canonical_name, domain, priority, reason, role_families, compensation_floor, location_constraints, source_config) -> TargetCompanyModel` (links/creates `CompanyModel` by normalized name/domain using `ingestion/deduplication` helpers; `watch_status` stays `PAUSED` until `set_status(id, "ACTIVE")`), `list(status=None)`, `set_status`, `add_observation(target_id, type, source_type, source_reference, observed_at, confidence, payload, dedupe_key, job_id=None) -> (row, created: bool)` (unique dedupe → existing row, `created=False`), `observations(target_id, since=None, status=None)`, `relationship_signal(target_id) -> RelationshipSignal(DerivedArtifactEnvelope)` with `known_contacts: list[EvidenceRef]`, `prior_applications: list[EvidenceRef]`, `prior_responses: bool` (any inbound message linked to those applications), `referral_paths: list[EvidenceRef]` (from `OpportunityGraphService.referral_paths_to_company`), all evidence-backed; no outreach.
- Tests: default PAUSED; duplicate observation collapses; relationship signal cites message/contact refs; company linking dedupes by normalized name.

### V23-TW-04 — WatchRunner
- SP2 · Parallel: after TW-01..03 · Model: Sonnet · Effort: high
- Objective: `WatchRunner(session, sources, dedupe=JobDeduplicationService, evaluator=JobEvaluationEngine|None)`: for each `ACTIVE` target with `source_config`, fetch; on `OK`: normalize postings to `ExtractedJobPosting` → `JobDeduplicationService.ingest_posting` (existing 4-tier dedupe; provider `GREENHOUSE`/`LEVER`, `source_job_id`, `canonical_apply_url`); classify each as `NEW_ROLE` (job first seen in this run), `ROLE_CHANGED` (same `source_job_id`, different `content_sha256` vs last observation payload), or unchanged; postings previously observed `NEW_ROLE`/unchanged and **absent** from a successful fetch → `ROLE_CLOSED`; on `UNAVAILABLE|RATE_LIMITED|INVALID`: record one `SOURCE_UNAVAILABLE` observation (dedupe key per day) and **no closures**; `dedupe_key = f"{provider}:{source_job_id}:{observation_type}"` (`ROLE_CHANGED` appends the content sha).
- Why: contract adversarial rows (temporarily unavailable page; URL change same requisition; duplicate across ATS/public page).
- Tests: run twice with identical fixture → second run creates zero observations; posting removed → `ROLE_CLOSED`; fetch failure → no closures; changed URL same `source_job_id` → no duplicate job (tier-3 dedupe) and no `NEW_ROLE`.
- Failure behavior: per-target exceptions are captured into a `WatchRunReport` and do not abort other targets; nothing is written for a failed fetch except the `SOURCE_UNAVAILABLE` observation.

### V23-TW-05 — Fit, suppression, paused semantics
- SP1 · Parallel: after TW-04 · Model: Sonnet · Effort: medium
- Objective: for `NEW_ROLE` observations, attach fit: `RoleFamilyClassifier.classify(title) in target_role_families`, `HardFilterService` result, `SemanticScorer` score/decision (stored in `normalized_payload.fit`); if an `ApplicationModel` exists for the job → observation `status="SUPPRESSED"`; targets not `ACTIVE` are skipped entirely; a `NEEDS_REVIEW`-style `TaskModel(task_type="TARGET_COMPANY_NEW_ROLE")` is created only for `ACTIVE` targets when decision is `SHORTLIST` and no pending task exists for that job.
- Tests: already-applied → SUPPRESSED; PAUSED target → no observations/tasks; shortlist creates one task; second run no duplicate task.

### V23-TW-06 — Watch CLI and optional worker hook
- SP1 · Parallel: after TW-05 · Model: Sonnet · Effort: low
- Objective: `intel targets add|list|set-status|observations`, `intel targets run-watch [--target-id] [--dry-run]`; `worker --watch-targets` flag (default off) runs `WatchRunner` after ingestion in the sweep and records counts in the worker run finalize metadata. Dry-run rolls back.
- Tests: click smoke; worker flag off → runner not called (mock); on → called once per sweep.

### V23-TW-07 — Watch adversarial tests
- SP1 · Parallel: after TW-05 · Model: Haiku/Sonnet · Effort: low
- Objective: encode acceptance rows: career page unavailable; role URL changes but requisition same; recruiter relation inferred from text only stays `REVIEW_REQUIRED` (observation `RECRUITER_SIGNAL` from a message never creates an `ASSERTED` edge); duplicate role across ATS and public page collapses to one job.
- Code: `tests/test_v23_target_watch_adversarial.py`.

---

## 5. A-V23-INTERVIEW-INTELLIGENCE

### V23-II-01 — Typed models
- SP1 · Parallel: after F01 · Model: Sonnet · Effort: medium
- Objective: in `intelligence/interview.py`: `PersonRef(name, email_fingerprint, role, evidence_refs)`, `RequirementRef(text, source_ref: EvidenceRef, matched_skills: list[str])`, `StoryMapEntry(requirement: RequirementRef, evidence_refs: list[CandidateEvidenceRef], allowed_claims: list[str], unsupported_claims_to_avoid: list[str], confidence)`, `CandidateStoryMap(DerivedArtifactEnvelope, entries)`, `InterviewBrief(DerivedArtifactEnvelope)` with the contract's minimum fields (`application_id, job_id, company_id, interview_id|None, interview_stage, scheduled_start|None, scheduled_end|None, timezone|None, people, role_summary, key_requirements, candidate_evidence_map: CandidateStoryMap, likely_question_areas: list[str], risk_gap_areas: list[str], questions_to_ask: list[str], staleness: StalenessReport, conflicts: list[str], security_signals: list[InjectionSignal]`), `FollowupPackage(DerivedArtifactEnvelope)` (`application_id, contact_refs, stage_context, facts: list[FactRef(text, evidence_ref)], draft_inputs: dict[str, str], unresolved_facts: list[str], send_performed: Literal[False]`).
- Tests: JSON round-trip; `send_performed` cannot be True.

### V23-II-02 — Expose requirement extraction from the scorer
- SP1 · Parallel: yes · Model: Sonnet · Effort: low
- Objective: refactor `evaluation/scorer.py` to expose `SemanticScorer.extract_requirements(job: JobModel) -> list[tuple[str, list[str]]]` (requirement phrase, matched skill keywords) reusing its existing keyword tables; scoring behavior and all existing tests unchanged.
- Tests: existing evaluation tests; new test asserts extraction on a fixture description.

### V23-II-03 — InterviewIntelligenceService.build_brief
- SP2 · Parallel: after II-01, II-02, F05 · Model: Sonnet · Effort: high
- Objective: `InterviewIntelligenceService(session, candidate_evidence, scorer)` `build_brief(application_id, as_of=None) -> InterviewBrief`: stage from latest `InterviewModel` (status `scheduled|rescheduling_needed|cancelled`) else `application.status`; schedule only from `InterviewModel` (never parsed ad hoc); people from contacts linked via `message_link.contact_id` (fallback: `ASSERTED` graph edges) with evidence refs; `role_summary` from job/company rows; requirements via II-02 with source ref = job `description_hash`; staleness: compare `job.description_hash` now vs `packet.generation_metadata_json["job_description_hash"]` (written by J20-20; missing → `unknown` warning), posting `last_seen_at` age, interview `scheduled_start` in the past; conflicts: >1 active interview, `rescheduling_needed`, `cancelled` after brief basis, ambiguous interviewer (≥2 contacts at company with no message link to this application) → `review_items`; `security_signals` from `detect_prompt_injection_signals(job.description_text, context="job_description")` and from linked message bodies.
- Required behavior: no field of the brief is populated from free text except `key_requirements[].text` and `role_summary` (which quote source rows); questions/likely areas are templates keyed by requirement + stage, labeled `heuristic`.
- Tests: fixture application with interview → brief fields populated with refs; no interview → `interview_stage` from status and `scheduled_start None`.
- Failure behavior: unknown application → `LookupError`; missing profile → fail closed (F05).

### V23-II-04 — CandidateStoryMap builder
- SP2 · Parallel: after II-03 · Model: Sonnet · Effort: high
- Objective: for each requirement, `evidence_for_requirement` → `allowed_claims` from profile literals only; requirements without evidence → `unsupported_claims_to_avoid=[requirement.text]`, `confidence LOW`; quantitative phrasing in requirements ("N+ years", "%", headcount) never yields an allowed claim unless the profile field is an exact numeric fact (reuse the quantitative guard pattern from `preparation/tailoring.py`).
- Tests: supported vs unsupported requirement; quantitative requirement with no numeric fact → unsupported; injected requirement text never appears in `allowed_claims`.

### V23-II-05 — FollowupPackage builder
- SP1 · Parallel: after II-03 · Model: Sonnet · Effort: medium
- Objective: `build_followup(application_id, contact_id=None)`: facts limited to evidence-backed items (last stage event, interview datetime/timezone, interviewer names with refs), `draft_inputs` structured keys (`recipient_name`, `stage`, `meeting_date_iso`, `topics_discussed: unknown`), unresolved facts (missing names/dates) as review items; no prose generation; `send_performed=False` always.
- Tests: package cites message refs; unresolved when no interview evidence.

### V23-II-06 — Interview adversarial tests
- SP2 · Parallel: after II-05 · Model: Sonnet · Effort: medium
- Objective: encode the ten contract cases: ambiguous interviewer; rescheduled interview; timezone conflict (two interview rows same time different tz → conflict); stale job description; role changed between application and interview (title differs from packet snapshot → warning); resume variant differs from another role (brief cites the packet's variant only); unsupported quantitative achievement request; injection in job/company content; duplicate calendar/interview evidence (two identical `InterviewModel` rows → conflict); interview cancelled after brief generation (`as_of` older than cancellation → `stale=True` on rebuild).
- Code: `tests/test_v23_interview_adversarial.py`.

### V23-II-07 — Interview CLI and endpoint
- SP1 · Parallel: after II-05 · Model: Sonnet · Effort: low
- Objective: `intel interview-brief <application_id> [--json]`, `intel followup-package <application_id> [--json]`, GET `/api/interviews/{application_id}/brief`.
- Tests: click smoke; endpoint 404 on unknown id.

---

## 6. A-V23-AGENT-TOOLS (transport-neutral, V3 bridge)

### V23-TL-01 — Tool envelope types
- SP2 · Parallel: after F01 · Model: Sonnet · Effort: high
- Objective: `src/jobs_automation/tools/envelope.py`: `ActionClass(StrEnum)` `P0_READ|P1_LOCAL_WRITE|P2_EXTERNAL_PREP|P3_USER_APPROVED_EXTERNAL|P4_BLOCKED` with `rank()`; `ToolStatus(StrEnum)` `SUCCEEDED|FAILED|BLOCKED|NEEDS_REVIEW|PARTIAL`; `ErrorCategory(StrEnum)` `PERMISSION_DENIED|MISSING_FACT|UNRESOLVED_REVIEW|PROVIDER_UNAVAILABLE|STALE_ENTITY|NOT_FOUND|INVALID_INPUT|NOT_IMPLEMENTED|POLICY_BLOCKED|DUPLICATE_REQUEST|INTERNAL_ERROR`; `PermissionContext(actor: str, actor_kind: Literal["USER","SERVICE","AGENT"], caller_ceiling: ActionClass = P1_LOCAL_WRITE, approval_id: UUID | None = None, allow_external_prep: bool = False, task_id: str | None = None, agent_id: str | None = None, agent_version: str | None = None)`; `ToolRequest(request_id: str (uuid4 default), tool_name, tool_version, action_class, target_refs: list[EvidenceRef], input_payload: dict[str, Any], input_hash: str (computed), permission_context, idempotency_key: str | None, created_at)`; `PermissionDecisionRecord(decision_id, request_id, permission_class, decision: Literal["ALLOW","DENY","REQUIRE_APPROVAL"], policy_refs: list[str], approval_ref: str | None, reason_code: str, evaluated_at)`; `ToolResult(request_id, tool_name, tool_version, status, entity_refs, evidence_refs, warnings, review_needs, audit_ref: str | None, external_reference: str | None, error_category: ErrorCategory | None, error_message_safe: str | None, result_payload: dict[str, Any], result_hash: str, simulated: bool, completed_at)`.
- Why: field-compatible with `V3_RUNTIME_DATA_CONTRACTS` `ToolRequest`/`ToolResult`/`PermissionDecision` so V3 wraps rather than redefines.
- Tests: `input_hash` deterministic; `PARTIAL` cannot be constructed with empty warnings (validator); `simulated` defaults False and must be set True by mock handlers (test in TL-05).

### V23-TL-02 — Tool registry
- SP1 · Parallel: after TL-01 · Model: Sonnet · Effort: medium
- Objective: `tools/registry.py`: `ToolSpec(name, version, action_class, capability: str | None (policy capability e.g. "submit_application"), input_model: type[BaseModel], output_model: type[BaseModel], handler: Callable[[Session, BaseModel, PermissionContext], ToolHandlerResult], requires_destination: bool)`, `ToolRegistry.register/get/list()`; duplicate name+version rejected; `describe()` returns JSON schemas (for a future MCP/HTTP wrapper, not implemented).
- Tests: register/get/list; duplicate rejected; schema export shape.

### V23-TL-03 — Deterministic PermissionGate
- SP2 · Parallel: after TL-01 · Model: **Opus recommended** (Sonnet with exact spec acceptable; lead review mandatory) · Effort: high
- Objective: `tools/permission_gate.py::PermissionGate(session, policy_evaluator, kill_switch, approval_lookup: Callable | None)` `decide(spec, request) -> PermissionDecisionRecord`:
  1. `spec.action_class == P4_BLOCKED` → DENY `POLICY_BLOCKED`.
  2. `rank(spec.action_class) > rank(context.caller_ceiling)` → DENY `PERMISSION_DENIED` (`min()` rule: no context flag can raise the ceiling).
  3. P0/P1 → ALLOW.
  4. P2 → requires `context.allow_external_prep is True`, and when `spec.requires_destination`: `PolicyEvaluator.evaluate(destination_domain, capability=spec.capability).decision in {ASSISTED, AUTO_ALLOWED}` and `KillSwitchManager` global/platform inactive → ALLOW; policy MANUAL_ONLY/BLOCKED → DENY `POLICY_BLOCKED`; missing flag → REQUIRE_APPROVAL `EXTERNAL_PREP_NOT_ENABLED`.
  5. P3 → requires `approval_lookup` (None until migration 005 lands → REQUIRE_APPROVAL with reason `APPROVAL_STORE_UNAVAILABLE`); approval must be `ACTIVE`, unexpired, unconsumed, unrevoked, `action_class` equal, `target_refs` ⊇ request targets, artifact hashes equal when present, `method` equal; plus policy `AUTO_ALLOWED` and kill switch off → ALLOW; otherwise DENY with a specific reason code (`APPROVAL_EXPIRED|APPROVAL_CONSUMED|APPROVAL_TARGET_MISMATCH|APPROVAL_HASH_MISMATCH|APPROVAL_METHOD_MISMATCH|POLICY_NOT_AUTO_ALLOWED|KILL_SWITCH_ACTIVE`).
  6. Every P2/P3 decision is written to `AuditLogModel(action_type="permission_decision", entity_type="tool_request", entity_id=None, external_reference=request_id, input_hash=request.input_hash, result=decision, metadata_json={tool, action_class, reason_code, policy_refs, approval_ref})`.
- Non-goals: no approval creation; no agent registry.
- Tests: table-driven for each rule; ceiling below tool class denies even for P0 when ceiling is misconfigured lower (not possible: P0 is minimum; test P1 tool with P0 ceiling → DENY); audit rows for P2/P3 only.
- Adversarial: request with `approval_id` for a different packet hash → DENY `APPROVAL_HASH_MISMATCH`; expired approval → DENY; a context claiming `actor_kind="AGENT"` with `caller_ceiling=P3` and a P3 tool but no approval → REQUIRE_APPROVAL (prompt cannot elevate); `allow_external_prep=True` does not help a P3 tool.
- Failure behavior: policy evaluator exception → DENY `INTERNAL_ERROR` (fail closed), audited.

### V23-TL-04 — Tool audit persistence and replay lookup
- SP1 · Parallel: after TL-01 · Model: Sonnet · Effort: medium
- Objective: `tools/audit.py`: `record_invocation(session, request, result, decision) -> UUID` writing `AuditLogModel(action_type="tool_invocation", entity_type="tool_request", external_reference=request.request_id, input_hash=request.input_hash, actor=context.actor, result=result.status, metadata_json={tool, version, action_class, idempotency_key, result_hash, simulated, error_category, entity_refs, evidence_refs, task_id, agent_id, agent_version, decision_id})`; `find_replay(session, idempotency_key) -> (input_hash, result_payload_ref) | None`. Result payloads are not stored in full (only `result_hash` + refs) to avoid private data in audit; callers re-run read tools on replay.
- Tests: row shape; find_replay hit/miss.

### V23-TL-05 — ToolRuntime invoke pipeline
- SP2 · Parallel: after TL-02..04 · Model: Sonnet · Effort: high
- Objective: `tools/runtime.py::ToolRuntime(session_factory, registry, gate)` `invoke(tool_name, payload: dict, context, idempotency_key=None, version=None) -> ToolResult`: validate input via `input_model` (errors → `FAILED INVALID_INPUT`, no handler call); build `ToolRequest`; idempotency: same key + same `input_hash` with a prior `SUCCEEDED|PARTIAL` → return a `SUCCEEDED` result with `warnings=["REPLAYED"]` and the prior `result_hash` (for write tools) / re-execute read tools; same key + different hash → `FAILED DUPLICATE_REQUEST`; gate decision → `BLOCKED` (`PERMISSION_DENIED`/`POLICY_BLOCKED`) or `NEEDS_REVIEW` (`REQUIRE_APPROVAL`) without calling the handler; handler exceptions mapped: `LookupError→NOT_FOUND`, `PermissionError→PERMISSION_DENIED`, `FileNotFoundError→MISSING_FACT`, provider errors→`PROVIDER_UNAVAILABLE`, else `INTERNAL_ERROR` with safe message (sanitize via `worker.sanitize_error_message`); handler returns `ToolHandlerResult(payload_model, status, warnings, review_needs, entity_refs, evidence_refs, external_reference, simulated)`; runtime never upgrades `PARTIAL|BLOCKED|NEEDS_REVIEW` to `SUCCEEDED`; each invocation is a single transaction: handler failure → rollback; audit written in a separate short transaction.
- Tests: full pipeline with a fake P1 tool; validation failure; replay; duplicate mismatch; exception mapping; mock handler must set `simulated=True` or runtime raises `ToolContractError` when result payload declares `origin="mock"`.

### V23-TL-06 — Read tools batch 1
- SP2 · Parallel: after TL-05 · Model: Sonnet · Effort: medium
- Objective: `tools/read_tools.py` P0 handlers wrapping existing queries: `list_jobs(status?, company_id?, min_score?, limit=50)` (job + latest `JobEvaluationModel` + sources), `get_job(job_id)` (adds recomputed `DimensionScore`s via `SemanticScorer` labeled `computed_with_profile_version`), `get_application(application_id)`, `get_application_timeline(application_id)` (`RecruiterCRMService.get_timeline_for_application` + events), `list_contacts(company_id?)`, `get_contact_history(contact_id)` (`get_timeline_for_contact` + `get_contact_summary`), `list_interviews(upcoming_only=True, application_id?)`, `list_review_queue()` (pending tasks). Each returns typed output models with `EvidenceRef`s.
- Tests: one test per tool over the shared fixture; unknown ids → `NOT_FOUND`.

### V23-TL-07 — Read tools batch 2
- SP2 · Parallel: after TL-06, OG-07, SL-02 · Model: Sonnet · Effort: medium
- Objective: `get_resume_variant(variant_id)`, `get_resume_performance(window_days?)` (StrategyLearningService), `get_company_context(company_id)` (company, jobs, contacts, applications, target-company row, active edges, relationship signal), `get_opportunity_graph(entity_type, entity_id, depth=1)`, `get_policy_decision(destination_domain, capability)`, `get_worker_health()` (`HealthCheckService.run_full_check` filtered through an allowlist: no paths, no secrets).
- Tests: per tool; health output contains no token/path strings (assert against a denylist regex).

### V23-TL-08 — Preparation tools (P1)
- SP2 · Parallel: after TL-05, II-05, SL-03, J20-15 · Model: Sonnet · Effort: high
- Objective: `tools/prep_tools.py`: `evaluate_job(job_id)` (`JobEvaluationEngine` single job; writes evaluation), `prepare_application_packet(job_id, resume_family?)` (`ApplicationPacketBuilder` with `build_model_gateway(mode="production")` from J20-17 — falls back to `DeterministicModelGateway` when no model configured; never Mock), `generate_interview_brief(application_id)`, `draft_followup(application_id, contact_id?)`, `propose_network_connection(company_id)` (referral paths + relationship signal; suggestion only), `get_strategy_recommendations(window_days?)`, `create_review_task(application_id|job_id, reason)`, `record_manual_application(job_id, resume_variant_id|packet_id, reported_at, attestation)` (wraps J20-15 service; creates `SUBMISSION_UNCONFIRMED`, never `SUBMITTED` without external confirmation). All P1: no external side effects; artifacts written locally are `entity_refs`.
- Tests: each tool over fixtures; `prepare_application_packet` result `simulated=False` with deterministic gateway labeled `deterministic`; unresolved questions → `NEEDS_REVIEW` status with review_needs listing question names only (no answers).

### V23-TL-09 — External-action tool contracts
- SP2 · Parallel: after TL-05 and the V1.5 clean port · Model: Sonnet (Opus review) · Effort: high
- Objective: `tools/action_tools.py`: `open_assisted_application(job_id, packet_id, mock_browser: bool=False)` P2, `capability="assisted_prefill"`, `requires_destination=True`, wraps `AssistedApplicationEngine.execute` (visible session; `mock_browser=True` forces `simulated=True`); `submit_application(job_id, packet_id, approval_id)` P3, `capability="submit_application"`, wraps `ControlledAutoApplicationEngine.execute_auto_apply(mock_mode=False)` — until V1.6 transport exists the adapter returns `NOT_IMPLEMENTED` → `ToolResult BLOCKED NOT_IMPLEMENTED` (truthful), and the gate returns `REQUIRE_APPROVAL APPROVAL_STORE_UNAVAILABLE` until migration 004; `send_message(...)` and `update_external_calendar(...)` are registered P3 with handlers that return `BLOCKED NOT_IMPLEMENTED` (contracts exist, no side effects).
- Non-goals: no new transport; no messaging; no calendar.
- Tests: P2 without `allow_external_prep` → NEEDS_REVIEW; MANUAL_ONLY destination → BLOCKED `POLICY_BLOCKED`; `submit_application` without approval → NEEDS_REVIEW; with a fake approval lookup returning a mismatched hash → BLOCKED; mock browser path labeled simulated; a simulated result can never produce `application.status == "SUBMITTED"` (assert on DB).
- Failure behavior: engine exceptions → `FAILED` with safe message; no retry.

### V23-TL-10 — Tool CLI
- SP1 · Parallel: after TL-06 · Model: Sonnet · Effort: low
- Objective: `intel tool list`, `intel tool describe <name>`, `intel tool call <name> --json '<payload>' [--actor USER] [--ceiling P1] [--allow-external-prep] [--approval-id]` printing the `ToolResult` JSON; default ceiling P1.
- Tests: click smoke for list/describe/call on a P0 tool; P2 call without flag → NEEDS_REVIEW printed, exit code 2.

### V23-TL-11 — Tool layer adversarial tests
- SP2 · Parallel: after TL-09 · Model: Sonnet · Effort: medium
- Objective: encode acceptance rows: caller omits permission context for a consequential tool (context required by type; a P3 call with default context → NEEDS_REVIEW); stale entity id (deleted job → NOT_FOUND, never partial success); duplicate request id / idempotency key; tool partially fails (fixture handler returns PARTIAL with warnings → status preserved); transport wrapper bypass attempt (calling a handler directly is not possible through the public API — test that `ToolRuntime` is the only exported entry and handlers are not exported from `tools/__init__`); no agent-framework import anywhere under `tools/` (assert via AST import scan).
- Code: `tests/test_v23_tools_adversarial.py`.

---

## 7. A-V23-CAREER-BRIEFING (new artifact; card `coordination/artifacts/A-V23-CAREER-BRIEFING.md`)

### V23-CB-01 — CareerBriefing typed model + JSON schema export
- SP1 · Parallel: after F01 · Model: Sonnet · Effort: medium
- Objective: `intelligence/briefing.py`: `OpportunityCard(job_ref, company_ref, title, company_name, score: float|None, decision: str|None, reasons: list[DimensionScore-like dicts], reason_codes, relationship_signal: RelationshipSignal|None, recommended_resume: ResumeRecommendation(variant_id|None, family, basis: Literal["selector","strategy"], rates: list[RateWithN], action), next_action: Literal["EVALUATE","PREPARE_PACKET","RESOLVE_UNRESOLVED","APPLY_MANUAL","ASSISTED_PREFILL","AWAIT_APPROVAL","FOLLOW_UP","NONE"], policy_decision: str, posting_age_days: int|None, stale: bool)`, `CareerBriefing(DerivedArtifactEnvelope)` with `profile_version, data_freshness: DataFreshness(last_ingestion_at, last_worker_run_at, gmail_mode: Literal["REAL","UNAVAILABLE","MOCK"], last_watch_run_at), top_opportunities: list[OpportunityCard], relationships: list[CompanyRelationships], interviews_upcoming, followups_due, review_queue_summary, strategy: list[StrategyRecommendation], watch_highlights: list[ObservationSummary], data_gaps: list[str], uncertainty_notes: list[str]`; `CareerBriefing.model_json_schema()` written by a test to `docs/schemas/career_briefing.schema.json` (committed, regenerated by test when changed).
- Tests: schema file up to date (test fails with a diff if stale).

### V23-CB-02 — CareerBriefingService compose
- SP2 · Parallel: after OG-07, SL-03, TW-05, II-03 · Model: Sonnet · Effort: high
- Objective: `CareerBriefingService(session, profile, guardrails).build(as_of=None, limit=10) -> CareerBriefing`: candidate jobs = `OPEN_JOB_STATUSES` without a non-terminal application; score from latest evaluation (recompute dimension reasons via `SemanticScorer`, label profile version); rank by score desc, then `first_seen_at` desc; `next_action` rule: no evaluation → EVALUATE; decision `REJECT` → NONE; unresolved consequential facts → RESOLVE_UNRESOLVED; no live-ready packet → PREPARE_PACKET; policy MANUAL_ONLY → APPLY_MANUAL; ASSISTED → ASSISTED_PREFILL; AUTO_ALLOWED without approval → AWAIT_APPROVAL; existing application with pending follow-up task → FOLLOW_UP; `recommended_resume` = selector variant + matching strategy rates (`GATHER_MORE_DATA` when low_n); relationships via graph per company; interviews from `InterviewModel` future; follow-ups from pending tasks of the three follow-up types; `data_gaps` sentences generated from: zero real applications, low_n on all resume rows, `gmail_mode != REAL`, no active targets; `uncertainty_notes` list every `LOW` confidence element; `simulated=True` if any input row has a simulation mode (should never happen in real data; the flag makes contamination visible).
- Tests: empty DB → briefing with only data gaps, no exceptions; fixture DB → deterministic output for fixed `as_of` (JSON equality); no field contains a candidate raw value other than the profile literals allowed by F05.
- Failure behavior: profile missing → fail closed; per-section exceptions are captured as `warnings` with the section marked unavailable (briefing still returns).

### V23-CB-03 — Briefing CLI
- SP1 · Parallel: after CB-02 · Model: Sonnet · Effort: low
- Objective: top-level `briefing [--json] [--limit N] [--as-of ISO]` (alias `intel briefing`) with a rich table view and JSON output validated against the schema.
- Tests: click smoke on fixture; `--json` parses and validates.

### V23-CB-04 — `/api/briefing`
- SP1 · Parallel: after CB-02 · Model: Sonnet · Effort: low
- Objective: GET `/api/briefing?limit=&as_of=` in `dashboard/server.py` returning the briefing JSON; loopback default unchanged; no write.
- Tests: `tests/test_dashboard.py` new test; unknown query param ignored; response includes `generated_at` and `data_gaps`.

### V23-CB-05 — Briefing invariants tests
- SP1 · Parallel: after CB-02 · Model: Haiku/Sonnet · Effort: low
- Objective: assert invariants across three fixtures (empty, sparse, rich): every rate has `n`; every card has ≥1 evidence ref; `next_action` never `AWAIT_APPROVAL` for MANUAL_ONLY destinations; simulated rows flagged; injected JD text never appears outside `key_requirements`/`security_signals`.

---

## 8. A-V23-ACCEPTANCE-CAMPAIGN (new artifact; card `coordination/artifacts/A-V23-ACCEPTANCE-CAMPAIGN.md`; procedure in `docs/V2_3_ACCEPTANCE_CAMPAIGN.md`)

### V23-AC-01 — Extend the golden fixture with V2.3 steps + engineering report
- SP2 · Parallel: after CB-02 and J20I-01 · Model: Sonnet · Effort: high
- Objective: `tests/integration/test_v23_campaign.py` extends the V2.0 golden scenario (J20I-01) with: target company added and activated; watch run over a captured public-source fixture (fake transport, labeled fixture); user-confirmed referral edge; manual application recorded; strategy over fixture outcomes (asserts `GATHER_MORE_DATA` at low N); interview brief for the fixture application; briefing composed; tool-layer invocations for each step through `ToolRuntime` (audit refs captured). Emits `artifacts/reports/v23_engineering_campaign_report.json` (gitignored path; test asserts schema) with `trace_id, code_sha, fixture_version, entity_ids, assertions[], tool_audit_refs[], simulated=True`.
- Tests: the campaign itself; report schema.

### V23-AC-02 — Campaign report verifier
- SP2 · Parallel: after AC-01 · Model: Sonnet · Effort: high
- Objective: `scripts/verify_v23_campaign.py --report <path> --mode engineering|live [--database-url]`: engineering mode checks schema, `simulated=True`, assertions all `pass`; live mode requires `simulated=False`, `gmail_mode == "REAL"`, no fixture markers (reuse `FORBIDDEN_TOKENS` approach from the V1.4 verifier), every `entity_id` resolvable in the configured DB, every `RateWithN` internally consistent, `code_sha` equals `git rev-parse HEAD`, report hash bound into a separate receipt file `v23_campaign_receipt.json` with `result: V23_CAMPAIGN_PASS|FAIL`; omitted DB target in live mode → FAIL (fail closed, mirroring P0A lessons).
- Tests: engineering pass; forged live report (fixture marker) → FAIL; missing DB target → FAIL; stale code sha → FAIL.

### V23-AC-03 — Live campaign runbook and redacted evidence schema
- SP1 · Parallel: yes · Model: Haiku/Sonnet · Effort: low
- Objective: finalize `docs/V2_3_ACCEPTANCE_CAMPAIGN.md` §Live with exact commands, the redaction allowlist for `coordination/proofs/v23_live_campaign_report.redacted.json` (job public URLs, entity ids, hashed emails, counts, rates with N, briefing hash, verifier receipt), and the blocked-state vocabulary.

### V23-AC-04 — Live campaign execution (`USER_GATE` inputs; LIVE)
- LIVE · not SP-rated · Owner: eligible machine with real profile/resume + Gmail token + owner-supplied target list · Model: n/a
- Objective: run the live campaign per the runbook after all required earlier live checkpoints (V1.4–V2.0) are accepted, Gmail canary is real, and ≥1 externally-confirmed real application exists; commit only the redacted report + receipt; request lead review. Result vocabulary: `V23_CAMPAIGN_PASS | V23_CAMPAIGN_FAIL | LIVE_PROOF_BLOCKED_*`.

---

## 9. Mapping from the legacy coarse prep queue

| Legacy (SP3–SP5) | Replaced by |
|---|---|
| V23-G01 schema/relationship audit | done in this planning pass (master plan §2.3, §8) |
| V23-G02 graph projection/query service | V23-OG-01..04, 07, 08 |
| V23-G03 evidence traversal | V23-OG-02, 09, 10 |
| V23-G04 identity/dedupe/invalidation | V23-OG-05, 06 |
| V23-S01 experiment persistence | V23-F03 + V23-SL-04 |
| V23-S02 descriptive performance engine | V23-SL-02 |
| V23-S03 min-sample/uncertainty | V23-SL-01, 03, 05 |
| V23-S04 recommendation object | V23-SL-03 |
| V23-T01 watchlist model | V23-F03 + V23-TW-03 |
| V23-T02 approved source adapters | V23-TW-01, 02 |
| V23-T03 new/changed/closed dedupe | V23-TW-04 |
| V23-T04 relationship signal | V23-TW-03, 05 |
| V23-I01..I04 | V23-II-01..07 |
| V23-TL01 typed tools | V23-TL-01, 02, 05, 06, 07, 08 |
| V23-TL02 authorization context | V23-TL-03 |
| V23-TL03 idempotency/audit envelope | V23-TL-04, 05 |
| V23-TL04 MCP wrapper | deferred after V2.3 |

Totals for this file: 55 tasks, 78 SP (SP1 × 32, SP2 × 23), 1 LIVE item.

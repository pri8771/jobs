# V2.3 Master Plan — Critical Path, Artifact Graph, V3 Compatibility

- Status: **LEAD_ACCEPTED WITH CORRECTIONS** — authoritative corrections: `docs/V23_LEAD_REVIEW_20260921.md`
- Planning pass: `docs/FABLE_V23_MASTER_PLANNING_BRIEF.md`
- Audited main: `e84da8d` (2026-09-21, 59 commits, orphan root `4c4e22f`)
- Companion documents (one canonical set, no duplicate roadmaps):
  - `docs/V23_TASK_GRAPH_RECOVERY.md` — V1.4→V1.7 tasks (P0A, clean ports, V1.6 engineering, V1.7 reconciliation)
  - `docs/V23_TASK_GRAPH_V20.md` — V2.0 tasks (Gmail runtime, control center, reliability, analytics, integration fixture)
  - `docs/V23_TASK_GRAPH_V23.md` — V2.3 tasks (graph, strategy, watch, interview, tools, briefing, campaign)
  - `docs/V23_TEST_MATRIX.md` — test/adversarial matrix by artifact → task IDs
  - `docs/V2_3_ACCEPTANCE_CAMPAIGN.md` — end-to-end V2.3 scenario, machine-verifiable outputs, live overlay
  - `coordination/V23_WORKER_QUEUE.md` — proposed canonical worker queue (lead promotes into `WORK_QUEUE.md`)

Operating rules: ChatGPT remains lead/acceptance authority. There is **one active implementation worker/session and one active five-minute heartbeat watcher**. PG1–PG4 below are dependency/parallelizability groups, not simultaneous implementation lanes. Lower-cost subagents may do bounded independent analysis/tests under the parent worker. Every consequential external action stays `USER_GATE`. Lead corrections in `docs/V23_LEAD_REVIEW_20260921.md` override any stale wording below.

---

## 1. Executive summary

1. **Brownfield is stronger than the coordination truth implies.** Main already holds a working discovery → dedupe → evaluate → packet → assisted/auto routing → lifecycle → CRM → interview → alerts → dashboard/analytics → worker/health system (12.5k LOC, 151 tests, ruff/mypy-strict clean under an independent Python 3.12 run). Nineteen relational tables already model company, job, job_source, application, application_event, contact, message, message_link, interview, task, resume_variant, application_packet, artifact, policy_registry and audit_log. V2.3 needs **five additive tables and one additive column**, not a new platform.
2. **Three finished-but-unintegrated bodies of work exist on branches and overlay cleanly onto main** (verified by scratch dry runs, §2.4): Lane 2's V1.5 browser safety (+38 tests), Lane 1's P0A proof tooling (+17 tests), and Lane D's opportunity-graph projection (933 LOC, reuse-with-repair). Integration is mechanical SP1 work, not re-implementation.
3. **The shortest engineering path to V2.3 may proceed ahead of blocked live gates, but the acceptance path remains sequential.** V2.3 engineering does not need automated submission to be developed, but V2.3 cannot be called `REAL_PROVEN`/`COMPLETE` until V1.4, V1.5, V1.6, V1.7, and V2.0 have each passed their required real-life checkpoint. Manual/user-reported applications remain `SUBMISSION_UNCONFIRMED` until accepted external confirmation exists.
4. **V2.3 engineering can be prepared and implemented ahead of live gates when write surfaces/dependencies allow**, because it largely touches new modules (`intelligence/`, `tools/`, `ingestion/sources/`). With the owner's one-worker rule, this means sequential artifact batches by the single implementation worker, optionally assisted by lower-cost subagents for bounded non-conflicting analysis. It becomes `REAL_PROVEN` only after all prior required live checkpoints and the V2.3 live campaign pass.
5. **V3 compatibility is designed now as five small interfaces inside V2.3 (§11)** — permission classes and a deterministic gate, a generic scoped-approval table shared with V1.6, a tool request/result envelope, a derived-artifact envelope, and audit rows that carry request/trace identity. No agent runtime, memory, or specialist code is on the V2.3 path.
6. Totals: **131 engineering tasks, 166 SP, 100% SP1/SP2** (plus gated LIVE items), four parallel groups, ~85% Sonnet-class, ~10% Opus-class, ~5% Haiku/lead review. First five executable tasks are in §13.

---

## 2. Current brownfield audit (Git truth at `e84da8d`)

### 2.1 Branches, PRs, CI

| Surface | Head | State | Tree diff vs main (src/tests/scripts) |
|---|---|---|---|
| `main` | `e84da8d` | authoritative; history rewritten (no merge base with any worker branch) | — |
| Lane 1 `worker/v14-real-proof` (PR #8 draft) | `f3a0c41` | P0A **REWORK**; commits after `5e50584` are heartbeat-only | +1621/−271: verifier/runner/import scripts, `packet_builder.py` helper, proof tests |
| Lane 2 `worker/v15-assisted-application` (PR #2 draft, non-mergeable) | `ddb4f84` | A-R15-01..05 lead-accepted at task scope; 06..09 open | browser/* +1267 LOC, `test_assisted_safety_adversarial.py` +2072; **behind main** on everything Lane 3 merged |
| Lane 3 `worker/recruiting-ops` (PR #3 merged 16:50Z) | `d32a4c8` | fully integrated | only `scripts/worker_heartbeat_watch.py` differs |
| Lane D `worker/v23-foundations` (PR #5 closed, paused) | `d99e774` | unreviewed opportunity graph | `intelligence/opportunity_graph.py` (933) + `tests/test_v23_opportunity_graph.py` (219); rest is stale-behind |
| worker-pc `worker/jobs-v14-p0a-remaining-tests-20260921-1449` | `cffae70` | review input only | Lane 1 head + `tests/test_real_proof_verifier.py` +420 |
| GitHub Actions | runs 552–563 | every run fails in ~4 s before any step (`steps: []`, `runner_id: 0`) → `CI_BLOCKED_ACCOUNT` | — |
| Issue #7 | 52 comments | bot heartbeat posting stopped 18:18Z; lead comments continue | — |

### 2.2 Artifact truth

| Class | Artifacts |
|---|---|
| ACCEPTED (engineering) | A-V14-PACKET-SAFETY, A-V20-WORKER-RUN-HISTORY |
| LEAD_REVIEW, code on main, blocked only by integrated CI evidence | A-V17-CRM-EVIDENCE, A-V17-INTERVIEW-FOLLOWUP, A-V20-CONTROL-CENTER (most J20 views already exist, see §7) |
| IN_PROGRESS on branches, not on main | A-V14-P0A-INTEGRITY (2 defects = 16 xfail tests), A-V15-BROWSER-SAFETY-CONTRACT + A-V15-ASSISTED-APPLICATION (01..05 accepted, 06..09 open) |
| READY/PROPOSED with contracts but no code | A-V16-* (6 engineering artifacts), A-V20-GMAIL-RUNTIME-READINESS (J20G-01..04), A-V20-INTEGRATION-FIXTURE, A-V12-CANDIDATE-PROVENANCE, A-V23-* (5), A-V30-* |
| Implemented but unlisted | Lane D opportunity graph (~45% of contract, `REUSE_WITH_REPAIR`) |
| Live proof | **none** for any version (V1.4–V2.0). `coordination/proofs/` holds only schema/README |

### 2.3 Code inventory findings that shape the plan

Persistence (`db/models.py`, migrations 001–003, consistent with `Base.metadata`; all downgrades real):
- UUID PKs, tz-aware UTC datetimes, JSON/JSONB variant, 15 JSON catch-all columns, **zero enums, zero CHECK constraints, zero indexed FKs, zero `ondelete`, zero `updated_at`**.
- Contact ↔ application linkage exists only through `company_id` and sender-string matching; `message_link` has **no `contact_id`** (root cause of Lane D's substring heuristic).
- `resume_variant.content_hash` / `application_packet.packet_hash` are convention-only (not unique/indexed); tests build schema with `create_all()` on SQLite, migrations run only via `scripts/verify_migrations.sh` against Postgres.

Operator/runtime:
- Dashboard = stdlib `ThreadingHTTPServer`, 19 GET endpoints + 1 gated POST; write gate applies to POST only.
- Analytics already reports funnel, source, role-family, resume-variant, time-to-stage with N and `low_sample_size` (N<5), excludes simulation modes, attributes resume by `packet → resume_variant` FK, attributes source to earliest `job_source`.
- Worker persists durable begin/finalize runs in `audit_log`; no cross-process lock; reconciliation timestamp in-memory only.
- Health: 6 checks; `check_gmail` is a placeholder that accepts an injected readiness result (ready for J20G-03/04).
- **No live LLM call is wired anywhere**: `LiteLLMModelGateway` is never instantiated, every `model_routing.example.yaml` task is `null`, `prepare-packets` hard-codes `MockModelGateway`, `prompt_version` columns are dead. V2.3 is therefore designed **deterministic-first**; LLM prose is an optional later enhancement behind a fail-closed gateway factory (J20-17).

Domain:
- Lifecycle: 11 ranked stages + 3 terminal; idempotent on `(application_id, provider_message_id)`; regression prevention; contradiction → NEEDS_REVIEW. **`OFFER_ACCEPTED` / `OFFER_DECLINED` are unreachable** (no writer) and there is **no path to record a manually submitted application** (applications are created only by the auto/assisted engines).
- CRM dedupes contacts by exact email only; timelines are computed on read from messages + links (good: the message table is the evidence log).
- Interview extraction is deterministic; never fabricates dates; follow-ups are task rows, not drafts; `task.due_at` doubles as the ingestion checkpoint.
- Evaluation: deterministic hard filters + weighted scorer with per-dimension reasons that are **computed but not persisted**; freshness dimension is a constant 1.0.
- Packet builder: content-addressed artifacts, canonical packet hash, EEO/quantitative-claim guards, fail-closed on missing resume bytes.
- Automation: Greenhouse/Lever live mode returns `NOT_IMPLEMENTED`; duplicate prevention is check-then-act; in-memory rate limiter; `platforms.yaml` is descriptive only (policy registry is the enforced one).
- Browser (main): missing Lane 2's safety work; `MockBrowserRunner` defaults `interactive_submitted=True`; `file://` URIs passed raw to Playwright.
- Ingestion: deterministic classifier, 4-tier job dedupe, JSONL importer; the only public ATS fetch (Greenhouse board API) lives in `scripts/import_v14_proof_job.py` and is reusable for target-company watch.

### 2.4 Independent validation evidence (sandbox, not CI)

Environment: this planning session's container, Python 3.12.3, SQLAlchemy 2.0.54, pydantic 2.13.5, alembic 1.20.0, SQLite; commands identical to CI except the Postgres migration step (no Postgres available).

| Run | Result |
|---|---|
| main `e84da8d`: `ruff check .` / `mypy src tests` / `pytest` | clean / clean (93 files) / **151 passed** |
| Lane 2 overlay on main (8 files: `browser/*`, `packet_builder.py`, 2 test files) | ruff clean / mypy clean (94 files) / **189 passed** |
| Lane 1 overlay on main (9 files: 3 scripts, `packet_builder.py`, 5 test files) | ruff clean / mypy clean / **168 passed** |
| worker-pc adversarial verifier suite vs Lane 1 head verifier | **27 passed, 16 xfailed** — the 16 xfails are exactly the two open P0A defects (list in `V23_TASK_GRAPH_RECOVERY.md` R14-P03) |
| Lane D overlay on main (3 files) | ruff clean / mypy clean / 1 passed |

These runs are evidence inputs for the lead, labeled `INDEPENDENT_SANDBOX_VALIDATION`; they are not CI green and not acceptance.

---

## 3. What "V2.3 genuinely working" means

The user asks: *What are the best opportunities for me right now, why, who do I know there, which resume should I use, what should I do next, and what interviews/follow-ups do I have?*

V2.3 answers through one typed, evidence-backed `CareerBriefing` (new artifact A-V23-CAREER-BRIEFING) composed from five services, exposed by CLI (`briefing`) and dashboard (`/api/briefing`), and callable through the transport-neutral tool layer:

| Question | Producer | Evidence source | Uncertainty surfaced as |
|---|---|---|---|
| best opportunities + why | evaluation (existing scorer/filters, recomputed per-dimension reasons) + opportunity graph relationship signal | job, job_source, job_evaluation, contacts, applications | score bands, missing-fact flags, staleness of posting |
| who do I know there | opportunity graph (FK projection + persisted evidence edges) | contact, message_link.contact_id, opportunity_edge | `inferred` flag, `REVIEW_REQUIRED` status |
| which resume | resume selector (existing) + strategy learning rates with N | resume_variant, packet, application events | `RateWithN.low_n`, `GATHER_MORE_DATA` |
| what next | review queue, unresolved facts, follow-up tasks, policy decision per destination | task, candidate profile provenance, policy_registry | explicit `next_action` enum incl. `MANUAL_ONLY` |
| interviews / follow-ups | lifecycle interview + alerts + interview intelligence brief | interview, task, messages | rescheduled/cancelled/ambiguous-interviewer flags |
| which targets have new roles | target-company watch over approved public APIs | target_company_observation, job_source | source fetch status, dedupe suppression |

Acceptance = `ENGINEERING_ACCEPTED` (deterministic fixture campaign, `docs/V2_3_ACCEPTANCE_CAMPAIGN.md`) **and** `REAL_PROVEN` (the same briefing over the user's real data after gates open). Low N is acceptable and expected; the system must say so truthfully.

---

## 4. Critical path to V2.3 (shortest safe path)

```
                 ┌────────────── PG1 Lane 1 ───────────────┐
 P0A rework ──► V1.4 clean port ──► [USER_GATE private inputs] ──► V1.4 REAL_PROOF ─┐
 (16 xfail→pass)                                                                     │ real resume identity
                                                                                     ▼
 J20G-01..04 Gmail runtime readiness ──► [USER_GATE Gmail OAuth] ──► canary ──► live ingestion ──► V1.7 live lifecycle proof (historical threads)
                                                                                     │ real jobs/messages/contacts/outcomes
                 ┌────────────── PG3/PG4 ──────────────┐                              ▼
 V1.7 reconciliation ──► V2.0 engineering gaps ──► golden fixture ──► V2.0 ENGINEERING_READY ──► V2.0 live campaign (C1..C5, manual/assisted application path)
                                                                                     │
 V2.3 engineering (fixtures; schedule ahead when safe / use bounded subagents) ───────────────────────────────────┴──► V2.3 acceptance campaign: engineering report → live report → lead review
                 └────────────── PG2 dependency group (engineering can be scheduled ahead; acceptance cannot skip it) ──────────────┘
 V1.5 clean port ──► A-R15-06..09 ──► [USER_GATE browser] V1.5 live proof ──► V1.6 engineering (scoped_approval, attempts, preflight, confirmation) ──► transport research ──► [deferred] V1.6 live submit
```

Rate-limiting items, in order: (1) P0A rework (Lane 1, 4 × SP1, machine-checkable DoD); (2) the two user gates (private inputs, Gmail OAuth) — engineering cannot shorten them, only be ready before they open; (3) V2.3 engineering volume (78 SP, parallelizable into two sub-groups); (4) real outcome accumulation (calendar time; guardrails make low-N outputs honest rather than blocking).

What is explicitly **off the V2.3 engineering critical path** (§12): LinkedIn network growth, MCP wrapper, optional LLM prose generation, pgvector, and V3 runtime/memory/specialists/evaluation. **V1.5 and V1.6 live proofs are not optional for formal V2.3 completion** even when their implementation/live gate is scheduled independently.

Gate labels used everywhere: `USER_GATE` (owner action required), `LEAD_GATE` (acceptance decision), `CI_BLOCKED_ACCOUNT` (runner outage; independent validation substitutes as evidence input only).

---

## 5. Artifact graph

### 5.1 Remaining artifacts through V2.3 (status now → proposed after acceptance)

| Artifact | Now | Depends on | Unblocks | Task group / lane |
|---|---|---|---|---|
| A-V14-P0A-INTEGRITY | IN_PROGRESS (REWORK) | A-V14-PACKET-SAFETY ✔ | A-V14-CLEAN-INTEGRATION, A-V14-REAL-PROOF | R14-P (Lane 1) |
| A-V14-CLEAN-INTEGRATION | BLOCKED | P0A accepted | A-V14-REAL-PROOF | R14-I (Lane 1) |
| A-V14-REAL-PROOF | BLOCKED | clean port + `USER_GATE` private inputs | V1.4 COMPLETE, real resume identity for V2.3 | R14-L (Lane 1 or eligible machine) |
| A-V15-CLEAN-INTEGRATION | BLOCKED | none technically (dry run green); lead decision D2 | A-V15-* residuals | R15-I (Lane 2) |
| A-V15-BROWSER-SAFETY-CONTRACT / A-V15-ASSISTED-APPLICATION | IN_PROGRESS | clean port | V1.5 engineering acceptance, V1.6, `open_assisted_application` tool | A-R15-06..09, R15-V01 (Lane 2) |
| A-V15-LIVE-ASSISTED-PROOF | BLOCKED | V1.5 accepted + `USER_GATE` browser | V1.5 COMPLETE; required before formal V2.3 completion | R15-L |
| A-V16-AUTHORIZATION / IDEMPOTENCY / PREFLIGHT / CONFIRMATION / HYGIENE | BLOCKED | V1.5 engineering accepted (lead may advance) | P3 tools, V1.6 proof | R16-* (Lane 2) |
| A-V16-TRANSPORT | READY | none for research | A-V16-FIRST-REAL-SUBMISSION | R16-T01/T02 (research only now) |
| A-V16-FIRST-REAL-SUBMISSION | PROPOSED | all V1.6 + eligible transport + exact per-application `USER_GATE` | V1.6 COMPLETE; required before V2.0 LIVE_ACCEPTED / V2.3 REAL_PROVEN | schedule when ready; do not bypass |
| A-V17-ENGINEERING-RECONCILIATION | READY | code on main | A-V17-MILESTONE-GATE | R17-E (Lane 3) |
| A-V17-LIVE-LIFECYCLE-PROOF | BLOCKED | `USER_GATE` Gmail + J20G | A-V17-MILESTONE-GATE, V2.0 live | R17-L |
| A-V20-GMAIL-RUNTIME-READINESS | READY | none | canary, health truth | J20G-01..04 (Lane 1 after V1.4 proof, or reassigned) |
| A-V20-CONTROL-CENTER | LEAD_REVIEW | none | A-V20-INTEGRATED-OS | J20-01..04, J20-15, J20-16 (Lane 3) |
| A-V20-RELIABILITY | IN_PROGRESS | none | A-V20-INTEGRATED-OS | J20-05, 06a/b, 08, 12, 17, 18, 19, 20 (Lane 3) |
| A-V20-ANALYTICS | IN_PROGRESS | none | A-V23-STRATEGY-LEARNING | J20-09..11 (Lane 3) |
| A-V20-INTEGRATION-FIXTURE | READY | V1.7 recon + J20 repairs | A-V20-INTEGRATED-OS, A-V23-ACCEPTANCE-CAMPAIGN | J20I-01..03 |
| A-V12-GMAIL-CANARY / A-V20-LIVE-INGESTION | PROPOSED / BLOCKED | J20G + `USER_GATE` OAuth | V1.7 live, V2.0 live, V2.3 live | G-01..05 |
| A-V20-INTEGRATED-OS | BLOCKED | above | V2.3 REAL_PROVEN | C1..C5 |
| A-V12-CANDIDATE-PROVENANCE | READY | none | story map, allowed-claims | implemented minimally by V23-F05 |
| A-V23-OPPORTUNITY-GRAPH | READY | migration 005, Lane D port | briefing, tools, watch | V23-OG-01..10 |
| A-V23-STRATEGY-LEARNING | PROPOSED | analytics + 004 | briefing, tools | V23-SL-01..07 |
| A-V23-TARGET-COMPANY-WATCH | READY | 004, sources | briefing, tools | V23-TW-01..07 |
| A-V23-INTERVIEW-INTELLIGENCE | PROPOSED | candidate evidence, lifecycle | briefing, tools, V3 Interview Agent | V23-II-01..07 |
| A-V23-AGENT-TOOLS | READY | services above; V1.6 only for P3 execution | V3 runtime | V23-TL-01..11 |
| **A-V23-CAREER-BRIEFING (new)** | PROPOSED | the five above | A-V23-CAREER-INTELLIGENCE | V23-CB-01..05 |
| **A-V23-ACCEPTANCE-CAMPAIGN (new)** | PROPOSED | fixture + services | A-V23-CAREER-INTELLIGENCE | V23-AC-01..04 |
| A-V23-CAREER-INTELLIGENCE | PROPOSED | all A-V23 + real data | V3.0 | `LEAD_GATE` |

### 5.2 V3 compatibility contracts (docs exist; small interfaces implemented inside V2.3)

`V3_PERMISSION_MODEL`, `V3_TOOL_PERMISSION_MATRIX`, `V3_RUNTIME_DATA_CONTRACTS`, `V3_SHARED_MEMORY_CONTRACT`, `V3_AGENT_HANDOFF_PROTOCOL`, `V3_SPECIALIST_AGENT_SPECS` remain the V3 contracts. §11 lists which of their fields V2.3 implements now (tool envelope, permission gate, scoped approval, derived-artifact envelope, audit identity) and which are deferred (AgentTask, checkpoint, memory, trace tables, runtime).

---

## 6. Parallel groups, lane mapping, write surfaces

| Group | Suggested lane | Write surfaces (non-overlapping) | Sequence |
|---|---|---|---|
| PG1 | Lane 1 | `scripts/*proof*`, `tests/test_real_proof_*`, then `adapters/gmail.py`, `health.py::check_gmail`, `worker.py` readiness plumbing, `docker-compose.yml` | R14-P → R14-I → R14-L (gate) → J20G-01..04 → G-01..05 (gate) → R17-L (gate) |
| PG2 | Lane 2 | `browser/*`, `tests/test_assisted_*`, then `automation/authorization.py`, `attempts.py`, `confirmation.py`, `auto_engine.py`, migration **005** | R15-I → A-R15-06..09/R15-V01 → R15-L (gate, optional) → R16-A/I/P/C/H → R16-T01/T02 |
| PG3 | Lane 3 | `dashboard/*`, `analytics.py`, `lifecycle/*`, `cli/main.py` (operator commands), `health.py` (non-Gmail), `scripts/backup|restore`, `evaluation/scorer.py` freshness | R17-E → J20-01..04, 05, 06a/b, 08, 09..12, 15..20 → J20I-01..03 → V23-SL, V23-CB |
| PG4 | Lane 3 second wave, or a reopened V2.3 lane if the owner authorizes (D3) | `intelligence/*`, `tools/*`, `ingestion/sources/*`, `cli/intelligence_cli.py`, migration **004** | V23-F → V23-OG → V23-TW → V23-II → V23-TL → V23-AC |

Rules: only one group modifies `db/models.py`/`migrations/` per window (004 = PG4, 005 = PG2; whoever lands second re-points `down_revision`, never forks the chain). New CLI commands from PG4 live in `cli/intelligence_cli.py` and are registered with one line in `cli/main.py` to avoid merge conflicts with PG3. Shared helpers introduced by one group (`intelligence/envelope.py`, `core/untrusted_text.py`, `intelligence/role_family.py`) are landed first as SP1 tasks so the other group imports rather than duplicates.

---

## 7. Code / module map (repair, reuse, new)

| Artifact / need | Existing anchor | Action |
|---|---|---|
| P0A verifier integrity | Lane 1 `scripts/verify_v14_real_proof.py` (+661 vs main), `verify_database_linkage()` bare return | REPAIR on Lane 1 (R14-P01/P02), then PORT to main |
| Packet hash helper | `preparation/packet_builder.py` — two branch variants of `compute_canonical_packet_hash` | RECONCILE to one superset signature (R14-I03/R15-I03) |
| Assisted browser safety | Lane 2 `browser/assisted_engine.py`, `base.py`, `mock_runner.py`, `playwright_runner.py` | PORT (8-file overlay, 189 tests green) |
| Submission truth | `automation/auto_engine.py::ControlledAutoApplicationEngine`, `automation/base.py`, adapters | EXTEND with `authorization.py`, `attempts.py`, `confirmation.py`; do not rewrite |
| Recruiter CRM / interviews / alerts | `lifecycle/crm.py`, `interview.py`, `alerts.py`, `engine.py` | REUSE; add `message_link.contact_id` writes (V23-OG-05), offer-decision path (J20-16) |
| Manual application recording | none | NEW `lifecycle/manual_application.py` + CLI (J20-15) |
| Gmail runtime | `adapters/gmail.py` (`GmailOAuthClient`, `GmailAdapter`, `MockEmailAdapter`), `ingestion/engine.py::run_sweep` transaction boundary, `health.py::check_gmail` placeholder | REPAIR/EXTEND (J20G-01..04) |
| Dashboard | `dashboard/server.py` (19 GET + gated POST: funnel, sources, kanban, jobs, reviews, interviews, contacts, audit, health, followups, analytics/{sources,roles,resumes,time-to-stage}, timeline, offers-rejections, policies, worker) | REUSE; add `/api/config` (allowlist), `/api/briefing`, `/api/strategy`, `/api/interviews/{id}/brief` |
| Analytics | `dashboard/analytics.py::FunnelAnalyticsService` (`_is_real_submission`, `_get_application_historical_outcomes`, five performance methods with N) | REUSE; add `window_days` and shared role-family classifier; StrategyLearningService wraps it |
| Evaluation reasons | `evaluation/scorer.py::SemanticScorer.score` → `DimensionScore` (not persisted) | REUSE by recomputation at query time (labeled with profile version); fix freshness (J20-19); expose `extract_requirements` (V23-II-02) |
| Resume choice | `preparation/tailoring.py::ResumeVariantSelector.select_variant/get_resume_family` | REUSE; strategy adds evidence |
| Candidate evidence / provenance | `core/candidate_profile.py::CandidateProfileConfig` (+`check_unresolved_facts`) | NEW thin `intelligence/candidate_evidence.py` implementing A-V12 minimal contract |
| Opportunity graph | Lane D `intelligence/opportunity_graph.py` | PORT + REPAIR (9 repairs) + NEW `intelligence/edges.py` over new `opportunity_edge` table |
| Target-company watch | `scripts/import_v14_proof_job.py` Greenhouse board API fetch; `ingestion/deduplication.py::JobDeduplicationService.ingest_posting`; `evaluation/*` | EXTRACT source client to `ingestion/sources/`, NEW `intelligence/target_companies.py` |
| Interview intelligence | `lifecycle/interview.py`, `crm.py` timelines, `InterviewModel`, scorer requirements | NEW `intelligence/interview.py` (deterministic assembly) |
| Tool layer | typed results already `extra="forbid"` (`EvaluationScoreResult`, `FilterResult`, `PacketBuildResult`, `PolicyEvaluationResult`), `PolicyEvaluator`, `KillSwitchManager`, `AuditLogModel` | NEW `tools/` package (envelope, registry, gate, audit, runtime, adapters) |
| Model gateway | `adapters/models.py` (`DeterministicModelGateway`, `MockModelGateway`, `LiteLLMModelGateway`), `core/model_routing.py` | NEW factory `build_model_gateway()` fail-closed (J20-17); no new provider |
| Independent validation | CI steps in `.github/workflows/ci.yml` | NEW `scripts/local_ci.sh` (J20-12) |

---

## 8. Migration sequence (additive, reversible, fail-closed defaults)

Chain today: `001_initial_foundation → 002_resume_variant_attribution → 003_generation_origin_readiness`.

| Revision | Owner group | Content | Fail-closed default rules |
|---|---|---|---|
| `004_v16_submission_truth` | V1.6 (R16-A01, R16-I02) | generic `scoped_approval`; `submission_attempt` with **partial unique index on `idempotency_key` for active states**; `external_confirmation_evidence` | `scoped_approval.status` and `external_confirmation_evidence.independently_validated` have **no server default**; no row becomes `CONFIRMED`/`ACTIVE` by default |
| `005_v23_intelligence_foundation` | V2.3 (V23-F03) | `opportunity_edge`; `message_link.contact_id`; `target_company`; `target_company_observation`; `strategy_experiment`; `strategy_experiment_assignment` | `opportunity_edge.status` defaults `REVIEW_REQUIRED`, `inferred` defaults `true`; `target_company.watch_status` defaults `PAUSED`; assignments are insert-only |
| `006_v3_agent_runtime_foundation` | V3 when implementation begins | durable agent task/checkpoint/memory/trace foundations per V3 contracts | no default authority; no external action state inferred |
| `007_existing_fk_indexes` (optional) | later cleanup only if justified | indexes on existing FK columns | none |

Acceptance for every revision (from `FUTURE_SCHEMA_MIGRATION_PLAN`): model/migration agreement, fresh upgrade, incremental upgrade, downgrade, re-upgrade, constraint tests, JSON defaults safe on SQLite and Postgres, and no existing row becomes confirmed/authorized via defaults. The numeric order above is canonical; do not dynamically swap prefixes or create multiple heads.

---

## 9. Model-routing plan

| Work class | Model | Effort | Examples |
|---|---|---|---|
| Architecture, safety semantics, reconciliation, final synthesis | Fable 5.1 (this pass) / lead review | high | this plan; review of gate and schema tasks |
| Consequential state semantics and schema | Opus-class | high | V23-TL-03 permission gate; R16-A01/R16-I02/R16-I03 (`scoped_approval`, `submission_attempt`, partial unique index, concurrency); V23-OG-06 edge status semantics (Sonnet may implement, Opus reviews) |
| Well-specified SP1/SP2 implementation, tests, adapters, CLI, endpoints, analytics | Sonnet-class | medium (SP1) / high (SP2) | ~85% of tasks |
| Docs, cards, inventories, boilerplate tests from exact specs | Haiku-class or Sonnet low | low/medium | card updates, runbooks, J20-01/J20-09 reconciliations, test scaffolds |

Subagent suitability: every task marked `Parallel: yes` in the task graphs is subagent-safe when write surfaces are respected. Never delegate final authority for candidate truth, submission authorization, idempotency semantics, external-confirmation truth, injection boundaries, or policy decisions (`MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`).

Allocation summary (engineering SP): recovery 56 SP / 51 tasks; V2.0 32 SP / 25 tasks; V2.3 78 SP / 55 tasks; total 166 SP / 131 tasks. Opus-class ≈ 16 SP; Sonnet ≈ 141 SP; Haiku ≈ 9 SP.

---

## 10. Live-proof matrix

| Version | Production path proven | Real inputs | Gate(s) | Evidence bundle | Needed for V2.3 working? |
|---|---|---|---|---|---|
| V1.4 | import live job → private profile → exact resume bytes → packet builder (deterministic gateway, labeled) → artifacts → runtime candidate → separate verifier receipt | private profile, selected resume file, live Greenhouse job | P0A `LEAD_GATE`; private inputs `USER_GATE` | redacted candidate + `REAL_PROOF_PASS` receipt in `coordination/proofs/` | **Yes** (real resume identity) |
| V1.5 | accepted packet → visible browser inspect → classify → safe prefill → exact uploads → review boundary; no submit | real application page | V1.5 engineering `LEAD_GATE`; browser `USER_GATE` | field classifications, manifest, hashes, session mode | **Yes** — required live checkpoint |
| V1.6 | scoped approval → preflight/idempotency → one system submit → external confirmation → truthful event | desired job, eligible `AUTO_ALLOWED` transport | V1.6 engineering; transport eligibility; per-application `USER_GATE` | approval/attempt/confirmation refs | **Yes** — required live checkpoint; if no eligible transport exists, completion remains truthfully blocked |
| V1.7 | real Gmail read-only canary over bounded historical recruiting threads → link → lifecycle/interview/follow-up → idempotent replay | OAuth, historical threads | J20G engineering; OAuth `USER_GATE` | hashed message refs, entity IDs, timeline digest, replay result | **Yes** (real contacts/messages/outcomes) |
| V2.0 | Campaigns 1–5 (`V2_0_LIVE_ACCEPTANCE_RUNBOOK`): canary, real opportunity, real externally-confirmed application lifecycle, operator/reliability, analytics | as above + real application evidence | OAuth + private inputs + applicable browser/submission `USER_GATE`; backup drill | live campaign report | **Yes**; requires prior live checkpoints including V1.6 |
| V2.3 | `briefing` over real data: real opportunities with reasons, real relationships, resume recommendation with N, next actions, interviews/follow-ups, ≥1 real target company watched via public API, interview brief for a real application (or truthful "no interview evidence") | all above + target-company list from owner | same gates + owner supplies targets | `v23_live_campaign_report.json` verified by `scripts/verify_v23_campaign.py` | **Yes — defines V2.3 REAL_PROVEN** |

Blocked-state vocabulary stays `LIVE_PROOF_BLOCKED_USER_AUTH | _PRIVATE_INPUT | _PROVIDER | _POLICY | _NO_ELIGIBLE_TRANSPORT | _OTHER`; never converted to PASS.

---

## 11. V3 compatibility check

| V3 requirement (contract) | V2.3 design decision | Implemented in V2.3? |
|---|---|---|
| Permission taxonomy P0–P4, `min()` rule, no prompt elevation (`V3_PERMISSION_MODEL`) | `tools/envelope.py::ActionClass`; `PermissionContext.caller_ceiling`; `PermissionGate.decide()` deterministic: P4 deny; class > ceiling deny; P0/P1 allow; P2 needs `allow_external_prep` + destination policy ASSISTED/AUTO_ALLOWED + kill switch off; P3 needs ACTIVE unexpired unconsumed scoped approval bound to exact target/artifact hash/method + AUTO_ALLOWED + kill switch off; every P2/P3 decision audited | **Yes** (V23-TL-01, TL-03) |
| Scoped approval record (`ScopedApproval` fields) | one generic `scoped_approval` table (migration 005) with `action_class`; V1.6 submit approval is its first action class; typed nullable FKs keep integrity for the submit case | Yes when PG2 lands; until then P3 tools return `BLOCKED/NOT_IMPLEMENTED` (safe) |
| Durable AgentTask / checkpoint / restart semantics | **Deferred to V3 migration 006**; V2.3 services are session-injected, side-effect free except through audited writes, so a V3 runtime can wrap them; `submission_attempt.state` maps 1:1 onto `external_action_state` (NOT_STARTED→PREPARED/AUTHORIZED, REQUEST_DISPATCHED_UNCONFIRMED→REQUEST_DISPATCHED/SUBMISSION_UNCONFIRMED, CONFIRMED→CONFIRMED) | Interface only (documented mapping) |
| Canonical-vs-derived memory boundary (M0–M4) | every V2.3 derived output (`StrategyRecommendation`, `InterviewBrief`, `CandidateStoryMap`, `FollowupPackage`, `CareerBriefing`, observations, proposed edges) inherits `DerivedArtifactEnvelope` (`source_refs`, `generated_at`, `generator_version`, `code_sha`, `confidence`, `warnings`, `valid_until`, `supersedes`, `stale`) → future M2/M4 entries wrap them; canonical truth stays in existing tables; `opportunity_edge` never asserts model inference (`REVIEW_REQUIRED` unless user-confirmed or evidence-backed) | **Yes** (V23-F01, OG-06) |
| Artifact-based handoff | all outputs are typed Pydantic artifacts with evidence refs; no transcript passing | Yes by construction |
| Trace/evaluation envelope (`ToolRequest`, `ToolResult`, `TraceEvent`) | `ToolRequest`/`ToolResult` field-compatible with `V3_RUNTIME_DATA_CONTRACTS` (`request_id`, optional `task_id`/`agent_id`/`agent_version`, `tool_name/version`, `action_class`, `target_refs`, `input_hash`, `permission_context`, `idempotency_key`; result `status ∈ {SUCCEEDED,FAILED,BLOCKED,NEEDS_REVIEW,PARTIAL}`, `evidence_refs`, `audit_ref`, `external_reference`, `warnings`, `error_category`, `result_hash`, explicit `simulated` flag); persisted as `audit_log` rows keyed by `request_id`/`input_hash` so V3 `agent_trace_event` can reference them | **Yes** (V23-TL-01, TL-04) |
| Specialist tool ceilings | `ToolSpec.action_class` per tool + `caller_ceiling` in context = the `min(agent ceiling, tool requirement, policy, approval)` rule without agents | Yes |
| No agent DB bypass | agents (later) call `ToolRuntime.invoke()`; services validate; direct ORM writes are not exposed as tools | Yes |
| Idempotent tool invocation | `idempotency_key` + `input_hash` replay from audit; same key/different input → `DUPLICATE_REQUEST` | Yes (V23-TL-05) |

Conclusion: V2.3 can support V3 without redesign. The only V3 items requiring new tables later are `agent_task`, `agent_checkpoint`, `agent_memory`, `agent_trace_event` (planned 006), all additive.

### Proposed decisions for lead ratification (append to `state/DECISIONS.md` only if accepted)

- **D1 (MODIFIED/ACCEPTED)** Decouple V1.6 from the **engineering scheduling** critical path only. V2.3 engineering may proceed while V1.6 live proof is gated, but V2.3 may not be `REAL_PROVEN`/`COMPLETE` while V1.6 remains incomplete. A-V16-FIRST-REAL-SUBMISSION remains mandatory.
- **D2** Lane 2 stops rebasing PR #2 and ports the 8 browser files onto a fresh branch from main (`A-V15-CLEAN-INTEGRATION`); PR #2 becomes history.
- **D3 (MODIFIED/ACCEPTED)** One active implementation worker/session owns execution. PG1–PG4 are dependency groups/work surfaces, not concurrent workers. Lower-cost subagents may perform bounded independent analysis/tests under the parent worker when write surfaces do not conflict.
- **D4 (MODIFIED/ACCEPTED)** Migration order: `004_v16_submission_truth` first (generic `scoped_approval`, submission attempt, confirmation evidence), then `005_v23_intelligence_foundation`; V3 runtime foundation begins at 006. This preserves version/truth dependencies while reusing the generic approval model.
- **D5 (MODIFIED/ACCEPTED)** `record-manual-application`: user attestation creates `application_mode="manual"`, truth-preserving `status="SUBMISSION_UNCONFIRMED"`, event `APPLICATION_SUBMISSION_REPORTED_BY_USER` (source `user_attestation`) with exact resume/packet attribution. It is reported-attempt evidence, not confirmed-submission evidence. Only accepted external confirmation may advance submission truth and confirmed-submission analytics.
- **D6** `INDEPENDENT_SANDBOX_VALIDATION` (exact-head `ruff`/`mypy`/`pytest` in a clean 3.12 environment via `scripts/local_ci.sh`) is an accepted evidence class while `CI_BLOCKED_ACCOUNT` persists; it never replaces lead review and is never called "CI green".
- **D7** V2.3 is deterministic-first; any LLM use goes through `build_model_gateway()` with fail-closed behavior and explicit origin labeling; no LLM output is required for V2.3 acceptance.
- **D8** Lane D's opportunity graph is adopted as the base (`REUSE_WITH_REPAIR`), not rewritten.
- **D9 (MODIFIED/ACCEPTED)** V2.3 engineering may proceed and be `ENGINEERING_ACCEPTED` on fixtures before V2.0 `LIVE_ACCEPTED`. V2.3 `REAL_PROVEN`/`COMPLETE` requires V2.0 `LIVE_ACCEPTED`, all required earlier live checkpoints, and the V2.3 live campaign. Any application asserted submitted in live acceptance must have accepted external confirmation.

---

## 12. Explicitly deferred until after V2.3

- Broad optimization of V1.6 transport beyond the first compliant supported transport. **A-V16-FIRST-REAL-SUBMISSION itself is not deferred past V2.3 acceptance**; it remains a mandatory earlier-version live checkpoint.
- A-LINKEDIN-NETWORK-GROWTH, external messaging, calendar mutation, spending — all remain `USER_GATE` and unimplemented.
- MCP/HTTP wrapper over the tool layer (V23-TL04 in the old prep queue).
- LLM-generated prose in briefs/follow-ups (optional enhancement behind J20-17).
- pgvector / semantic similarity, graph database, Temporal/LangGraph/CrewAI/Redis/Kafka/Kubernetes.
- HTML career-page scraping (V2.3 watch uses approved public JSON APIs only).
- V3 runtime, shared memory, trace tables, specialists, evaluation harness (A-V30-*).
- Dashboard framework replacement; authentication for GET endpoints beyond loopback default (documented risk, not a V2.3 blocker).

---

## 13. Open lead decisions and first five worker tasks

Open decisions: D1–D9 above, plus: proof-job approval (A-PROOF-JOB-SELECTION), the owner's target-company list, and whether Lane 1 or Lane 3 takes J20G-01..04 after the V1.4 proof.

First five executable tasks after lead review (details in the task graphs and `coordination/V23_WORKER_QUEUE.md`):
1. **R14-P01 + R14-P02** (Lane 1, SP1+SP1, Sonnet high) — close the two P0A defects; DoD = the 16 xfail tests in the worker-pc suite pass with xfail markers removed.
2. **R14-P03** (same active worker, SP1) — run the complete adversarial proof-integrity set with all former xfails converted to required passes.
3. **R14-P04** (same active worker, SP1) — exact-head local/independent validation; record `CI_BLOCKED_ACCOUNT` if hosted runner remains unavailable.
4. **R14-I01..I05** (same active worker on a clean V1.4 integration branch) — port only accepted proof tooling to current main and request lead review.
5. **Next unblocked artifact after the V1.4 lead gate** — normally V1.4 real-proof readiness/live proof if the private-input gate is open; otherwise advance one safe non-conflicting SP1/SP2 artifact such as V1.5 clean integration while keeping formal acceptance gates intact.

---

## 14. Evidence appendix

Commands run in the planning sandbox (Python 3.12.3 venv with the project's pinned dependency ranges; package importable via `PYTHONPATH=src`, matching `pyproject` `pythonpath`):

```
ruff check .                      # main e84da8d: All checks passed
mypy src tests                    # main e84da8d: Success: no issues found in 93 source files
pytest -q                         # main e84da8d: 151 passed
# overlays built with `git show <branch>:<path>` into disposable worktrees of origin/main:
pytest -q  (Lane 2 8-file overlay)                 # 189 passed; ruff/mypy clean
pytest -q  (Lane 1 9-file overlay)                 # 168 passed; ruff/mypy clean
pytest -q tests/test_real_proof_verifier.py (worker-pc cffae70 file vs Lane 1 head)   # 27 passed, 16 xfailed
pytest -q tests/test_v23_opportunity_graph.py (Lane D 3-file overlay)                 # 1 passed; ruff/mypy clean
```

Not run: `scripts/verify_migrations.sh` (no Postgres in the sandbox). No private data, OAuth, browser, submission, messaging, calendar, or spending action was performed.

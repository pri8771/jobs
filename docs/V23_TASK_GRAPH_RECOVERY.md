# Task Graph — Recovery V1.4 → V1.7 (P0A, clean ports, V1.5 residuals, V1.6 engineering, V1.7 reconciliation)

- Status: PROPOSED (lead review required; existing lane assignments in `coordination/lanes/*.md` remain authoritative until ChatGPT promotes changes)
- Parent plan: `docs/V23_MASTER_PLAN.md`
- Reconciles: `docs/V1_4_TO_V1_7_RECOVERY_EXECUTION.md`, `coordination/RECOVERY_QUEUE_V14_TO_V17.md`, `coordination/lanes/LANE_1.md`, `LANE_2.md`, `LANE_3.md`, `docs/LANE_A_REAUDIT_2.md`, `docs/V1_6_DATA_CONTRACTS.md`, `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`
- Evidence used: master plan §2.4 dry runs (Lane 1 overlay 168 passed; Lane 2 overlay 189 passed; worker-pc adversarial suite 27 passed / 16 xfailed)

Conventions: see `docs/V23_TASK_GRAPH_V23.md` §0 (quality gate, model/effort semantics, acceptance evidence, no self-acceptance). Never port `scripts/worker_heartbeat_watch.py` or `coordination/heartbeats/*` between branches; those are lead-owned tooling/history. All live items are `USER_GATE`/`LIVE` and never self-authorized.

---

## 1. A-V14-P0A-INTEGRITY (Lane 1, branch `worker/v14-real-proof`, PR #8)

### R14-P01 — Mandatory database linkage for REAL_PROOF_PASS (RP14-T7)
- SP1 · Parallel: with R14-P02 (same file, coordinate in one batch) · Model: Sonnet · Effort: high
- Objective: `scripts/verify_v14_real_proof.py::verify_database_linkage()` must fail closed when no proof DB target is configured and must validate persisted rows.
- Why: lead re-review 15:50 ET confirmed a bare `return` when neither `database_url` nor `db_path` is present; omitting the target bypasses persisted packet/resume/artifact validation.
- Depends on: none.
- Code: `scripts/verify_v14_real_proof.py`; tests `tests/test_real_proof_verifier.py`.
- Required behavior: absence of both `database_url` and `db_path` → `REAL_PROOF_FAIL` with reason `DB_TARGET_MISSING`; unopenable/unresolvable target → FAIL `DB_TARGET_UNAVAILABLE`; persisted `ApplicationPacketModel` must match proof `packet_id`, `job_id`, `resume_variant_id`, `packet_hash`, `generation_metadata_json.generation_origin`; persisted `ResumeVariantModel` must match selected family/name/version and `resume_artifact_id`; resume/cover-letter `ArtifactModel.sha256` must match candidate evidence; unrelated/tampered rows → FAIL with the specific field name in the reason.
- Non-goals: no private input use; no runner changes beyond what the verifier needs.
- Tests: the seven `test_omitting_database_target_must_not_bypass_persisted_record_checks[...]` and `test_real_proof_pass_requires_a_configured_proof_database_target` cases from the worker-pc suite (R14-P03) pass without `xfail`.
- Failure behavior: every mismatch is a FAIL receipt (never an exception without a receipt).
- Output: verifier change + tests.
- Acceptance evidence: focused tests, full checks, `READY_FOR_LEAD_REVIEW`.

### R14-P02 — Independently bound Greenhouse source attestation (RP14-T3)
- SP1 · Parallel: with R14-P01 · Model: Sonnet · Effort: high
- Objective: bind the local `source_attestation` to persisted `JobSourceModel`/`JobModel` import evidence.
- Why: a self-consistent forged attestation + locally authored questions + fabricated description SHA currently passes.
- Code: `scripts/verify_v14_real_proof.py` (new `verify_persisted_source_binding()`), `scripts/import_v14_proof_job.py` (ensure `source_payload_json` carries `api_url`, `fetched_at_utc`, `content_sha256`, `question_list_sha256`, `source_kind`, `public_job_id`; it already carries most), tests.
- Required behavior: load `JobSourceModel` for the proof `job_id` with `provider == "GREENHOUSE"`; compare provider, `source_kind`, public/source job id, `api_url`, `fetched_at_utc`, description/content SHA, question-list SHA (recompute from the persisted questions payload with `compute_questions_sha256`), `canonical_apply_url`, and that the `JobSource.job_id` equals the proof job; any divergence → FAIL naming the field; missing persisted source → FAIL `SOURCE_EVIDENCE_MISSING`.
- Tests: the seven `test_source_attestation_must_bind_to_persisted_greenhouse_evidence[...]` cases plus `test_self_consistent_forged_questions_and_description_sha_cannot_pass` and `test_self_consistent_forgery_without_database_target_cannot_pass` pass without `xfail`.
- Failure behavior: as above; no partial PASS.

### R14-P03 — Adopt the worker-pc adversarial suite and run full checks
- SP1 · Parallel: after P01/P02 · Model: Sonnet · Effort: medium
- Objective: replace `tests/test_real_proof_verifier.py` with the worker-pc version from `worker/jobs-v14-p0a-remaining-tests-20260921-1449` (`cffae70`, +420 lines, tests only), remove the 16 `xfail` markers, run focused + full `pytest`, `ruff check .`, `mypy src tests`.
- Why: the suite encodes exactly the two remaining defects; it is review input the lead has already inspected.
- Definition of done (machine-checkable): these 16 tests pass un-xfailed —
  `test_real_proof_pass_requires_a_configured_proof_database_target`; `test_omitting_database_target_must_not_bypass_persisted_record_checks[packet_generation_origin|packet_hash|packet_row_absent|resume_artifact_sha256|resume_variant_family|resume_variant_name]`; `test_source_attestation_must_bind_to_persisted_greenhouse_evidence[provider|source_kind|public_job_id|api_url|fetched_at_utc|description_sha256|question_list_sha256]`; `test_self_consistent_forged_questions_and_description_sha_cannot_pass`; `test_self_consistent_forgery_without_database_target_cannot_pass`.
- Output: green suite (expected ≈ 43 tests in the file), full-suite count.

### R14-P04 — Exact-head validation evidence
- SP1 · Parallel: no · Model: Haiku/Sonnet · Effort: low
- Objective: obtain exact-head GitHub CI; if Actions still fail before steps, record `CI_BLOCKED_ACCOUNT` and attach `INDEPENDENT_SANDBOX_VALIDATION` output (`scripts/local_ci.sh` once J20-12 exists; until then the four commands and their summary lines) in the heartbeat/handoff; set `READY_FOR_LEAD_REVIEW`; stop implementation.

## 2. A-V14-CLEAN-INTEGRATION (Lane 1, after P0A `LEAD_GATE`)

### R14-I01 — Fresh branch
- SP1 · Model: Haiku · Effort: low · Objective: `git checkout -B worker/v14-clean-integration origin/main`; no history carried.

### R14-I02 — Overlay proof files only
- SP1 · Model: Sonnet · Effort: medium
- Objective: copy exactly these files from the accepted Lane 1 head: `scripts/import_v14_proof_job.py`, `scripts/run_v14_real_proof.py`, `scripts/verify_v14_real_proof.py`, `src/jobs_automation/preparation/packet_builder.py`, `tests/test_artifact_store.py`, `tests/test_packet_safety_adversarial.py`, `tests/test_preparation.py`, `tests/test_real_proof_runner.py`, `tests/test_real_proof_verifier.py`. Do **not** port `tests/test_dashboard.py`, `test_health.py`, `test_lifecycle.py`, `test_worker.py` (Lane 1's copies are behind main), nor heartbeat tooling.
- Evidence: this overlay on `e84da8d` passed 168 tests with ruff/mypy clean in the planning sandbox (before P01/P02; re-run after).

### R14-I03 — Reconcile the packet-hash helper
- SP1 · Model: Sonnet · Effort: medium
- Objective: `preparation/packet_builder.py` keeps one superset helper so Lane 1 and Lane 2 ports agree:
  `compute_canonical_packet_hash(job_id: str | uuid.UUID, profile_version: int | str, resume_variant_id: str | uuid.UUID | None, resume_sha: str, cover_letter_sha: str | None, answers: dict[str, Any] | None, answer_provenance: dict[str, Any] | None) -> str` with payload `{"job_id": str(job_id), "profile_version": profile_version, "resume_variant_id": str(resume_variant_id) if resume_variant_id else "", "resume_sha": resume_sha, "cover_letter_sha": cover_letter_sha, "answers": answers or {}, "answer_provenance": answer_provenance or {}}` hashed as `sha256(json.dumps(payload, sort_keys=True))`; plus `compute_questions_sha256(questions: list[str]) -> str` (`separators=(",", ":")`).
- Tests: golden test proving the helper reproduces the hash of the pre-refactor inline formula for a fixed non-None input (backward compatibility of existing `packet_hash` values); None variant → `""`.

### R14-I04 — Full checks · SP1 · Model: Sonnet · Effort: low — `ruff`, `mypy src tests`, `pytest`, record `INDEPENDENT_SANDBOX_VALIDATION` if CI blocked.
### R14-I05 — Small PR + review · SP1 · Model: Haiku · Effort: low — draft PR to main with the file list and evidence; `READY_FOR_LEAD_REVIEW`.

## 3. A-V14-REAL-PROOF (`USER_GATE` private inputs; eligible machine; after clean integration accepted)

- R14-L01 SP1 verify private profile is genuine (content evidence, not filename) → readiness report or `LIVE_PROOF_BLOCKED_PRIVATE_INPUT`.
- R14-L02 SP1 run production resume selector; record exact selected variant id.
- R14-L03 SP1 verify exact resume bytes exist for that variant; absent → `LIVE_PROOF_BLOCKED_PRIVATE_INPUT`; never synthesize/relabel/substitute.
- R14-L04 SP1 `python scripts/import_v14_proof_job.py` against the currently live public job (default OpenSesame 7967740 unless A-PROOF-JOB-SELECTION changes it).
- R14-L05 LIVE `python scripts/run_v14_real_proof.py ...` (deterministic gateway, labeled).
- R14-L06 LIVE `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...` with the proof DB target configured.
- R14-L07 SP1 commit redacted candidate + receipt under `coordination/proofs/`; `READY_FOR_LEAD_REVIEW`.
- Gate: no execution before ChatGPT accepts P0A and the owner authorizes private-input use.

## 4. A-V15-CLEAN-INTEGRATION (Lane 2; pending lead decision D2)

### R15-I01 — Fresh branch · SP1 · Model: Haiku — `git checkout -B worker/v15-clean-integration origin/main` (after R14-I is merged if the lead sequences it so; otherwise from current main).
### R15-I02 — Overlay the eight browser-safety files
- SP1 · Model: Sonnet · Effort: medium
- Objective: copy from `worker/v15-assisted-application` head `ddb4f84`: `src/jobs_automation/browser/__init__.py`, `browser/assisted_engine.py`, `browser/base.py`, `browser/mock_runner.py`, `browser/playwright_runner.py`, `tests/test_assisted_application.py`, `tests/test_assisted_safety_adversarial.py`; take `src/jobs_automation/preparation/packet_builder.py` from R14-I03's reconciled version (or apply the same superset if Lane 2 lands first). Do **not** port Lane 2's copies of `dashboard/*`, `health.py`, `lifecycle/*`, `worker.py`, `ingestion/*`, `tests/test_dashboard.py`, `test_health.py`, `test_lifecycle.py`, `test_worker.py` (all behind main).
- Evidence: this overlay on `e84da8d` passed 189 tests, ruff and mypy clean.
### R15-I03 — Helper reconciliation check · SP1 · Model: Sonnet — assert `compute_canonical_packet_hash` signature/behavior equals R14-I03; run the A-R15 adversarial suite.
### R15-I04 — Full checks + PR · SP1 · Model: Haiku — new draft PR supersedes PR #2 for review (PR #2 stays as history); `READY_FOR_LEAD_REVIEW`.

## 5. A-V15 residuals on the clean branch (Lane 2)

### A-R15-06 — Page-level prompt-injection signal
- SP2 · Model: Sonnet · Effort: high
- Objective: browser inspection returns a bounded page-security signal from visible/accessible text around the form using the shared detector `core/untrusted_text.py::detect_prompt_injection_signals` (V23-F02; if not yet on main, land that module first as part of this task — same spec — so both branches share it).
- Required behavior: signals are untrusted evidence in the plan/manifest; optional/non-required page injection → `security_warnings`, safe unrelated prefill may proceed; required field containing injection-like text → manual/policy-blocked; page text can never set live-ready/submitted/authorization state.
- Tests (four from `LANE_A_REAUDIT_2`): page-level override text outside labels → signal, no instruction execution; optional injection + safe form → safe fields prepared, warning retained; required field injection → block; injection cannot set live-ready/submitted/authorization.

### A-R15-07 — Cover-letter upload wiring with field-specific mapping
- SP2 · Model: Sonnet · Effort: high
- Required behavior: when `packet.cover_letter_artifact_id` exists, `build_plan()` adds the exact artifact to `file_uploads["cover_letter"]`; field-aware mapping (resume field ← resume, cover-letter field ← cover letter); required cover-letter field + missing artifact → blocking review; optional + missing → manual/unfilled with evidence; bytes re-verified via `ArtifactStore.verify` immediately before upload; no generic `input[type=file]` fallback.
- Tests: distinct paths/bytes/hashes for both uploads; missing required → no prefill/upload; tampered cover letter → blocked; two file inputs cannot cross-attach.

### A-R15-08 — Accepted-packet integrity revalidation before browser use
- SP2 · Model: Sonnet · Effort: high
- Required behavior: recompute packet identity with `compute_canonical_packet_hash` from persisted `answers_json`/`answer_provenance_json`/artifact SHAs and compare to `packet_hash`; verify each answer has provenance and none were added/changed; verify `resume_variant_id`/artifact ids belong to the packet; fail closed before inspection/prefill; audit rejection reason without answer contents.
- Tests: mutated `answers_json` → blocked; mutated provenance → blocked; swapped variant/artifact → blocked; unchanged → passes.

### A-R15-09 — Unknown file inputs stay manual
- SP1 · Model: Sonnet · Effort: medium
- Required behavior: only positively identified resume/CV inputs map to resume; only positively identified cover-letter inputs map to cover letter; unknown required file input → `UNKNOWN_REQUIRED` manual blocking review; unknown optional → `UNKNOWN_OPTIONAL` unfilled; no default artifact for generic file inputs.
- Tests: required "Work sample" file input → manual, no resume; optional unknown → unfilled; positive matches still map.

### R15-V01 — Main-branch browser defects check
- SP1 · Model: Sonnet · Effort: medium
- Objective: on the clean branch verify and, if still present, fix: `MockBrowserRunner.interactive_submitted` default must be `False`; `PlaywrightBrowserRunner` must convert `file://` storage URIs to filesystem paths before `set_input_files` (fail closed if the path does not exist); `AssistedApplicationEngine` must write an `AuditLogModel` row for `REVIEW_REQUIRED` outcomes (not only BLOCKED/confirmed).
- Tests: mock runner default; URI conversion; audit row on review-required path.

## 6. A-V15-LIVE-ASSISTED-PROOF (`USER_GATE` browser; optional for V2.3)
- R15-L01 SP1 choose real page + accepted packet; R15-L02 USER_GATE owner authorization; R15-L03..L06 LIVE inspect/classify/prefill/verify/stop at review boundary; R15-L07 SP1 redacted evidence commit. No submit unless separately authorized.

## 7. A-V17-ENGINEERING-RECONCILIATION (Lane 3; code already on main)

### R17-E01 — CRM criteria audit
- SP1 · Model: Haiku/Sonnet · Effort: low
- Objective: fill the card's acceptance checklist with test names from current main: evidence-linked inbound/outbound (`test_lifecycle.py` CRM tests), contact spanning roles (multi-role timeline test), new role in existing thread (thread divergence test), ambiguity → review, reconstructable timeline (`get_timeline_for_*` tests), manual relink/unlink/merge tests, no generated summary replaces messages (by construction). Record the one gap: `get_or_create_contact` no-parseable-email branch creates a new row each time (untested) → R17-E03.
### R17-E02 — Interview/follow-up criteria audit
- SP1 · Model: Haiku/Sonnet · Effort: low
- Objective: same for interview extraction (evidence preserved, explicit schedule/tz, no fabricated dates, reschedule/cancel idempotency), follow-up dedupe/auto-resolve, stale detection, offer/rejection/background/onboarding classes, repeated-sweep idempotency. Record gaps: follow-up tasks carry only a `reason` string (drafting inputs are minimal) → R17-E03b; `OFFER_ACCEPTED`/`OFFER_DECLINED` unreachable → closed by J20-16.
### R17-E03 — Only genuinely missing tests
- SP1 · Model: Sonnet · Effort: medium
- Objective: add tests for the no-email contact branch (document/decide: create with `email=None` but dedupe by exact `name`+`company_id`, or keep creating and flag) — implement the smallest safe behavior: dedupe by `(company_id, normalized name)` when email is absent; add one plaintext-fallback parser test per board parser.
### R17-E03b — Structured follow-up draft inputs (optional, lead decides)
- SP1 · Model: Sonnet · Effort: low
- Objective: `LifecycleAlertService` task `payload_json` gains `draft_inputs: {contact_name, contact_email_fingerprint, last_inbound_at, stage, application_id}`; no prose, no send.
### R17-E04 — Full checks with independent validation record · SP1 · Model: Haiku.
### R17-E05 — Reconcile cards for lead acceptance · SP1 · Model: Haiku — update A-V17-CRM-EVIDENCE / A-V17-INTERVIEW-FOLLOWUP "Lead evidence state" with SHA, test names, validation record; lead decides ACCEPTED.

## 8. A-V17-LIVE-LIFECYCLE-PROOF (`USER_GATE` Gmail; after J20G engineering)
- R17-L01 USER_GATE read-only Gmail authorization; R17-L02 SP1 `gmail-diagnose` canary; R17-L03 SP1 select bounded historical thread set; R17-L04..L07 LIVE ingest → link → lifecycle/interview/follow-up → idempotent replay; R17-L08 SP1 redacted timeline proof; R17-L09 SP1 independent review request.

## 9. V1.6 engineering (Lane 2 after V1.5 acceptance or lead advancement; parallel to V2.3; not on the V2.3 critical path)

Schema note: all V1.6 tables land in **`005_v16_submission_truth`** (`down_revision` = `004_v23_intelligence_foundation`, or `003` if V1.6 lands first — re-point, never fork).

### A-V16-AUTHORIZATION
- R16-A01 **SP2** · Model: Opus (Sonnet with this spec acceptable; lead review mandatory) · Objective: generic `scoped_approval` table + `ScopedApprovalModel`: `id`; `action_class` String(32) NOT NULL (`SUBMIT_APPLICATION|SEND_MESSAGE|CALENDAR_MUTATION|EXTERNAL_PROFILE_UPDATE|SPEND`); `actor` String(64) NOT NULL; `target_refs_json` JSON NOT NULL; `job_id` FK NULL; `application_id` FK NULL; `packet_id` FK NULL; `packet_hash` String(64) NULL; `candidate_profile_version` Integer NULL; `resume_variant_id` FK NULL; `resume_artifact_sha256` String(64) NULL; `cover_letter_artifact_sha256` String(64) NULL; `destination` String(512) NULL; `destination_provider` String(64) NULL; `method` String(64) NOT NULL; `policy_decision` String(32) NULL; `policy_version` String(64) NULL; `authorization_source` String(64) NOT NULL; `authorization_reference` String(255) NULL; `issued_at` NOT NULL; `expires_at` NOT NULL; `one_time_use` Boolean NOT NULL; `consumed_at` NULL; `revoked_at` NULL; `status` String(16) NOT NULL **(no server default)** (`ACTIVE|CONSUMED|EXPIRED|REVOKED`); `created_at`. Indexes `(action_class, status)`, `job_id`, `packet_id`, `expires_at`. Service invariant: `SUBMIT_APPLICATION` rows require `job_id`, `packet_id`, `packet_hash`, `resume_variant_id`, `resume_artifact_sha256`, `destination`, `method` non-null (validated in code, tested).
- R16-A02 SP1 · Sonnet · `automation/authorization.py::ScopedApprovalService(session)`: `issue(...)` (status ACTIVE set explicitly), `resolve(approval_id) -> ScopedApprovalView | None` (view: `approval_id, action_class, status, target_refs, packet_hash, resume_artifact_sha256, method, expires_at, one_time_use, consumed_at, revoked_at`), `validate(view, *, action_class, job_id, packet_hash, method, now) -> AuthorizationCheck(ok, reason_code)` with reason codes `APPROVAL_MISSING|APPROVAL_EXPIRED|APPROVAL_CONSUMED|APPROVAL_REVOKED|APPROVAL_TARGET_MISMATCH|APPROVAL_HASH_MISMATCH|APPROVAL_METHOD_MISMATCH`, `consume(approval_id, attempt_id)`, `revoke(approval_id, reason)`. This service is the `approval_lookup` used by the V2.3 `PermissionGate` (V23-TL-03).
- R16-A03 SP1 · Sonnet · changed job/packet/method/hash invalidates reuse (validate compares exact values; `supersede_on_packet_change(packet_id)` revokes ACTIVE approvals bound to a packet whose hash changed).
- R16-A04 SP1 · Sonnet · adversarial tests: matrix "Authorization" rows (missing/expired/other job/other packet hash/other method/reused one-time/valid).

### A-V16-IDEMPOTENCY
- R16-I01 SP1 · Sonnet · `automation/attempts.py::compute_idempotency_key(destination_domain, requisition_identity, candidate_identity) -> str` = `sha256("v1|" + canonical_domain + "|" + requisition_identity + "|" + candidate_identity)`; `requisition_identity` = `job_source.requisition_id` else cleaned `canonical_apply_url` else `f"{provider}:{source_job_id}"`; `candidate_identity` = sha256 of canonical profile JSON (`CandidateProfileConfig.model_dump_json(sort_keys)`); packet excluded by design.
- R16-I02 **SP2** · Opus/Sonnet · `submission_attempt` table + model: `id`; `application_id` FK NULL; `job_id` FK NOT NULL; `approval_id` FK `scoped_approval.id` NOT NULL; `idempotency_key` String(128) NOT NULL; `destination` String(512) NOT NULL; `method` String(64) NOT NULL; `packet_id` FK NOT NULL; `packet_hash` String(64) NOT NULL; `attempt_number` Integer NOT NULL; `state` String(32) NOT NULL (`PREPARED|AUTHORIZED|PREFLIGHT_VALIDATED|REQUEST_DISPATCHED|SUBMISSION_UNCONFIRMED|CONFIRMED|DEFINITE_PRE_SUBMIT_FAILURE|BLOCKED|NEEDS_REVIEW|CANCELLED`); `started_at` NOT NULL; `request_dispatched_at`, `response_received_at`, `completed_at` NULL; `error_category` String(64) NULL; `error_summary_redacted` String(512) NULL; `manifest_hash` String(64) NULL; `audit_ref` UUID NULL; `created_at`, `updated_at`. `external_confirmation_evidence` table + model: `id`; `attempt_id` FK NOT NULL; `source_type` String(32) NOT NULL (`CONFIRMATION_PAGE|PROVIDER_REFERENCE|ACCOUNT_STATE|CONFIRMATION_EMAIL|OTHER_REVIEWED`); `provider` String(64) NOT NULL; `external_reference` String(255) NULL; `observed_at` NOT NULL; `evidence_hash` String(64) NULL; `evidence_reference` String(512) NULL; `validation_method` String(64) NOT NULL; `confidence_category` String(32) NOT NULL; `independently_validated` Boolean NOT NULL **(no server default)**; `redacted_summary` Text NULL; `created_at`.
- R16-I03 SP1 · Opus/Sonnet · partial unique index `uq_submission_attempt_active_key` on `idempotency_key` where `state IN ('PREPARED','AUTHORIZED','PREFLIGHT_VALIDATED','REQUEST_DISPATCHED','SUBMISSION_UNCONFIRMED')` (`postgresql_where` and `sqlite_where`); concurrency test: two sessions inserting active attempts with the same key → second raises `IntegrityError` → engine maps to `BLOCKED DUPLICATE_ACTIVE_ATTEMPT`.
- R16-I04 SP1 · Sonnet · duplicate blocks: existing application `SUBMITTED|CONFIRMED` for the same requisition identity → BLOCKED duplicate; existing attempt `SUBMISSION_UNCONFIRMED` → NEEDS_REVIEW (no blind retry); duplicate local `JobModel` for same requisition → dedupe block.
- R16-I05 SP1 · Sonnet · tests: matrix "Idempotency" rows.

### A-V16-PREFLIGHT (all SP1 · Sonnet)
- R16-P01 explicit packet required when `mock_mode=False` (remove implicit latest-packet lookup on the real path).
- R16-P02 `packet.job_id == job.id` hard guard.
- R16-P03 resume/cover-letter artifact read-back SHA via `ArtifactStore.verify` immediately before dispatch.
- R16-P04 answer/provenance gate: unresolved consequential → NEEDS_REVIEW; `model_assisted` answer for personal-fact categories → BLOCKED/NEEDS_REVIEW; page prompt asking to ignore candidate truth → ignored + warning.
- R16-P05 gate order: policy → authorization → kill switch → rate pacing (no `record_submission` here) → adapter preflight.
- R16-P06 immutable `PreSubmitManifest` (Pydantic, fields per `V1_6_DATA_CONTRACTS`; stored as `ArtifactModel(type="pre_submit_manifest")`; `manifest_hash` on the attempt; any material mutation after creation invalidates it).
- R16-P07 tests for P01–P06.

### A-V16-CONFIRMATION (all SP1 · Sonnet)
- R16-C01 evidence model wiring (`automation/confirmation.py`).
- R16-C02 adapter/transport success → `REQUEST_DISPATCHED` → `SUBMISSION_UNCONFIRMED`; never `SUBMITTED` from `SubmissionResult.success`.
- R16-C03 ambiguous post-dispatch exception → `SUBMISSION_UNCONFIRMED` + NEEDS_REVIEW task; no blind retry.
- R16-C04 `ConfirmationValidator.validate(evidence) -> CONFIRMED|INSUFFICIENT`: requires `source_type` in the four validated classes, `independently_validated=True`, non-simulated provider; only then application `SUBMITTED` + `APPLICATION_SUBMITTED` event + approval consumed.
- R16-C05 tests: matrix "Confirmation truth" rows (forged artifact rejected; navigation insufficient; generated receipt insufficient).

### A-V16-HYGIENE (all SP1 · Sonnet)
- R16-H01 `_complete_tasks_for_job` closes only tasks whose `task_type` ∈ `{"SUBMIT_APPLICATION","PACKET_READY_FOR_SUBMISSION"}` (exact set decided from current task types) and linked to this job/application.
- R16-H02 rate limiter: `record_attempt()` on dispatch, `record_submission()` only on CONFIRMED; analytics excludes failed attempts.
- R16-H03 sanitize error/audit evidence via `worker.sanitize_error_message`; no token/secret substrings in persisted rows.
- R16-H04 tests: matrix "Audit/task hygiene" and "Concurrency/recovery" rows (crash after authorization → resumable; crash after dispatch → UNCONFIRMED; restart restores state; race → one winner; retry after timeout checks evidence first).

### A-V16-TRANSPORT (research now; implementation deferred)
- R16-T01 SP1 · Sonnet · `docs/V1_6_TRANSPORT_FEASIBILITY.md`: current public policy/technical feasibility for direct ATS submission (Greenhouse Job Board API application POST requires board-owner API credentials — verify; Lever/Ashby/Workday equivalents), evidence URLs, dates; no implementation.
- R16-T02 SP1 · lead · decision record: eligible transport (→ R16-T03..T05 later) or `LIVE_PROOF_BLOCKED_NO_ELIGIBLE_TRANSPORT`.
- R16-T03..T05, R16-L01..L06: **deferred after V2.3** (master plan D1).

## 10. Totals

Engineering tasks: 51 (R14-P 4, R14-I 5, R15-I 4, A-R15 4, R15-V 1, R17-E 6 incl. E03b, R16-A 4, R16-I 5, R16-P 7, R16-C 5, R16-H 4, R16-T 2) = 56 SP (all SP1 except R14-P01/P02 rated SP1 with high effort, A-R15-06/07/08 SP2, R16-A01 SP2, R16-I02 SP2). LIVE/gated items: R14-L (7), R15-L (7), R17-L (9), R16-L (6, deferred).

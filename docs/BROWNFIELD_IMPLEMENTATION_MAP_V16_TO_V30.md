# Brownfield Implementation Map — V1.6 to V3.0

Purpose:
Map future prepared tasks to the current repository so Antigravity extends existing systems instead of rebuilding them.

This is a snapshot of current `main`; worker must re-audit before implementation.

## V1.6 — Controlled submission

### Existing anchors

`src/jobs_automation/automation/auto_engine.py`
- `ControlledAutoApplicationEngine.execute_auto_apply()`
- current policy/kill-switch/rate-limit/adapter/packet flow
- current automatic retry loop
- current local status/event/audit write
- current `_complete_tasks_for_job()`

`src/jobs_automation/automation/base.py`
- `ValidationResult`
- `SubmissionResult`
- `ATSAdapter`

`src/jobs_automation/automation/adapters/registry.py`
- adapter selection

`src/jobs_automation/automation/adapters/greenhouse.py`
`src/jobs_automation/automation/adapters/lever.py`
- current live mode truthfully returns `NOT_IMPLEMENTED`
- mock simulation is explicitly labeled

`src/jobs_automation/policy/evaluator.py`
- deny by default
- expiry handling
- AUTO_ALLOWED calculation

`src/jobs_automation/core/policy_registry.py`
- MANUAL_ONLY / ASSISTED / AUTO_ALLOWED / BLOCKED
- config validation

`src/jobs_automation/db/models.py`
Existing useful models:
- ApplicationPacketModel
- ApplicationModel
- ApplicationEventModel
- TaskModel
- PolicyRegistryModel
- AuditLogModel
- ArtifactModel / ResumeVariantModel

### Current known V1.6 brownfield gaps

Based on lead audit/current code:
- real mode permits implicit "latest packet" lookup,
- explicit packet/job mismatch needs hard guard,
- no scoped SubmissionAuthorization persistence,
- no durable SubmissionAttempt model/state,
- ApplicationModel same-job SUBMITTED check is insufficient idempotency,
- ambiguous post-dispatch errors may be retried blindly,
- `SubmissionResult.success` can currently drive SUBMITTED without independent external confirmation,
- rate limiter calls `record_submission()` after attempts even when not confirmed,
- `_complete_tasks_for_job()` completes all pending job tasks,
- adapter `receipt_id` is not sufficient proof of external confirmation.

### Recommended extension strategy

Do not replace `ControlledAutoApplicationEngine`.

Refactor it into explicit stages:
1. resolve job/destination
2. evaluate current policy
3. validate authorization
4. resolve explicit packet
5. pre-submit packet/artifact integrity
6. dedupe/idempotency
7. kill switch/rate pacing
8. adapter preflight
9. durable attempt begin
10. dispatch once
11. reconcile/validate external confirmation
12. persist confirmed/unconfirmed/failed outcome
13. close only submission-specific tasks

Suggested new implementation surfaces:
- `src/jobs_automation/automation/authorization.py`
- `src/jobs_automation/automation/attempts.py`
- `src/jobs_automation/automation/confirmation.py`

Exact placement may adapt if existing architecture suggests a cleaner local module.

Likely schema/migration work:
- SubmissionAuthorizationModel
- SubmissionAttemptModel
- ExternalConfirmationEvidenceModel or equivalent normalized evidence representation

Avoid putting all durable submission semantics in JSON blobs on ApplicationModel.

### Existing tests to extend

`tests/test_auto_application.py`
Currently covers:
- adapter validation
- controlled apply success path
- live NOT_IMPLEMENTED
- unknown-question stop
- kill switch
- policy expiration
- rate limiting

`tests/test_policy.py`
Currently covers:
- deny by default
- LinkedIn/Indeed manual only
- assisted policies
- expiry
- explicit unexpired AUTO_ALLOWED

Add V1.6 adversarial cases from:
- `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`

---

## V1.7 — Recruiter CRM / lifecycle

### Existing anchors

`src/jobs_automation/lifecycle/crm.py`
- RecruiterCRMService
- contact identity
- application/contact timelines
- relink/unlink
- contact merge

`src/jobs_automation/lifecycle/engine.py`
- message processing
- lifecycle transition/audit
- thread-role divergence detection
- ambiguity/contradiction review routing

`src/jobs_automation/lifecycle/interview.py`
- explicit datetime/timezone parsing
- round detection
- reschedule reconciliation
- cancellation/update/idempotency

`src/jobs_automation/lifecycle/alerts.py`
- unanswered recruiter / stale application logic

### Existing regression strength

`tests/test_lifecycle.py` already includes tests for:
- recruiter CRM
- interview extraction
- lifecycle transitions
- ambiguity review
- unanswered/stale alerts
- idempotent repeated sweep
- no fabricated date
- explicit schedule/timezone
- reschedule
- cancellation
- stage regression prevention
- recruiter multi-role / cross-application timeline
- thread-role divergence
- auto-resolve unanswered on reply
- duplicate task suppression
- manual relink/unlink
- contact merge
- extended transitions
- classifier→lifecycle integration
- rejection protection
- background-check non-fabrication

### V1.7 implementation direction

Treat V1.7 as:
1. audit artifact acceptance criteria against existing code/tests,
2. identify actual gaps,
3. add only missing edge cases/evidence,
4. run full checks,
5. lead review.

Do not rewrite CRM/interview/lifecycle services for milestone optics.

---

## V2.0 — Integrated OS

### Gmail/ingestion anchors

`src/jobs_automation/adapters/gmail.py`
- GmailOAuthClient
- GmailAdapter
- MockEmailAdapter

`src/jobs_automation/ingestion/engine.py`
- ingestion transaction/checkpoint path

`src/jobs_automation/worker.py`
- sweep orchestration
- durable worker run/error behavior

`src/jobs_automation/health.py`
- operational health/status

Prepared Gmail contract:
- `docs/V2_0_GMAIL_RUNTIME_READINESS.md`

### Dashboard/analytics anchors

`src/jobs_automation/dashboard/server.py`
- current operator HTTP surfaces
- loopback/write safety

`src/jobs_automation/dashboard/analytics.py`
Existing:
- funnel summary
- source breakdown/performance
- role-family performance
- resume performance
- time-to-stage
- Kanban

`tests/test_dashboard.py` already covers:
- dashboard endpoints
- advanced metrics
- historical outcomes
- real-submission denominator
- neutral statistical wording/sample sizes
- write safety
- exclusion of simulation
- final interview/accepted rates

### V2.0 direction

Most work is integration, missing operator views, Gmail runtime safety, reliability drills, and live acceptance—not rebuilding core discovery/lifecycle/analytics.

Primary prepared acceptance:
- `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`
- `docs/V2_0_LIVE_ACCEPTANCE_RUNBOOK.md`
- `docs/V2_0_INTEGRATION_FIXTURE.md`

---

## V2.3 — Career intelligence

### Existing reusable foundations

- CompanyModel / JobModel / JobSourceModel
- ApplicationModel / ApplicationEventModel
- MessageLinkModel / ContactModel / InterviewModel
- ResumeVariantModel / ArtifactModel
- lifecycle CRM/timeline services
- dashboard analytics
- evaluation/dedupe/ingestion services

Current default-branch code search did not expose a dedicated TargetCompany/OpportunityEdge/experiment subsystem at prep time. Re-audit before implementation.

### Recommended new package boundary

Prefer a cohesive intelligence/service package rather than mixing V2.3 logic into dashboard rendering:

Possible:
- `src/jobs_automation/intelligence/opportunity_graph.py`
- `src/jobs_automation/intelligence/strategy.py`
- `src/jobs_automation/intelligence/target_companies.py`
- `src/jobs_automation/intelligence/interview.py`

Typed domain services first.
Dashboard/agents consume them later.

### Persistence

Use existing relational truth wherever possible.

Only add tables for genuinely missing durable concepts, e.g.:
- OpportunityEdge for evidence-backed relationships not represented by FKs
- TargetCompany
- TargetCompanyObservation
- StrategyExperiment / assignment

Avoid copying existing FK relationships into a generic graph table without need.

### Tool layer

After intelligence services stabilize, expose transport-neutral tools/services.
Do not couple core behavior to MCP/CrewAI/LangGraph.

---

## V3.0 — Agent network

### Foundation-first path

Do not start specialist agents before:
- V2.3 typed tools are stable,
- permission model is deterministic,
- durable AgentTask/checkpoints exist,
- shared memory semantics exist,
- evaluation/trace schema exists.

### Recommended package boundaries

Possible:
- `src/jobs_automation/agents/models.py` — AgentTask/definitions/checkpoints
- `src/jobs_automation/agents/permissions.py` — orchestration-facing permission client/interceptor
- `src/jobs_automation/agents/memory.py` — scoped memory
- `src/jobs_automation/agents/runtime.py` — leases/retries/checkpoints/router
- `src/jobs_automation/agents/registry.py` — specialist registry
- `src/jobs_automation/agents/tracing.py` — task/model/tool traces
- `src/jobs_automation/agents/evaluation.py` — offline eval harness
- `src/jobs_automation/tools/` or equivalent — transport-neutral V2.3 tool facade

These are proposed locations, not permission to bypass existing architectural conventions. Re-audit before implementation.

### No direct canonical DB bypass

Specialist agents should consume stable services/tools.

Particularly:
- Application Operator must use V1.5/V1.6 execution services.
- CRM Agent must use lifecycle/CRM services.
- Interview Agent must use V2.3 interview-intelligence services.
- Analytics Agent must use accepted analytics/strategy services.
- Policy/Safety Agent audits but deterministic enforcement remains authoritative.

### Prepared V3 contracts

- `docs/V3_PERMISSION_MODEL.md`
- `docs/V3_TOOL_PERMISSION_MATRIX.md`
- `docs/V3_RUNTIME_DATA_CONTRACTS.md`
- `docs/V3_SHARED_MEMORY_CONTRACT.md`
- `docs/V3_AGENT_HANDOFF_PROTOCOL.md`
- `docs/V3_SPECIALIST_AGENT_SPECS.md`
- `docs/V3_AGENT_EVAL_MATRIX.md`
- `docs/V3_INTEGRATION_ACCEPTANCE_SCENARIOS.md`

## Worker efficiency rule

Before implementing a prepared task:
1. inspect the named current anchor,
2. reuse existing behavior,
3. add the smallest stable abstraction needed,
4. avoid duplicate sources of truth,
5. add adversarial/regression tests,
6. preserve current safety semantics,
7. keep each implementation batch <= SP5.

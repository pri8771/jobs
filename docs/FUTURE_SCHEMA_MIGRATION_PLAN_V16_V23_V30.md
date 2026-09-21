# Future Schema / Migration Plan — V1.6, V2.3, V3.0

Current migration chain at prep time:
- 001_initial_foundation
- 002_resume_variant_attribution
- 003_generation_origin_readiness

This plan is preparation only. Do not create these migrations until the corresponding phase gate opens and the implementation worker re-audits current main.

## Design rules

- migrations are additive and reversible where practical,
- one phase should not pre-create speculative V3 tables during V1.6,
- canonical existing FKs remain the source of truth,
- avoid JSON-only persistence for identities/state that need uniqueness, locking, or referential integrity,
- create indexes/constraints for idempotency and worker queries,
- downgrade must be tested,
- migrations must work for SQLite test/dev semantics and PostgreSQL production semantics where the project supports both.

# Proposed 004 — V1.6 submission truth

Suggested tables:

## submission_authorization
- id UUID PK
- job_id FK job
- application_id nullable FK application
- packet_id FK application_packet
- packet_hash string64
- candidate_profile_version int
- resume_variant_id nullable FK resume_variant
- resume_artifact_sha256 string64
- destination string/url/domain
- destination_provider nullable
- method string
- action string
- authorized_by string
- authorization_reference nullable
- policy_version/reference
- issued_at
- expires_at
- one_time_use bool
- consumed_at nullable
- revoked_at nullable
- status string

Indexes:
- job_id
- packet_id
- status
- expires_at

## submission_attempt
- id UUID PK
- application_id nullable FK application
- job_id FK job
- authorization_id FK submission_authorization
- idempotency_key string
- destination
- method
- packet_id FK application_packet
- packet_hash
- attempt_number
- state
- started_at
- request_dispatched_at nullable
- response_received_at nullable
- completed_at nullable
- error_category nullable
- error_summary_redacted nullable
- external_confirmation_id nullable FK external_confirmation_evidence
- audit_ref nullable

Constraints:
- durable uniqueness preventing concurrent active attempts for the same logical idempotency identity.
Exact DB representation should match implementation semantics.

## external_confirmation_evidence
- id UUID PK
- attempt_id FK submission_attempt
- source_type
- provider
- external_reference nullable
- observed_at
- evidence_hash nullable
- evidence_reference nullable
- validation_method
- confidence/category
- independently_validated bool
- redacted_summary nullable

Cycle note:
If FK cycle between attempt and confirmation complicates migration, keep attempt.external_confirmation_id nullable and add FK after both tables, or use confirmation.attempt_id as the authoritative relation.

No raw secrets/private page bodies required.

# Proposed 005 — V2.3 intelligence foundation

Create only concepts not already represented by current relational truth.

## target_company
- id UUID PK
- company_id nullable FK company
- canonical_name/domain fallback
- priority
- reason/strategy note
- target_role_families JSON or normalized child table depending query pressure
- compensation_floor nullable
- location/remote constraints
- watch_status
- created_at/updated_at

## target_company_observation
- id
- target_company_id FK
- observation_type
- source_type
- source_reference
- observed_at
- confidence
- normalized_payload
- dedupe_key
- status

Unique/index:
- target_company_id + dedupe_key

## opportunity_edge
Only for relationships not represented cleanly by existing FKs:
- id
- subject_type/id
- predicate
- object_type/id
- source_type
- source_reference
- confidence
- evidence_hash nullable
- valid_from
- valid_to nullable
- status ASSERTED | REVIEW_REQUIRED | INVALIDATED
- created_at/updated_at

Index:
- subject_type/id
- object_type/id
- predicate/status
- source_reference

## strategy_experiment
- id
- hypothesis
- target_population_json
- metric_definition_json
- status
- created_at
- started_at nullable
- ended_at nullable
- created_by

## strategy_experiment_assignment
- id
- experiment_id FK
- application/job identity
- treatment_type
- resume_variant_id nullable
- treatment_payload/hash
- assigned_at
- immutable assignment identity

Do not retroactively infer treatment.

# Proposed 006 — V3 permission/runtime foundation

May be split into smaller revisions if implementation benefits.

## scoped_approval
- approval_id
- actor
- action_class
- target_refs structured
- artifact/hash refs
- method/transport
- policy_version
- issued_at
- expires_at
- one_time
- consumed_at nullable
- revoked_at nullable
- status

This may reuse/bridge V1.6 SubmissionAuthorization for application-specific submit approvals rather than duplicating semantics. Prefer one generalized permission service with compatible migration path.

## agent_task
- task_id PK
- parent_task_id nullable self-FK
- root_goal_id
- task_type
- requested_by
- assigned_agent_id nullable
- goal
- constraints JSON
- input_artifact_refs JSON
- expected_output_types JSON
- permission_ceiling
- model_policy_id
- max_cost nullable
- status
- attempt
- lease_owner nullable
- lease_expires_at nullable
- checkpoint_ref nullable
- timestamps
- error/review fields
- output_artifact_refs JSON

Indexes:
- status
- assigned_agent_id
- lease_expires_at
- root_goal_id

## agent_checkpoint
- checkpoint_id
- task_id FK
- attempt
- completed_step_ids
- pending_step_ids
- output_artifact_refs
- outstanding_approval_refs
- external_action_state
- created_at

## agent_memory
- memory_id
- memory_class
- entity/task scope
- source_refs
- payload
- confidence nullable
- sensitivity_class
- allowed_agent_scopes
- created/updated
- review_at/valid_until
- supersedes/superseded_by
- invalidated_at

## agent_trace_event
- trace_id
- root_goal_id
- task_id FK
- agent/version
- event_type
- model/provider nullable
- tool refs
- permission decision ref
- artifact refs
- cost/tokens/latency nullable
- timestamp
- error category/details safe

Potential high-volume trace storage can be revisited after real scale. Start simple.

# Proposed 007 — optional V3 eval/registry persistence

Only if code/config files are insufficient.

Possible:
- agent_definition registry table
- model_policy table
- evaluation_run/evaluation_case result tables

Do not persist configuration merely for architectural symmetry if versioned Git config is simpler and auditable.

# Migration acceptance for every revision

- model definitions and migration agree,
- fresh upgrade from zero succeeds,
- incremental upgrade from prior head succeeds,
- downgrade to prior revision succeeds,
- upgrade again succeeds,
- constraints/indexes tested,
- JSON defaults safe on SQLite/Postgres,
- no existing rows become misleadingly "confirmed"/"authorized" through server defaults,
- live/external state defaults fail closed.

# Data Model

The runtime database should use UUID primary keys and UTC timestamps.

## candidate_profile

Canonical reusable candidate facts.

Important fields:
- id
- version
- structured_profile_json
- created_at
- superseded_at

Sensitive or volatile fields may live outside Git and be loaded at runtime.

## source_account

Represents a job-board/source identity.

Fields:
- id
- provider
- external_account_hint
- enabled
- profile_status
- alert_status
- last_verified_at

Never store passwords here.

## source_alert

Represents a configured search/alert.

Fields:
- id
- source_account_id
- name
- query_json
- cadence
- email_match_rule
- enabled

## inbound_message

A normalized Gmail message.

Fields:
- id
- provider_message_id
- provider_thread_id
- received_at
- sender
- subject
- headers_json
- body_text
- body_html_hash
- classification
- raw_reference
- created_at

Unique constraint on provider_message_id.

## company

Fields:
- id
- normalized_name
- domain
- aliases_json

## job

Fields:
- id
- company_id
- normalized_title
- location_text
- remote_type
- employment_type
- compensation_min
- compensation_max
- compensation_currency
- description_text
- description_hash
- posted_at
- first_seen_at
- last_seen_at
- status

## job_source

Links a normalized job to a source listing.

Fields:
- id
- job_id
- provider
- source_job_id
- source_url
- canonical_apply_url
- requisition_id
- source_payload_json
- first_seen_at
- last_seen_at

## job_evaluation

Fields:
- id
- job_id
- profile_version
- rules_version
- decision
- score
- reason_codes_json
- explanation
- model_provider
- model_name
- prompt_version
- created_at

## application

Fields:
- id
- job_id
- status
- application_mode
- destination_domain
- policy_decision
- policy_version
- packet_id
- applied_at
- last_activity_at
- closed_at

Unique active application per job unless explicitly overridden.

## application_packet

Fields:
- id
- job_id
- candidate_profile_version
- resume_artifact_id
- cover_letter_artifact_id
- answers_json
- unresolved_questions_json
- packet_hash
- created_at

## artifact

Represents a resume, cover letter, exported PDF, text answer pack, or other application material.

Fields:
- id
- type
- storage_uri
- sha256
- metadata_json
- created_at

## application_event

Append-only lifecycle event.

Fields:
- id
- application_id
- event_type
- occurred_at
- source
- source_reference
- payload_json
- actor
- created_at

## message_link

Links inbound messages to entities.

Fields:
- id
- inbound_message_id
- job_id nullable
- application_id nullable
- company_id nullable
- confidence
- method
- created_at

## contact

Recruiter, hiring manager, coordinator, or other job-related contact.

Fields:
- id
- company_id
- name
- email
- role
- source

## interview

Fields:
- id
- application_id
- round_type
- scheduled_start
- scheduled_end
- timezone
- location_or_link
- status
- notes

## task

Follow-up or manual-review work item.

Fields:
- id
- application_id nullable
- job_id nullable
- task_type
- due_at
- status
- payload_json

## policy_registry

Fields:
- id
- platform
- domain_pattern
- adapter
- capability
- decision
- evidence_url
- reviewed_at
- review_due_at
- notes

## audit_log

Append-only external-action record.

Fields:
- id
- action_type
- entity_type
- entity_id
- actor
- input_hash
- result
- external_reference
- occurred_at
- metadata_json

## Core invariants

- provider message IDs are unique
- job/source IDs are deduplicated
- submit operations use idempotency keys
- every application state change emits an application_event
- every external write emits an audit_log record
- automatic submit requires an unexpired AUTO_ALLOWED policy decision

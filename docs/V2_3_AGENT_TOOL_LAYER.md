# V2.3 Agent Tool Layer Contract

Artifact: A-V23-AGENT-TOOLS

## Purpose

Expose stable typed career operations to future agents without coupling business logic to MCP, LangGraph, Claude, ChatGPT, or another framework.

## Principle

Agents call service/tool interfaces.
They do not mutate the database directly.

Transport-neutral first; MCP can wrap the same interfaces later.

## Read tools

Examples:
- list_jobs(filters)
- get_job(job_id)
- get_application(application_id)
- get_application_timeline(application_id)
- list_contacts(company_id?)
- get_contact_history(contact_id)
- list_interviews(filters)
- list_review_queue()
- get_resume_variant(variant_id)
- get_resume_performance(filters)
- get_company_context(company_id)
- get_opportunity_graph(entity)
- get_policy_decision(destination, capability)
- get_worker_health()

## Preparation tools

Examples:
- evaluate_job(job_id)
- prepare_application_packet(job_id, resume_family?)
- generate_interview_brief(application_id)
- draft_followup(application_id/contact_id)
- propose_network_connection(contact/company context)

These may create local artifacts but not perform external side effects.

## External-action tools

Examples:
- open_assisted_application(...)
- send_message(...)
- submit_application(...)
- update_external_calendar(...)

Every external-action tool must:
- declare required permission class,
- validate policy,
- validate user approval when required,
- produce audit evidence,
- be idempotent where applicable.

## Tool result envelope

Every tool result should include:
- tool name/version
- request ID
- status
- artifact/entity references
- evidence/source references
- warnings/review needs
- audit reference
- error class if failed

## Error behavior

Do not convert:
- permission denied,
- missing fact,
- unresolved review,
- provider unavailable

into a generic success response.

## Audit

Persist:
- agent identity
- tool
- request hash
- referenced artifacts
- permission decision
- result
- external reference when applicable

## Acceptance

- tool interfaces can be called without an agent framework.
- mock/simulation results are explicitly labeled.
- no agent can bypass service-level policy by writing DB state directly.
- transport wrapper can be swapped without changing domain behavior.

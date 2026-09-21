# V3 Shared Memory Contract

Artifact:
- A-V30-SHARED-MEMORY

## Purpose

Give V3 specialist agents durable continuity without allowing agent-written summaries to become a competing source of truth.

## Principle

Canonical domain truth stays in:
- candidate provenance/profile,
- jobs/applications,
- messages/contacts/interviews,
- artifacts/manifests,
- policy/permission records,
- analytics/outcomes,
- opportunity graph evidence.

Agent memory stores references, derived summaries, working state, and learned preferences/strategy hypotheses.

Derived memory never overwrites raw evidence.

## Memory classes

### M0 Canonical reference
Pointer to authoritative entity/artifact/event.
Agents may cite/read but not replace it.

### M1 User-confirmed durable preference
Explicit preference/constraint with provenance and timestamp.
Examples:
- preferred role families,
- location/remote preference,
- compensation target,
- networking style preference.

### M2 Derived durable summary
Evidence-backed synthesis with source refs and generated/version metadata.
Must be recomputable or invalidatable.

### M3 Task/session working memory
Short-lived plan/checkpoint/intermediate state for a durable AgentTask.

### M4 Strategy hypothesis
A proposed belief/recommendation based on outcomes.
Carries sample size, evidence, uncertainty and expiration/review date.

## Required fields

- memory_id
- class
- subject/entity scope
- owner/source agent
- source_refs
- content or structured payload
- confidence if derived
- created_at
- updated_at
- valid_until/review_at when appropriate
- supersedes/superseded_by
- sensitivity class
- permitted agent/tool scopes

## Write rules

Agents may:
- add task checkpoints,
- create derived summaries,
- propose strategy hypotheses,
- store user-confirmed preferences after explicit confirmation.

Agents may not:
- change canonical candidate facts through memory,
- convert model inference into user-confirmed truth,
- remove source evidence,
- store secrets/tokens,
- expand permissions through memory,
- store an external success without canonical external evidence.

## Retrieval rules

- retrieve by task/entity relevance,
- prefer canonical refs over summaries,
- include source links for consequential reasoning,
- respect sensitivity/agent scope,
- stale/superseded memory is not returned as current without labeling.

## Invalidation

Memory becomes stale/invalid when:
- source artifact invalidated,
- newer user confirmation supersedes preference,
- strategy window expires,
- application/job state changes materially,
- evidence conflict discovered.

## Evaluation

Test:
- conflicting old/new preference,
- stale recruiter summary after new message,
- model-inferred fact cannot become candidate truth,
- permission denial cannot be bypassed via memory,
- task restart restores M3 checkpoint,
- one agent cannot read memory outside its scope,
- summary recomputation preserves source links.

## Acceptance

V3 runtime can resume and coordinate agents using durable scoped memory while every consequential fact remains traceable to canonical truth.

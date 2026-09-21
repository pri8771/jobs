# Cross-Lane Integration Matrix — V2.0 / V2.3

Updated after fresh code re-audit.

## Purpose

Prevent individually correct worker branches from failing when merged together.

This document defines the interfaces each lane may depend on and the merge/review order.

## Lane A -> shared system

Producer:
- ApplicationPacketModel
- ResumeVariantModel
- ArtifactModel
- browser/pre-submit evidence

Stable fields now on main:
- ApplicationPacket.id
- job_id
- resume_variant_id
- resume_artifact_id
- cover_letter_artifact_id
- packet_hash
- is_live_ready
- generation_metadata_json
- unresolved_questions_json
- answer_provenance_json

Consumers:
- Lane B analytics
- Lane D read-only agent tools
- V1.6 submission engine

Rules:
- consumers must not infer live readiness from packet existence alone,
- exact resume attribution comes through packet -> resume_variant,
- submitted analytics must use real application/lifecycle evidence, not packet existence.

## Lane B -> shared system

Producer:
- ApplicationEvent evidence
- recruiter/contact timelines
- InterviewModel state
- dashboard/analytics services

Consumers:
- V2 integration fixture
- Lane D opportunity graph / tool wrappers
- future V3 agents

Required semantics:
- source_reference must support idempotency,
- historical reached stages must remain reconstructable even after current status changes,
- contradictory/ambiguous evidence routes to review,
- current Application.status is current state, not complete history.

## Lane C -> Lane B health integration

Producer:
- GmailReadinessReport from J20G-03

Required shape:
- mode = REAL
- configured
- token_path safe path only
- token_present
- credentials_parseable
- refresh_ok
- api_canary_ok
- scopes
- error_category
- checked_at

Lane B / health consumer must:
- treat ready only when required REAL checks pass,
- never inspect OAuth token values,
- never trigger interactive OAuth,
- expose safe readiness/error/timestamp only.

Do not use environment-variable heuristics after this interface is available.

## Lane C -> V2 integration

Producer:
- candidate provenance service
- real Gmail adapter safety
- bounded Gmail diagnostic

Consumers:
- packet/application validation
- health
- integration fixture

Provenance integration rule:
- `allowed_for_application` is an additional gate, not a replacement for existing packet field provenance.
- demographic/self-ID stays manual regardless of provenance availability.

## Lane D -> V3

Producer:
- opportunity graph projection
- target-company service
- transport-neutral agent tools

Consumers:
- V3 agent runtime

Rules:
- read-only graph projection must reference V2 relational truth,
- no duplicated authoritative datastore,
- no direct DB writes from agents,
- external-action tool contracts may be defined but not implemented as side effects in V2.3 foundation batch.

## Shared DB schema

Current merge-sensitive files:
- src/jobs_automation/db/models.py
- migrations/versions/

Rule:
Only one lane should modify shared schema in a coherent integration window unless ChatGPT explicitly coordinates both migrations.

Current:
- Lane A migration 003 is on main.
- B repair should avoid schema changes.
- C should avoid schema changes for provenance unless lead explicitly approves; prefer service/config representation first.
- D must not add schema in its current V2.3 foundation batch.

## Merge order

Independent batches should be reviewed in this order when available:

1. Lane B bounded rework if it has no schema conflict.
2. Lane C Gmail/provenance foundation.
3. Lane A V1.5 engineering.
4. Lane D V2.3 foundations.

Actual order may change based on readiness; this is not a milestone dependency.

After B + C:
- perform J20G-04 health integration.

After A + B + C stable:
- implement/run A-V20-INTEGRATION-FIXTURE.

## Integration regression invariants

Every final V2 integration run must prove:

1. same provider message replay does not duplicate entities/events,
2. current terminal status does not erase historical stages from analytics,
3. mock packet/browser/Gmail evidence never counts as live,
4. exact resume variant remains reconstructable,
5. unknown/private candidate facts cannot become application truth,
6. Gmail partial fetch cannot advance checkpoint,
7. health cannot report REAL Gmail ready from config heuristics,
8. dashboard mutations are protected,
9. worker crashes/failures are visible in operational evidence,
10. no branch creates a second authoritative truth store.

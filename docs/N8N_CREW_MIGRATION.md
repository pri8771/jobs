# Jobs crew migration to n8n — owner direction, 2026-09-25

Status: migration specification, not a claim that the n8n replacement is installed, live, or accepted.

The owner wants the Jobs mission run as a long-lived n8n crew. Current Python code is reference material for behavior, data contracts, and evidence, not a default implementation to preserve. The broader shared-tool architecture is recorded in `pri8771/bots/ops/N8N_CREW_PLATFORM_PLAN.md`. Every crew, including Jobs, may discover and request any qualified tool through the shared action gateway; credentials and consequential actions remain scoped.

## Behavior to retain

| Capability | Existing reference | n8n migration acceptance |
| --- | --- | --- |
| Discovery | `README.md`, `docs/ARCHITECTURE.md`, `src/jobs_automation/ingestion/` | Ingest email alerts and supported public ATS sources; normalize, deduplicate, retain source and freshness. |
| Matching and materials | `docs/CANDIDATE_POSITIONING.md`, `src/jobs_automation/evaluation/`, `preparation/` | Use verified candidate facts and the correct resume variant; retain reasons, version, and unresolved facts. |
| Application actions | `docs/PLATFORM_CONSTRAINTS.md`, `docs/AUTHORIZATION_GATES.md`, `browser/`, `automation/` | Respect destination policy and action-specific approval. LinkedIn/Indeed submission remains manual unless a currently permitted route is established. A prefill, attempted submit, and confirmed submission are separate states. |
| Mail and CRM | `docs/EMAIL_TRACKING.md`, `src/jobs_automation/lifecycle/` | Preserve Gmail message/thread IDs, company/job/application linkage, recruiter replies, interview changes, follow-ups, and source evidence. Do not send recruiter mail merely because ingestion works. |
| Analytics and learning | `docs/RESUME_OUTCOME_TRACKING.md`, `src/jobs_automation/dashboard/analytics.py` | Preserve submission, recruiter response, screen, interview, offer, and acceptance rates with truthful denominators. Compare resume variants only with sufficient evidence. |
| Audit and recovery | `docs/LIVE_CHECKPOINT_EVIDENCE_STANDARD_V14_V17.md`, `docs/V3_SHARED_MEMORY_CONTRACT.md` | Record proposed, allowed, denied, attempted, delivered, and externally verified actions; idempotent replay and agent/crew lessons. |

## Migration sequence

1. Inventory current Jobs runtime, schedules, credentials, database, active owner, live data, and exact accepted features. Reconcile contradictory older version/status documents against current code and external evidence.
2. Export a redacted schema/field map and backup. Keep original private candidate, resume, Gmail, and application evidence out of Git.
3. Build n8n workflows for ingestion, triage, preparation, approval, permitted action, lifecycle correlation, follow-up, analytics, and learning. Use PostgreSQL for durable state; do not place a whole mission in one long-running execution.
4. Run nonpublic fixtures, then authorized bounded live reads. Check deduplication, state transitions, response-rate denominators, and error/restart behavior.
5. Cut over each old scheduler only after its n8n replacement has destination evidence and a rollback path. Do not count a prompt, draft, local test, or HTTP 200 as a real application or recruiter response.

This document changes future architecture. It does not itself grant mailbox access, profile use, application submission, public messaging, or retirement of the existing system.

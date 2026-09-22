# Jobs A-V20-CONTROL-CENTER J20-01 read-only inventory

## Identity and scope

- Source: `832d85f5177ca82564c9d0b6c168790f26ea1dc3`
- Tree: `047eb8501e562cbbca450e946e260a1b8454f74b`
- Contract: `coordination/artifacts/A-V20-CONTROL-CENTER.md`; released by the formal verdict at `0c89bc9aa20d55e4b759b0117502b664ab8cf18e`.
- Method: static production-code and existing-test inventory only. No service, database, browser or test was run.

All listed API operations are GET and execute in the request handler's database session (`dashboard/server.py:498-775`). The embedded HTML has seven views: funnel analytics, Kanban, discovered jobs, review queue, interviews, recruiter contact list and audit (`server.py:95-103`).

## Acceptance-surface inventory

| Required surface | GET route and selection criteria | Returned fields | Embedded view / existing test |
|---|---|---|---|
| New jobs / shortlist | `/api/jobs`; latest 100 `JobModel` rows by `first_seen_at DESC`, with no status predicate (`server.py:522-540`). Shortlist is represented only by `JobModel.status == "shortlisted"`; evaluation records separately contain decision, score, reason codes and explanation (`db/models.py:179-197`). | id, company, title, remote_type, status, apply_url, first_seen_at | Discovered Jobs table renders company/title/remote/status/date/link (`server.py:157-177,336-369`). Existing test proves only one title is returned (`tests/test_dashboard.py:257-263`); it does not prove shortlist/evaluation visibility. |
| Review queue | `/api/reviews`; every pending `TaskModel`, due time ascending/null last (`server.py:543-560`). | id, job_id, `reason` = task_type, payload, status, due_at | Review Queue renders type, raw payload, due time and a resolve action (`server.py:179-197,372-403`). Existing test checks only row identity (`test_dashboard.py:228-255`). |
| Application pipeline | `/api/kanban`; every application ordered by last activity and bucketed into seven normalized columns (`analytics.py:539-590`). | id, job_id, company, title, status, policy_decision, application_mode, applied_at, last_activity_at | Kanban view exists. Existing test checks column names, not card semantics (`test_dashboard.py:220-226`). |
| Recruiter contacts / timeline | `/api/contacts`; all contacts by last_contact_at (`server.py:591-611`). `/api/timeline?application_id=UUID` uses linked messages; `?contact_id=UUID` uses contact aliases and lifecycle references; malformed UUID is 400; missing selector returns `[]` (`server.py:685-709`, `lifecycle/crm.py:114-142,211-247`). | contacts: id/name/email/role/company/last_contact_at. Timeline: message/provider/thread IDs, direction, sender, subject, received_at, classification, snippet; contact timeline also application_id. | UI exposes contact list only; it has no timeline navigation (`server.py:218-236,425-444`). Existing dashboard test calls only selector-less `/api/timeline` and therefore proves the intentional empty default, not either real timeline (`test_dashboard.py:315-320`). |
| Interviews | `/api/interviews`; all interviews ordered scheduled_start descending (`server.py:563-589`). | id, application_id, company, round_type, start/end, location_or_link, status | Interviews table exists (`server.py:199-216,405-423`). |
| Follow-ups | `/api/followups`; all tasks whose type is unanswered recruiter or stale application/screening follow-up, all statuses, due time ascending/null last (`server.py:639-663`). | id, application_id, job_id, task_type, status, due_at, payload | API only; no embedded view. Existing test asserts only list shape (`test_dashboard.py:280-285`). |
| Offers / rejections | `/api/offers-rejections`; applications in six offer/terminal statuses, last activity descending (`server.py:711-738`). | application_id, company, title, status, applied_at, closed_at, last_activity_at | API only; no embedded view. Existing test asserts only list shape (`test_dashboard.py:322-327`). |
| Audit trail | `/api/audit`; latest 50 audit rows by occurred_at descending (`server.py:613-632`). | id, action_type, entity_type, actor, result, occurred_at, metadata | Audit table exists (`server.py:238-250,446-465`). Existing test asserts only list shape (`test_dashboard.py:265-270`). |
| Source / Gmail / worker health | `/api/health` returns `HealthCheckService.run_full_check()`; `/api/worker` reads latest 20 legacy `worker_sweep` audit entries; `/api/sources` and `/api/analytics/sources` provide source counts/performance (`server.py:507-515,634-637,665-668,758-775`). | health structured component report; worker id/result/time/metrics; source analytics service outputs | Funnel/source counts have a view. Health and worker are API only. Existing tests verify health top-level keys and worker list shape (`test_dashboard.py:272-278,336-341`). |
| Policy / kill switch | `/api/policies` returns every registry policy (`server.py:740-756`); kill-switch state is available only within `/api/health`. | policy id/platform/domain/capability/decision/adapter/review dates; health component details | API only; no embedded view. Existing policy test asserts only list shape (`test_dashboard.py:329-334`). |
| Safe read-only config/status | No `/api/config`, `/api/status`, or equivalent GET branch exists in `DashboardRequestHandler.do_GET` (`server.py:498-775`). CLI config/status commands are not dashboard read surfaces. | None | No embedded view and no dashboard test. |

## Stop point and unchecked areas

The root coordinator stopped this lane after a separate agent reproduced the first concrete control-center gap: `/api/worker` reads only legacy `AuditLogModel.action_type == "worker_sweep"` entries (`server.py:758-775`), whereas current worker execution truth is durable `worker_run` / finished-run state used by health. Therefore a current successful worker run can be visible in `/api/health` while `/api/worker` returns no corresponding run. Root owns the actual PostgreSQL reproduction and the single bounded repair request; this inventory does not duplicate or independently claim that evidence.

Per the stop instruction, no further diagnostic was performed. The following remain static inventory observations only and are **unchecked as defect claims**:

- safe read-only config/status has no identified dashboard GET branch;
- several API surfaces have no embedded HTML view;
- the jobs endpoint/view exposes status but not evaluation score/reasons;
- externally derived values flow into HTML rendering, but no exploit reproduction was performed by this lane.

No repair or new test is proposed here. Root should use its reproduced `/api/worker` gap as the first bounded control-center finding and defer these observations until that review cycle finishes.

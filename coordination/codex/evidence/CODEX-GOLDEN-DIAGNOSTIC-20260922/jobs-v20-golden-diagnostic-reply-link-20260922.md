# Jobs V2.0 golden diagnostic: candidate reply linkage

Source: `e1dbfeb6d4ddac9c49a5ac2b3d8d0a5c6ebc8273` (tree `e5409f04e15ca7d21dd2357c000c03e5c53ebd09`).
Evidence class: synthetic engineering diagnostic only. The job/application were explicitly seeded prior state. Addresses used `.invalid`; MockEmailAdapter performed no external action.

## Result

Partial integration failure reproduced. The real `EmailIngestionEngine -> WorkerDaemon -> LifecycleAlertService` path ingested an outbound `CANDIDATE_REPLY`, and the pending `UNANSWERED_RECRUITER` task changed from `pending` to `completed` with its exact `resolved_by_reply_id`. The redacted lifecycle truth export included the reply as `thread_sibling`.

The reply was not linked to the application (`reply_link_count=0`), produced no application event, did not advance `Application.last_activity_at`, and was absent from both `RecruiterCRMService.get_timeline_for_application()` and `get_timeline_for_contact()`. Those CRM timelines contained only the recruiter inbound message.

Expected for golden step 13: candidate outbound reply closes/suppresses the unanswered task and is attributable in the application/contact CRM record without inventing a lifecycle stage transition.

Actual: closure succeeds by thread scan, but CRM attribution remains incomplete.

## Root cause

- `ingestion/engine.py:268-277` sends only confirmation/interview/rejection/offer/outreach classifications through `_link_recruiting_message`; `CANDIDATE_REPLY` is excluded.
- `lifecycle/engine.py:103-110` returns immediately when no application MessageLink exists, so it cannot record reply activity/event.
- `lifecycle/alerts.py:81-130` independently searches outbound messages by thread and therefore correctly resolves the alert.
- `lifecycle/crm.py:80-108` builds application CRM timelines only through MessageLink rows, so it omits the unlinked reply.
- `lifecycle/timeline.py:89-104` separately includes same-thread siblings, which explains why the redacted truth timeline is complete while CRM is not.

This is the first diagnosed gap; no implementation or broader fixture was attempted.

Artifacts:
- `/tmp/jobs-v20-golden-diagnostic-reply-link-20260922.py`
- `/tmp/jobs-v20-golden-diagnostic-reply-link-20260922.out`
- `/tmp/jobs-v20-golden-diagnostic-migrate-20260922.log`
- `/tmp/jobs-v20-golden-diagnostic-cleanup-20260922.log`

Execution exit 0; owned PostgreSQL database cleanup count 0.

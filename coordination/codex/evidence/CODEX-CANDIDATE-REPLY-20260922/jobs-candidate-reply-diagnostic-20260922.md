# Candidate reply attribution pre-edit diagnostic

Base inspected: `/Users/pchordia/Downloads/swarm_codex/review/jobs-fixture-source` at accepted `e1dbfeb6d4ddac9c49a5ac2b3d8d0a5c6ebc8273` (clean). Release read from `origin/codex/portfolio-review-20260922@398656d055e58b879dd433bec70df622756e6c18`.

## Narrow implementation path

1. Add an ingestion helper invoked only after persistence when `msg.direction == "outbound"` and `msg.classification == "CANDIDATE_REPLY"`. The current dispatch excludes replies (`ingestion/engine.py:246-292`); inbound recruiting linkage is company matching (`:335-387`) and must not be reused.
2. Query strictly earlier messages in the same `provider_thread_id`; exclude the reply itself and `_provider.canary == true`. Join their `MessageLinkModel` rows with non-null `application_id`. Do not use sender/company/address matching.
3. Resolve distinct application IDs. Zero means no action. More than one, or any prior link below the existing lifecycle threshold `0.8` (`lifecycle/engine.py:95-127`), means one idempotent `NEEDS_REVIEW` task and no link/event. For a single application, use the minimum prior-link confidence (conservative evidence aggregation), never `1.0`; validate/copy consistent prior job/company IDs. Existing-link lookup by reply message ID must precede insertion because `message_link` has no uniqueness constraint (`db/models.py:318-336`).
4. Let `LifecycleEngine.process_message()` create the stage-preserving event after the new link is visible. Add `CANDIDATE_REPLY: CANDIDATE_REPLIED` to the evidence-only path (`lifecycle/engine.py:67-71, 169-203`), preserving status/closed/interview state and updating `last_activity_at` with `max(existing, message.received_at)`. The existing application + source-reference check (`:135-148`) supplies event replay idempotency.
5. Before recording that event, resolve contact only from prior same-thread lifecycle evidence for the same application: prior provider message IDs -> `ApplicationEventModel(source="email_lifecycle", source_reference in ids)` -> payload `contact_id`. Validate referenced contacts exist. Exactly one ID may be attached; zero or multiple yields `contact=None` without creating a contact. Never call `get_or_create_contact` for outbound mail (`:159-168`). `_record_event_and_audit` already emits candidate actor and `contact_id` (`:320-364`).

## Existing read surfaces that then work without special casing

- Application CRM timeline joins MessageLink directly (`lifecycle/crm.py:80-108`).
- Contact timeline admits candidate-sent messages only through event source reference/contact ID (`lifecycle/crm.py:130-154, 177-213`).
- Redacted timeline already renders actual `link.method/confidence`; without a link it labels a thread sibling (`lifecycle/timeline.py:78-130`). New link method should be `thread_reply_attribution`.
- Alert resolution is a separate same-thread outbound check (`lifecycle/alerts.py:81-131`); leave it unchanged.

## Pitfalls

- Existing ambiguity helpers always append a new review task (`ingestion/engine.py:375-387`; `lifecycle/engine.py:401-418`). The new review path needs a stable `reason_code` plus provider/message ID lookup so repeated lifecycle/restart passes retain one task.
- Ingestion provider-message dedupe (`ingestion/engine.py:197-206`) helps normal replay but is not enough to guarantee link/review idempotency for reconciliation or direct lifecycle reruns.
- Do not accept a high-confidence link merely because all links name one app if another link for that app is below `0.8`; that silently discards uncertainty. Use the conservative minimum and route review.
- Do not use the outbound sender to create/lookup a recruiter. It is the candidate by contract.
- Do not overwrite `last_activity_at` backward. Current evidence/general paths assign directly (`lifecycle/engine.py:176, 207, 275`); the new reply path must be monotonic.
- Avoid broad changes to thread-sibling export behavior. Once the reply has a real link, existing export selection automatically uses it.
- Consider excluding a canary-tagged reply itself as well as canary prior evidence, so synthetic outbound evidence cannot become genuine CRM attribution.

## Focused regressions

Cover: unique app/contact; unique app/no or multiple contact; zero app; multiple apps; low-confidence prior link; canary-only prior evidence; duplicate ingestion plus repeated lifecycle processing; older provider-time reply; terminal/interviewing application stage preservation; alert task resolution unchanged. Assert one link/event/review at most, exact method/confidence, no new contact, contact timeline inclusion only with a uniquely proven contact, and redacted timeline no longer reports the linked reply as `thread_sibling`.

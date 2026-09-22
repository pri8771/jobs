"""Offline mechanical reproduction, no external calls and no repository writes."""
from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.ingestion.engine import canonical_email_addresses, EmailIngestionEngine, persisted_message_matches_canary_policy, reclassify_persisted_canary_messages, is_durable_canary
from jobs_automation.db.models import InboundMessageModel
from jobs_automation.db.session import init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

alias = 'owner+canary@example.com'
adapter = GmailAdapter(service=object())
payload = {
    'id': 'review-only-id', 'threadId': 'review-only-thread',
    'internalDate': '1790078400000',
    'payload': {'headers': [
        {'name': 'From', 'value': 'a@b.com;c@d.com'},
        {'name': 'To', 'value': alias},
        {'name': 'Subject', 'value': 'Recruiter followup'},
    ]},
}
raw = adapter._parse_gmail_message_payload(payload)
database = create_engine('sqlite:///:memory:')
init_db(database)
with Session(database) as session:
    ingestion = EmailIngestionEngine(session, adapter, canary_identities=[alias])
    print({
        'adapter_sender': raw.sender,
        'adapter_recipients': raw.recipients,
        'sender_address': raw.provider_metadata['sender_address'],
        'canonical_participants': sorted(canonical_email_addresses([
            raw.sender, *raw.recipients, raw.provider_metadata['sender_address'],
        ])),
        'engine_fresh_is_canary': ingestion._is_canary(raw),
    })
    message = InboundMessageModel(
        provider_message_id=raw.provider_message_id,
        provider_thread_id=raw.provider_thread_id,
        received_at=raw.received_at,
        sender=raw.sender,
        recipients_json=raw.recipients,
        subject=raw.subject,
        headers_json={'_provider': raw.provider_metadata},
        body_text='', classification='RECRUITER_OUTREACH',
    )
    session.add(message)
    session.flush()
    print({
        'historical_match': persisted_message_matches_canary_policy(message, {alias}),
        'reclassified_count': reclassify_persisted_canary_messages(session, [alias]),
        'durable_canary': is_durable_canary(message),
    })

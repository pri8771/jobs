"""Offline replay preflight probe: a pre-repair audit, unchanged display-name policy."""
import datetime
from email.utils import getaddresses
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from jobs_automation.db.session import init_db
from jobs_automation.db.models import InboundMessageModel
from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.ingestion.bounded import BoundedIngestionRequest, BoundedIngestionRunner, BoundedIngestionError
import jobs_automation.ingestion.engine as ingestion
from tests.test_gmail_adapter_bounded import FakeGmailService, _message, NOW

alias = 'owner+canary@example.com'
policy = ['Owner <OWNER+CANARY@example.com>']
data = _message('legacy-missed-canary', sender='a@b.com;c@d.com', to=alias,
    subject='Recruiter followup',body='Can we discuss this role?',internal=NOW)
service=FakeGmailService([data])
adapter=GmailAdapter(service=service)
request=BoundedIngestionRequest(mailbox='candidate@invalid',query='label:recruiting',window_start=NOW-datetime.timedelta(days=1),window_end=NOW+datetime.timedelta(days=1),cap=10)
engine=create_engine('sqlite:///:memory:');init_db(engine)
with Session(engine) as session:
    current=ingestion.canonical_email_addresses
    def legacy(values):
        return {address.strip().lower() for _,address in getaddresses([str(value) for value in values if value]) if '@' in address and address.strip()}
    ingestion.canonical_email_addresses=legacy
    original=BoundedIngestionRunner(session,adapter,canary_identities=policy,adapter_kind='offline_review',synthetic=True).run(request)
    ingestion.canonical_email_addresses=current
    stored=session.scalar(select(InboundMessageModel))
    print({'original_status':original.status,'original_canary_messages':original.canary_messages,'original_tag':ingestion.is_durable_canary(stored)})
    before=len(service.list_calls)
    runner=BoundedIngestionRunner(session,adapter,canary_identities=policy,adapter_kind='offline_review',synthetic=True)
    print({'same_policy_fingerprint':runner.canary_policy_sha256==original.canary_policy_sha256,'current_policy_match':ingestion.persisted_message_matches_canary_policy(stored,current(policy)),'preflight_references_canary':runner._audit_references_current_canary(original.audit_metadata())})
    try:
        replay=runner.replay(original.run_id,request,allow_stateful_replay=True)
        print({'replay_status':replay.status,'replay_errors':replay.errors,'new_poll_list_calls':len(service.list_calls)-before,'durable_tag_after':ingestion.is_durable_canary(stored)})
    except BoundedIngestionError as exc:
        print({'preflight_error':str(exc),'new_poll_list_calls':len(service.list_calls)-before})

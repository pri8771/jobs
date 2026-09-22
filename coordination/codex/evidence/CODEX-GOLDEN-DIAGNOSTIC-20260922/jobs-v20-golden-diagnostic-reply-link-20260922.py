import datetime, json, os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import (
    ApplicationEventModel, ApplicationModel, CompanyModel, ContactModel,
    InboundMessageModel, JobModel, MessageLinkModel, TaskModel,
)
from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.timeline import build_timeline_export
from jobs_automation.worker import WorkerDaemon

url=os.environ['DATABASE_URL']
engine=create_engine(url)
factory=sessionmaker(bind=engine, expire_on_commit=False)
now=datetime.datetime.now(datetime.UTC).replace(microsecond=0)
inbound_at=now-datetime.timedelta(days=4)
reply_at=now-datetime.timedelta(hours=1)
thread='diag-thread-reply-link'
candidate='candidate@diagnostic.invalid'

# Explicit prior state, not fixture proof of job discovery/application creation.
with factory() as s:
    company=CompanyModel(normalized_name='Diagnosticco', domain='diagnostic.invalid')
    s.add(company); s.flush()
    job=JobModel(company_id=company.id, normalized_title='Diagnostic Engineer', status='active')
    s.add(job); s.flush()
    app=ApplicationModel(job_id=job.id,status='SUBMITTED',application_mode='manual',
        destination_domain='diagnostic.invalid', policy_decision='allowed',
        applied_at=inbound_at-datetime.timedelta(days=1),
        last_activity_at=inbound_at-datetime.timedelta(days=1))
    s.add(app); s.commit(); app_id=app.id

inbound=RawEmailMessage(
    provider_message_id='diag-inbound-1', provider_thread_id=thread,
    received_at=inbound_at, sender='Recruiter <recruiter@diagnostic.invalid>',
    recipients=[candidate], direction='inbound', subject='Opportunity at Diagnosticco - Engineer',
    body_text='I came across your profile and am reaching out regarding an opportunity at Diagnosticco.',
    raw_reference='synthetic://diag/inbound')
reply=RawEmailMessage(
    provider_message_id='diag-reply-1', provider_thread_id=thread,
    received_at=reply_at, sender=candidate, recipients=['recruiter@diagnostic.invalid'],
    direction='outbound', subject='Re: Opportunity at Diagnosticco - Engineer',
    body_text='Synthetic diagnostic reply; no message was sent.', raw_reference='synthetic://diag/reply')

first=WorkerDaemon(factory,email_adapter=MockEmailAdapter([inbound]),candidate_emails=[candidate]).run_sweep(reconcile=False)
with factory() as s:
    task=s.scalar(select(TaskModel).where(TaskModel.task_type=='UNANSWERED_RECRUITER'))
    first_status=task.status if task else None
    first_task_id=str(task.id) if task else None

second=WorkerDaemon(factory,email_adapter=MockEmailAdapter([inbound,reply]),candidate_emails=[candidate]).run_sweep(reconcile=False)
with factory() as s:
    messages=list(s.scalars(select(InboundMessageModel).order_by(InboundMessageModel.received_at)))
    by_provider={m.provider_message_id:m for m in messages}
    reply_row=by_provider['diag-reply-1']; inbound_row=by_provider['diag-inbound-1']
    task=s.get(TaskModel, first_task_id)
    links=list(s.scalars(select(MessageLinkModel)))
    link_by_message={str(x.inbound_message_id):x for x in links}
    events=list(s.scalars(select(ApplicationEventModel).where(ApplicationEventModel.application_id==app_id)))
    app=s.get(ApplicationModel,app_id)
    contact=s.scalar(select(ContactModel).where(ContactModel.email=='recruiter@diagnostic.invalid'))
    crm=RecruiterCRMService(s)
    app_timeline=crm.get_timeline_for_application(app_id)
    contact_timeline=crm.get_timeline_for_contact(contact.id) if contact else []
    export=build_timeline_export(s,app_id,identity={'git_sha':os.environ['SOURCE_SHA'],'package_version':'diagnostic'},now=now)
    output={
      'source_sha':os.environ['SOURCE_SHA'], 'scenario':'synthetic diagnostic; seeded prior job/application',
      'first_worker':first, 'second_worker':second,
      'messages':[{'provider_id':m.provider_message_id,'direction':m.direction,'classification':m.classification} for m in messages],
      'inbound_linked_to_application': bool(link_by_message.get(str(inbound_row.id)) and link_by_message[str(inbound_row.id)].application_id==app_id),
      'reply_link_count':sum(1 for x in links if x.inbound_message_id==reply_row.id),
      'unanswered_task_initial_status':first_status,
      'unanswered_task_final_status':task.status if task else None,
      'unanswered_task_resolved_by_reply':(task.payload_json or {}).get('resolved_by_reply_id')==str(reply_row.id) if task else False,
      'application_last_activity_at':app.last_activity_at.isoformat(),
      'application_event_source_refs':[e.source_reference for e in events],
      'crm_application_timeline_provider_ids':[x['provider_message_id'] for x in app_timeline],
      'crm_contact_timeline_provider_ids':[x['provider_message_id'] for x in contact_timeline],
      'truth_timeline_sources':[{'provider_message_id':x['provider_message_id'],'direction':x['direction'],'link_method':x['link_method']} for x in export['sources']],
    }
    print(json.dumps(output,indent=2,sort_keys=True,default=str))

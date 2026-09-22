from __future__ import annotations
import datetime, json, os, tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker
from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.models import ApplicationEventModel, ApplicationModel, ContactModel, InboundMessageModel, InterviewModel, MessageLinkModel, TaskModel
from jobs_automation.ingestion.models import PollReport, RawEmailMessage
from jobs_automation.worker import WorkerDaemon
from jobs_automation.dashboard.analytics import FunnelAnalyticsService
from jobs_automation.health import HealthCheckService
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.timeline import build_timeline_export
from tests.test_dashboard import DummyRequestHandler

spec=spec_from_file_location('golden_setup','/tmp/jobs-v20-golden-setup.py'); setup_mod=module_from_spec(spec); spec.loader.exec_module(setup_mod)
url=URL.create('postgresql+psycopg',username=os.environ.get('USER'),host=os.environ['JOBS_PG_SOCKET'],port=int(os.environ['JOBS_PG_PORT']),database=os.environ['JOBS_DB'])
engine=create_engine(url); factory=sessionmaker(bind=engine,expire_on_commit=False)
now=datetime.datetime.now(datetime.UTC).replace(microsecond=0); candidate='engineering-candidate@invalid'; thread='golden-recruiting-thread'

def msg(pid,at,direction,subject,body,sender,recipients):
    return RawEmailMessage(provider_message_id=pid,provider_thread_id=thread,received_at=at,direction=direction,subject=subject,body_text=body,sender=sender,recipients=recipients,raw_reference=f'synthetic://{pid}')

messages=[
msg('golden-confirm-1',now-datetime.timedelta(days=6),'inbound','Thank you for applying at Golden Synthetic Co','We have received your application for Senior AI Automation Engineer Python FastAPI.','no-reply@goldensyntheticco.invalid',[candidate]),
msg('golden-outreach-1',now-datetime.timedelta(days=5),'inbound','Opportunity at Golden Synthetic Co - AI Automation','I came across your profile and would like to schedule a time to chat.','Recruiter <recruiter@goldensyntheticco.invalid>',[candidate]),
msg('golden-interview-1',now-datetime.timedelta(days=4),'inbound','Interview with Golden Synthetic Co - Technical Screen','Your technical screen is scheduled for 2026-10-15 14:00 UTC: https://meet.google.com/abc-defg-hij','Recruiter <recruiter@goldensyntheticco.invalid>',[candidate]),
msg('golden-reply-1',now-datetime.timedelta(days=3),'outbound','Re: Opportunity at Golden Synthetic Co - AI Automation','Thank you. I confirm my availability for the interview.',candidate,['recruiter@goldensyntheticco.invalid']),
msg('golden-rejection-1',now-datetime.timedelta(days=2),'inbound','Application update from Golden Synthetic Co','Unfortunately, we have decided not to move forward with your application.','Recruiter <recruiter@goldensyntheticco.invalid>',[candidate]),
]
messages[0].provider_thread_id='golden-application-thread'

class FullReplayMockEmailAdapter(MockEmailAdapter):
    """Synthetic overlap/restart adapter that deliberately re-delivers the full fixture."""
    def poll_messages(self, query=None, since_timestamp=None, max_results=100):
        return super().poll_messages(query=query, since_timestamp=None, max_results=max_results)

with tempfile.TemporaryDirectory(prefix='jobs-v20-golden-cont-') as td:
    setup=setup_mod.run_steps_1_8(factory,Path(td),os.environ['SOURCE_SHA']); app_id=setup['application_id']
    observed=[]
    for raw in messages[:3]:
        result=WorkerDaemon(factory,email_adapter=MockEmailAdapter([raw]),candidate_emails=[candidate]).run_sweep(reconcile=False)
        assert result['errors']==[], {'provider_id':raw.provider_message_id,'result':result}
        observed.append({'provider_id':raw.provider_message_id,'worker':result})
    # Actual duplicate/restart of the interview must be inert.
    duplicate=WorkerDaemon(factory,email_adapter=MockEmailAdapter([messages[2]]),candidate_emails=[candidate]).run_sweep(reconcile=True)
    assert duplicate['errors']==[] and duplicate['messages_ingested']==0 and duplicate['lifecycle_transitions']==0, duplicate
    with factory() as s:
        app=s.get(ApplicationModel,app_id)
        events=list(s.scalars(select(ApplicationEventModel).where(ApplicationEventModel.application_id==app_id)))
        interviews=list(s.scalars(select(InterviewModel).where(InterviewModel.application_id==app_id)))
        contacts=list(s.scalars(select(ContactModel)))
        alert=s.scalar(select(TaskModel).where(TaskModel.task_type=='UNANSWERED_RECRUITER'))
        assert app.status=='INTERVIEWING', {'status':app.status,'events':[(e.event_type,e.source_reference) for e in events]}
        assert len(interviews)==1 and interviews[0].scheduled_start==datetime.datetime(2026,10,15,14,0,tzinfo=datetime.UTC) and interviews[0].location_or_link=='https://meet.google.com/abc-defg-hij', {'interviews':[{'start':x.scheduled_start,'end':x.scheduled_end,'link':x.location_or_link,'round':x.round_type} for x in interviews]}
        recruiter_contacts=[c for c in contacts if c.email=='recruiter@goldensyntheticco.invalid']
        assert len(recruiter_contacts)==1, {'contacts':[c.email for c in contacts]}
        assert alert is not None and alert.status=='pending'
    reply_result=WorkerDaemon(factory,email_adapter=MockEmailAdapter([messages[3]]),candidate_emails=[candidate]).run_sweep(reconcile=False)
    assert reply_result['errors']==[], reply_result
    with factory() as s:
        alert=s.scalar(select(TaskModel).where(TaskModel.task_type=='UNANSWERED_RECRUITER'))
        assert alert is not None and alert.status=='completed', {'task':None if alert is None else {'status':alert.status,'payload':alert.payload_json}}
    reject_result=WorkerDaemon(factory,email_adapter=MockEmailAdapter([messages[4]]),candidate_emails=[candidate]).run_sweep(reconcile=False)
    assert reject_result['errors']==[], reject_result
    with factory() as s:
        app=s.get(ApplicationModel,app_id); events=list(s.scalars(select(ApplicationEventModel).where(ApplicationEventModel.application_id==app_id)))
        assert app.status=='REJECTED', {'status':app.status,'events':[(e.event_type,e.source_reference) for e in events]}
        assert len([e for e in events if e.source_reference=='golden-interview-1'])==1
        assert len([e for e in events if e.source_reference=='golden-reply-1'])==1
        analytics=FunnelAnalyticsService(s); funnel=analytics.get_funnel_summary(); resume_perf=analytics.get_resume_performance()
        assert funnel['total_jobs_discovered']==1
        assert funnel['total_submitted']==1 and funnel['total_screening']==1 and funnel['total_interviewing']==1 and funnel['total_rejected']==1, funnel
        assert len(resume_perf)==1 and resume_perf[0]['variant_name']=='resume_ai_software_engineer' and resume_perf[0]['applications_count']==1 and resume_perf[0]['interviews']==1
    def durable_snapshot():
        with factory() as s:
            recruiter=s.scalar(select(ContactModel).where(ContactModel.email=='recruiter@goldensyntheticco.invalid'))
            crm=RecruiterCRMService(s)
            app_crm=crm.get_timeline_for_application(app_id); contact_crm=crm.get_timeline_for_contact(recruiter.id)
            redacted=build_timeline_export(s,app_id,identity={'git_sha':os.environ['SOURCE_SHA'],'package_version':'golden-synthetic'},now=now)
            analytics=FunnelAnalyticsService(s)
            reviews=[{'task_type':t.task_type,'status':t.status,'reason':(t.payload_json or {}).get('reason'),'unresolved_questions':(t.payload_json or {}).get('unresolved_questions')} for t in s.scalars(select(TaskModel).where(TaskModel.status=='pending')).all()]
            return {'counts':{'messages':s.scalar(select(func.count()).select_from(InboundMessageModel)),'links':s.scalar(select(func.count()).select_from(MessageLinkModel)),'events':s.scalar(select(func.count()).select_from(ApplicationEventModel)),'followups':s.scalar(select(func.count()).select_from(TaskModel).where(TaskModel.task_type.in_(['UNANSWERED_RECRUITER','STALE_APPLICATION_FOLLOW_UP','STALE_SCREENING_FOLLOW_UP']))),'interviews':s.scalar(select(func.count()).select_from(InterviewModel))},'funnel':analytics.get_funnel_summary(),'resume_performance':analytics.get_resume_performance(),'app_crm_provider_ids':[x['provider_message_id'] for x in app_crm],'contact_crm_provider_ids':[x['provider_message_id'] for x in contact_crm],'redacted_source_ids':[x['provider_message_id'] for x in redacted['sources']],'redacted_reply':next(x for x in redacted['sources'] if x['provider_message_id']=='golden-reply-1'),'redacted_digest':redacted['export_sha256'],'pending_reviews':reviews}
    before_replay=durable_snapshot()
    assert before_replay['app_crm_provider_ids']==['golden-confirm-1','golden-outreach-1','golden-interview-1','golden-reply-1','golden-rejection-1']
    assert before_replay['contact_crm_provider_ids']==['golden-outreach-1','golden-interview-1','golden-reply-1','golden-rejection-1']
    assert before_replay['redacted_reply']['link_method']=='thread_reply_attribution' and before_replay['redacted_reply']['link_confidence']>=0.8
    assert any(r['reason'] and 'unresolved question' in r['reason'].lower() and r['unresolved_questions'] for r in before_replay['pending_reviews']), before_replay['pending_reviews']
    assert any(r['reason']=='Interview requested but no explicit schedule confirmed' for r in before_replay['pending_reviews']), before_replay['pending_reviews']
    # Same database, new daemon and adapter: deliberately re-deliver every original message.
    full_replay=WorkerDaemon(factory,email_adapter=FullReplayMockEmailAdapter([setup['alert_message'],*messages]),candidate_emails=[candidate]).run_sweep(reconcile=False)
    assert full_replay['errors']==[] and full_replay['messages_ingested']==0 and full_replay['lifecycle_transitions']==0, full_replay
    after_replay=durable_snapshot()
    assert after_replay==before_replay, {'before':before_replay,'after':after_replay,'worker':full_replay}
    endpoints=['/api/jobs','/api/kanban','/api/contacts','/api/interviews','/api/reviews','/api/followups','/api/audit',f'/api/timeline?application_id={app_id}']
    dashboard={}
    for endpoint in endpoints:
        handler=DummyRequestHandler('GET',endpoint,session_factory=factory); handler.do_GET()
        assert handler.status_code==200, {'endpoint':endpoint,'status':handler.status_code}
        dashboard[endpoint]=json.loads(handler.mock_wfile.getvalue().decode())
    assert any(row['id']==str(setup['job_id']) for row in dashboard['/api/jobs'])
    assert any(row['application_id']==str(app_id) for row in dashboard['/api/interviews'])
    assert any(row['email']=='recruiter@goldensyntheticco.invalid' for row in dashboard['/api/contacts'])
    assert any(row['provider_message_id']=='golden-reply-1' for row in dashboard[f'/api/timeline?application_id={app_id}'])
    health=HealthCheckService(factory).run_full_check()
    assert health.components['database'].status=='HEALTHY'
    assert health.components['worker'].details['last_attempt_status']=='SUCCESS', health.components['worker'].model_dump()
    print(json.dumps({'result':'PASS_STEPS_1_17','fixture':setup['report'],'lifecycle':{'final_status':app.status,'events':[(e.event_type,e.source_reference,e.actor) for e in events],'interviews':1,'contacts':2},'initial_interview_duplicate':duplicate,'same_db_full_replay':full_replay,'durable_snapshot':after_replay,'dashboard_counts':{k:len(v) if isinstance(v,list) else len(v) for k,v in dashboard.items()},'health':health.model_dump(mode='json')},indent=2,default=str))
engine.dispose()

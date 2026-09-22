from __future__ import annotations

import hashlib, json, os, subprocess, tempfile, uuid
from pathlib import Path
from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.adapters.models import DeterministicModelGateway
from jobs_automation.browser.assisted_engine import AssistedApplicationEngine
from jobs_automation.browser.mock_runner import MockBrowserRunner
from jobs_automation.core.config import ConfigLoader
from jobs_automation.db.models import ApplicationModel, ApplicationPacketModel, ArtifactModel, InboundMessageModel, JobEvaluationModel, JobModel, JobSourceModel, MessageLinkModel, ResumeVariantModel, TaskModel
from jobs_automation.evaluation.engine import JobEvaluationEngine
from jobs_automation.ingestion.engine import EmailIngestionEngine
from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder, compute_canonical_packet_hash
from jobs_automation.storage.artifact_store import ArtifactStore
from tests.test_real_proof_verifier import engineering_profile_yaml

def run_steps_1_8(factory, workspace: Path | str, source_sha: str) -> dict:
    trace_id=f'j20i-{uuid.uuid4()}'
    root=Path(workspace); resume_dir=root/'resume'; artifact_dir=root/'artifacts'; config_dir=root/'config'
    resume_dir.mkdir(parents=True); artifact_dir.mkdir(parents=True); config_dir.mkdir(parents=True)
    resume=resume_dir/'engineering_resume_ai_software_engineer.md'
    resume.write_text('# Synthetic Engineering Candidate\n\nPython FastAPI workflow automation.\n',encoding='utf-8')
    profile_path=config_dir/'candidate_profile.yaml'
    profile_path.write_text(engineering_profile_yaml(resume.resolve()),encoding='utf-8')
    loader=ConfigLoader(config_dir)
    profile,_=loader.load_candidate_profile(profile_path)
    search,_=ConfigLoader('config').load_job_search()
    policy,_=ConfigLoader('config').load_policy_registry()
    
    # One internally consistent synthetic alert; the production parser must create the job.
    alert=RawEmailMessage(provider_message_id='golden-alert-1',provider_thread_id='golden-alert-thread',received_at=__import__('datetime').datetime.now(__import__('datetime').UTC)-__import__('datetime').timedelta(days=10),sender='alert@indeed.com',recipients=[profile.identity.email],direction='inbound',subject='Indeed Job Alert: Senior AI Automation Engineer Python FastAPI',body_text='Senior AI Automation Engineer Python FastAPI at Golden Synthetic Co',body_html='''<html><body><table><tr><td><a href="https://www.indeed.com/viewjob?jk=golden123&from=ja">Senior AI Automation Engineer Python FastAPI</a><div>Golden Synthetic Co</div><div>Remote</div><div>$170,000 - $190,000 a year</div></td></tr></table></body></html>''')
    with factory() as s:
        first=EmailIngestionEngine(s,MockEmailAdapter([alert]),candidate_emails=[profile.identity.email]).run_sweep(reconcile=False)
        assert first.errors==[] and first.messages_ingested==1 and first.jobs_discovered_new==1, first
        jobs=list(s.scalars(select(JobModel)))
        assert len(jobs)==1
        job=jobs[0]
        assert job.normalized_title=='Senior AI Automation Engineer Python FastAPI'
        assert job.company.normalized_name=='Golden Synthetic Co'
        assert len(job.sources)==1
        assert s.scalar(select(func.count()).select_from(MessageLinkModel))==1
        job_id=job.id
    
    # Duplicate replay through the same production ingestion service.
    with factory() as s:
        replay=EmailIngestionEngine(s,MockEmailAdapter([alert]),candidate_emails=[profile.identity.email]).run_sweep(reconcile=False)
        assert replay.errors==[] and replay.messages_skipped_duplicate==1, replay
        assert s.scalar(select(func.count()).select_from(JobModel))==1
        assert s.scalar(select(func.count()).select_from(JobSourceModel))==1
    
        job=s.get(JobModel,job_id)
        evaluation=JobEvaluationEngine(s,profile,search).evaluate_job(job)
        s.commit()
        assert evaluation.decision=='SHORTLIST', {'decision':evaluation.decision,'score':evaluation.score,'reasons':evaluation.reason_codes_json,'job_status':job.status}
    
        questions=['Are you legally authorized to work in the US?','What is your gender?','Describe a production quantum compiler you personally built.']
        store=ArtifactStore(artifact_dir)
        packet,result=ApplicationPacketBuilder(s,profile,DeterministicModelGateway(),artifact_store=store).build_packet(job,questions=questions)
        s.commit()
        assert result.resume_variant=='resume_ai_software_engineer'
        assert result.resume_family and result.resume_artifact_uri.startswith(f'file://{artifact_dir.resolve()}')
        assert store.verify(result.resume_artifact_uri,result.resume_artifact_sha256)
        assert store.verify(result.cover_letter_artifact_uri,result.cover_letter_artifact_sha256)
        manifest=json.loads(store.read(result.manifest_artifact_uri))
        assert manifest['resume_source_reference']==str(resume.resolve())
        assert manifest['resume_artifact_sha256']==hashlib.sha256(resume.read_bytes()).hexdigest()
        assert packet.answers_json['Are you legally authorized to work in the US?']=='Yes'
        assert 'work_authorization.authorized_to_work_in_us' in packet.answer_provenance_json['Are you legally authorized to work in the US?']['sources']
        assert len(packet.unresolved_questions_json)==2
        assert any('Demographic/EEO' in x for x in packet.unresolved_questions_json)
        assert any('quantum compiler' in x.lower() for x in packet.unresolved_questions_json)
        resume_art=s.get(ArtifactModel,packet.resume_artifact_id); cover_art=s.get(ArtifactModel,packet.cover_letter_artifact_id); variant=s.get(ResumeVariantModel,packet.resume_variant_id)
        recomputed=compute_canonical_packet_hash(job_id=str(job.id),profile_version=packet.candidate_profile_version,resume_variant_id=str(variant.id),resume_sha=resume_art.sha256,cover_letter_sha=cover_art.sha256,answers=packet.answers_json,answer_provenance=packet.answer_provenance_json)
        assert recomputed==packet.packet_hash==result.packet_hash
    
        app_result=AssistedApplicationEngine(s,PolicyEvaluator(policy),MockBrowserRunner(),profile).execute(job_id=job.id,packet_id=packet.id,auto_confirm=False)
        assert app_result.status=='REVIEW_REQUIRED' and app_result.policy_decision=='manual_only', app_result.model_dump()
        app=s.scalar(select(ApplicationModel).where(ApplicationModel.job_id==job.id))
        assert app is not None and app.application_mode=='manual' and app.status=='MANUAL_IN_PROGRESS' and app.packet_id==packet.id
        s.commit(); app_id=app.id; packet_id=packet.id
    
    with factory() as s:
        packet=s.get(ApplicationPacketModel,packet_id); variant=s.get(ResumeVariantModel,packet.resume_variant_id); resume_art=s.get(ArtifactModel,packet.resume_artifact_id); cover_art=s.get(ArtifactModel,packet.cover_letter_artifact_id)
        source_tree=subprocess.check_output(['git','rev-parse',f'{source_sha}^{{tree}}'],text=True).strip()
        review_tasks=list(s.scalars(select(TaskModel).where(TaskModel.status=='pending')))
        report={'trace_id':trace_id,'fixture_version':'v2.0-golden-synthetic-20260922','source':{'sha':source_sha,'tree':source_tree},'result':'PASS_STEPS_1_8','entities':{'source_message_id':'golden-alert-1','job_id':str(job_id),'packet_id':str(packet_id),'application_id':str(app_id),'resume_variant_id':str(variant.id),'resume_artifact_id':str(resume_art.id),'cover_letter_artifact_id':str(cover_art.id)},'packet':{'packet_hash':packet.packet_hash,'resume_family':variant.resume_family,'resume_variant_name':variant.name,'resume_source_reference':str(resume.resolve()),'resume_source_sha256':hashlib.sha256(resume.read_bytes()).hexdigest(),'resume_artifact_sha256':resume_art.sha256,'cover_letter_artifact_sha256':cover_art.sha256,'generation_origin':packet.generation_metadata_json.get('generation_origin'),'is_live_ready':packet.is_live_ready,'answers':packet.answers_json,'answer_provenance':packet.answer_provenance_json,'unresolved_questions':packet.unresolved_questions_json},'review_visibility':[{'task_type':t.task_type,'status':t.status,'reason':(t.payload_json or {}).get('reason'),'unresolved_questions':(t.payload_json or {}).get('unresolved_questions')} for t in review_tasks],'assertions':{'one_normalized_job':s.scalar(select(func.count()).select_from(JobModel))==1,'duplicate_no_second_job':s.scalar(select(func.count()).select_from(JobModel))==1 and s.scalar(select(func.count()).select_from(JobSourceModel))==1,'shortlisted':s.scalar(select(JobEvaluationModel.decision))=='SHORTLIST','packet_hash_verified':True,'explicit_resume_source':str(resume.resolve()),'unknown_and_eeo_unresolved':True,'non_live_manual_application':s.get(ApplicationModel,app_id).status=='MANUAL_IN_PROGRESS'},'temporary_workspace':str(root)}
        pass
    return {'factory':factory,'workspace':root,'profile':profile,'trace_id':trace_id,'job_id':job_id,'packet_id':packet_id,'application_id':app_id,'alert_message':alert,'report':report}

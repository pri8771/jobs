"""V23 Typed P0 Read Tools (V23-TL-06 & TL-07)."""

from __future__ import annotations

import datetime
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobEvaluationModel,
    JobModel,
    ResumeVariantModel,
    TargetCompanyModel,
    TaskModel,
)
from jobs_automation.health import HealthCheckService
from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.intelligence.opportunity_graph import OpportunityGraphService
from jobs_automation.intelligence.strategy import StrategyLearningService
from jobs_automation.intelligence.target_companies import TargetCompanyService
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.tools.envelope import ActionClass, PermissionContext, ToolStatus
from jobs_automation.tools.registry import ToolHandlerResult, ToolRegistry, ToolSpec


# ──────────────────────────────── Models ────────────────────────────────

class ListJobsInput(BaseModel):
    status: str | None = None
    company_id: str | None = None
    min_score: float | None = None
    limit: int = 50


class JobSummary(BaseModel):
    id: str
    company_name: str
    title: str
    location: str | None = None
    status: str
    posted_at: str | None = None


class ListJobsOutput(BaseModel):
    jobs: list[JobSummary] = Field(default_factory=list)


class GetJobInput(BaseModel):
    job_id: str


class GetJobOutput(BaseModel):
    id: str
    company_name: str
    title: str
    description_text: str | None = None
    status: str
    evidence_ref: EvidenceRef


class GetApplicationInput(BaseModel):
    application_id: str


class GetApplicationOutput(BaseModel):
    id: str
    job_id: str
    status: str
    applied_at: str | None = None
    evidence_ref: EvidenceRef


class GetTimelineInput(BaseModel):
    application_id: str


class GetTimelineOutput(BaseModel):
    application_id: str
    events: list[dict[str, Any]] = Field(default_factory=list)


class ListContactsInput(BaseModel):
    company_id: str | None = None


class ListContactsOutput(BaseModel):
    contacts: list[dict[str, Any]] = Field(default_factory=list)


class GetContactHistoryInput(BaseModel):
    contact_id: str


class GetContactHistoryOutput(BaseModel):
    contact_id: str
    events: list[dict[str, Any]] = Field(default_factory=list)


class ListInterviewsInput(BaseModel):
    upcoming_only: bool = True
    application_id: str | None = None


class ListInterviewsOutput(BaseModel):
    interviews: list[dict[str, Any]] = Field(default_factory=list)


class ListReviewQueueInput(BaseModel):
    limit: int = 50


class ListReviewQueueOutput(BaseModel):
    pending_tasks: list[dict[str, Any]] = Field(default_factory=list)


class GetResumeVariantInput(BaseModel):
    variant_id: str


class GetResumeVariantOutput(BaseModel):
    id: str
    name: str
    version: int
    resume_family: str
    tailoring_method: str


class GetCompanyContextInput(BaseModel):
    company_id: str


class GetCompanyContextOutput(BaseModel):
    company_id: str
    name: str
    domain: str | None = None
    jobs_count: int
    contacts_count: int


class GetPolicyDecisionInput(BaseModel):
    destination_domain: str
    capability: str


class GetPolicyDecisionOutput(BaseModel):
    destination_domain: str
    capability: str
    decision: str
    reason: str


class GetWorkerHealthInput(BaseModel):
    pass


class GetWorkerHealthOutput(BaseModel):
    overall_status: str
    checks: list[dict[str, Any]] = Field(default_factory=list)


# ──────────────────────────────── Handlers ────────────────────────────────

def handle_list_jobs(session: Session, input_model: ListJobsInput, context: PermissionContext) -> ToolHandlerResult:
    stmt = select(JobModel)
    if input_model.status:
        stmt = stmt.where(JobModel.status == input_model.status)
    if input_model.company_id:
        stmt = stmt.where(JobModel.company_id == uuid.UUID(input_model.company_id))

    stmt = stmt.order_by(JobModel.first_seen_at.desc()).limit(input_model.limit)
    jobs = session.scalars(stmt).all()

    summaries = [
        JobSummary(
            id=str(j.id),
            company_name=j.company_name,
            title=j.title,
            location=j.location_text,
            status=j.status,
            posted_at=j.posted_at.isoformat() if j.posted_at else None,
        )
        for j in jobs
    ]
    entity_refs = [EvidenceRef(ref_type="job", ref_id=str(j.id)) for j in jobs]
    return ToolHandlerResult(payload_model=ListJobsOutput(jobs=summaries), entity_refs=entity_refs)


def handle_get_job(session: Session, input_model: GetJobInput, context: PermissionContext) -> ToolHandlerResult:
    job_uuid = uuid.UUID(input_model.job_id)
    job = session.get(JobModel, job_uuid)
    if not job:
        raise LookupError(f"Job not found: {input_model.job_id}")

    ref = EvidenceRef(ref_type="job", ref_id=str(job.id))
    output = GetJobOutput(
        id=str(job.id),
        company_name=job.company_name,
        title=job.title,
        description_text=job.description_text,
        status=job.status,
        evidence_ref=ref,
    )
    return ToolHandlerResult(payload_model=output, entity_refs=[ref])


def handle_get_application(session: Session, input_model: GetApplicationInput, context: PermissionContext) -> ToolHandlerResult:
    app_uuid = uuid.UUID(input_model.application_id)
    app = session.get(ApplicationModel, app_uuid)
    if not app:
        raise LookupError(f"Application not found: {input_model.application_id}")

    ref = EvidenceRef(ref_type="application", ref_id=str(app.id))
    output = GetApplicationOutput(
        id=str(app.id),
        job_id=str(app.job_id),
        status=app.status,
        applied_at=app.applied_at.isoformat() if app.applied_at else None,
        evidence_ref=ref,
    )
    return ToolHandlerResult(payload_model=output, entity_refs=[ref])


def handle_get_application_timeline(session: Session, input_model: GetTimelineInput, context: PermissionContext) -> ToolHandlerResult:
    app_uuid = uuid.UUID(input_model.application_id)
    app = session.get(ApplicationModel, app_uuid)
    if not app:
        raise LookupError(f"Application not found: {input_model.application_id}")

    crm = RecruiterCRMService(session)
    events = crm.get_timeline_for_application(app_uuid)
    event_dicts = [{"event_id": str(e.event_id), "type": e.event_type, "timestamp": e.timestamp.isoformat()} for e in events]

    output = GetTimelineOutput(application_id=str(app.id), events=event_dicts)
    return ToolHandlerResult(payload_model=output, entity_refs=[EvidenceRef(ref_type="application", ref_id=str(app.id))])


def handle_list_contacts(session: Session, input_model: ListContactsInput, context: PermissionContext) -> ToolHandlerResult:
    stmt = select(ContactModel)
    if input_model.company_id:
        stmt = stmt.where(ContactModel.company_id == uuid.UUID(input_model.company_id))

    contacts = session.scalars(stmt).all()
    dicts = [{"id": str(c.id), "name": c.name, "email": c.email, "role": c.role} for c in contacts]
    refs = [EvidenceRef(ref_type="contact", ref_id=str(c.id)) for c in contacts]
    return ToolHandlerResult(payload_model=ListContactsOutput(contacts=dicts), entity_refs=refs)


def handle_get_contact_history(session: Session, input_model: GetContactHistoryInput, context: PermissionContext) -> ToolHandlerResult:
    c_uuid = uuid.UUID(input_model.contact_id)
    contact = session.get(ContactModel, c_uuid)
    if not contact:
        raise LookupError(f"Contact not found: {input_model.contact_id}")

    crm = RecruiterCRMService(session)
    events = crm.get_timeline_for_contact(c_uuid)
    event_dicts = [{"event_id": str(e.event_id), "type": e.event_type, "timestamp": e.timestamp.isoformat()} for e in events]
    return ToolHandlerResult(payload_model=GetContactHistoryOutput(contact_id=str(contact.id), events=event_dicts))


def handle_list_interviews(session: Session, input_model: ListInterviewsInput, context: PermissionContext) -> ToolHandlerResult:
    stmt = select(InterviewModel)
    if input_model.application_id:
        stmt = stmt.where(InterviewModel.application_id == uuid.UUID(input_model.application_id))

    interviews = session.scalars(stmt).all()
    dicts = [{"id": str(i.id), "application_id": str(i.application_id), "round_type": i.round_type, "status": i.status} for i in interviews]
    refs = [EvidenceRef(ref_type="interview", ref_id=str(i.id)) for i in interviews]
    return ToolHandlerResult(payload_model=ListInterviewsOutput(interviews=dicts), entity_refs=refs)


def handle_list_review_queue(session: Session, input_model: ListReviewQueueInput, context: PermissionContext) -> ToolHandlerResult:
    tasks = session.scalars(select(TaskModel).where(TaskModel.status == "pending").limit(input_model.limit)).all()
    dicts = [{"id": str(t.id), "task_type": t.task_type, "status": t.status} for t in tasks]
    refs = [EvidenceRef(ref_type="task", ref_id=str(t.id)) for t in tasks]
    return ToolHandlerResult(payload_model=ListReviewQueueOutput(pending_tasks=dicts), entity_refs=refs)


def handle_get_resume_variant(session: Session, input_model: GetResumeVariantInput, context: PermissionContext) -> ToolHandlerResult:
    v_uuid = uuid.UUID(input_model.variant_id)
    variant = session.get(ResumeVariantModel, v_uuid)
    if not variant:
        raise LookupError(f"ResumeVariant not found: {input_model.variant_id}")

    out = GetResumeVariantOutput(
        id=str(variant.id),
        name=variant.name,
        version=variant.version,
        resume_family=variant.resume_family,
        tailoring_method=variant.tailoring_method,
    )
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="resume_variant", ref_id=str(variant.id))])


def handle_get_company_context(session: Session, input_model: GetCompanyContextInput, context: PermissionContext) -> ToolHandlerResult:
    c_uuid = uuid.UUID(input_model.company_id)
    company = session.get(CompanyModel, c_uuid)
    if not company:
        raise LookupError(f"Company not found: {input_model.company_id}")

    jobs_count = len(company.jobs) if company.jobs else 0
    contacts_count = len(company.contacts) if company.contacts else 0
    out = GetCompanyContextOutput(
        company_id=str(company.id),
        name=company.normalized_name,
        domain=company.domain,
        jobs_count=jobs_count,
        contacts_count=contacts_count,
    )
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="company", ref_id=str(company.id))])


def handle_get_policy_decision(session: Session, input_model: GetPolicyDecisionInput, context: PermissionContext) -> ToolHandlerResult:
    evaluator = PolicyEvaluator(session)
    res = evaluator.evaluate(input_model.destination_domain, capability=input_model.capability)
    out = GetPolicyDecisionOutput(
        destination_domain=input_model.destination_domain,
        capability=input_model.capability,
        decision=res.decision,
        reason=res.reason,
    )
    return ToolHandlerResult(payload_model=out)


def handle_get_worker_health(session: Session, input_model: GetWorkerHealthInput, context: PermissionContext) -> ToolHandlerResult:
    svc = HealthCheckService()
    report = svc.run_full_check(session)
    checks_clean = []
    # Filter through allowlist (no raw paths or tokens)
    for c in report.checks:
        checks_clean.append({
            "name": c.name,
            "status": c.status,
            "message": re.sub(r"(/[a-zA-Z0-9_\-\.]+)+", "[REDACTED_PATH]", c.message),
        })

    out = GetWorkerHealthOutput(overall_status=report.overall_status, checks=checks_clean)
    return ToolHandlerResult(payload_model=out)


# ──────────────────────────────── Registration ────────────────────────────────

def register_read_tools(registry: ToolRegistry) -> None:
    """Register all P0 Read tools into the provided ToolRegistry."""
    registry.register(ToolSpec(name="list_jobs", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=ListJobsInput, output_model=ListJobsOutput, handler=handle_list_jobs))
    registry.register(ToolSpec(name="get_job", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetJobInput, output_model=GetJobOutput, handler=handle_get_job))
    registry.register(ToolSpec(name="get_application", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetApplicationInput, output_model=GetApplicationOutput, handler=handle_get_application))
    registry.register(ToolSpec(name="get_application_timeline", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetTimelineInput, output_model=GetTimelineOutput, handler=handle_get_application_timeline))
    registry.register(ToolSpec(name="list_contacts", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=ListContactsInput, output_model=ListContactsOutput, handler=handle_list_contacts))
    registry.register(ToolSpec(name="get_contact_history", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetContactHistoryInput, output_model=GetContactHistoryOutput, handler=handle_get_contact_history))
    registry.register(ToolSpec(name="list_interviews", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=ListInterviewsInput, output_model=ListInterviewsOutput, handler=handle_list_interviews))
    registry.register(ToolSpec(name="list_review_queue", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=ListReviewQueueInput, output_model=ListReviewQueueOutput, handler=handle_list_review_queue))
    registry.register(ToolSpec(name="get_resume_variant", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetResumeVariantInput, output_model=GetResumeVariantOutput, handler=handle_get_resume_variant))
    registry.register(ToolSpec(name="get_company_context", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetCompanyContextInput, output_model=GetCompanyContextOutput, handler=handle_get_company_context))
    registry.register(ToolSpec(name="get_policy_decision", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetPolicyDecisionInput, output_model=GetPolicyDecisionOutput, handler=handle_get_policy_decision))
    registry.register(ToolSpec(name="get_worker_health", version="1.0", action_class=ActionClass.P0_READ, capability=None, input_model=GetWorkerHealthInput, output_model=GetWorkerHealthOutput, handler=handle_get_worker_health))

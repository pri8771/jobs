"""V23 Typed P1 Preparation Tools (V23-TL-08)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from jobs_automation.db.models import ApplicationModel, JobModel, TaskModel
from jobs_automation.evaluation.engine import JobEvaluationEngine
from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.intelligence.interview_service import InterviewIntelligenceService
from jobs_automation.tools.envelope import ActionClass, PermissionContext, ToolStatus
from jobs_automation.tools.registry import ToolHandlerResult, ToolRegistry, ToolSpec


class EvaluateJobInput(BaseModel):
    job_id: str


class EvaluateJobOutput(BaseModel):
    job_id: str
    decision: str
    composite_score: float
    explanation: str


class GenerateInterviewBriefInput(BaseModel):
    application_id: str


class GenerateInterviewBriefOutput(BaseModel):
    application_id: str
    interview_stage: str
    role_summary: str
    key_requirements_count: int


class DraftFollowupInput(BaseModel):
    application_id: str
    contact_id: str | None = None


class DraftFollowupOutput(BaseModel):
    application_id: str
    stage_context: str
    facts_count: int
    send_performed: bool = False


class CreateReviewTaskInput(BaseModel):
    task_type: str
    reason: str
    job_id: str | None = None
    application_id: str | None = None


class CreateReviewTaskOutput(BaseModel):
    task_id: str
    status: str = "pending"


# ──────────────────────────────── Handlers ────────────────────────────────

def handle_evaluate_job(session: Session, input_model: EvaluateJobInput, context: PermissionContext) -> ToolHandlerResult:
    job_uuid = uuid.UUID(input_model.job_id)
    job = session.get(JobModel, job_uuid)
    if not job:
        raise LookupError(f"Job not found: {input_model.job_id}")

    engine = JobEvaluationEngine(session)
    res = engine.evaluate_job(job)
    out = EvaluateJobOutput(
        job_id=str(job.id),
        decision=res.decision,
        composite_score=res.composite_score,
        explanation=res.explanation,
    )
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="job", ref_id=str(job.id))])


def handle_generate_interview_brief(session: Session, input_model: GenerateInterviewBriefInput, context: PermissionContext) -> ToolHandlerResult:
    svc = InterviewIntelligenceService(session)
    brief = svc.build_brief(input_model.application_id)
    out = GenerateInterviewBriefOutput(
        application_id=brief.application_id,
        interview_stage=brief.interview_stage,
        role_summary=brief.role_summary,
        key_requirements_count=len(brief.key_requirements),
    )
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="application", ref_id=brief.application_id)])


def handle_draft_followup(session: Session, input_model: DraftFollowupInput, context: PermissionContext) -> ToolHandlerResult:
    svc = InterviewIntelligenceService(session)
    pkg = svc.build_followup(input_model.application_id, contact_id=input_model.contact_id)
    out = DraftFollowupOutput(
        application_id=pkg.application_id,
        stage_context=pkg.stage_context,
        facts_count=len(pkg.facts),
        send_performed=pkg.send_performed,
    )
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="application", ref_id=pkg.application_id)])


def handle_create_review_task(session: Session, input_model: CreateReviewTaskInput, context: PermissionContext) -> ToolHandlerResult:
    j_uuid = uuid.UUID(input_model.job_id) if input_model.job_id else None
    a_uuid = uuid.UUID(input_model.application_id) if input_model.application_id else None

    task = TaskModel(
        job_id=j_uuid,
        application_id=a_uuid,
        task_type=input_model.task_type,
        status="pending",
        payload_json={"reason": input_model.reason},
    )
    session.add(task)
    session.flush()

    out = CreateReviewTaskOutput(task_id=str(task.id), status="pending")
    return ToolHandlerResult(payload_model=out, entity_refs=[EvidenceRef(ref_type="task", ref_id=str(task.id))])


def register_prep_tools(registry: ToolRegistry) -> None:
    """Register all P1 Preparation tools into the provided ToolRegistry."""
    registry.register(ToolSpec(name="evaluate_job", version="1.0", action_class=ActionClass.P1_LOCAL_WRITE, capability=None, input_model=EvaluateJobInput, output_model=EvaluateJobOutput, handler=handle_evaluate_job))
    registry.register(ToolSpec(name="generate_interview_brief", version="1.0", action_class=ActionClass.P1_LOCAL_WRITE, capability=None, input_model=GenerateInterviewBriefInput, output_model=GenerateInterviewBriefOutput, handler=handle_generate_interview_brief))
    registry.register(ToolSpec(name="draft_followup", version="1.0", action_class=ActionClass.P1_LOCAL_WRITE, capability=None, input_model=DraftFollowupInput, output_model=DraftFollowupOutput, handler=handle_draft_followup))
    registry.register(ToolSpec(name="create_review_task", version="1.0", action_class=ActionClass.P1_LOCAL_WRITE, capability=None, input_model=CreateReviewTaskInput, output_model=CreateReviewTaskOutput, handler=handle_create_review_task))

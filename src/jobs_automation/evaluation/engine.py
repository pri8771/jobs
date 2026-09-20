"""Job evaluation engine coordinating hard filtering and semantic scoring."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.core import CandidateProfileConfig, JobSearchConfig
from jobs_automation.db.models import JobEvaluationModel, JobModel, TaskModel
from jobs_automation.evaluation.filters import FilterDecisionStatus, HardFilterService
from jobs_automation.evaluation.scorer import SemanticScorer


class EvaluationRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime.datetime
    completed_at: datetime.datetime
    total_evaluated: int = 0
    shortlisted: int = 0
    considered: int = 0
    rejected: int = 0
    needs_review: int = 0
    errors: list[str] = Field(default_factory=list)


class JobEvaluationEngine:
    """Evaluates candidate-job fit using deterministic hard filters and semantic scoring."""

    def __init__(
        self,
        session: Session,
        candidate_profile: CandidateProfileConfig,
        job_search_config: JobSearchConfig,
    ) -> None:
        self.session = session
        self.profile = candidate_profile
        self.search_config = job_search_config
        self.filter_service = HardFilterService(candidate_profile, job_search_config)
        self.scorer = SemanticScorer(candidate_profile, job_search_config)

    def evaluate_job(self, job: JobModel) -> JobEvaluationModel:
        """Evaluate a single job posting through hard filter and scoring pipeline."""
        filter_res = self.filter_service.evaluate(job)

        # 1. Disqualified by hard filters
        if filter_res.status == FilterDecisionStatus.REJECT:
            job.status = "rejected"
            eval_record = JobEvaluationModel(
                job_id=job.id,
                profile_version=self.profile.version,
                rules_version=self.search_config.version,
                decision="REJECT",
                score=0.0,
                reason_codes_json=filter_res.reason_codes,
                explanation=filter_res.explanation,
                model_provider="deterministic_rule",
                model_name="hard_filter",
            )
            self.session.add(eval_record)
            self.session.flush()
            return eval_record

        # 2. Hard filter requires human review
        if filter_res.status == FilterDecisionStatus.MUST_REVIEW:
            job.status = "needs_review"
            eval_record = JobEvaluationModel(
                job_id=job.id,
                profile_version=self.profile.version,
                rules_version=self.search_config.version,
                decision="MUST_REVIEW",
                score=50.0,
                reason_codes_json=filter_res.reason_codes,
                explanation=filter_res.explanation,
                model_provider="deterministic_rule",
                model_name="hard_filter",
            )
            self.session.add(eval_record)

            # Create review task
            task = TaskModel(
                task_type="NEEDS_REVIEW",
                status="pending",
                payload_json={
                    "reason": filter_res.explanation,
                    "job_id": str(job.id),
                    "job_title": job.normalized_title,
                    "company": job.company.normalized_name if job.company else None,
                },
            )
            self.session.add(task)
            self.session.flush()
            return eval_record

        # 3. Passed hard filters -> Multi-dimensional scoring
        score_res = self.scorer.score(job)
        all_reasons = filter_res.reason_codes + score_res.reason_codes

        if score_res.decision == "SHORTLIST":
            job.status = "shortlisted"
        elif score_res.decision == "CONSIDER":
            job.status = "needs_review"
            # Route to review queue for consideration
            task = TaskModel(
                task_type="NEEDS_REVIEW",
                status="pending",
                payload_json={
                    "reason": f"Borderline score ({score_res.composite_score:.1f}/100) requires review",
                    "job_id": str(job.id),
                    "job_title": job.normalized_title,
                    "composite_score": score_res.composite_score,
                },
            )
            self.session.add(task)
        else:
            job.status = "rejected"

        eval_record = JobEvaluationModel(
            job_id=job.id,
            profile_version=self.profile.version,
            rules_version=self.search_config.version,
            decision=score_res.decision,
            score=score_res.composite_score,
            reason_codes_json=all_reasons,
            explanation=score_res.explanation,
            model_provider="semantic_engine",
            model_name="scoring_v1",
        )
        self.session.add(eval_record)
        self.session.flush()
        return eval_record

    def run_evaluation_batch(self, limit: int = 100) -> EvaluationRunSummary:
        """Run evaluation on all pending/discovered jobs."""
        start_time = datetime.datetime.now(datetime.UTC)
        summary = EvaluationRunSummary(
            started_at=start_time,
            completed_at=start_time,
        )

        try:
            stmt = (
                select(JobModel)
                .where(JobModel.status == "discovered")
                .order_by(JobModel.first_seen_at.desc())
                .limit(limit)
            )
            jobs = self.session.execute(stmt).scalars().all()

            for job in jobs:
                summary.total_evaluated += 1
                eval_record = self.evaluate_job(job)
                if eval_record.decision == "SHORTLIST":
                    summary.shortlisted += 1
                elif eval_record.decision == "CONSIDER":
                    summary.considered += 1
                elif eval_record.decision == "MUST_REVIEW":
                    summary.needs_review += 1
                else:
                    summary.rejected += 1

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            summary.errors.append(str(e))

        summary.completed_at = datetime.datetime.now(datetime.UTC)
        return summary

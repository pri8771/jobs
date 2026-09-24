"""CareerBriefingService — Aggregates top opportunities, strategy, relationships, and data gaps (V23-CB-02)."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.core.config import ConfigLoader
from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobEvaluationModel,
    JobModel,
    TargetCompanyModel,
    TaskModel,
)
from jobs_automation.evaluation.scorer import SemanticScorer
from jobs_automation.intelligence.briefing import (
    CareerBriefing,
    DataFreshness,
    OpportunityCard,
    ResumeRecommendation,
)
from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.intelligence.opportunity_graph import OpportunityGraphService
from jobs_automation.intelligence.target_companies import TargetCompanyService
from jobs_automation.policy.evaluator import PolicyEvaluator


class CareerBriefingService:
    """Service that composes comprehensive CareerBriefing artifacts."""

    def __init__(
        self,
        session: Session,
        config_dir: str = "config",
    ) -> None:
        self.session = session
        self.config_dir = config_dir
        self.target_service = TargetCompanyService(session)
        self.opp_graph_service = OpportunityGraphService(session)

    def build(
        self,
        as_of: datetime.datetime | None = None,
        limit: int = 10,
    ) -> CareerBriefing:
        """Compose and return a CareerBriefing artifact."""
        now = as_of or utc_now()
        data_gaps: list[str] = []
        uncertainty_notes: list[str] = []
        warnings: list[str] = []

        # 1. Load profile & config
        profile = None
        search_config = None
        try:
            loader = ConfigLoader(self.config_dir)
            profile, search_config = loader.load_all()
        except Exception as e:
            warnings.append(f"Config load warning: {e}")

        scorer = SemanticScorer(profile, search_config) if (profile and search_config) else None

        # 2. Fetch jobs
        all_jobs = list(self.session.scalars(select(JobModel)).all())
        opportunity_cards: list[OpportunityCard] = []

        from jobs_automation.policy.evaluator import PolicyRegistryConfig

        policy_reg = search_config.policy_registry if (search_config and hasattr(search_config, "policy_registry")) else PolicyRegistryConfig(version=1)
        policy_evaluator = PolicyEvaluator(policy_reg)

        for job in all_jobs:
            if len(opportunity_cards) >= limit:
                break

            company = job.company
            comp_name = company.normalized_name if company else "Unknown"

            # Latest evaluation
            latest_eval = self.session.scalars(
                select(JobEvaluationModel)
                .where(JobEvaluationModel.job_id == job.id)
                .order_by(JobEvaluationModel.created_at.desc())
            ).first()

            score = latest_eval.score if latest_eval else None
            decision = latest_eval.decision if latest_eval else None

            # Policy decision
            domain = company.domain or "" if company else ""
            pol = policy_evaluator.evaluate(domain, capability="submit_application")

            # Determine next action
            next_action = "EVALUATE"
            if not latest_eval:
                next_action = "EVALUATE"
            elif decision == "REJECT":
                next_action = "NONE"
            elif pol.decision == "MANUAL_ONLY":
                next_action = "APPLY_MANUAL"
            elif pol.decision == "ASSISTED":
                next_action = "ASSISTED_PREFILL"
            elif pol.decision == "AUTO_ALLOWED":
                next_action = "AWAIT_APPROVAL"

            job_ref = EvidenceRef(ref_type="job", ref_id=str(job.id))
            company_ref = EvidenceRef(ref_type="company", ref_id=str(company.id)) if company else EvidenceRef(ref_type="job", ref_id=str(job.id))

            posting_age = (now - job.first_seen_at).days if job.first_seen_at else None

            card = OpportunityCard(
                job_ref=job_ref,
                company_ref=company_ref,
                title=job.title,
                company_name=comp_name,
                score=score,
                decision=decision,
                reason_codes=latest_eval.reason_codes_json if latest_eval else [],
                next_action=next_action,  # type: ignore
                policy_decision=pol.decision,
                posting_age_days=posting_age,
            )
            opportunity_cards.append(card)

        # 3. Data Freshness & Data Gaps
        total_apps = len(list(self.session.scalars(select(ApplicationModel)).all()))
        active_targets = len(self.target_service.list(status="ACTIVE"))

        if total_apps == 0:
            data_gaps.append("Zero real applications recorded in database.")
        if active_targets == 0:
            data_gaps.append("No active target companies configured in watchlist.")

        data_freshness = DataFreshness(
            last_ingestion_at=now,
            last_worker_run_at=now,
            gmail_mode="UNAVAILABLE",
        )

        # 4. Upcoming interviews
        upcoming_interviews = list(
            self.session.scalars(
                select(InterviewModel)
                .where(InterviewModel.status == "scheduled")
                .order_by(InterviewModel.scheduled_start.asc())
            ).all()
        )
        int_dicts = [
            {
                "id": str(i.id),
                "application_id": str(i.application_id),
                "round_type": i.round_type,
                "scheduled_start": i.scheduled_start.isoformat(),
            }
            for i in upcoming_interviews
        ]

        # 5. Pending tasks (followups / queue)
        pending_tasks = list(
            self.session.scalars(
                select(TaskModel).where(TaskModel.status == "pending").limit(20)
            ).all()
        )
        task_dicts = [{"id": str(t.id), "task_type": t.task_type} for t in pending_tasks]

        return CareerBriefing(
            artifact_type="career_briefing",
            generated_at=now,
            generator="CareerBriefingService",
            generator_version="2.3",
            source_refs=[],
            profile_version=1,
            data_freshness=data_freshness,
            top_opportunities=opportunity_cards,
            interviews_upcoming=int_dicts,
            followups_due=task_dicts,
            data_gaps=data_gaps,
            uncertainty_notes=uncertainty_notes,
            warnings=warnings,
            confidence="HIGH" if opportunity_cards else "MEDIUM",
        )

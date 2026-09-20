"""Analytics and metrics service for application funnels and performance."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationModel,
    JobModel,
    JobSourceModel,
    TaskModel,
)


class FunnelAnalyticsResult(BaseModel):
    """Structured funnel analytics metrics."""

    total_jobs_discovered: int
    total_submitted: int
    total_screening: int
    total_interviewing: int
    total_offers: int
    total_rejected: int
    pending_reviews: int
    conversion_rates: dict[str, float]
    status_breakdown: dict[str, int]


class FunnelAnalyticsService:
    """Computes funnel metrics, conversion rates, and pipeline health."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_funnel_summary(self) -> dict[str, Any]:
        """Calculates discovery-to-submission-to-offer funnel stages and rates."""
        total_discovered = self.session.scalar(select(func.count(JobModel.id))) or 0

        # Query counts grouped by application status
        status_counts_raw = self.session.execute(
            select(ApplicationModel.status, func.count(ApplicationModel.id)).group_by(
                ApplicationModel.status
            )
        ).all()
        status_map: dict[str, int] = {
            s: count for s, count in status_counts_raw
        }

        submitted = sum(
            status_map.get(s, 0)
            for s in [
                "SUBMITTED",
                "CONFIRMED",
                "SCREENING",
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
                "REJECTED",
                "WITHDRAWN",
            ]
        )
        screening = sum(
            status_map.get(s, 0)
            for s in [
                "SCREENING",
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
            ]
        )
        interviewing = sum(
            status_map.get(s, 0)
            for s in [
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
            ]
        )
        offers = sum(
            status_map.get(s, 0)
            for s in [
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
            ]
        )
        rejected = status_map.get("REJECTED", 0)

        # Pending reviews count
        pending_reviews = (
            self.session.scalar(
                select(func.count(TaskModel.id)).where(
                    TaskModel.status == "pending"
                )
            )
            or 0
        )

        # Conversion percentages
        app_rate = round((submitted / total_discovered * 100), 1) if total_discovered else 0.0
        screen_rate = round((screening / submitted * 100), 1) if submitted else 0.0
        interview_rate = round((interviewing / screening * 100), 1) if screening else 0.0
        offer_rate = round((offers / interviewing * 100), 1) if interviewing else 0.0

        return {
            "total_jobs_discovered": total_discovered,
            "total_submitted": submitted,
            "total_screening": screening,
            "total_interviewing": interviewing,
            "total_offers": offers,
            "total_rejected": rejected,
            "pending_reviews": pending_reviews,
            "conversion_rates": {
                "discovery_to_submission_pct": app_rate,
                "submission_to_screen_pct": screen_rate,
                "screen_to_interview_pct": interview_rate,
                "interview_to_offer_pct": offer_rate,
            },
            "status_breakdown": status_map,
        }

    def get_source_breakdown(self) -> dict[str, int]:
        """Calculates discovery count by source platform/provider."""
        results = self.session.execute(
            select(JobSourceModel.provider, func.count(JobSourceModel.id)).group_by(
                JobSourceModel.provider
            )
        ).all()
        return {provider: count for provider, count in results}

    def get_kanban_board(self) -> dict[str, list[dict[str, Any]]]:
        """Groups applications into Kanban columns for pipeline visualization."""
        applications = self.session.scalars(
            select(ApplicationModel).order_by(ApplicationModel.last_activity_at.desc())
        ).all()

        columns: dict[str, list[dict[str, Any]]] = {
            "DISCOVERED": [],
            "PREPARED": [],
            "SUBMITTED": [],
            "SCREENING": [],
            "INTERVIEWING": [],
            "OFFER": [],
            "CLOSED": [],
        }

        for app in applications:
            job = app.job
            company_name = job.company_name if job else "Unknown Company"
            job_title = job.title if job else "Unknown Role"

            card_data = {
                "id": str(app.id),
                "job_id": str(app.job_id),
                "company": company_name,
                "title": job_title,
                "status": app.status,
                "policy_decision": app.policy_decision,
                "application_mode": app.application_mode,
                "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                "last_activity_at": app.last_activity_at.isoformat() if app.last_activity_at else None,
            }

            status = app.status.upper()
            if status in ["DISCOVERED", "NEEDS_REVIEW", "DRAFT"]:
                columns["DISCOVERED"].append(card_data)
            elif status == "PREPARED":
                columns["PREPARED"].append(card_data)
            elif status in ["SUBMITTED", "CONFIRMED"]:
                columns["SUBMITTED"].append(card_data)
            elif status == "SCREENING":
                columns["SCREENING"].append(card_data)
            elif status == "INTERVIEWING":
                columns["INTERVIEWING"].append(card_data)
            elif status in ["OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_DECLINED"]:
                columns["OFFER"].append(card_data)
            elif status in ["REJECTED", "WITHDRAWN"]:
                columns["CLOSED"].append(card_data)
            else:
                columns["DISCOVERED"].append(card_data)

        return columns

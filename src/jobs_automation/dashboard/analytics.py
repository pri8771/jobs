"""Analytics and metrics service for application funnels, sources, roles, and resume performance."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    JobModel,
    JobSourceModel,
    ResumeVariantModel,
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
    """Computes funnel metrics, source attribution, resume efficacy, and pipeline velocity."""

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
                "ASSESSMENT",
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
                "ONBOARDING",
                "REJECTED",
                "WITHDRAWN",
            ]
        )
        screening = sum(
            status_map.get(s, 0)
            for s in [
                "SCREENING",
                "ASSESSMENT",
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
                "ONBOARDING",
            ]
        )
        interviewing = sum(
            status_map.get(s, 0)
            for s in [
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
                "ONBOARDING",
            ]
        )
        offers = sum(
            status_map.get(s, 0)
            for s in [
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "OFFER_DECLINED",
                "ONBOARDING",
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

    def get_source_performance(self) -> list[dict[str, Any]]:
        """Calculates downstream application funnel conversion grouped by job discovery source."""
        stmt = (
            select(
                JobSourceModel.provider,
                func.count(JobSourceModel.id).label("jobs_discovered"),
                func.count(ApplicationModel.id).label("applications_submitted"),
            )
            .join(JobModel, JobModel.id == JobSourceModel.job_id)
            .outerjoin(ApplicationModel, ApplicationModel.job_id == JobModel.id)
            .group_by(JobSourceModel.provider)
        )
        rows = self.session.execute(stmt).all()

        performance: list[dict[str, Any]] = []
        for provider, disc, apps in rows:
            # Query status breakdown for applications from this provider
            app_stmt = (
                select(ApplicationModel.status, func.count(ApplicationModel.id))
                .join(JobModel, JobModel.id == ApplicationModel.job_id)
                .join(JobSourceModel, JobSourceModel.job_id == JobModel.id)
                .where(JobSourceModel.provider == provider)
                .group_by(ApplicationModel.status)
            )
            app_status_counts: dict[str, int] = {
                str(st): int(cnt) for st, cnt in self.session.execute(app_stmt).all()
            }

            screens = sum(
                app_status_counts.get(s, 0)
                for s in ["SCREENING", "ASSESSMENT", "INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            interviews = sum(
                app_status_counts.get(s, 0)
                for s in ["INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            offers = sum(
                app_status_counts.get(s, 0)
                for s in ["OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            rejections = app_status_counts.get("REJECTED", 0)

            response_rate = round((screens / apps * 100), 1) if apps else 0.0
            offer_rate = round((offers / apps * 100), 1) if apps else 0.0

            performance.append(
                {
                    "provider": provider,
                    "jobs_discovered": disc,
                    "applications_submitted": apps,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "rejections": rejections,
                    "response_rate_pct": response_rate,
                    "offer_rate_pct": offer_rate,
                    "low_sample_size": apps < 5,
                    "note": "Sample size warning: N < 5" if apps < 5 else "Reliable sample",
                }
            )
        return performance

    def get_role_family_performance(self) -> list[dict[str, Any]]:
        """Calculates conversion and outcome distribution by target role/title family."""
        stmt = (
            select(
                JobModel.normalized_title,
                func.count(ApplicationModel.id).label("applications_count"),
            )
            .join(ApplicationModel, ApplicationModel.job_id == JobModel.id)
            .group_by(JobModel.normalized_title)
            .order_by(func.count(ApplicationModel.id).desc())
        )
        rows = self.session.execute(stmt).all()

        results: list[dict[str, Any]] = []
        for role, apps_count in rows:
            sub_stmt = (
                select(ApplicationModel.status, func.count(ApplicationModel.id))
                .join(JobModel, JobModel.id == ApplicationModel.job_id)
                .where(JobModel.normalized_title == role)
                .group_by(ApplicationModel.status)
            )
            counts: dict[str, int] = {
                str(st): int(cnt) for st, cnt in self.session.execute(sub_stmt).all()
            }

            screens = sum(
                counts.get(s, 0)
                for s in ["SCREENING", "ASSESSMENT", "INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            interviews = sum(
                counts.get(s, 0)
                for s in ["INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            offers = sum(
                counts.get(s, 0)
                for s in ["OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            rejections = counts.get("REJECTED", 0)

            results.append(
                {
                    "role_family": role,
                    "applications_count": apps_count,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "rejections": rejections,
                    "interview_rate_pct": round((interviews / apps_count * 100), 1) if apps_count else 0.0,
                    "offer_rate_pct": round((offers / apps_count * 100), 1) if apps_count else 0.0,
                    "low_sample_size": apps_count < 5,
                }
            )
        return results

    def get_resume_performance(self) -> list[dict[str, Any]]:
        """Calculates funnel efficacy grouped by immutable resume variant and resume family."""
        stmt = (
            select(
                ResumeVariantModel.resume_family,
                ResumeVariantModel.name,
                ResumeVariantModel.version,
                func.count(ApplicationModel.id).label("applications_count"),
            )
            .join(ApplicationPacketModel, ApplicationPacketModel.resume_variant_id == ResumeVariantModel.id)
            .join(ApplicationModel, ApplicationModel.packet_id == ApplicationPacketModel.id)
            .group_by(ResumeVariantModel.resume_family, ResumeVariantModel.name, ResumeVariantModel.version)
        )
        rows = self.session.execute(stmt).all()

        results: list[dict[str, Any]] = []
        for family, name, version, count in rows:
            app_stmt = (
                select(ApplicationModel.status, func.count(ApplicationModel.id))
                .join(ApplicationPacketModel, ApplicationPacketModel.id == ApplicationModel.packet_id)
                .join(ResumeVariantModel, ResumeVariantModel.id == ApplicationPacketModel.resume_variant_id)
                .where(
                    ResumeVariantModel.name == name,
                    ResumeVariantModel.version == version,
                )
                .group_by(ApplicationModel.status)
            )
            counts: dict[str, int] = {
                str(st): int(cnt) for st, cnt in self.session.execute(app_stmt).all()
            }

            screens = sum(
                counts.get(s, 0)
                for s in ["SCREENING", "ASSESSMENT", "INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            interviews = sum(
                counts.get(s, 0)
                for s in ["INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )
            offers = sum(
                counts.get(s, 0)
                for s in ["OFFER_RECEIVED", "OFFER_ACCEPTED", "ONBOARDING"]
            )

            results.append(
                {
                    "resume_family": family,
                    "variant_name": name,
                    "version": version,
                    "applications_count": count,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "interview_rate_pct": round((interviews / count * 100), 1) if count else 0.0,
                    "offer_rate_pct": round((offers / count * 100), 1) if count else 0.0,
                    "low_sample_size": count < 5,
                    "confidence_label": "Descriptive (N < 5)" if count < 5 else "Statistically robust",
                }
            )
        return results

    def get_time_to_stage(self) -> dict[str, Any]:
        """Calculates average latency in days from application submission to various lifecycle stages."""
        apps = self.session.scalars(
            select(ApplicationModel).where(ApplicationModel.applied_at.is_not(None))
        ).all()

        time_to_first_response: list[float] = []
        time_to_interview: list[float] = []
        time_to_offer: list[float] = []
        time_to_rejection: list[float] = []

        for app in apps:
            if not app.applied_at:
                continue

            events = sorted(app.events, key=lambda e: e.occurred_at)
            has_first_response = False
            has_interview = False
            has_offer = False
            has_rejection = False

            for ev in events:
                elapsed_days = max(0.0, (ev.occurred_at - app.applied_at).total_seconds() / 86400.0)
                if ev.event_type in ("RECRUITER_CONTACTED", "SCREENING_REQUESTED") and not has_first_response:
                    time_to_first_response.append(elapsed_days)
                    has_first_response = True
                elif ev.event_type in ("INTERVIEW_REQUESTED", "INTERVIEW_CONFIRMED") and not has_interview:
                    time_to_interview.append(elapsed_days)
                    has_interview = True
                elif ev.event_type == "OFFER_EXTENDED" and not has_offer:
                    time_to_offer.append(elapsed_days)
                    has_offer = True
                elif ev.event_type == "APPLICATION_REJECTED" and not has_rejection:
                    time_to_rejection.append(elapsed_days)
                    has_rejection = True

        def avg_or_none(values: list[float]) -> float | None:
            return round(sum(values) / len(values), 1) if values else None

        return {
            "avg_days_to_first_response": avg_or_none(time_to_first_response),
            "avg_days_to_interview": avg_or_none(time_to_interview),
            "avg_days_to_offer": avg_or_none(time_to_offer),
            "avg_days_to_rejection": avg_or_none(time_to_rejection),
            "sample_sizes": {
                "first_response": len(time_to_first_response),
                "interview": len(time_to_interview),
                "offer": len(time_to_offer),
                "rejection": len(time_to_rejection),
            },
            "interpretation_note": "Averages are descriptive. Standard sample-size warnings apply when N < 5.",
        }

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
            elif status in ["SCREENING", "ASSESSMENT"]:
                columns["SCREENING"].append(card_data)
            elif status == "INTERVIEWING":
                columns["INTERVIEWING"].append(card_data)
            elif status in ["OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_DECLINED", "ONBOARDING"]:
                columns["OFFER"].append(card_data)
            elif status in ["REJECTED", "WITHDRAWN"]:
                columns["CLOSED"].append(card_data)
            else:
                columns["DISCOVERED"].append(card_data)

        return columns

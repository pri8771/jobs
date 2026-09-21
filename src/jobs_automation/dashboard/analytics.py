"""Analytics and metrics service for application funnels, sources, roles, and resume performance."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.db.models import (
    ApplicationModel,
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

    def _is_real_submission(self, app: ApplicationModel) -> bool:
        """Determines if an application represents a confirmed real submission.

        Excludes draft, discovered, prepared states, and explicit simulation mode.
        Requires applied_at timestamp and/or verified submission event evidence.
        """
        if app.status in ("DISCOVERED", "PREPARED", "DRAFT"):
            return False
        if getattr(app, "application_mode", None) == "simulation":
            return False
        if app.applied_at is not None:
            return True
        return any(e.event_type == "APPLICATION_SUBMITTED" for e in (app.events or []))

    def _get_application_historical_outcomes(self, app: ApplicationModel) -> dict[str, bool]:
        """Derives cumulative 'ever reached stage' flags from ApplicationEvent history, interviews, and status.

        Ensures that downstream outcomes (e.g. interviewed then rejected, or offered then declined)
        preserve historical funnel stage achievements.
        """
        events = app.events or []
        event_types = {e.event_type for e in events}
        interviews = app.interviews or []

        screen_events = {
            "SCREENING_REQUESTED",
            "SCREENING_SCHEDULED",
            "SCREENING_CONFIRMED",
            "ASSESSMENT_REQUESTED",
            "ASSESSMENT_INVITATION",
            "RECRUITER_CONTACTED",
            "RECRUITER_FOLLOWED_UP",
        }
        ever_screened = bool(
            (event_types & screen_events)
            or len(interviews) > 0
            or app.status in (
                "SCREENING",
                "ASSESSMENT",
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "ONBOARDING",
            )
        )

        interview_events = {
            "INTERVIEW_REQUESTED",
            "INTERVIEW_CONFIRMED",
            "INTERVIEW_SCHEDULED",
            "INTERVIEW_RESCHEDULED",
        }
        ever_interviewed = bool(
            (event_types & interview_events)
            or len(interviews) > 0
            or app.status in (
                "INTERVIEWING",
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "ONBOARDING",
            )
        )

        offer_events = {
            "OFFER_EXTENDED",
            "OFFER_RECEIVED",
            "OFFER_ACCEPTED",
            "OFFER_DECLINED",
        }
        ever_offered = bool(
            (event_types & offer_events)
            or app.status in (
                "OFFER_RECEIVED",
                "OFFER_ACCEPTED",
                "ONBOARDING",
            )
        )

        ever_accepted = bool(
            ("OFFER_ACCEPTED" in event_types)
            or app.status in ("OFFER_ACCEPTED", "ONBOARDING")
        )

        ever_rejected = bool(
            ("APPLICATION_REJECTED" in event_types)
            or app.status == "REJECTED"
        )

        ever_withdrawn = bool(
            ("APPLICATION_WITHDRAWN" in event_types)
            or app.status == "WITHDRAWN"
        )

        return {
            "ever_screened": ever_screened,
            "ever_interviewed": ever_interviewed,
            "ever_offered": ever_offered,
            "ever_accepted": ever_accepted,
            "ever_rejected": ever_rejected,
            "ever_withdrawn": ever_withdrawn,
        }

    def get_source_performance(self) -> list[dict[str, Any]]:
        """Calculates downstream application funnel conversion grouped by job discovery source.

        Follows B-R20-01 and B-R20-02:
        - uses historical 'ever reached stage' event evidence rather than current status alone,
        - uses confirmed submissions (applied_at present / not simulation) for the denominator,
        - attributes jobs with multiple sources to the primary (earliest) discovery source to avoid double-counting.
        """
        all_sources = self.session.scalars(
            select(JobSourceModel).order_by(
                JobSourceModel.job_id,
                JobSourceModel.first_seen_at.asc(),
                JobSourceModel.id.asc(),
            )
        ).all()

        # Group sources by provider and map each job to its primary discovery source
        primary_source_by_job: dict[uuid.UUID, str] = {}
        jobs_discovered_by_provider: dict[str, set[uuid.UUID]] = {}
        all_providers: set[str] = set()

        for s in all_sources:
            all_providers.add(s.provider)
            if s.job_id not in primary_source_by_job:
                primary_source_by_job[s.job_id] = s.provider
            if s.provider not in jobs_discovered_by_provider:
                jobs_discovered_by_provider[s.provider] = set()
            jobs_discovered_by_provider[s.provider].add(s.job_id)

        all_apps = self.session.scalars(select(ApplicationModel)).all()

        performance: list[dict[str, Any]] = []
        for provider in sorted(all_providers):
            disc_count = len(jobs_discovered_by_provider.get(provider, set()))

            # Attribute applications whose job primary source is this provider
            provider_apps = [
                app for app in all_apps
                if app.job_id and primary_source_by_job.get(app.job_id) == provider
            ]

            # Denominator: only count real submissions (exclude DRAFT, DISCOVERED, PREPARED, simulation)
            submitted_apps = [a for a in provider_apps if self._is_real_submission(a)]
            submitted_count = len(submitted_apps)

            # Historical outcome counts across all submitted applications
            screens = 0
            interviews = 0
            offers = 0
            rejections = 0
            for a in submitted_apps:
                outcomes = self._get_application_historical_outcomes(a)
                if outcomes["ever_screened"]:
                    screens += 1
                if outcomes["ever_interviewed"]:
                    interviews += 1
                if outcomes["ever_offered"]:
                    offers += 1
                if outcomes["ever_rejected"]:
                    rejections += 1

            response_rate = round((screens / submitted_count * 100), 1) if submitted_count else 0.0
            offer_rate = round((offers / submitted_count * 100), 1) if submitted_count else 0.0
            low_sample = submitted_count < 5

            performance.append(
                {
                    "provider": provider,
                    "jobs_discovered": disc_count,
                    "applications_submitted": submitted_count,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "rejections": rejections,
                    "response_rate_pct": response_rate,
                    "offer_rate_pct": offer_rate,
                    "low_sample_size": low_sample,
                    "note": f"Descriptive (N={submitted_count})" if not low_sample else f"Low sample size (N={submitted_count} < 5)",
                }
            )
        return performance

    def get_role_family_performance(self) -> list[dict[str, Any]]:
        """Calculates conversion and historical outcome distribution by target role/title family."""
        all_apps = self.session.scalars(select(ApplicationModel)).all()

        # Group applications by normalized job title
        apps_by_role: dict[str, list[ApplicationModel]] = {}
        for a in all_apps:
            title = a.job.normalized_title if a.job and a.job.normalized_title else "Unspecified"
            if title not in apps_by_role:
                apps_by_role[title] = []
            apps_by_role[title].append(a)

        results: list[dict[str, Any]] = []
        for role, apps in sorted(apps_by_role.items(), key=lambda x: len(x[1]), reverse=True):
            submitted_apps = [a for a in apps if self._is_real_submission(a)]
            submitted_count = len(submitted_apps)

            screens = 0
            interviews = 0
            offers = 0
            rejections = 0
            for a in submitted_apps:
                outcomes = self._get_application_historical_outcomes(a)
                if outcomes["ever_screened"]:
                    screens += 1
                if outcomes["ever_interviewed"]:
                    interviews += 1
                if outcomes["ever_offered"]:
                    offers += 1
                if outcomes["ever_rejected"]:
                    rejections += 1

            low_sample = submitted_count < 5
            results.append(
                {
                    "role_family": role,
                    "applications_count": submitted_count,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "rejections": rejections,
                    "interview_rate_pct": round((interviews / submitted_count * 100), 1) if submitted_count else 0.0,
                    "offer_rate_pct": round((offers / submitted_count * 100), 1) if submitted_count else 0.0,
                    "low_sample_size": low_sample,
                    "sample_size_note": f"Descriptive (N={submitted_count})" if not low_sample else f"Low sample size (N={submitted_count} < 5)",
                }
            )
        return results

    def get_resume_performance(self) -> list[dict[str, Any]]:
        """Calculates funnel efficacy grouped by immutable resume variant and resume family."""
        variants = self.session.scalars(select(ResumeVariantModel)).all()

        results: list[dict[str, Any]] = []
        for variant in variants:
            # Applications linked to this resume variant via packets
            apps = [
                pkt_app
                for pkt in variant.packets
                for pkt_app in self.session.scalars(
                    select(ApplicationModel).where(ApplicationModel.packet_id == pkt.id)
                ).all()
            ]

            submitted_apps = [a for a in apps if self._is_real_submission(a)]
            submitted_count = len(submitted_apps)

            screens = 0
            interviews = 0
            offers = 0
            for a in submitted_apps:
                outcomes = self._get_application_historical_outcomes(a)
                if outcomes["ever_screened"]:
                    screens += 1
                if outcomes["ever_interviewed"]:
                    interviews += 1
                if outcomes["ever_offered"]:
                    offers += 1

            low_sample = submitted_count < 5
            results.append(
                {
                    "resume_family": variant.resume_family,
                    "variant_name": variant.name,
                    "version": variant.version,
                    "applications_count": submitted_count,
                    "screenings": screens,
                    "interviews": interviews,
                    "offers": offers,
                    "interview_rate_pct": round((interviews / submitted_count * 100), 1) if submitted_count else 0.0,
                    "offer_rate_pct": round((offers / submitted_count * 100), 1) if submitted_count else 0.0,
                    "low_sample_size": low_sample,
                    "confidence_label": f"Descriptive (N={submitted_count})" if not low_sample else f"Low sample size (N={submitted_count} < 5)",
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

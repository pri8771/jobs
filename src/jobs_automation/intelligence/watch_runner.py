"""WatchRunner — fetches postings for ACTIVE target companies and records observations.

V23-TW-04: For each ACTIVE target with source_config, fetch postings via the registered
source client; classify each posting as NEW_ROLE, ROLE_CHANGED, or unchanged; detect
ROLE_CLOSED when a previously seen posting is absent from a successful fetch.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    TargetCompanyModel,
    TargetCompanyObservationModel,
)
from jobs_automation.ingestion.deduplication import JobDeduplicationService
from jobs_automation.ingestion.models import ExtractedJobPosting
from jobs_automation.ingestion.sources.base import PublicJobSource, SourceFetchResult

logger = logging.getLogger(__name__)


@dataclass
class WatchTargetReport:
    target_id: str
    canonical_name: str
    status: str  # OK, UNAVAILABLE, RATE_LIMITED, INVALID, ERROR
    new_roles: int = 0
    changed_roles: int = 0
    closed_roles: int = 0
    unchanged_roles: int = 0
    error: str | None = None


@dataclass
class WatchRunReport:
    started_at: datetime.datetime = field(default_factory=utc_now)
    finished_at: datetime.datetime | None = None
    target_reports: list[WatchTargetReport] = field(default_factory=list)

    @property
    def total_new(self) -> int:
        return sum(r.new_roles for r in self.target_reports)

    @property
    def total_changed(self) -> int:
        return sum(r.changed_roles for r in self.target_reports)

    @property
    def total_closed(self) -> int:
        return sum(r.closed_roles for r in self.target_reports)


class WatchRunner:
    """Fetches postings for ACTIVE target companies and records observations."""

    def __init__(
        self,
        session: Session,
        sources: dict[str, PublicJobSource],
        dedupe: JobDeduplicationService | None = None,
        fit_evaluator: Any | None = None,
    ) -> None:
        self.session = session
        self.sources = sources
        self.dedupe = dedupe or JobDeduplicationService(session)
        self.fit_evaluator = fit_evaluator

    def run(self, target_id: uuid.UUID | None = None) -> WatchRunReport:
        """Run a watch sweep for all ACTIVE targets (or a single target)."""
        report = WatchRunReport()

        if target_id:
            targets = [self.session.get(TargetCompanyModel, target_id)]
            targets = [t for t in targets if t and t.watch_status == "ACTIVE"]
        else:
            targets = list(
                self.session.scalars(
                    select(TargetCompanyModel).where(
                        TargetCompanyModel.watch_status == "ACTIVE"
                    )
                ).all()
            )

        for target in targets:
            try:
                target_report = self._process_target(target)
                report.target_reports.append(target_report)
            except Exception as e:
                logger.warning(f"Watch target {target.canonical_name} failed: {e}")
                report.target_reports.append(
                    WatchTargetReport(
                        target_id=str(target.id),
                        canonical_name=target.canonical_name,
                        status="ERROR",
                        error=str(e),
                    )
                )

        report.finished_at = utc_now()
        return report

    def _process_target(self, target: TargetCompanyModel) -> WatchTargetReport:
        """Process a single target company."""
        source_config = target.source_config or {}
        provider = source_config.get("provider", "").upper()
        source_key = source_config.get("source_key", "")

        if not provider or not source_key:
            return WatchTargetReport(
                target_id=str(target.id),
                canonical_name=target.canonical_name,
                status="ERROR",
                error="Missing provider or source_key in source_config",
            )

        source_client = self.sources.get(provider)
        if not source_client:
            return WatchTargetReport(
                target_id=str(target.id),
                canonical_name=target.canonical_name,
                status="ERROR",
                error=f"No source client registered for provider: {provider}",
            )

        # Fetch postings
        result: SourceFetchResult = source_client.fetch(source_key)
        now = utc_now()

        if result.status != "OK":
            # Record SOURCE_UNAVAILABLE observation (dedupe by day)
            day_key = now.strftime("%Y-%m-%d")
            dedupe_key = f"{provider}:{source_key}:SOURCE_UNAVAILABLE:{day_key}"
            self._add_observation_safe(
                target_id=target.id,
                observation_type="SOURCE_UNAVAILABLE",
                source_type="public_api",
                source_reference=result.api_url,
                observed_at=now,
                confidence=1.0,
                payload={"status": result.status, "error_category": result.error_category},
                dedupe_key=dedupe_key,
            )

            return WatchTargetReport(
                target_id=str(target.id),
                canonical_name=target.canonical_name,
                status=result.status,
            )

        # Get previous observations for this target to detect changes/closures
        prev_observations = self._get_previous_posting_observations(target.id)
        prev_by_source_job_id: dict[str, TargetCompanyObservationModel] = {}
        for obs in prev_observations:
            payload = obs.normalized_payload or {}
            sjid = payload.get("source_job_id")
            if sjid:
                prev_by_source_job_id[sjid] = obs

        current_source_job_ids: set[str] = set()
        report = WatchTargetReport(
            target_id=str(target.id),
            canonical_name=target.canonical_name,
            status="OK",
        )

        for posting in result.postings:
            current_source_job_ids.add(posting.source_job_id)

            # Classify: NEW_ROLE, ROLE_CHANGED, or unchanged
            prev_obs = prev_by_source_job_id.get(posting.source_job_id)

            if prev_obs is None:
                # NEW_ROLE
                observation_type = "NEW_ROLE"
                dedupe_key = f"{provider}:{posting.source_job_id}:{observation_type}"

                # Ingest into deduplication service
                extracted = ExtractedJobPosting(
                    title=posting.title,
                    company=target.canonical_name,
                    location=posting.location_text,
                    job_url=posting.absolute_url,
                    source_job_id=posting.source_job_id,
                    source_provider=provider,
                    source_url=posting.absolute_url,
                    description_snippet=None,
                )
                job_model, is_new = self.dedupe.ingest_posting(extracted, now)

                self._add_observation_safe(
                    target_id=target.id,
                    observation_type=observation_type,
                    source_type="public_api",
                    source_reference=posting.absolute_url,
                    observed_at=now,
                    confidence=1.0,
                    payload={
                        "source_job_id": posting.source_job_id,
                        "title": posting.title,
                        "content_sha256": posting.content_sha256,
                        "location": posting.location_text,
                        "absolute_url": posting.absolute_url,
                    },
                    dedupe_key=dedupe_key,
                    job_id=job_model.id,
                )
                report.new_roles += 1

            else:
                # Check if content changed
                prev_content_sha = (prev_obs.normalized_payload or {}).get("content_sha256", "")
                if prev_content_sha and prev_content_sha != posting.content_sha256:
                    # ROLE_CHANGED
                    observation_type = "ROLE_CHANGED"
                    dedupe_key = f"{provider}:{posting.source_job_id}:{observation_type}:{posting.content_sha256}"

                    self._add_observation_safe(
                        target_id=target.id,
                        observation_type=observation_type,
                        source_type="public_api",
                        source_reference=posting.absolute_url,
                        observed_at=now,
                        confidence=1.0,
                        payload={
                            "source_job_id": posting.source_job_id,
                            "title": posting.title,
                            "content_sha256": posting.content_sha256,
                            "previous_content_sha256": prev_content_sha,
                            "location": posting.location_text,
                            "absolute_url": posting.absolute_url,
                        },
                        dedupe_key=dedupe_key,
                        job_id=prev_obs.job_id,
                    )
                    report.changed_roles += 1
                else:
                    # Unchanged
                    report.unchanged_roles += 1

        # Detect ROLE_CLOSED: previously observed postings absent from this fetch
        for sjid, prev_obs in prev_by_source_job_id.items():
            if sjid not in current_source_job_ids:
                # Check it wasn't already closed
                if prev_obs.observation_type != "ROLE_CLOSED":
                    dedupe_key = f"{provider}:{sjid}:ROLE_CLOSED"
                    self._add_observation_safe(
                        target_id=target.id,
                        observation_type="ROLE_CLOSED",
                        source_type="public_api",
                        source_reference=prev_obs.source_reference,
                        observed_at=now,
                        confidence=0.8,
                        payload={
                            "source_job_id": sjid,
                            "title": (prev_obs.normalized_payload or {}).get("title", ""),
                            "reason": "absent_from_successful_fetch",
                        },
                        dedupe_key=dedupe_key,
                        job_id=prev_obs.job_id,
                    )
                    report.closed_roles += 1

        return report

    def _get_previous_posting_observations(
        self, target_id: uuid.UUID
    ) -> list[TargetCompanyObservationModel]:
        """Get the most recent NEW_ROLE or ROLE_CHANGED observation per source_job_id."""
        all_obs = list(
            self.session.scalars(
                select(TargetCompanyObservationModel)
                .where(
                    TargetCompanyObservationModel.target_company_id == target_id,
                    TargetCompanyObservationModel.observation_type.in_(
                        ["NEW_ROLE", "ROLE_CHANGED"]
                    ),
                )
                .order_by(TargetCompanyObservationModel.observed_at.desc())
            ).all()
        )

        # Deduplicate: keep only latest observation per source_job_id
        seen: dict[str, TargetCompanyObservationModel] = {}
        for obs in all_obs:
            sjid = (obs.normalized_payload or {}).get("source_job_id")
            if sjid and sjid not in seen:
                seen[sjid] = obs
        return list(seen.values())

    def _add_observation_safe(
        self,
        target_id: uuid.UUID,
        observation_type: str,
        source_type: str,
        source_reference: str,
        observed_at: datetime.datetime,
        confidence: float,
        payload: dict[str, Any],
        dedupe_key: str,
        job_id: uuid.UUID | None = None,
    ) -> tuple[TargetCompanyObservationModel, bool]:
        """Add observation with dedupe safety — returns (obs, created)."""
        existing = self.session.scalars(
            select(TargetCompanyObservationModel).where(
                TargetCompanyObservationModel.target_company_id == target_id,
                TargetCompanyObservationModel.dedupe_key == dedupe_key,
            )
        ).first()

        if existing:
            return existing, False

        obs = TargetCompanyObservationModel(
            target_company_id=target_id,
            observation_type=observation_type,
            source_type=source_type,
            source_reference=source_reference,
            observed_at=observed_at,
            confidence=confidence,
            normalized_payload=payload,
            dedupe_key=dedupe_key,
            job_id=job_id,
        )
        self.session.add(obs)
        self.session.flush()
        return obs, True

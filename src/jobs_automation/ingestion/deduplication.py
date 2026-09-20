"""Job normalization and deduplication service."""

from __future__ import annotations

import datetime
import hashlib
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.db.models import CompanyModel, JobModel, JobSourceModel
from jobs_automation.ingestion.models import ExtractedJobPosting


def normalize_string(val: str | None) -> str:
    if not val:
        return ""
    # Lowercase, remove special characters, collapse whitespace
    cleaned = re.sub(r"[^\w\s]", " ", val.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def compute_hash(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class JobDeduplicationService:
    """Normalizes companies and jobs and ensures idempotent deduplication."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_company(self, name: str, domain: str | None = None) -> CompanyModel:
        clean_name = name.strip()
        norm = normalize_string(clean_name)

        # Check existing company by normalized_name or domain
        stmt = select(CompanyModel).where(func.lower(CompanyModel.normalized_name) == norm)
        company = self.session.execute(stmt).scalar_one_or_none()
        if company:
            if domain and not company.domain:
                company.domain = domain
            return company

        company = CompanyModel(
            normalized_name=clean_name,
            domain=domain,
            aliases_json=[clean_name],
        )
        self.session.add(company)
        self.session.flush()
        return company

    def ingest_posting(
        self,
        posting: ExtractedJobPosting,
        observed_at: datetime.datetime,
    ) -> tuple[JobModel, bool]:
        """Ingest extracted job posting according to deduplication evidence order:

        1. Exact requisition_id (if present)
        2. Canonical destination apply URL
        3. Source provider + source_job_id
        4. Company + normalized title + location
        """
        # Ensure company exists
        company = self.get_or_create_company(posting.company)

        existing_job: JobModel | None = None

        # 1. Exact requisition_id
        if posting.requisition_id:
            src_stmt = select(JobSourceModel).where(
                JobSourceModel.requisition_id == posting.requisition_id
            )
            match_src = self.session.execute(src_stmt).scalars().first()
            if match_src:
                existing_job = match_src.job

        # 2. Canonical apply URL
        if not existing_job and posting.job_url:
            src_stmt = select(JobSourceModel).where(
                JobSourceModel.canonical_apply_url == posting.job_url
            )
            match_src = self.session.execute(src_stmt).scalars().first()
            if match_src:
                existing_job = match_src.job

        # 3. Source provider + source_job_id
        if not existing_job and posting.source_job_id:
            src_stmt = select(JobSourceModel).where(
                JobSourceModel.provider == posting.source_provider,
                JobSourceModel.source_job_id == posting.source_job_id,
            )
            match_src = self.session.execute(src_stmt).scalars().first()
            if match_src:
                existing_job = match_src.job

        # 4. Normalized company + title + location (within 60 days)
        if not existing_job:
            norm_title = normalize_string(posting.title)
            cutoff = observed_at - datetime.timedelta(days=60)
            job_stmt = select(JobModel).where(
                JobModel.company_id == company.id,
                func.lower(JobModel.normalized_title) == norm_title,
                JobModel.first_seen_at >= cutoff,
            )
            existing_job = self.session.execute(job_stmt).scalars().first()

        if existing_job:
            # Update last_seen_at and return
            existing_job.last_seen_at = max(existing_job.last_seen_at, observed_at)

            # Check if this source link already recorded
            has_source = any(
                s.provider == posting.source_provider and s.source_job_id == posting.source_job_id
                for s in existing_job.sources
            )
            if not has_source:
                new_source = JobSourceModel(
                    job=existing_job,
                    job_id=existing_job.id,
                    provider=posting.source_provider,
                    source_job_id=posting.source_job_id,
                    source_url=posting.source_url,
                    canonical_apply_url=posting.job_url,
                    requisition_id=posting.requisition_id,
                    source_payload_json=posting.model_dump(),
                    first_seen_at=observed_at,
                    last_seen_at=observed_at,
                )
                self.session.add(new_source)
                if new_source not in existing_job.sources:
                    existing_job.sources.append(new_source)

            self.session.flush()
            return existing_job, False

        # Create new Job
        new_job = JobModel(
            company_id=company.id,
            normalized_title=posting.title.strip(),
            location_text=posting.location,
            remote_type=posting.remote_type,
            compensation_min=int(posting.compensation_min) if posting.compensation_min else None,
            compensation_max=int(posting.compensation_max) if posting.compensation_max else None,
            compensation_currency=posting.compensation_currency,
            description_text=posting.description_snippet,
            description_hash=compute_hash(posting.description_snippet),
            posted_at=observed_at,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            status="discovered",
        )
        self.session.add(new_job)
        self.session.flush()

        # Create JobSource link
        source = JobSourceModel(
            job_id=new_job.id,
            provider=posting.source_provider,
            source_job_id=posting.source_job_id,
            source_url=posting.source_url,
            canonical_apply_url=posting.job_url,
            requisition_id=posting.requisition_id,
            source_payload_json=posting.model_dump(),
            first_seen_at=observed_at,
            last_seen_at=observed_at,
        )
        self.session.add(source)
        self.session.flush()

        return new_job, True

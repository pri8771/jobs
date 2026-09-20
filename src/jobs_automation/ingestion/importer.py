"""Pipeline and direct job importer service."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from jobs_automation.ingestion.deduplication import JobDeduplicationService
from jobs_automation.ingestion.models import ExtractedJobPosting
from jobs_automation.ingestion.parsers.base import clean_url, detect_remote_type, parse_salary_range

logger = logging.getLogger(__name__)


class JobImportSummary:
    """Summary metrics of an import run."""

    def __init__(self) -> None:
        self.total_processed: int = 0
        self.new_jobs_added: int = 0
        self.existing_jobs_updated: int = 0
        self.skipped_gone: int = 0
        self.errors: list[str] = []


class JobImporter:
    """Imports job postings from structured JSONL pipeline files or direct sources."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.dedup_service = JobDeduplicationService(session)

    def import_from_jsonl(
        self,
        file_path: str | Path,
        skip_gone: bool = True,
        limit: int | None = None,
    ) -> JobImportSummary:
        """Import jobs from a JSONL file (e.g. candidate pipeline file)."""
        summary = JobImportSummary()
        path = Path(file_path)
        if not path.exists():
            summary.errors.append(f"File not found: {file_path}")
            return summary

        observed_at = datetime.datetime.now(datetime.UTC)
        count = 0

        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if limit is not None and count >= limit:
                    break
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                except json.JSONDecodeError as err:
                    summary.errors.append(f"Line {line_no}: Invalid JSON - {err}")
                    continue

                status = str(data.get("status", "")).lower()
                if skip_gone and status in ("gone", "expired", "closed"):
                    summary.skipped_gone += 1
                    continue

                posting = self._posting_from_dict(data)
                if not posting:
                    continue

                summary.total_processed += 1
                try:
                    _, is_new = self.dedup_service.ingest_posting(posting, observed_at)
                    if is_new:
                        summary.new_jobs_added += 1
                    else:
                        summary.existing_jobs_updated += 1
                    count += 1
                except Exception as ex:
                    summary.errors.append(f"Line {line_no} ({posting.title}): {ex}")

        self.session.commit()
        return summary

    def _posting_from_dict(self, data: dict[str, Any]) -> ExtractedJobPosting | None:
        title = str(data.get("title", "")).strip()
        company = str(data.get("company", "")).strip()
        if not title or not company:
            return None

        salary_text = str(data.get("salary", ""))
        sal_min, sal_max, currency = parse_salary_range(salary_text)

        location = data.get("location")
        remote_val = data.get("remote")
        remote_type: str | None = None
        if remote_val is True:
            remote_type = "remote"
        elif remote_val is False:
            remote_type = detect_remote_type(str(location or "")) or "on_site"
        elif location:
            remote_type = detect_remote_type(str(location))

        apply_url = data.get("apply_url") or data.get("url") or ""
        clean_apply_url = clean_url(str(apply_url)) if apply_url else None

        key = str(data.get("key", ""))
        # If key is gh:snorkelai:6150440004 -> requisition_id is 6150440004
        req_id: str | None = None
        if key and ":" in key:
            parts = key.split(":")
            if len(parts) >= 3 and parts[-1].isdigit():
                req_id = parts[-1]

        ats_provider = str(data.get("ats") or "pipeline_import")

        return ExtractedJobPosting(
            title=title,
            company=company,
            location=str(location) if location else None,
            remote_type=remote_type,
            compensation_min=sal_min,
            compensation_max=sal_max,
            compensation_currency=currency,
            job_url=clean_apply_url,
            source_url=str(data.get("url")) if data.get("url") else None,
            source_job_id=key or clean_apply_url,
            requisition_id=req_id,
            source_provider=ats_provider,
            description_snippet=str(data.get("note")) if data.get("note") else None,
        )

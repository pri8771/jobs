import datetime
import hashlib
import json
from typing import Any

from jobs_automation.ingestion.sources.base import PublicPosting, SourceFetchResult, Transport
from jobs_automation.ingestion.sources.greenhouse_board import DefaultTransport


class LeverPostingsSource:
    def __init__(self, transport: Transport | None = None):
        self.transport = transport or DefaultTransport()
        self.provider = "LEVER"
        self._user_agent = "jobs-automation/2.3"

    def fetch(self, source_key: str) -> SourceFetchResult:
        """Fetch all postings for a Lever site token."""
        api_url = f"https://api.lever.co/v0/postings/{source_key}?mode=json"
        
        try:
            status_code, body = self.transport.get(
                api_url, 
                timeout=20.0, 
                headers={"User-Agent": self._user_agent}
            )
        except TimeoutError:
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="UNAVAILABLE",
                error_category="timeout"
            )

        if status_code == 429:
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="RATE_LIMITED",
                http_status=status_code,
                error_category="rate_limit"
            )
        elif status_code >= 500:
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="UNAVAILABLE",
                http_status=status_code,
                error_category="server_error"
            )
        elif status_code != 200:
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="UNAVAILABLE",
                http_status=status_code,
                error_category="http_error"
            )

        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="INVALID",
                http_status=status_code,
                error_category="json_decode_error"
            )

        if not isinstance(payload, list):
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="INVALID",
                http_status=status_code,
                error_category="invalid_schema"
            )

        postings = []
        for job in payload:
            if not isinstance(job, dict):
                continue
            
            job_id = str(job.get("id", ""))
            if not job_id:
                continue

            title = job.get("text", "").strip()
            absolute_url = job.get("hostedUrl", "")
            
            categories = job.get("categories", {})
            location_text = None
            if isinstance(categories, dict):
                location_text = str(categories.get("location") or "").strip()
            
            created_at_ms = job.get("createdAt")
            updated_at = None
            if created_at_ms and isinstance(created_at_ms, (int, float)):
                try:
                    updated_at = datetime.datetime.fromtimestamp(created_at_ms / 1000.0, tz=datetime.UTC)
                except (ValueError, OSError):
                    pass

            content_text = job.get("descriptionPlain", "") or ""
            content_sha256 = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
            raw_payload_hash = hashlib.sha256(json.dumps(job, sort_keys=True).encode("utf-8")).hexdigest()

            postings.append(
                PublicPosting(
                    provider=self.provider,
                    source_job_id=job_id,
                    title=title,
                    absolute_url=absolute_url,
                    location_text=location_text,
                    updated_at=updated_at,
                    content_sha256=content_sha256,
                    raw_payload_hash=raw_payload_hash,
                )
            )

        return SourceFetchResult(
            provider=self.provider,
            source_key=source_key,
            api_url=api_url,
            status="OK",
            http_status=status_code,
            postings=postings
        )

import datetime
import hashlib
import json
import urllib.error
import urllib.request
from typing import Any, Literal

from jobs_automation.ingestion.sources.base import PublicPosting, SourceFetchResult, Transport


class DefaultTransport(Transport):
    def get(self, url: str, timeout: float = 20.0, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        req = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except urllib.error.URLError as e:
            raise TimeoutError(f"Connection failed: {e}") from e
        except TimeoutError as e:
            raise TimeoutError(f"Request timed out: {e}") from e


class GreenhouseBoardSource:
    def __init__(self, transport: Transport | None = None):
        self.transport = transport or DefaultTransport()
        self.provider = "GREENHOUSE"
        self._user_agent = "jobs-automation/2.3"

    def fetch(self, source_key: str) -> SourceFetchResult:
        """Fetch all postings for a greenhouse board token."""
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{source_key}/jobs?content=true"
        
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

        if not isinstance(payload, dict) or "jobs" not in payload:
            return SourceFetchResult(
                provider=self.provider,
                source_key=source_key,
                api_url=api_url,
                status="INVALID",
                http_status=status_code,
                error_category="invalid_schema"
            )

        postings = []
        for job in payload.get("jobs", []):
            if not isinstance(job, dict):
                continue
            
            job_id = str(job.get("id", ""))
            if not job_id:
                continue

            title = job.get("title", "").strip()
            absolute_url = job.get("absolute_url", "")
            
            location_obj = job.get("location")
            location_text = None
            if isinstance(location_obj, dict):
                location_text = str(location_obj.get("name") or "").strip()
            
            updated_str = job.get("updated_at")
            updated_at = None
            if updated_str:
                try:
                    updated_at = datetime.datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            content_text = job.get("content", "") or ""
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

    def fetch_single_job(self, board_token: str, job_id: str) -> dict[str, Any]:
        """Fetch a single job with questions=true for the importer script."""
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}?questions=true"
        try:
            status_code, body = self.transport.get(
                api_url, 
                timeout=20.0, 
                headers={"User-Agent": self._user_agent}
            )
        except TimeoutError as e:
            raise TimeoutError(f"Connection failed: {e}") from e

        if status_code != 200:
            raise urllib.error.URLError(f"HTTP Error {status_code}")

        try:
            return json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError("Invalid JSON response") from e


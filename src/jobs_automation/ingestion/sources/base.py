import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from jobs_automation.db.base import utc_now


class PublicPosting(BaseModel):
    provider: str
    source_job_id: str
    title: str
    absolute_url: str
    location_text: str | None = None
    updated_at: datetime.datetime | None = None
    content_sha256: str
    raw_payload_hash: str


class SourceFetchResult(BaseModel):
    provider: str
    source_key: str
    api_url: str
    fetched_at_utc: datetime.datetime = Field(default_factory=utc_now)
    status: Literal["OK", "UNAVAILABLE", "RATE_LIMITED", "INVALID"]
    http_status: int | None = None
    postings: list[PublicPosting] = Field(default_factory=list)
    error_category: str | None = None


class Transport(Protocol):
    def get(self, url: str, timeout: float = 20.0, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        ...


class PublicJobSource(Protocol):
    def fetch(self, source_key: str) -> SourceFetchResult:
        ...


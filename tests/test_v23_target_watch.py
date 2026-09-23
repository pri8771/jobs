import pytest
from jobs_automation.ingestion.sources.greenhouse_board import GreenhouseBoardSource
from jobs_automation.ingestion.sources.base import Transport
import json

class FakeTransport(Transport):
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.body = body

    def get(self, url: str, timeout: float = 20.0, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        if self.status_code == -1:
            raise TimeoutError("Fake timeout")
        return self.status_code, self.body

def test_greenhouse_fetch_ok():
    payload = {
        "jobs": [
            {
                "id": "123",
                "title": "Engineer",
                "absolute_url": "https://url",
                "content": "some text",
                "location": {"name": "Remote"}
            }
        ]
    }
    transport = FakeTransport(200, json.dumps(payload).encode("utf-8"))
    source = GreenhouseBoardSource(transport=transport)
    res = source.fetch("test_token")
    
    assert res.status == "OK"
    assert len(res.postings) == 1
    p = res.postings[0]
    assert p.source_job_id == "123"
    assert p.title == "Engineer"
    assert p.location_text == "Remote"

def test_greenhouse_fetch_rate_limit():
    transport = FakeTransport(429, b"Rate Limited")
    source = GreenhouseBoardSource(transport=transport)
    res = source.fetch("test_token")
    assert res.status == "RATE_LIMITED"

def test_greenhouse_fetch_invalid_json():
    transport = FakeTransport(200, b"not json")
    source = GreenhouseBoardSource(transport=transport)
    res = source.fetch("test_token")
    assert res.status == "INVALID"

def test_greenhouse_fetch_timeout():
    transport = FakeTransport(-1, b"")
    source = GreenhouseBoardSource(transport=transport)
    res = source.fetch("test_token")
    assert res.status == "UNAVAILABLE"

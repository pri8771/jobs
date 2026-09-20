"""Tests for JobImporter service."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.models import JobModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.importer import JobImporter


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_job_importer_jsonl(tmp_path: Path, db_session: Session) -> None:
    sample_data = [
        {
            "key": "gh:snorkelai:6150440004",
            "title": "Senior IT Platform and Automation Engineer",
            "url": "https://job-boards.greenhouse.io/snorkelai/jobs/6150440004",
            "apply_url": "https://job-boards.greenhouse.io/snorkelai/jobs/6150440004",
            "location": "New York City, NY (Hybrid); San Francisco, CA (Hybrid)",
            "remote": False,
            "posted": "2026-09-09",
            "salary": "$150,000–$220,000",
            "company": "Snorkel AI",
            "ats": "greenhouse",
            "status": "new",
            "note": "high fit",
        },
        {
            "key": "gh:snorkelai:9999999999",
            "title": "Old Expired Role",
            "url": "https://job-boards.greenhouse.io/snorkelai/jobs/9999999999",
            "company": "Snorkel AI",
            "status": "gone",
        },
    ]

    file_path = tmp_path / "pipeline.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")

    importer = JobImporter(db_session)
    summary = importer.import_from_jsonl(file_path=file_path, skip_gone=True)

    assert summary.total_processed == 1
    assert summary.new_jobs_added == 1
    assert summary.skipped_gone == 1
    assert len(summary.errors) == 0

    # Verify job persisted in DB
    jobs = db_session.query(JobModel).all()
    assert len(jobs) == 1
    assert jobs[0].normalized_title == "Senior IT Platform and Automation Engineer"
    assert jobs[0].company is not None
    assert jobs[0].company.normalized_name == "Snorkel AI"

    # Second run: test idempotency and deduplication
    summary2 = importer.import_from_jsonl(file_path=file_path, skip_gone=True)
    assert summary2.total_processed == 1
    assert summary2.new_jobs_added == 0
    assert summary2.existing_jobs_updated == 1

    jobs2 = db_session.query(JobModel).all()
    assert len(jobs2) == 1

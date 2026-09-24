"""Unit tests for Interview Intelligence CLI & dashboard endpoint (V23-II-07)."""

import json
import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.cli.intelligence_cli import intel_cli
from jobs_automation.db.base import Base
from jobs_automation.db.models import ApplicationModel, CompanyModel, JobModel
from jobs_automation.dashboard.server import DashboardRequestHandler


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_cli_interview_brief_smoke() -> None:
    runner = CliRunner()
    res = runner.invoke(intel_cli, ["interview-brief", "00000000-0000-0000-0000-000000000000"])
    assert res.exit_code == 0
    assert "Error" in res.output or "Application not found" in res.output


def test_cli_followup_package_smoke() -> None:
    runner = CliRunner()
    res = runner.invoke(intel_cli, ["followup-package", "00000000-0000-0000-0000-000000000000"])
    assert res.exit_code == 0
    assert "Error" in res.output or "Application not found" in res.output

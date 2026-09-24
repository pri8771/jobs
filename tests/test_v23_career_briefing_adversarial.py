"""Adversarial and invariant tests for V2.3 Career Briefing (V23-CB-03..05)."""

import json
import os
import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.cli.intelligence_cli import intel_cli
from jobs_automation.db.base import Base
from jobs_automation.db.models import CompanyModel, JobModel
from jobs_automation.intelligence.briefing import export_briefing_schema
from jobs_automation.intelligence.briefing_service import CareerBriefingService


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


def test_briefing_schema_export_up_to_date() -> None:
    """Contract rule CB-01: JSON schema export is up to date with CareerBriefing model."""
    exported_json = export_briefing_schema()
    assert os.path.exists("docs/schemas/career_briefing.schema.json")
    with open("docs/schemas/career_briefing.schema.json", "r", encoding="utf-8") as f:
        content = f.read()
    assert content.strip() == exported_json.strip()


def test_empty_db_briefing_has_data_gaps_no_exceptions(db_session: Session) -> None:
    """Contract rule CB-02: Empty DB produces briefing with data gaps and zero exceptions."""
    svc = CareerBriefingService(db_session)
    briefing = svc.build()

    assert briefing.artifact_type == "career_briefing"
    assert len(briefing.data_gaps) >= 1
    assert "Zero real applications" in briefing.data_gaps[0]
    assert len(briefing.top_opportunities) == 0


def test_briefing_opportunities_ordering(db_session: Session) -> None:
    """Contract rule CB-02: Top opportunities ranked deterministically."""
    c = CompanyModel(normalized_name="RankCo")
    db_session.add(c)
    db_session.flush()

    j1 = JobModel(company_id=c.id, normalized_title="SWE 1", status="active")
    j2 = JobModel(company_id=c.id, normalized_title="SWE 2", status="active")
    db_session.add_all([j1, j2])
    db_session.commit()

    svc = CareerBriefingService(db_session)
    briefing = svc.build(limit=10)

    assert len(briefing.top_opportunities) == 2


def test_cli_briefing_smoke(db_session) -> None:
    """Contract rule CB-03: CLI intel briefing smoke test."""
    from unittest.mock import patch
    from sqlalchemy.orm import sessionmaker

    runner = CliRunner()
    with patch("jobs_automation.cli.intelligence_cli.get_sessionmaker") as mock_sm:
        mock_sm.return_value = lambda: db_session
        res = runner.invoke(intel_cli, ["briefing"])
        assert res.exit_code == 0
        assert "Career Briefing Summary" in res.output or "Opportunities" in res.output


def test_cli_briefing_json(db_session) -> None:
    """Contract rule CB-03: CLI intel briefing --json output."""
    from unittest.mock import patch

    runner = CliRunner()
    with patch("jobs_automation.cli.intelligence_cli.get_sessionmaker") as mock_sm:
        mock_sm.return_value = lambda: db_session
        res = runner.invoke(intel_cli, ["briefing", "--json"])
        assert res.exit_code == 0
        parsed = json.loads(res.output)
        assert parsed["artifact_type"] == "career_briefing"

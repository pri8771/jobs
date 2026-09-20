"""Tests for ProfileWorksheetGenerator."""

from jobs_automation.core.config import ConfigLoader
from jobs_automation.worksheets.generator import ProfileWorksheetGenerator


def test_worksheet_contains_positioning_and_tracks() -> None:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile()
    job_search, _ = loader.load_job_search()

    gen = ProfileWorksheetGenerator(profile, job_search)
    md = gen.generate_markdown()

    # Core positioning
    assert "Enterprise Automation & Solutions Architect" in md
    assert "$150,000+" in md
    assert "Carnegie Mellon University" in md
    assert "Viatris" in md

    # Targeted resume versions
    assert "enterprise_automation_solutions_architect" in md
    assert "senior_software_ai_automation" in md
    assert "senior_ios_mobile_lead" in md
    assert "it_apps_infrastructure_manager" in md

    # 4 Platforms
    assert "Platform Setup: LinkedIn" in md
    assert "Platform Setup: Indeed" in md
    assert "Platform Setup: ZipRecruiter" in md
    assert "Platform Setup: Dice" in md

    # 4-hour email polling checklist
    assert "Every 4 hours (240 minutes)" in md

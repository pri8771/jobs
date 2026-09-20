"""Unit tests for alert email parsers and normalization utilities."""

import datetime

from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.ingestion.parsers import AlertParserRegistry
from jobs_automation.ingestion.parsers.base import (
    clean_url,
    detect_remote_type,
    parse_salary_range,
)
from jobs_automation.ingestion.parsers.dice import DiceAlertParser
from jobs_automation.ingestion.parsers.generic import GenericAlertParser
from jobs_automation.ingestion.parsers.indeed import IndeedAlertParser
from jobs_automation.ingestion.parsers.linkedin import LinkedInAlertParser
from jobs_automation.ingestion.parsers.ziprecruiter import ZipRecruiterAlertParser
from tests.fixtures.emails.sample_generator import get_sample_email_fixtures


def test_clean_url_strips_tracking_params() -> None:
    raw = "https://www.linkedin.com/jobs/view/4100112233?utm_source=alert&trk=eml-jobs-alert&refId=abc1234&midToken=xyz"
    cleaned = clean_url(raw)
    assert cleaned == "https://www.linkedin.com/jobs/view/4100112233"

    indeed_raw = "https://www.indeed.com/viewjob?jk=a1b2c3d4e5f6&from=ja&utm_campaign=daily_alert"
    indeed_clean = clean_url(indeed_raw)
    assert "from=" not in indeed_clean
    assert "utm_campaign=" not in indeed_clean
    assert "jk=a1b2c3d4e5f6" in indeed_clean


def test_parse_salary_range() -> None:
    min_sal, max_sal, curr = parse_salary_range("$150,000 - $185,000/yr")
    assert min_sal == 150000.0
    assert max_sal == 185000.0
    assert curr == "USD"

    min_k, max_k, _ = parse_salary_range("$160K - $190K")
    assert min_k == 160000.0
    assert max_k == 190000.0

    min_plus, max_plus, _ = parse_salary_range("$150,000+")
    assert min_plus == 150000.0
    assert max_plus is None

    hourly_min, _, _ = parse_salary_range("$75/hr")
    assert hourly_min == 75.0 * 2080.0


def test_detect_remote_type() -> None:
    assert detect_remote_type("Pittsburgh, PA (Hybrid)") == "hybrid"
    assert detect_remote_type("Remote - United States") == "remote"
    assert detect_remote_type("New York, NY (On-site)") == "on_site"
    assert detect_remote_type("Pittsburgh, PA") is None


def test_linkedin_parser_with_sample_fixture() -> None:
    fixtures = get_sample_email_fixtures()
    linkedin_msg = fixtures[0]  # LinkedIn alert
    parser = LinkedInAlertParser()

    assert parser.can_parse(linkedin_msg) is True
    postings = parser.parse(linkedin_msg)

    assert len(postings) == 2
    assert postings[0].title == "Enterprise Automation Architect"
    assert postings[0].company == "Viatris Global"
    assert postings[0].location == "Pittsburgh, PA (Hybrid)"
    assert postings[0].remote_type == "hybrid"
    assert postings[0].compensation_min == 165000.0
    assert postings[0].compensation_max == 195000.0
    assert postings[0].source_job_id == "4100112233"
    assert postings[0].job_url is not None
    assert "https://www.linkedin.com/jobs/view/4100112233" in postings[0].job_url


def test_indeed_parser_with_sample_fixture() -> None:
    fixtures = get_sample_email_fixtures()
    indeed_msg = fixtures[1]  # Indeed alert
    parser = IndeedAlertParser()

    assert parser.can_parse(indeed_msg) is True
    postings = parser.parse(indeed_msg)

    assert len(postings) == 1
    assert postings[0].title == "Senior AI Automation Engineer"
    assert postings[0].company == "Cresta AI"
    assert postings[0].remote_type == "remote"
    assert postings[0].source_job_id == "a1b2c3d4e5f6"
    assert postings[0].compensation_min == 160000.0
    assert postings[0].compensation_max == 190000.0


def test_ziprecruiter_parser_with_sample_fixture() -> None:
    fixtures = get_sample_email_fixtures()
    zip_msg = fixtures[2]  # ZipRecruiter alert
    parser = ZipRecruiterAlertParser()

    assert parser.can_parse(zip_msg) is True
    postings = parser.parse(zip_msg)

    assert len(postings) == 1
    assert postings[0].title == "Principal Solutions Architect"
    assert postings[0].company == "Databricks"
    assert postings[0].remote_type == "remote"
    assert postings[0].compensation_min == 180000.0


def test_dice_parser_with_sample_fixture() -> None:
    fixtures = get_sample_email_fixtures()
    dice_msg = fixtures[3]  # Dice alert
    parser = DiceAlertParser()

    assert parser.can_parse(dice_msg) is True
    postings = parser.parse(dice_msg)

    assert len(postings) == 1
    assert postings[0].title == "SAP Integration & Automation Lead"
    assert postings[0].company == "Siemens Enterprise"
    assert postings[0].source_job_id == "dice_job_555"
    assert postings[0].compensation_min == 155000.0


def test_generic_alert_parser() -> None:
    now = datetime.datetime.now(datetime.UTC)
    html = """
    <html>
      <body>
        <h2>Career Opportunities at Stripe</h2>
        <div>
          <a href="https://boards.greenhouse.io/stripe/jobs/5678901?utm_source=alert">
            Staff Enterprise Architect
          </a>
          <div>Stripe</div>
          <div>Remote, US</div>
        </div>
      </body>
    </html>
    """
    msg = RawEmailMessage(
        provider_message_id="generic_msg_1",
        provider_thread_id="thread_generic_1",
        received_at=now,
        sender="careers@stripe.com",
        recipients=["candidate@gmail.com"],
        direction="inbound",
        subject="New Job Openings at Stripe",
        body_text="Staff Enterprise Architect at Stripe",
        body_html=html,
    )
    parser = GenericAlertParser()
    assert parser.can_parse(msg) is True
    postings = parser.parse(msg)
    assert len(postings) == 1
    assert postings[0].title == "Staff Enterprise Architect"
    assert postings[0].company == "Stripe"


def test_alert_parser_registry_dispatches_correctly() -> None:
    registry = AlertParserRegistry()
    fixtures = get_sample_email_fixtures()

    # LinkedIn
    li_jobs = registry.parse_alert_email(fixtures[0])
    assert len(li_jobs) == 2
    assert li_jobs[0].source_provider == "linkedin"

    # Indeed
    in_jobs = registry.parse_alert_email(fixtures[1])
    assert len(in_jobs) == 1
    assert in_jobs[0].source_provider == "indeed"

    # ZipRecruiter
    zr_jobs = registry.parse_alert_email(fixtures[2])
    assert len(zr_jobs) == 1
    assert zr_jobs[0].source_provider == "ziprecruiter"

    # Dice
    dice_jobs = registry.parse_alert_email(fixtures[3])
    assert len(dice_jobs) == 1
    assert dice_jobs[0].source_provider == "dice"

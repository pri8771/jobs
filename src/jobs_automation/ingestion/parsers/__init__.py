"""Alert parser registry and factory."""

from __future__ import annotations

from jobs_automation.ingestion.models import ExtractedJobPosting, RawEmailMessage
from jobs_automation.ingestion.parsers.base import BaseAlertParser
from jobs_automation.ingestion.parsers.dice import DiceAlertParser
from jobs_automation.ingestion.parsers.generic import GenericAlertParser
from jobs_automation.ingestion.parsers.indeed import IndeedAlertParser
from jobs_automation.ingestion.parsers.linkedin import LinkedInAlertParser
from jobs_automation.ingestion.parsers.ziprecruiter import ZipRecruiterAlertParser


class AlertParserRegistry:
    """Manages alert parsers and dispatches emails to the correct parser."""

    def __init__(self) -> None:
        self.parsers: list[BaseAlertParser] = [
            LinkedInAlertParser(),
            IndeedAlertParser(),
            ZipRecruiterAlertParser(),
            DiceAlertParser(),
            GenericAlertParser(),
        ]

    def parse_alert_email(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        for parser in self.parsers:
            if parser.can_parse(email):
                postings = parser.parse(email)
                if postings:
                    return postings
        return []


__all__ = [
    "AlertParserRegistry",
    "BaseAlertParser",
    "DiceAlertParser",
    "GenericAlertParser",
    "IndeedAlertParser",
    "LinkedInAlertParser",
    "ZipRecruiterAlertParser",
]

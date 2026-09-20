"""Email ingestion module."""

from jobs_automation.ingestion.classifier import EmailClassifier
from jobs_automation.ingestion.deduplication import JobDeduplicationService
from jobs_automation.ingestion.engine import EmailIngestionEngine, IngestionSweepSummary
from jobs_automation.ingestion.models import (
    EmailClassification,
    EmailClassificationResult,
    ExtractedJobPosting,
    RawEmailMessage,
)
from jobs_automation.ingestion.parsers import AlertParserRegistry

__all__ = [
    "AlertParserRegistry",
    "EmailClassification",
    "EmailClassificationResult",
    "EmailClassifier",
    "EmailIngestionEngine",
    "ExtractedJobPosting",
    "IngestionSweepSummary",
    "JobDeduplicationService",
    "RawEmailMessage",
]

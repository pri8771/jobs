"""Interview details extraction and calendar schedule management."""

from __future__ import annotations

import datetime
import re
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from jobs_automation.db.models import InboundMessageModel, InterviewModel


class ExtractedInterviewDetails(BaseModel):
    """Structured interview information parsed from recruiting messages."""

    model_config = ConfigDict(extra="forbid")

    round_type: str  # recruiter_screen, technical_screen, system_design, hiring_manager, panel, general_interview
    scheduled_start: datetime.datetime
    scheduled_end: datetime.datetime
    timezone: str = "UTC"
    meeting_link: str | None = None
    notes: str | None = None


class InterviewExtractor:
    """Extracts round type, meeting link, and schedules from interview communications."""

    MEETING_LINK_PATTERNS = [
        re.compile(r"https://[a-zA-Z0-9.-]*zoom\.us/j/[0-9?=\-_a-zA-Z]+", re.IGNORECASE),
        re.compile(r"https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}", re.IGNORECASE),
        re.compile(r"https://teams\.microsoft\.com/l/meetup-join/[^\s\"'>]+", re.IGNORECASE),
        re.compile(r"https://[a-zA-Z0-9.-]*webex\.com/[^\s\"'>]+", re.IGNORECASE),
        re.compile(r"https://calendly\.com/[^\s\"'>]+", re.IGNORECASE),
    ]

    ROUND_PATTERNS = [
        (
            re.compile(r"\b(recruiter|introductory|phone)\s+screen\b", re.IGNORECASE),
            "recruiter_screen",
        ),
        (
            re.compile(r"\b(technical|coding|architecture)\s+(interview|screen)\b", re.IGNORECASE),
            "technical_screen",
        ),
        (
            re.compile(r"\b(system\s+design|architecture\s+deep\s+dive)\b", re.IGNORECASE),
            "system_design",
        ),
        (
            re.compile(
                r"\b(hiring\s+manager|manager|director)\s+(interview|chat|screen)\b", re.IGNORECASE
            ),
            "hiring_manager",
        ),
        (re.compile(r"\b(onsite|panel|final\s+round)\b", re.IGNORECASE), "panel"),
    ]

    def __init__(self, session: Session) -> None:
        self.session = session

    def extract_meeting_link(self, text: str) -> str | None:
        for pat in self.MEETING_LINK_PATTERNS:
            match = pat.search(text)
            if match:
                return match.group(0)
        return None

    def detect_round_type(self, text: str) -> str:
        for pat, r_type in self.ROUND_PATTERNS:
            if pat.search(text):
                return r_type
        return "general_interview"

    def extract_from_message(
        self,
        message: InboundMessageModel,
    ) -> ExtractedInterviewDetails | None:
        """Parses interview details from an inbound message."""
        body = message.body_text
        subject = message.subject
        combined = f"{subject}\n{body}"

        if message.classification not in (
            "INTERVIEW_REQUEST",
            "INTERVIEW_CONFIRMATION",
            "INTERVIEW_RESCHEDULE",
            "SCREENING_REQUEST",
        ):
            return None

        round_type = self.detect_round_type(combined)
        meeting_link = self.extract_meeting_link(combined)

        # Default start to received_at + 2 days (45 minute standard round) if not explicitly parsed
        start_time = message.received_at + datetime.timedelta(days=2, hours=2)
        end_time = start_time + datetime.timedelta(minutes=45)

        return ExtractedInterviewDetails(
            round_type=round_type,
            scheduled_start=start_time,
            scheduled_end=end_time,
            timezone="UTC",
            meeting_link=meeting_link,
            notes=f"Extracted from email subject: {subject}",
        )

    def record_interview(
        self,
        application_id: uuid.UUID,
        details: ExtractedInterviewDetails,
    ) -> InterviewModel:
        """Persists or updates an InterviewModel for the application."""
        interview = InterviewModel(
            application_id=application_id,
            round_type=details.round_type,
            scheduled_start=details.scheduled_start,
            scheduled_end=details.scheduled_end,
            timezone=details.timezone,
            location_or_link=details.meeting_link,
            status="scheduled",
            notes=details.notes,
        )
        self.session.add(interview)
        self.session.flush()
        return interview

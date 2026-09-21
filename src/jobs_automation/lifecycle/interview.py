"""Interview details extraction, parsing, and calendar schedule management."""

from __future__ import annotations

import datetime
import logging
import re
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.models import InboundMessageModel, InterviewModel, TaskModel

logger = logging.getLogger(__name__)


class ExtractedInterviewDetails(BaseModel):
    """Structured interview information parsed from recruiting messages."""

    model_config = ConfigDict(extra="forbid")

    round_type: str  # recruiter_screen, technical_screen, system_design, hiring_manager, panel, general_interview
    scheduled_start: datetime.datetime | None = None
    scheduled_end: datetime.datetime | None = None
    timezone: str = "UTC"
    meeting_link: str | None = None
    notes: str | None = None
    is_reschedule: bool = False
    is_cancellation: bool = False
    has_explicit_schedule: bool = False


class InterviewExtractor:
    """Extracts round type, meeting link, and explicit schedules from interview communications."""

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

    TZ_OFFSETS: dict[str, datetime.timezone] = {
        "UTC": datetime.UTC,
        "GMT": datetime.UTC,
        "EDT": datetime.timezone(datetime.timedelta(hours=-4)),
        "EST": datetime.timezone(datetime.timedelta(hours=-5)),
        "CDT": datetime.timezone(datetime.timedelta(hours=-5)),
        "CST": datetime.timezone(datetime.timedelta(hours=-6)),
        "MDT": datetime.timezone(datetime.timedelta(hours=-6)),
        "MST": datetime.timezone(datetime.timedelta(hours=-7)),
        "PDT": datetime.timezone(datetime.timedelta(hours=-7)),
        "PST": datetime.timezone(datetime.timedelta(hours=-8)),
    }

    MONTH_MAP: dict[str, int] = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

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

    def parse_explicit_datetime(
        self, text: str
    ) -> tuple[datetime.datetime | None, datetime.datetime | None, str]:
        """Attempts to parse an explicit date, time, duration, and timezone from text.

        Returns (start_utc, end_utc, detected_tz_name). Never fabricates defaults.
        """
        # 1. ISO 8601 pattern: e.g. 2026-10-15T14:00:00Z or 2026-10-15 14:00
        iso_match = re.search(
            r"\b(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}(?::\d{2})?)\s*([A-Z]{3}|Z|[+-]\d{2}:?\d{2})?\b",
            text,
        )
        if iso_match:
            date_part, time_part, tz_part = iso_match.groups()
            tz_str = tz_part or "UTC"
            tzinfo = self._resolve_timezone(tz_str)
            try:
                dt_str = f"{date_part}T{time_part}"
                if len(time_part) == 5:
                    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
                else:
                    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                dt = dt.replace(tzinfo=tzinfo)
                start_utc = dt.astimezone(datetime.UTC)
                end_utc = self._estimate_end_time(start_utc, text)
                return start_utc, end_utc, tz_str
            except ValueError:
                pass

        # 2. English written date: e.g. "October 15, 2026 at 2:00 PM EDT" or "Oct 15, 2026 14:00 UTC"
        written_pattern = re.compile(
            r"\b(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+)?"
            r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})"
            r"(?:\s+(?:at|from|@)\s+|\s+)"
            r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?"
            r"(?:\s+([A-Z]{3}|[+-]\d{2}:?\d{2}))?\b",
            re.IGNORECASE,
        )
        m = written_pattern.search(text)
        if m:
            month_str, day_str, year_str, hour_str, min_str, _sec_str, am_pm, tz_str = m.groups()
            month_key = month_str.lower()
            if month_key in self.MONTH_MAP:
                month = self.MONTH_MAP[month_key]
                day = int(day_str)
                year = int(year_str)
                hour = int(hour_str)
                minute = int(min_str)
                if am_pm:
                    am_pm = am_pm.upper()
                    if am_pm == "PM" and hour < 12:
                        hour += 12
                    elif am_pm == "AM" and hour == 12:
                        hour = 0

                resolved_tz_str = tz_str or "UTC"
                tzinfo = self._resolve_timezone(resolved_tz_str)
                try:
                    dt = datetime.datetime(year, month, day, hour, minute, tzinfo=tzinfo)
                    start_utc = dt.astimezone(datetime.UTC)
                    end_utc = self._estimate_end_time(start_utc, text)
                    return start_utc, end_utc, resolved_tz_str
                except ValueError:
                    pass

        # 3. Day-Month-Year: e.g. "15 October 2026 at 14:00 UTC"
        dmy_pattern = re.compile(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})"
            r"(?:\s+(?:at|from|@)\s+|\s+)"
            r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?"
            r"(?:\s+([A-Z]{3}|[+-]\d{2}:?\d{2}))?\b",
            re.IGNORECASE,
        )
        m2 = dmy_pattern.search(text)
        if m2:
            day_str, month_str, year_str, hour_str, min_str, _sec_str, am_pm, tz_str = m2.groups()
            month_key = month_str.lower()
            if month_key in self.MONTH_MAP:
                month = self.MONTH_MAP[month_key]
                day = int(day_str)
                year = int(year_str)
                hour = int(hour_str)
                minute = int(min_str)
                if am_pm:
                    am_pm = am_pm.upper()
                    if am_pm == "PM" and hour < 12:
                        hour += 12
                    elif am_pm == "AM" and hour == 12:
                        hour = 0

                resolved_tz_str = tz_str or "UTC"
                tzinfo = self._resolve_timezone(resolved_tz_str)
                try:
                    dt = datetime.datetime(year, month, day, hour, minute, tzinfo=tzinfo)
                    start_utc = dt.astimezone(datetime.UTC)
                    end_utc = self._estimate_end_time(start_utc, text)
                    return start_utc, end_utc, resolved_tz_str
                except ValueError:
                    pass

        return None, None, "UTC"

    def _resolve_timezone(self, tz_str: str) -> datetime.timezone:
        clean = tz_str.strip().upper()
        if clean in self.TZ_OFFSETS:
            return self.TZ_OFFSETS[clean]
        if clean.startswith(("+", "-")):
            try:
                sign = 1 if clean[0] == "+" else -1
                parts = clean[1:].split(":")
                hours = int(parts[0])
                mins = int(parts[1]) if len(parts) > 1 else 0
                return datetime.timezone(sign * datetime.timedelta(hours=hours, minutes=mins))
            except Exception:
                pass
        return datetime.UTC

    def _estimate_end_time(
        self, start_utc: datetime.datetime, text: str
    ) -> datetime.datetime:
        """Determines end time from explicit duration or defaults to 45 min from explicit start."""
        dur_match = re.search(r"\b(\d+)\s*(?:min|minute|minutes)\b", text, re.IGNORECASE)
        if dur_match:
            mins = int(dur_match.group(1))
            return start_utc + datetime.timedelta(minutes=mins)
        hour_match = re.search(r"\b(1|1\.5|2)\s*(?:hour|hours|hr|hrs)\b", text, re.IGNORECASE)
        if hour_match:
            hrs = float(hour_match.group(1))
            return start_utc + datetime.timedelta(minutes=int(hrs * 60))
        return start_utc + datetime.timedelta(minutes=45)

    def extract_from_message(
        self,
        message: InboundMessageModel,
    ) -> ExtractedInterviewDetails | None:
        """Parses interview details from an inbound message."""
        body = message.body_text
        subject = message.subject
        combined = f"{subject}\n{body}"

        classification = message.classification
        allowed_classes = (
            "INTERVIEW_REQUEST",
            "INTERVIEW_CONFIRMATION",
            "INTERVIEW_RESCHEDULE",
            "INTERVIEW_CANCELLED",
            "SCREENING_REQUEST",
        )
        if classification not in allowed_classes:
            return None

        round_type = self.detect_round_type(combined)
        meeting_link = self.extract_meeting_link(combined)

        # Detect reschedule / cancellation
        is_reschedule = (classification == "INTERVIEW_RESCHEDULE") or bool(
            re.search(
                r"\b(reschedule|rescheduled|rescheduling|move our interview|new time for our)\b",
                combined,
                re.IGNORECASE,
            )
        )
        is_cancellation = (classification == "INTERVIEW_CANCELLED") or bool(
            re.search(
                r"\b(cancel the interview|interview is cancelled|cancelled our interview|canceled)\b",
                combined,
                re.IGNORECASE,
            )
        )

        start_time, end_time, tz_name = self.parse_explicit_datetime(combined)
        has_explicit_schedule = start_time is not None

        return ExtractedInterviewDetails(
            round_type=round_type,
            scheduled_start=start_time,
            scheduled_end=end_time,
            timezone=tz_name,
            meeting_link=meeting_link,
            notes=f"Extracted from email subject: {subject}",
            is_reschedule=is_reschedule,
            is_cancellation=is_cancellation,
            has_explicit_schedule=has_explicit_schedule,
        )

    def record_interview(
        self,
        application_id: uuid.UUID,
        details: ExtractedInterviewDetails,
        source_message_id: str | None = None,
    ) -> InterviewModel | None:
        """Persists or updates an InterviewModel for the application, enforcing idempotency."""
        # 1. Cancellation reconciliation
        if details.is_cancellation:
            active_interviews = self.session.scalars(
                select(InterviewModel).where(
                    InterviewModel.application_id == application_id,
                    InterviewModel.status == "scheduled",
                )
            ).all()

            if len(active_interviews) == 1:
                interview = active_interviews[0]
                interview.status = "cancelled"
                note_suffix = (
                    f"Cancelled via message {source_message_id}."
                    if source_message_id
                    else "Cancelled."
                )
                interview.notes = (
                    f"{interview.notes}\n{note_suffix}".strip()
                    if interview.notes
                    else note_suffix
                )
                self.session.flush()
                return interview
            elif len(active_interviews) > 1:
                task = TaskModel(
                    application_id=application_id,
                    task_type="NEEDS_REVIEW",
                    status="pending",
                    payload_json={
                        "reason": "Ambiguous interview cancellation: multiple active scheduled interviews exist",
                        "application_id": str(application_id),
                        "source_message_id": source_message_id,
                    },
                )
                self.session.add(task)
                self.session.flush()
                return None
            return None

        # 2. Reschedule reconciliation
        if details.is_reschedule:
            active_interviews = self.session.scalars(
                select(InterviewModel).where(
                    InterviewModel.application_id == application_id,
                    InterviewModel.status.in_(["scheduled", "rescheduling_needed"]),
                )
            ).all()

            if len(active_interviews) == 1:
                interview = active_interviews[0]
                if (
                    details.has_explicit_schedule
                    and details.scheduled_start is not None
                    and details.scheduled_end is not None
                ):
                    prev_start = interview.scheduled_start.isoformat()
                    interview.scheduled_start = details.scheduled_start
                    interview.scheduled_end = details.scheduled_end
                    interview.timezone = details.timezone
                    if details.meeting_link:
                        interview.location_or_link = details.meeting_link
                    interview.status = "scheduled"
                    note_update = f"Rescheduled from {prev_start} via message {source_message_id}."
                    interview.notes = (
                        f"{interview.notes}\n{note_update}".strip()
                        if interview.notes
                        else note_update
                    )
                    self.session.flush()
                    return interview
                else:
                    interview.status = "rescheduling_needed"
                    task = TaskModel(
                        application_id=application_id,
                        task_type="NEEDS_REVIEW",
                        status="pending",
                        payload_json={
                            "reason": "Interview reschedule requested but new schedule is not confirmed",
                            "application_id": str(application_id),
                            "interview_id": str(interview.id),
                            "source_message_id": source_message_id,
                        },
                    )
                    self.session.add(task)
                    return interview
            elif len(active_interviews) > 1:
                task = TaskModel(
                    application_id=application_id,
                    task_type="NEEDS_REVIEW",
                    status="pending",
                    payload_json={
                        "reason": "Ambiguous interview reschedule: multiple active scheduled interviews exist",
                        "application_id": str(application_id),
                        "source_message_id": source_message_id,
                    },
                )
                self.session.add(task)
                return None
            else:
                # No existing interview, but explicit schedule provided in reschedule message
                if (
                    details.has_explicit_schedule
                    and details.scheduled_start is not None
                    and details.scheduled_end is not None
                ):
                    interview = InterviewModel(
                        application_id=application_id,
                        round_type=details.round_type,
                        scheduled_start=details.scheduled_start,
                        scheduled_end=details.scheduled_end,
                        timezone=details.timezone,
                        location_or_link=details.meeting_link,
                        status="scheduled",
                        notes=f"Created from reschedule message {source_message_id}.",
                    )
                    self.session.add(interview)
                    self.session.flush()
                    return interview
                return None

        # 3. New interview request or confirmation
        if (
            details.has_explicit_schedule
            and details.scheduled_start is not None
            and details.scheduled_end is not None
        ):
            # Idempotency check: does an interview with same round_type and scheduled_start already exist?
            existing = self.session.scalar(
                select(InterviewModel).where(
                    InterviewModel.application_id == application_id,
                    InterviewModel.round_type == details.round_type,
                    InterviewModel.scheduled_start == details.scheduled_start,
                )
            )
            if existing:
                return existing

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

        # 4. Schedule is absent or ambiguous: do NOT synthesize date! Route to review.
        task = TaskModel(
            application_id=application_id,
            task_type="NEEDS_REVIEW",
            status="pending",
            payload_json={
                "reason": "Interview requested but no explicit schedule confirmed",
                "application_id": str(application_id),
                "round_type": details.round_type,
                "meeting_link": details.meeting_link,
                "source_message_id": source_message_id,
            },
        )
        self.session.add(task)
        return None

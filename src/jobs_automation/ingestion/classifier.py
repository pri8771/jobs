"""Email classification engine for recruiting and lifecycle communications."""

from __future__ import annotations

import logging
import re

from jobs_automation.ingestion.models import (
    EmailClassification,
    EmailClassificationResult,
    RawEmailMessage,
)

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Deterministic email classifier for job alerts and recruiting lifecycle messages.

    Follows docs/EMAIL_TRACKING.md:
    - Never replaces source messages with summaries.
    - If evidence is ambiguous, routes to UNKNOWN_REVIEW_REQUIRED with needs_review=True.
    - Detects direction (inbound / outbound).
    """

    def __init__(self, candidate_emails: list[str] | None = None) -> None:
        self.candidate_emails = [e.lower() for e in (candidate_emails or []) if e]
        if not self.candidate_emails:
            logger.warning(
                "EmailClassifier initialized with no candidate emails; outbound detection confidence will be reduced."
            )

    def classify(self, email: RawEmailMessage) -> EmailClassificationResult:
        sender_lower = email.sender.lower()
        subject_lower = email.subject.lower()
        body_lower = email.body_text.lower()

        # 1. Outbound / Candidate reply detection
        is_candidate_sender = bool(
            self.candidate_emails and any(cand in sender_lower for cand in self.candidate_emails)
        )
        if email.direction == "outbound" or is_candidate_sender:
            confidence = 0.95 if is_candidate_sender else 0.70
            return EmailClassificationResult(
                classification=EmailClassification.CANDIDATE_REPLY,
                confidence=confidence,
                direction="outbound",
                needs_review=False,
            )

        # 2. Job alert detection
        alert_domains = ["linkedin.com", "indeed.com", "ziprecruiter.com", "dice.com"]
        if any(dom in sender_lower for dom in alert_domains):
            if any(
                term in subject_lower
                for term in ["alert", "recommend", "new job", "match", "opportunity"]
            ):
                return EmailClassificationResult(
                    classification=EmailClassification.JOB_ALERT,
                    confidence=0.95,
                    direction="inbound",
                    needs_review=False,
                )

        # 3. Application confirmation
        confirmation_patterns = [
            "thank you for applying",
            "application received",
            "we received your application",
            "thanks for your application",
            "application submitted",
            "we have received your application",
            "confirming your application",
        ]
        if any(p in subject_lower or p in body_lower[:500] for p in confirmation_patterns):
            company = self._extract_company_hint(email)
            return EmailClassificationResult(
                classification=EmailClassification.APPLICATION_CONFIRMATION,
                confidence=0.90,
                direction="inbound",
                company_hint=company,
                needs_review=False,
            )

        # 4. Withdrawal confirmation (must clearly indicate application was withdrawn)
        withdrawal_patterns = [
            "withdrawn your application",
            "application has been withdrawn",
            "confirming your withdrawal",
            "withdrawal confirmation",
            "you have withdrawn",
            "withdrew your application",
            "requested to withdraw",
        ]
        if any(p in subject_lower or p in body_lower[:1000] for p in withdrawal_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.WITHDRAWAL,
                confidence=0.92,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 5. Background check
        background_check_patterns = [
            "background check",
            "background screening",
            "pre-employment screening",
            "background verification",
            "sterling background",
            "checkr",
            "hireright",
        ]
        if any(p in subject_lower or p in body_lower[:1000] for p in background_check_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.BACKGROUND_CHECK,
                confidence=0.90,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 6. Onboarding
        onboarding_patterns = [
            "onboarding",
            "new hire paperwork",
            "welcome to the team",
            "onboarding documents",
            "first day details",
            "i-9 verification",
        ]
        if any(p in subject_lower or p in body_lower[:1000] for p in onboarding_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.ONBOARDING,
                confidence=0.90,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 7. Rejection
        rejection_patterns = [
            "not moving forward",
            "other candidates",
            "pursuing other",
            "we have decided not to move forward",
            "unfortunately",
            "unsuccessful with your application",
            "position has been filled",
            "will not be moving forward",
            "decided to pursue other applicants",
        ]
        if any(p in body_lower for p in rejection_patterns) and any(
            t in subject_lower
            for t in ["application", "update", "status", "role", "position", "candidacy"]
        ):
            return EmailClassificationResult(
                classification=EmailClassification.REJECTION,
                confidence=0.88,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 5. Offer
        offer_patterns = [
            "offer of employment",
            "job offer",
            "offer letter",
            "formal offer",
            "we would like to extend an offer",
            "pleased to offer you",
        ]
        if any(p in subject_lower or p in body_lower[:1000] for p in offer_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.OFFER,
                confidence=0.92,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 6. Interview scheduling / invitation
        interview_reschedule_patterns = ["reschedule", "rescheduled", "change your interview"]
        if any(p in subject_lower or p in body_lower[:500] for p in interview_reschedule_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.INTERVIEW_RESCHEDULE,
                confidence=0.85,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        interview_cancelled_patterns = [
            "interview cancelled",
            "cancelled interview",
            "interview has been cancelled",
        ]
        if any(p in subject_lower or p in body_lower[:500] for p in interview_cancelled_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.INTERVIEW_CANCELLED,
                confidence=0.85,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        interview_confirmation_patterns = [
            "interview confirmation",
            "confirmed: interview",
            "your interview is confirmed",
            "interview with",
        ]
        if any(p in subject_lower for p in interview_confirmation_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.INTERVIEW_CONFIRMATION,
                confidence=0.88,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        interview_request_patterns = [
            "interview request",
            "schedule an interview",
            "invitation to interview",
            "interview invitation",
            "like to invite you for an interview",
            "schedule a time to chat",
            "availability for a call",
            "phone screen",
            "screening call",
            "introductory call",
        ]
        if any(p in subject_lower or p in body_lower[:800] for p in interview_request_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.INTERVIEW_REQUEST,
                confidence=0.85,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 7. Assessments
        assessment_patterns = [
            "coding assessment",
            "technical assessment",
            "take-home",
            "hackerrank",
            "coderpad",
            "codesignal",
        ]
        if any(p in subject_lower or p in body_lower[:800] for p in assessment_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.ASSESSMENT_REQUEST,
                confidence=0.85,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 10. Recruiter follow-up (explicit follow-up on previous communication)
        recruiter_followup_patterns = [
            "following up on my previous",
            "following up on our conversation",
            "following up regarding your application",
            "just following up",
            "checking in on my last email",
            "touching base on my previous note",
            "circling back on",
            "wanted to follow up",
        ]
        if any(p in subject_lower or p in body_lower[:1000] for p in recruiter_followup_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.RECRUITER_FOLLOW_UP,
                confidence=0.85,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 11. Recruiter initial outreach
        recruiter_patterns = [
            "came across your profile",
            "impressed by your background",
            "reaching out regarding",
            "opportunity at",
            "recruiter at",
            "talent acquisition",
        ]
        if any(p in body_lower[:1000] for p in recruiter_patterns):
            return EmailClassificationResult(
                classification=EmailClassification.RECRUITER_OUTREACH,
                confidence=0.80,
                direction="inbound",
                company_hint=self._extract_company_hint(email),
                needs_review=False,
            )

        # 9. Fallback / Ambiguous -> NEEDS_REVIEW
        return EmailClassificationResult(
            classification=EmailClassification.UNKNOWN_REVIEW_REQUIRED,
            confidence=0.30,
            direction="inbound",
            company_hint=self._extract_company_hint(email),
            needs_review=True,
            review_reason="Message could not be deterministically classified. Review required.",
        )

    def _extract_company_hint(self, email: RawEmailMessage) -> str | None:
        """Heuristically extract company name from subject or sender domain."""
        # Try from subject e.g. "Application to [Company]" or "Update from [Company]"
        match = re.search(
            r"(?:at|with|from)\s+([A-Z][a-zA-Z0-9\s&]+?)(?:\s+[-–|:]|\s+for|\s*$)", email.subject
        )
        if match:
            cand = match.group(1).strip()
            if len(cand) > 1 and len(cand) < 40:
                return cand

        # Try from sender domain e.g. recruiter@uber.com -> Uber
        if "@" in email.sender:
            domain = email.sender.split("@")[-1].strip(">").lower()
            parts = domain.split(".")
            if len(parts) >= 2 and parts[-2] not in {
                "gmail",
                "yahoo",
                "outlook",
                "hotmail",
                "linkedin",
                "indeed",
                "dice",
                "ziprecruiter",
            }:
                return parts[-2].capitalize()

        return None

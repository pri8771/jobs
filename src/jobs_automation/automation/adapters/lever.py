"""Lever ATS submission adapter."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from jobs_automation.automation.base import ATSAdapter, SubmissionResult, ValidationResult
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.db.models import ApplicationPacketModel


class LeverATSAdapter(ATSAdapter):
    """Structured adapter for Lever (jobs.lever.co)."""

    @property
    def platform_name(self) -> str:
        return "lever"

    def can_handle(self, destination_domain: str) -> bool:
        norm = destination_domain.lower()
        return "lever.co" in norm

    def validate_packet(
        self,
        packet: ApplicationPacketModel,
        candidate_profile: CandidateProfileConfig,
        form_schema: dict[str, Any] | None = None,
    ) -> ValidationResult:
        missing: list[str] = []
        if not candidate_profile.identity.full_name:
            missing.append("full_name")
        if not candidate_profile.identity.email:
            missing.append("email")
        if not packet.resume_artifact_id:
            missing.append("resume")

        # Unknown question stop condition
        unresolved = list(packet.unresolved_questions_json)
        if unresolved:
            return ValidationResult(
                is_valid=False,
                missing_fields=missing,
                unresolved_questions=unresolved,
                unknown_question_stop=True,
                message=f"Halted on unknown screening questions: {', '.join(unresolved)}",
            )

        if missing:
            return ValidationResult(
                is_valid=False,
                missing_fields=missing,
                message=f"Missing essential candidate facts: {', '.join(missing)}",
            )

        return ValidationResult(
            is_valid=True,
            missing_fields=[],
            unresolved_questions=[],
            unknown_question_stop=False,
            message="Lever packet validation passed",
        )

    def submit_application(
        self,
        packet: ApplicationPacketModel,
        target_url: str,
        candidate_profile: CandidateProfileConfig,
        mock_mode: bool = False,
    ) -> SubmissionResult:
        now = datetime.datetime.now(datetime.UTC)
        validation = self.validate_packet(packet, candidate_profile)
        if not validation.is_valid:
            if validation.unknown_question_stop:
                return SubmissionResult(
                    success=False,
                    status="STOPPED_UNKNOWN_QUESTION",
                    submitted_at=now,
                    message=validation.message,
                )
            return SubmissionResult(
                success=False,
                status="FATAL_ERROR",
                submitted_at=now,
                message=validation.message,
            )

        if not mock_mode:
            return SubmissionResult(
                success=False,
                status="NOT_IMPLEMENTED",
                submitted_at=now,
                message="Live Lever ATS automated submission is not yet implemented. External submissions require explicit provider integration.",
            )

        # In mock mode, simulate submission cleanly without pretending it is live
        receipt_uuid = uuid.uuid4().hex[:12].upper()
        receipt_id = f"SIM-LEVER-{receipt_uuid}"

        response_payload = {
            "platform": "lever",
            "receipt_id": receipt_id,
            "target_url": target_url,
            "simulated": True,
            "submitted_fields": {
                "name": candidate_profile.identity.full_name,
                "email": candidate_profile.identity.email,
                "phone": candidate_profile.identity.phone,
                "resume_artifact_id": str(packet.resume_artifact_id),
                "answers_count": len(packet.answers_json),
            },
            "status": "simulated",
        }

        return SubmissionResult(
            success=True,
            status="SIMULATED",
            receipt_id=receipt_id,
            confirmation_url=None,
            response_payload=response_payload,
            submitted_at=now,
            retry_count=0,
            message="Application simulated successfully in mock mode. External submission was NOT performed.",
        )

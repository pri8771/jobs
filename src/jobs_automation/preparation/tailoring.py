"""Candidate resume variant selection, cover letter drafting, and question answering."""

from __future__ import annotations

from typing import Any

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import CandidateProfileConfig
from jobs_automation.db.models import JobModel


class ResumeVariantSelector:
    """Selects the most targeted base resume variant according to role family and job title."""

    @staticmethod
    def select_variant(job: JobModel, matched_role_family: str | None = None) -> str:
        title_lower = (job.normalized_title or "").lower()
        fam_lower = (matched_role_family or "").lower()

        if "sap" in title_lower or "sap" in fam_lower:
            return "resume_sap_btp"
        elif any(k in title_lower for k in ["ios", "mobile", "swift", "apple"]):
            return "resume_mobile_ios"
        elif any(k in title_lower for k in ["product", "platform product", "technical product"]):
            return "resume_technical_product"
        elif any(k in title_lower for k in ["software", "ai automation", "applied ai", "python"]):
            return "resume_ai_software_engineer"
        else:
            # Default to primary high-value positioning
            return "resume_enterprise_automation"


class CoverLetterDrafter:
    """Generates a truthful, tailored cover letter citing verified candidate accomplishments."""

    def __init__(self, model_gateway: ModelGateway) -> None:
        self.gateway = model_gateway

    def draft(self, job: JobModel, profile: CandidateProfileConfig) -> str:
        company_name = job.company.normalized_name if job.company else "Hiring Team"
        title = job.normalized_title

        prompt = (
            f"Draft a tailored, concise cover letter for Priyansh Chordia applying for the role of '{title}' at '{company_name}'.\n"
            f"Ground all claims strictly in these verified candidate facts:\n"
            f"- Current: Contractor at Viatris in SAP BTP and Enterprise Automation.\n"
            f"- Prior: Head of IT / Business Operations at Thar Process (manufacturing, enterprise systems, custom software).\n"
            f"- Degree: B.S. in Chemical Engineering from Carnegie Mellon University.\n"
            f"- Key strengths: Enterprise integrations, Python, FastAPI, Docker, AI/OCR workflow automation.\n"
            f"Do not hallucinate any personal details, dates, or certifications."
        )

        res = self.gateway.complete(task="cover_letter", prompt=prompt)
        return str(res.get("cover_letter_text") or res.get("content") or "")


class ScreeningQuestionAnsweringService:
    """Prepares screening question answers, strictly routing unknown facts to unresolved review queue."""

    def __init__(self, model_gateway: ModelGateway) -> None:
        self.gateway = model_gateway

    def resolve_questions(
        self,
        questions: list[str],
        profile: CandidateProfileConfig,
    ) -> tuple[dict[str, Any], list[str]]:
        """Answers verified questions and flags unknown/unverified facts for human review.

        Returns: (resolved_answers_dict, unresolved_questions_list)
        """
        answers: dict[str, Any] = {}
        unresolved: list[str] = []

        for q in questions:
            q_clean = q.strip()
            q_lower = q_clean.lower()

            # 1. Check for demographic / EEO questions: NEVER guess
            if any(
                term in q_lower
                for term in [
                    "race",
                    "ethnicity",
                    "gender",
                    "veteran",
                    "disability",
                    "sexual orientation",
                ]
            ):
                unresolved.append(
                    f"Demographic question: '{q_clean}' requires explicit candidate choice."
                )
                continue

            # 2. Check for Work Authorization / Sponsorship
            if any(
                term in q_lower
                for term in ["authorized to work", "legally authorized", "sponsorship"]
            ):
                if profile.work_authorization.authorized_to_work_in_us is None:
                    unresolved.append(
                        f"Work authorization question: '{q_clean}' is unconfirmed in candidate profile."
                    )
                    continue
                else:
                    ans = "Yes" if profile.work_authorization.authorized_to_work_in_us else "No"
                    answers[q_clean] = ans
                    continue

            # 3. Check for Location / Relocation
            if "relocate" in q_lower or "willing to relocate" in q_lower:
                if profile.target.relocation is None:
                    unresolved.append(
                        f"Relocation question: '{q_clean}' has no confirmed relocation preference."
                    )
                    continue
                else:
                    answers[q_clean] = "Yes" if profile.target.relocation else "No"
                    continue

            # 4. Check for Salary / Compensation Expectations
            if any(term in q_lower for term in ["salary", "compensation", "hourly rate"]):
                if not profile.target.target_compensation_usd_min:
                    unresolved.append(f"Compensation question: '{q_clean}' requires confirmation.")
                    continue
                else:
                    answers[q_clean] = f"${profile.target.target_compensation_usd_min:,} USD"
                    continue

            # 5. Technical Experience / Skills resolution
            prompt = f"Question: {q_clean}"
            res = self.gateway.complete(task="question_answering", prompt=prompt)

            if res.get("resolved") and res.get("answer"):
                answers[q_clean] = res["answer"]
            else:
                unresolved.append(
                    f"Unverified question: '{q_clean}' (Reason: {res.get('reason', 'Missing profile fact')})"
                )

        return answers, unresolved

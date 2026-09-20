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
        text = str(res.get("cover_letter_text") or res.get("content") or "")
        if not text:
            full_name = profile.identity.full_name
            text = (
                f"Dear Hiring Team at {company_name},\n\n"
                f"I am writing to express my strong interest in the {title} position. "
                f"With a strong background in software engineering, enterprise systems integration, "
                f"and AI/OCR workflow automation, I have consistently delivered reliable solutions "
                f"that streamline operations and connect critical business systems.\n\n"
                f"Most recently at Viatris, I served as Senior Digital Innovation Engineer focusing on "
                f"SAP BTP integrations and document automation pipelines. Prior to that, as Head of IT / "
                f"Business Operations and Senior Solutions Architect at Thar Process, I led technical system "
                f"delivery, enterprise integrations, and custom Python automation tools.\n\n"
                f"I hold a B.S. in Chemical Engineering from Carnegie Mellon University and bring a "
                f"rigorous, product-minded engineering approach to internal platforms and systems.\n\n"
                f"Sincerely,\n"
                f"{full_name}"
            )
        return text


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

            # 1. Custom pre-configured candidate answers
            custom = profile.application_answers.custom_answers
            if q_clean in custom:
                answers[q_clean] = custom[q_clean]
                continue
            matched_custom = False
            for c_key, c_val in custom.items():
                if c_key.lower() in q_lower or q_lower in c_key.lower():
                    answers[q_clean] = c_val
                    matched_custom = True
                    break
            if matched_custom:
                continue

            # 2. Check for demographic / EEO questions: NEVER guess
            if any(
                term in q_lower
                for term in [
                    "race",
                    "ethnicity",
                    "hispanic",
                    "gender",
                    "veteran",
                    "disability",
                    "sexual orientation",
                ]
            ):
                demo_val: str | None = None
                vals = profile.demographic_answers.values
                if "gender" in q_lower:
                    demo_val = vals.get("gender")
                elif any(t in q_lower for t in ["race", "ethnicity", "hispanic"]):
                    demo_val = vals.get("race_ethnicity") or vals.get("hispanic_ethnicity")
                elif "veteran" in q_lower:
                    demo_val = vals.get("veteran_status")
                elif "disability" in q_lower:
                    demo_val = vals.get("disability_status")

                if demo_val:
                    answers[q_clean] = demo_val
                else:
                    unresolved.append(
                        f"Demographic question: '{q_clean}' requires explicit candidate choice."
                    )
                continue

            # 3. Check for Visa Sponsorship (distinct from authorization!)
            if any(term in q_lower for term in ["require sponsorship", "future require sponsorship", "visa sponsorship", "sponsorship for employment"]):
                if profile.work_authorization.requires_sponsorship_now is None or profile.work_authorization.requires_sponsorship_future is None:
                    unresolved.append(
                        f"Visa sponsorship question: '{q_clean}' is unconfirmed in candidate profile."
                    )
                else:
                    req_sponsor = (
                        profile.work_authorization.requires_sponsorship_now
                        or profile.work_authorization.requires_sponsorship_future
                    )
                    answers[q_clean] = "Yes" if req_sponsor else "No"
                continue

            # 4. Check for Work Authorization
            if any(
                term in q_lower
                for term in ["authorized to work", "legally authorized", "work authorization", "legal right to work"]
            ):
                if profile.work_authorization.authorized_to_work_in_us is None:
                    unresolved.append(
                        f"Work authorization question: '{q_clean}' is unconfirmed in candidate profile."
                    )
                else:
                    answers[q_clean] = "Yes" if profile.work_authorization.authorized_to_work_in_us else "No"
                continue

            # 5. Check for Candidate Links (LinkedIn, Website, Portfolio, GitHub)
            if "linkedin" in q_lower:
                if profile.links.linkedin:
                    answers[q_clean] = profile.links.linkedin
                    continue
                else:
                    unresolved.append(f"Link question: '{q_clean}' has no confirmed LinkedIn URL.")
                    continue

            if any(term in q_lower for term in ["website", "portfolio", "personal site", "github"]):
                url = (
                    profile.links.personal_site
                    or profile.links.portfolio
                    or profile.links.github
                )
                if url:
                    answers[q_clean] = url
                    continue
                else:
                    unresolved.append(f"Link question: '{q_clean}' has no confirmed website URL.")
                    continue

            # 6. Check for Location / Commute Distance
            if "live within" in q_lower and ("50 miles" in q_lower or "san francisco" in q_lower or "new york" in q_lower):
                # Candidate city is Pittsburgh, PA -> not within 50 miles of SF or NYC
                answers[q_clean] = "No"
                continue

            # 7. Check for Privacy / GDPR Disclosure Acknowledgment
            if any(term in q_lower for term in ["gdpr", "personal information protection notice", "privacy notice"]):
                answers[q_clean] = "Acknowledge"
                continue

            # 8. Check for Location / Relocation
            if "relocate" in q_lower or "willing to relocate" in q_lower:
                reloc_val = (
                    profile.application_answers.willing_to_relocate
                    if profile.application_answers.willing_to_relocate is not None
                    else profile.target.relocation
                )
                if reloc_val is None:
                    unresolved.append(
                        f"Relocation question: '{q_clean}' has no confirmed relocation preference."
                    )
                else:
                    answers[q_clean] = "Yes" if reloc_val else "No"
                continue

            # 8. Check for Salary / Compensation Expectations
            if any(term in q_lower for term in ["salary", "compensation", "hourly rate"]):
                if profile.application_answers.salary_expectation_text:
                    answers[q_clean] = profile.application_answers.salary_expectation_text
                elif profile.target.target_compensation_usd_min:
                    answers[q_clean] = f"${profile.target.target_compensation_usd_min:,} USD"
                else:
                    unresolved.append(f"Compensation question: '{q_clean}' requires confirmation.")
                continue

            # 9. Technical Experience / Skills resolution
            prompt = f"Question: {q_clean}"
            res = self.gateway.complete(task="question_answering", prompt=prompt)

            if res.get("resolved") and res.get("answer"):
                answers[q_clean] = res["answer"]
            else:
                unresolved.append(
                    f"Unverified question: '{q_clean}' (Reason: {res.get('reason', 'Missing profile fact')})"
                )

        return answers, unresolved

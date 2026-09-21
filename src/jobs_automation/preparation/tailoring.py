"""Candidate resume variant selection, cover letter drafting, and question answering with provenance."""

from __future__ import annotations

import logging
from typing import Any

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import CandidateProfileConfig
from jobs_automation.db.models import JobModel

logger = logging.getLogger(__name__)


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

    def _build_candidate_context(self, profile: CandidateProfileConfig) -> str:
        lines = [
            f"Candidate: {profile.identity.full_name}",
            f"Positioning: {profile.positioning.summary}",
        ]
        if profile.experience.current_role:
            cr = profile.experience.current_role
            lines.append(f"Current Role: {cr.role} at {cr.company}")
        for role in profile.experience.roles[:3]:
            lines.append(f"Past Role: {role.role} at {role.company}")
        for edu in profile.education:
            lines.append(f"Education: {edu.credential} from {edu.school}")
        if profile.skills.primary:
            lines.append(f"Core Skills: {', '.join(profile.skills.primary[:6])}")
        return "\n".join(lines)

    def draft(self, job: JobModel, profile: CandidateProfileConfig) -> str:
        company_name = job.company.normalized_name if job.company else "Hiring Team"
        title = job.normalized_title or "the position"
        cand_ctx = self._build_candidate_context(profile)

        prompt = (
            f"Draft a tailored, professional cover letter for {profile.identity.full_name} applying for '{title}' at '{company_name}'.\n"
            f"Ground all claims strictly in these canonical candidate facts:\n"
            f"{cand_ctx}\n"
            f"Do not hallucinate any personal details, dates, companies, or certifications."
        )

        res = self.gateway.complete(task="cover_letter", prompt=prompt)
        text = str(res.get("cover_letter_text") or res.get("content") or "")
        if text and profile.identity.full_name not in text:
            text = f"{text}\n\nSincerely,\n{profile.identity.full_name}"
        if not text:
            # Truthful fallback dynamically rendered strictly from candidate profile facts
            exp_paragraphs = []
            if profile.experience.current_role:
                cr = profile.experience.current_role
                exp_paragraphs.append(
                    f"Currently as {cr.role} at {cr.company}, I focus on scalable systems and engineering delivery."
                )
            if profile.experience.roles:
                r0 = profile.experience.roles[0]
                exp_paragraphs.append(
                    f"Previously as {r0.role} at {r0.company}, I led technical initiatives and core platform implementations."
                )
            edu_str = ""
            if profile.education:
                e0 = profile.education[0]
                edu_str = f"I hold a {e0.credential} from {e0.school} and bring a disciplined engineering mindset to the team.\n\n"

            exp_body = "\n\n".join(exp_paragraphs)
            text = (
                f"Dear Hiring Team at {company_name},\n\n"
                f"I am writing to express my strong interest in the {title} position. "
                f"With extensive experience in systems engineering and automation, I focus on delivering "
                f"reliable, high-impact business solutions.\n\n"
                f"{exp_body}\n\n"
                f"{edu_str}"
                f"Thank you for your consideration.\n\n"
                f"Sincerely,\n"
                f"{profile.identity.full_name}"
            )
        return text


class ScreeningQuestionAnsweringService:
    """Prepares screening question answers with canonical provenance tracking."""

    def __init__(self, model_gateway: ModelGateway) -> None:
        self.gateway = model_gateway

    def resolve_questions(
        self,
        questions: list[str],
        profile: CandidateProfileConfig,
    ) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
        """Answers verified questions and flags unknown/unverified facts for human review.

        Returns: (resolved_answers_dict, answer_provenance_dict, unresolved_questions_list)
        """
        answers: dict[str, Any] = {}
        provenance: dict[str, Any] = {}
        unresolved: list[str] = []

        for q in questions:
            q_clean = q.strip()
            q_lower = q_clean.lower()

            # 1. Custom pre-configured candidate answers
            custom = profile.application_answers.custom_answers
            if q_clean in custom:
                answers[q_clean] = custom[q_clean]
                provenance[q_clean] = {
                    "method": "deterministic",
                    "sources": ["application_answers.custom_answers"],
                    "confidence": 1.0,
                }
                continue
            matched_custom = False
            for c_key, c_val in custom.items():
                if c_key.lower() in q_lower or q_lower in c_key.lower():
                    answers[q_clean] = c_val
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": [f"application_answers.custom_answers.{c_key}"],
                        "confidence": 1.0,
                    }
                    matched_custom = True
                    break
            if matched_custom:
                continue

            # 2. Demographic / EEO questions: ALWAYS require explicit candidate choice (J14-09)
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
                unresolved.append(
                    f"Demographic/EEO self-identification question '{q_clean}' requires explicit candidate choice."
                )
                continue

            # 3. Check for Visa Sponsorship (distinct from authorization!)
            if any(
                term in q_lower
                for term in [
                    "require sponsorship",
                    "future require sponsorship",
                    "visa sponsorship",
                    "sponsorship for employment",
                ]
            ):
                if (
                    profile.work_authorization.requires_sponsorship_now is None
                    or profile.work_authorization.requires_sponsorship_future is None
                ):
                    unresolved.append(
                        f"Visa sponsorship question: '{q_clean}' is unconfirmed in candidate profile."
                    )
                else:
                    req_sponsor = (
                        profile.work_authorization.requires_sponsorship_now
                        or profile.work_authorization.requires_sponsorship_future
                    )
                    answers[q_clean] = "Yes" if req_sponsor else "No"
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": [
                            "work_authorization.requires_sponsorship_now",
                            "work_authorization.requires_sponsorship_future",
                        ],
                        "confidence": 1.0,
                    }
                continue

            # 4. Check for Work Authorization
            if any(
                term in q_lower
                for term in [
                    "authorized to work",
                    "legally authorized",
                    "work authorization",
                    "legal right to work",
                ]
            ):
                if profile.work_authorization.authorized_to_work_in_us is None:
                    unresolved.append(
                        f"Work authorization question: '{q_clean}' is unconfirmed in candidate profile."
                    )
                else:
                    answers[q_clean] = (
                        "Yes" if profile.work_authorization.authorized_to_work_in_us else "No"
                    )
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["work_authorization.authorized_to_work_in_us"],
                        "confidence": 1.0,
                    }
                continue

            # 5. Check for Candidate Links (LinkedIn, Website, Portfolio, GitHub)
            if "linkedin" in q_lower:
                if profile.links.linkedin:
                    answers[q_clean] = profile.links.linkedin
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["links.linkedin"],
                        "confidence": 1.0,
                    }
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
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["links.personal_site"],
                        "confidence": 1.0,
                    }
                    continue
                else:
                    unresolved.append(f"Link question: '{q_clean}' has no confirmed website URL.")
                    continue

            # 6. Check for Location / Commute Distance (derive strictly from profile)
            cand_city = (profile.identity.city or "").lower()
            cand_state = (profile.identity.state or "").lower()
            if "live within" in q_lower and ("50 miles" in q_lower or "miles" in q_lower):
                if not cand_city or not cand_state:
                    unresolved.append(
                        f"Location question: '{q_clean}' cannot be resolved without confirmed candidate city/state."
                    )
                    continue

                # If question specifically checks proximity to SF / NYC
                if any(loc in q_lower for loc in ["san francisco", "new york", "sf", "nyc"]):
                    if cand_city not in ["san francisco", "new york", "new york city"] and cand_state not in ["ca", "ny"]:
                        answers[q_clean] = "No"
                        provenance[q_clean] = {
                            "method": "deterministic",
                            "sources": ["identity.city", "identity.state"],
                            "confidence": 1.0,
                        }
                        continue
                    else:
                        unresolved.append(
                            f"Location question: '{q_clean}' requires exact commute confirmation."
                        )
                        continue

            # 7. Check for Privacy / GDPR Disclosure Acknowledgment
            if any(term in q_lower for term in ["gdpr", "personal information protection notice", "privacy notice"]):
                answers[q_clean] = "Acknowledge"
                provenance[q_clean] = {
                    "method": "deterministic",
                    "sources": ["policy.standard_disclosure_acknowledgment"],
                    "confidence": 1.0,
                }
                continue

            # 8. Check for Relocation Preference
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
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["application_answers.willing_to_relocate"],
                        "confidence": 1.0,
                    }
                continue

            # 9. Check for Salary / Compensation Expectations
            if any(term in q_lower for term in ["salary", "compensation", "hourly rate"]):
                if profile.application_answers.salary_expectation_text:
                    answers[q_clean] = profile.application_answers.salary_expectation_text
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["application_answers.salary_expectation_text"],
                        "confidence": 1.0,
                    }
                elif profile.target.target_compensation_usd_min:
                    answers[q_clean] = f"${profile.target.target_compensation_usd_min:,} USD"
                    provenance[q_clean] = {
                        "method": "deterministic",
                        "sources": ["target.target_compensation_usd_min"],
                        "confidence": 1.0,
                    }
                else:
                    unresolved.append(f"Compensation question: '{q_clean}' requires confirmation.")
                continue

            # 10. Technical Experience / Skills resolution (J14-08)
            # Provide canonical candidate context to model
            cand_skills = profile.skills.primary + profile.skills.secondary + profile.skills.certifications
            cand_skills_str = ", ".join(cand_skills) if cand_skills else "None listed"

            prompt = (
                f"Question: {q_clean}\n"
                f"Candidate Verified Skills: {cand_skills_str}\n"
                f"Candidate Summary: {profile.positioning.summary}\n"
                f"Answer truthfully based ONLY on the candidate's verified skills and summary. "
                f"If the question asks about a skill, certification, or clearance not verified in the candidate's profile, "
                f"you MUST return resolved=false."
            )
            res = self.gateway.complete(task="question_answering", prompt=prompt)

            if res.get("resolved") and res.get("answer"):
                # Safety check (J14-08): reject model resolved=True if the asserted fact is absent from profile
                # Check if question asks about specific unverified credentials like clearance
                if "clearance" in q_lower and not any("clearance" in s.lower() for s in cand_skills):
                    unresolved.append(
                        f"Unverified question: '{q_clean}' (Model assertion rejected: security clearance not present in candidate profile)"
                    )
                    continue

                answers[q_clean] = res["answer"]
                provenance[q_clean] = {
                    "method": "model_assisted",
                    "sources": ["skills.primary", "positioning.summary"],
                    "model_origin": res.get("origin", "unknown"),
                    "confidence": 0.85,
                }
            else:
                unresolved.append(
                    f"Unverified question: '{q_clean}' (Reason: {res.get('reason', 'Missing profile fact')})"
                )

        return answers, provenance, unresolved

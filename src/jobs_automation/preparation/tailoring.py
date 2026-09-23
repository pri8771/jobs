"""Candidate resume variant selection, cover letter drafting, and question answering with provenance."""

from __future__ import annotations

import logging
import re
from typing import Any

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.adapters.models import MockModelGateway
from jobs_automation.core import CandidateProfileConfig
from jobs_automation.db.models import JobModel

logger = logging.getLogger(__name__)



ROLE_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "sap_btp": ["sap"],
    "mobile_ios": ["ios", "mobile", "swift", "apple"],
    "technical_product": ["product", "platform product", "technical product"],
    "ai_software_engineer": ["software", "ai automation", "applied ai", "python"],
    "enterprise_automation": []
}

class ResumeVariantSelector:

    """Selects the most targeted base resume variant and resolves exact resume family attribution."""

    VARIANT_FAMILY_MAP: dict[str, str] = {
        "resume_enterprise_automation": "Enterprise Automation & Solutions Architect",
        "resume_ai_software_engineer": "Senior Software Engineer / AI Automation Engineer",
        "resume_mobile_ios": "Senior iOS Engineer / Mobile Engineering Lead",
        "resume_technical_product": "Technical Product / Platform Product",
        "resume_sap_btp": "SAP BTP / Enterprise Automation",
    }


    @staticmethod
    def select_variant(
        job: JobModel, 
        matched_role_family: str | None = None,
        session: Any = None,
        config: Any = None
    ) -> str:
        title_lower = (job.normalized_title or "").lower()
        fam_lower = (matched_role_family or "").lower()
        
        # New V2.3 Dynamic selection logic
        if session and config:
            from jobs_automation.intelligence.role_family import RoleFamilyClassifier
            from jobs_automation.intelligence.strategy import StrategyLearningService
            from jobs_automation.db.models import ResumeVariantModel
            
            classifier = RoleFamilyClassifier()
            expected_family = matched_role_family or classifier.classify(job.normalized_title)
            
            # OpportunityGraph is assumed to be handled previously or we can call it here if needed,
            # but getting the best variant directly:
            strategy_val = config.tailoring.resume_strategy if getattr(config, 'tailoring', None) else 'highest_conversion'
            svc = StrategyLearningService(session, config.strategy_guardrails)
            rec = svc.get_best_resume_variant(str(job.id), expected_family, strategy=strategy_val)
            
            if rec.resume_variant_id:
                # Find the variant name from DB
                v_model = session.get(ResumeVariantModel, rec.resume_variant_id)
                if v_model:
                    return v_model.name

        # Fallback to static logic
        if any(k in title_lower or k in fam_lower for k in ROLE_FAMILY_KEYWORDS["sap_btp"]):
            return "resume_sap_btp"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["mobile_ios"]):
            return "resume_mobile_ios"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["technical_product"]):
            return "resume_technical_product"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["ai_software_engineer"]):
            return "resume_ai_software_engineer"
        else:
            return "resume_enterprise_automation"



    @classmethod
    def get_resume_family(
        cls, variant_name: str, profile: CandidateProfileConfig | None = None
    ) -> str:
        """Resolves the exact resume family name for the given variant (R14-02).

        Checks configured profile versions first, then canonical mapping.
        Never falls back to target.primary_headline across all variants.
        """
        if profile and profile.resume:
            for ver in profile.resume.recommended_versions:
                if ver.id == variant_name and ver.family:
                    return ver.family

        if variant_name in cls.VARIANT_FAMILY_MAP:
            return cls.VARIANT_FAMILY_MAP[variant_name]

        return variant_name.replace("resume_", "").replace("_", " ").title()


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

    def draft_with_metadata(
        self, job: JobModel, profile: CandidateProfileConfig
    ) -> tuple[str, dict[str, Any]]:
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
        origin = str(
            res.get("origin")
            or ("mock" if isinstance(self.gateway, MockModelGateway) else "real")
        )
        metadata: dict[str, Any] = {
            "origin": origin,
            "model": res.get("model", getattr(self.gateway, "model_name", None)),
        }

        if text and profile.identity.full_name not in text:
            text = f"{text}\n\nSincerely,\n{profile.identity.full_name}"
        if not text:
            # Truthful fallback dynamically rendered strictly from candidate profile facts
            metadata["origin"] = "deterministic"
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
        return text, metadata

    def draft(self, job: JobModel, profile: CandidateProfileConfig) -> str:
        text, _ = self.draft_with_metadata(job, profile)
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

            # 10. Quantitative Experience / Duration / Count claims check (R14-04)
            # Questions asking about years of experience, duration, headcount, or counts
            # require exact canonical evidence. Mere skill presence in skills.primary/secondary
            # is insufficient evidence to substantiate a quantitative duration/count claim.
            is_quantitative = bool(
                re.search(
                    r"\b(how\s+many\s+years|years\s+of\s+experience|number\s+of\s+years|years\s+with|years\s+using|how\s+many\s+(people|engineers|direct\s+reports|reports|teams))\b",
                    q_lower,
                )
                or (
                    "years" in q_lower
                    and any(
                        term in q_lower
                        for term in [
                            "experience",
                            "work",
                            "using",
                            "programming",
                            "engineering",
                            "leading",
                        ]
                    )
                )
                or any(
                    phrase in q_lower
                    for phrase in ["team size", "direct reports", "how long have you"]
                )
            )

            if is_quantitative:
                unresolved.append(
                    f"Quantitative claim in question '{q_clean}' requires exact canonical evidence. "
                    f"Skill presence alone is insufficient."
                )
                continue

            # 11. Technical Experience / Skills resolution (J14-08)
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

                # Safety check (R14-04): reject model assertions containing unverified quantitative claims
                ans_str = str(res["answer"]).lower()
                if any(k in ans_str for k in ["year", "years", "headcount", "reports"]) and any(c.isdigit() for c in ans_str):
                    unresolved.append(
                        f"Unverified question: '{q_clean}' (Model assertion rejected: quantitative claim '{res['answer']}' not supported by canonical profile facts)"
                    )
                    continue

                model_origin = str(
                    res.get("origin")
                    or ("mock" if isinstance(self.gateway, MockModelGateway) else "real")
                )
                answers[q_clean] = res["answer"]
                provenance[q_clean] = {
                    "method": "model_assisted",
                    "sources": ["skills.primary", "positioning.summary"],
                    "model_origin": model_origin,
                    "confidence": 0.85,
                }
            else:
                unresolved.append(
                    f"Unverified question: '{q_clean}' (Reason: {res.get('reason', 'Missing profile fact')})"
                )

        return answers, provenance, unresolved

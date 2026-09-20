"""Deterministic hard filters for job postings."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from jobs_automation.core import CandidateProfileConfig, JobSearchConfig
from jobs_automation.db.models import JobModel


class FilterDecisionStatus(StrEnum):
    PASS = "PASS"
    REJECT = "REJECT"
    MUST_REVIEW = "MUST_REVIEW"


class FilterResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FilterDecisionStatus
    passed: bool
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str = ""


class HardFilterService:
    """Evaluates deterministic pass/reject rules before semantic scoring."""

    def __init__(
        self,
        candidate_profile: CandidateProfileConfig,
        job_search_config: JobSearchConfig,
    ) -> None:
        self.profile = candidate_profile
        self.search_config = job_search_config

    def evaluate(self, job: JobModel) -> FilterResult:
        reasons: list[str] = []
        must_review_reasons: list[str] = []

        title_lower = (job.normalized_title or "").lower()
        desc_lower = (job.description_text or "").lower()

        # 1. Hard Reject Title Keywords
        for kw in self.search_config.hard_reject.title_keywords:
            if kw.lower() in title_lower:
                reasons.append(f"rejected_title_keyword:{kw}")

        # 2. Excluded Company Names
        comp_name = job.company.normalized_name.lower() if job.company else ""
        for exc_co in self.search_config.hard_reject.company_names:
            if exc_co.lower() in comp_name:
                reasons.append(f"rejected_company:{exc_co}")

        # 3. Minimum Compensation Check
        target_min = (
            self.search_config.global_config.target_compensation_usd_min
            or self.profile.target.target_compensation_usd_min
        )
        if target_min and job.compensation_max:
            if job.compensation_max < target_min:
                reasons.append(
                    f"insufficient_compensation:max_{job.compensation_max}_below_min_{target_min}"
                )

        # 4. Location & Remote Compatibility
        allowed_locations = [loc.lower() for loc in self.search_config.locations.include]
        job_loc = (job.location_text or "").lower()
        job_remote = (job.remote_type or "").lower()

        is_remote = "remote" in job_loc or job_remote == "remote"
        is_pgh = "pittsburgh" in job_loc or "pa" in job_loc
        is_hybrid_pgh = job_remote == "hybrid" and ("pittsburgh" in job_loc or not job_loc)

        matched_allowed_location = False
        if allowed_locations:
            for loc in allowed_locations:
                parts = [p.strip() for p in loc.split(",") if len(p.strip()) > 2]
                if loc in job_loc or (parts and any(p in job_loc for p in parts)):
                    matched_allowed_location = True
                    break

        location_match = (
            is_remote
            or is_pgh
            or is_hybrid_pgh
            or matched_allowed_location
            or (self.profile.target.relocation is True)
        )

        for exc_loc in self.search_config.locations.exclude:
            if exc_loc.lower() in job_loc:
                reasons.append(f"excluded_location:{exc_loc}")
                break
        else:
            if not location_match and job_loc and not is_remote:
                if job_remote in {"on_site", "hybrid"}:
                    reasons.append(f"incompatible_location:{job.location_text}")

        # 5. Clearance Requirement
        clearance_terms = ["security clearance", "ts/sci", "top secret", "polygraph", "dod secret"]
        for term in clearance_terms:
            if term in desc_lower:
                reasons.append(f"requires_security_clearance:{term}")
                break

        # 6. Work Authorization / Sponsorship
        # If posting explicitly requires US Citizen only / No sponsorship, and profile status is unverified:
        sponsorship_unsupported_terms = [
            "u.s. citizenship required",
            "us citizens only",
            "no sponsorship",
            "unable to sponsor",
            "without sponsorship",
        ]
        requires_citizen = any(term in desc_lower for term in sponsorship_unsupported_terms)
        if requires_citizen:
            if self.profile.work_authorization.authorized_to_work_in_us is None:
                must_review_reasons.append("unverified_work_authorization_vs_citizenship_req")
            elif self.profile.work_authorization.requires_sponsorship_now:
                reasons.append("sponsorship_unavailable")

        # 7. Final Decision synthesis
        if reasons:
            return FilterResult(
                status=FilterDecisionStatus.REJECT,
                passed=False,
                reason_codes=reasons,
                explanation=f"Disqualified by hard filters: {', '.join(reasons)}",
            )

        if must_review_reasons:
            return FilterResult(
                status=FilterDecisionStatus.MUST_REVIEW,
                passed=False,
                reason_codes=must_review_reasons,
                explanation=f"Requires human review: {', '.join(must_review_reasons)}",
            )

        return FilterResult(
            status=FilterDecisionStatus.PASS,
            passed=True,
            reason_codes=["passed_hard_filters"],
            explanation="Job passed all deterministic hard filters.",
        )

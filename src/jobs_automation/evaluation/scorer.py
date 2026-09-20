"""Multi-dimensional semantic fit scoring for job postings."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from jobs_automation.core import CandidateProfileConfig, JobSearchConfig
from jobs_automation.db.models import JobModel


class DimensionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    weight: float
    raw_score: float  # 0.0 to 1.0
    weighted_score: float  # raw_score * weight
    details: str = ""


class EvaluationScoreResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    composite_score: float  # 0.0 to 100.0
    decision: str  # "SHORTLIST" | "CONSIDER" | "REJECT"
    matched_role_family: str | None = None
    role_family_id: str | None = None
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str = ""


class SemanticScorer:
    """Calculates multidimensional fit score according to configured weights and role families."""

    def __init__(
        self,
        candidate_profile: CandidateProfileConfig,
        job_search_config: JobSearchConfig,
    ) -> None:
        self.profile = candidate_profile
        self.search_config = job_search_config
        self.scoring = job_search_config.scoring
        self.weights = job_search_config.scoring.weights

    def score(self, job: JobModel) -> EvaluationScoreResult:
        title_lower = (job.normalized_title or "").lower()
        desc_lower = (job.description_text or "").lower()
        full_text = f"{title_lower} {desc_lower}"

        dimensions: list[DimensionScore] = []
        reason_codes: list[str] = []

        # 1. Role Family & Title Match (Weight from config, default 25)
        best_family_id: str | None = None
        best_family_name: str | None = None
        best_title_score = 0.0

        for family in self.search_config.role_families:
            if not family.enabled:
                continue

            for expected_title in family.include_titles:
                exp_clean = expected_title.lower()
                if exp_clean in title_lower:
                    best_title_score = max(best_title_score, 1.0)
                    best_family_id = family.id
                    best_family_name = expected_title
                elif any(word in title_lower for word in exp_clean.split()):
                    # Partial title overlap
                    overlap_ratio = sum(
                        1 for word in exp_clean.split() if word in title_lower
                    ) / max(len(exp_clean.split()), 1)
                    if overlap_ratio > best_title_score:
                        best_title_score = max(best_title_score, overlap_ratio * 0.8)
                        best_family_id = family.id
                        best_family_name = expected_title

        w_title = float(self.weights.title_match)
        dimensions.append(
            DimensionScore(
                name="title_match",
                weight=w_title,
                raw_score=best_title_score,
                weighted_score=best_title_score * w_title,
                details=f"Matched role family: {best_family_name or 'None'}",
            )
        )
        if best_title_score >= 0.7:
            reason_codes.append(f"strong_title_match:{best_family_id}")
        elif best_title_score > 0.0:
            reason_codes.append(f"partial_title_match:{best_family_id}")
        else:
            reason_codes.append("weak_title_match")

        # 2. Skills Match (Weight from config, default 25)
        primary_skills = self.profile.skills.primary
        secondary_skills = self.profile.skills.secondary

        matched_primary: list[str] = []
        for sk in primary_skills:
            pattern = rf"\b{re.escape(sk.lower())}\b"
            if re.search(pattern, full_text):
                matched_primary.append(sk)

        matched_secondary: list[str] = []
        for sk in secondary_skills:
            pattern = rf"\b{re.escape(sk.lower())}\b"
            if re.search(pattern, full_text):
                matched_secondary.append(sk)

        prim_ratio = len(matched_primary) / max(len(primary_skills), 1)
        sec_ratio = len(matched_secondary) / max(len(secondary_skills), 1)
        skills_raw_score = min(
            1.0, (prim_ratio * 0.8) + (sec_ratio * 0.4) + (0.2 if matched_primary else 0.0)
        )

        w_skills = float(self.weights.must_have_skills + self.weights.preferred_skills)
        dimensions.append(
            DimensionScore(
                name="skills_match",
                weight=w_skills,
                raw_score=skills_raw_score,
                weighted_score=skills_raw_score * w_skills,
                details=f"Matched {len(matched_primary)} primary, {len(matched_secondary)} secondary skills",
            )
        )
        if matched_primary:
            reason_codes.append(f"skills_matched:{len(matched_primary)}_primary")

        # 3. Seniority Match (Weight from config, default 5)
        senior_keywords = ["staff", "architect", "lead", "principal", "senior", "head", "manager"]
        junior_keywords = ["junior", "associate", "intern", "entry level", "graduate"]

        seniority_score = 0.5  # Neutral default
        if any(w in title_lower for w in senior_keywords):
            seniority_score = 1.0
            reason_codes.append("seniority_fit:senior_staff_architect")
        elif any(w in title_lower for w in junior_keywords):
            seniority_score = 0.1
            reason_codes.append("seniority_mismatch:junior_entry")

        w_sen = float(self.weights.seniority)
        dimensions.append(
            DimensionScore(
                name="seniority_match",
                weight=w_sen,
                raw_score=seniority_score,
                weighted_score=seniority_score * w_sen,
                details=f"Seniority alignment: {seniority_score:.1f}",
            )
        )

        # 4. Compensation Match (Weight from config, default 15)
        target_min = self.profile.target.target_compensation_usd_min or 150000
        comp_score = 0.7  # Default if unstated
        if job.compensation_min and job.compensation_min >= target_min:
            comp_score = 1.0
            reason_codes.append(f"compensation_exceeds_target:${job.compensation_min}")
        elif job.compensation_max and job.compensation_max >= target_min:
            comp_score = 0.85
            reason_codes.append(f"compensation_max_meets_target:${job.compensation_max}")
        elif job.compensation_max and job.compensation_max < target_min:
            comp_score = 0.3
            reason_codes.append("compensation_below_target")

        w_comp = float(self.weights.compensation)
        dimensions.append(
            DimensionScore(
                name="compensation_match",
                weight=w_comp,
                raw_score=comp_score,
                weighted_score=comp_score * w_comp,
                details=f"Compensation score: {comp_score:.2f}",
            )
        )

        # 5. Location / Remote Match (Weight from config, default 10)
        loc_score = 0.5
        job_loc = (job.location_text or "").lower()
        job_rem = (job.remote_type or "").lower()

        if "remote" in job_loc or job_rem == "remote":
            loc_score = 1.0
            reason_codes.append("location_fit:remote_us")
        elif "pittsburgh" in job_loc or "pa" in job_loc:
            loc_score = 1.0
            reason_codes.append("location_fit:pittsburgh_local")
        elif job_rem == "hybrid" and not job_loc:
            loc_score = 0.8
        else:
            loc_score = 0.4

        w_loc = float(self.weights.location)
        dimensions.append(
            DimensionScore(
                name="location_match",
                weight=w_loc,
                raw_score=loc_score,
                weighted_score=loc_score * w_loc,
                details=f"Location alignment: {loc_score:.1f}",
            )
        )

        # 6. Freshness Match (Weight from config, default 5)
        fresh_score = 1.0  # Fresh by default during ingestion
        w_fresh = float(self.weights.freshness)
        dimensions.append(
            DimensionScore(
                name="freshness",
                weight=w_fresh,
                raw_score=fresh_score,
                weighted_score=fresh_score * w_fresh,
                details="Fresh posting",
            )
        )

        # Calculate composite score
        total_weighted = sum(d.weighted_score for d in dimensions)
        total_weight = sum(d.weight for d in dimensions)
        composite = (total_weighted / total_weight) * 100.0 if total_weight > 0 else 0.0
        composite = round(composite, 2)

        # Threshold Decision
        shortlist_threshold = float(self.scoring.threshold_shortlist)
        consider_threshold = float(self.scoring.threshold_review)

        if composite >= shortlist_threshold:
            decision = "SHORTLIST"
        elif composite >= consider_threshold:
            decision = "CONSIDER"
        else:
            decision = "REJECT"

        explanation = (
            f"Overall score {composite:.1f}/100 ({decision}). "
            f"Role match: {best_family_name or 'General'} (score: {best_title_score:.2f}). "
            f"Skills matched: {len(matched_primary)} primary ({', '.join(matched_primary[:3]) if matched_primary else 'none'})."
        )

        return EvaluationScoreResult(
            composite_score=composite,
            decision=decision,
            matched_role_family=best_family_name,
            role_family_id=best_family_id,
            dimension_scores=dimensions,
            reason_codes=reason_codes,
            explanation=explanation,
        )

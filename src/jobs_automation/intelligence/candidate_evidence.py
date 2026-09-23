import hashlib
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from jobs_automation.core.candidate_profile import CandidateProfileConfig

class CandidateEvidenceRef(BaseModel):
    field_path: str
    present: bool
    provenance_class: Literal["user_confirmed", "source_document", "inferred", "unknown"]
    source_reference: str | None = None
    verified_at: datetime | None = None
    reviewer: str | None = None
    allowed_for_application: bool
    value_fingerprint: str | None = None

class SkillEvidence(BaseModel):
    skill: str
    evidence_refs: list[CandidateEvidenceRef]
    projects: list[str]
    employers: list[str]

class ProjectEvidence(BaseModel):
    name: str
    skills: list[str]
    evidence_ref: CandidateEvidenceRef

class CandidateEvidenceService:
    def __init__(self, profile: CandidateProfileConfig):
        self.profile = profile

    def _fingerprint(self, val: str) -> str:
        return hashlib.sha256(val.encode('utf-8')).hexdigest()

    def _get_evidence_ref(self, field_path: str, raw_value: str | None, is_demographic: bool = False) -> CandidateEvidenceRef:
        present = bool(raw_value)
        allowed = not is_demographic and present
        
        prov_item = self.profile.provenance.get(field_path)
        if prov_item:
            p_class = prov_item.provenance_class
            s_ref = prov_item.source_reference
            v_at = prov_item.verified_at
            reviewer = prov_item.reviewer
        else:
            p_class = "user_confirmed" if present else "unknown"
            s_ref = None
            v_at = None
            reviewer = None

        fp = self._fingerprint(raw_value) if present and raw_value else None

        return CandidateEvidenceRef(
            field_path=field_path,
            present=present,
            provenance_class=p_class,
            source_reference=s_ref,
            verified_at=v_at,
            reviewer=reviewer,
            allowed_for_application=allowed,
            value_fingerprint=fp
        )

    def skills(self) -> list[SkillEvidence]:
        res = []
        all_skills = set(self.profile.skills.primary + self.profile.skills.secondary + self.profile.skills.certifications)
        
        for skill in sorted(all_skills):
            projects_with_skill = [p.name for p in self.profile.experience.projects if skill in p.skills]
            employers_with_skill = [] # Our current profile model doesn't link skills to employers directly
            
            field_path = f"skills.any[{skill}]"
            ref = self._get_evidence_ref(field_path, skill)
            res.append(SkillEvidence(
                skill=skill,
                evidence_refs=[ref],
                projects=projects_with_skill,
                employers=employers_with_skill
            ))
        return res

    def projects(self) -> list[ProjectEvidence]:
        res = []
        for idx, p in enumerate(self.profile.experience.projects):
            path = f"experience.projects[{idx}].name"
            ref = self._get_evidence_ref(path, p.name)
            res.append(ProjectEvidence(
                name=p.name,
                skills=p.skills,
                evidence_ref=ref
            ))
        return res

    def evidence_for_requirement(self, text: str) -> list[CandidateEvidenceRef]:
        if not text:
            return []
        t = text.lower()
        refs = []
        
        # Skill check
        for skill_ev in self.skills():
            if skill_ev.skill.lower() in t:
                refs.extend(skill_ev.evidence_refs)
                
        # Project check
        for proj_ev in self.projects():
            if proj_ev.name.lower() in t:
                refs.append(proj_ev.evidence_ref)
                
        return refs

    def allowed_claims_for(self, field_paths: list[str]) -> list[str]:
        # Helper to extract a value from the profile by dotted path
        claims = []
        for path in field_paths:
            if "demographic" in path:
                continue
            
            parts = path.split('.')
            curr = self.profile
            for p in parts:
                if hasattr(curr, p):
                    curr = getattr(curr, p)
                elif isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    curr = None
                    break
            
            if curr and isinstance(curr, str):
                claims.append(curr)
        return claims

import pytest
import yaml
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.intelligence.candidate_evidence import CandidateEvidenceService

@pytest.fixture
def example_profile():
    with open("config/candidate_profile.example.yaml", "r") as f:
        data = yaml.safe_load(f)
    return CandidateProfileConfig(**data)

def test_evidence_service_skills(example_profile):
    svc = CandidateEvidenceService(example_profile)
    skills = svc.skills()
    
    assert len(skills) > 0
    py_skill = next((s for s in skills if s.skill == "Python"), None)
    assert py_skill is not None
    assert len(py_skill.projects) >= 0

def test_evidence_service_projects(example_profile):
    svc = CandidateEvidenceService(example_profile)
    projects = svc.projects()
    assert len(projects) > 0
    assert projects[0].evidence_ref.present is True
    assert projects[0].evidence_ref.value_fingerprint is not None
    
def test_evidence_service_requirement(example_profile):
    svc = CandidateEvidenceService(example_profile)
    refs = svc.evidence_for_requirement("Looking for strong Python and Kubernetes")
    assert len(refs) > 0
    
    unknown = svc.evidence_for_requirement("Looking for strong brainfuck skills")
    assert len(unknown) == 0

def test_evidence_service_demographic(example_profile):
    svc = CandidateEvidenceService(example_profile)
    ref = svc._get_evidence_ref("demographic_answers.race", "Asian", is_demographic=True)
    assert ref.allowed_for_application is False

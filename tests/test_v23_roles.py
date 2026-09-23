import pytest
from jobs_automation.db.models import JobModel
from jobs_automation.intelligence.role_family import RoleFamilyClassifier

def test_match_job_to_family():
    classifier = RoleFamilyClassifier()
    
    # 1. Exact abbreviation replacement "Sr. SWE"
    job1 = JobModel(normalized_title="Sr. SWE")
    assert classifier.match_job_to_family(job1) == "ai_software_engineer"
    
    # 2. "Senior Software Engineer"
    job2 = JobModel(normalized_title="Senior Software Engineer")
    assert classifier.match_job_to_family(job2) == "ai_software_engineer"
    
    # 3. Fuzzy match fallback
    job3 = JobModel(normalized_title="mobil ios dev")
    assert classifier.match_job_to_family(job3) == "mobile_ios"
    
    # 4. Unknown returns None
    job4 = JobModel(normalized_title="Janitor")
    assert classifier.match_job_to_family(job4) is None
    

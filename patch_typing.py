import os

def fix_file(filepath):
    content = open(filepath).read()
    if "from jobs_automation.core.job_search import JobSearchConfig" in content:
        content = content.replace("from jobs_automation.core.job_search import JobSearchConfig", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from jobs_automation.core.job_search import JobSearchConfig\n    from jobs_automation.core.candidate_profile import CandidateProfileConfig")
        # Remove any other profile imports
        content = content.replace("from jobs_automation.core.candidate_profile import CandidateProfileConfig\n", "")
        with open(filepath, "w") as f:
            f.write(content)

fix_file("src/jobs_automation/evaluation/engine.py")
fix_file("src/jobs_automation/evaluation/filters.py")

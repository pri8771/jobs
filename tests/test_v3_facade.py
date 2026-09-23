from jobs_automation.tools.facade import get_interview_brief, add_target_company, evaluate_job_match

def test_get_interview_brief():
    result = get_interview_brief.invoke({"company_name": "Acme Corp", "role_title": "Engineer"})
    assert result["company"] == "Acme Corp"
    assert "strategy" in result

def test_add_target_company():
    result = add_target_company.invoke({"company_name": "Globex", "domain": "globex.com"})
    assert "Globex" in result

def test_evaluate_job_match():
    result = evaluate_job_match.invoke({"job_title": "Dev", "description": "Needs python", "resume_id": "123"})
    assert result["score"] == 85.0

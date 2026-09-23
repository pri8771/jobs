from typing import Any
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import tailor_resume

def build_resume_strategist_agent(llm: Any):
    system_prompt = (
        "You are the ResumeStrategistAgent. Your job is to tailor "
        "resumes for specific job descriptions."
    )
    tools = [tailor_resume]
    return create_react_agent(llm, tools, prompt=system_prompt)

from typing import Any
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import draft_recruiter_reply

def build_recruiter_crm_agent(llm: Any):
    system_prompt = (
        "You are the RecruiterCRMAgent. Your job is to read lifecycle state "
        "and draft replies to recruiters."
    )
    tools = [draft_recruiter_reply]
    return create_react_agent(llm, tools, prompt=system_prompt)

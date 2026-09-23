from typing import Any
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import generate_interview_story_map, get_interview_brief

def build_interview_agent(llm: Any):
    system_prompt = (
        "You are the InterviewAgent. Your job is to generate interview briefs "
        "and story maps for candidates."
    )
    tools = [generate_interview_story_map, get_interview_brief]
    return create_react_agent(llm, tools, prompt=system_prompt)

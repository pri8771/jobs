from typing import Any
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import evaluate_job_match

def build_opportunity_matcher_agent(llm: Any):
    """
    Builds the OpportunityMatcherAgent.
    Uses evaluation tools to output a match decision.
    """
    system_prompt = (
        "You are the OpportunityMatcherAgent. Your job is to evaluate how well "
        "a job description matches the candidate's resume, and output a match decision."
    )
    tools = [evaluate_job_match]
    
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
    return agent_executor

from typing import Any
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import prepare_application, submit_application

def build_application_operator_agent(llm: Any):
    system_prompt = (
        "You are the ApplicationOperatorAgent. You can prepare applications "
        "but you must NEVER submit them unless explicitly authorized."
    )
    tools = [prepare_application, submit_application]
    return create_react_agent(llm, tools, prompt=system_prompt)

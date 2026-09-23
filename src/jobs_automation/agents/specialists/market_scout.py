from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from jobs_automation.tools.facade import add_target_company

# In a real implementation this would use a real LLM, e.g., ChatOpenAI or ChatAnthropic
# For now we define the agent signature

def build_market_scout_agent(llm: Any):
    """
    Builds the MarketScoutAgent using LangGraph's create_react_agent.
    Permissions: P0_READ, P1_LOCAL_WRITE
    """
    system_prompt = (
        "You are the MarketScoutAgent. Your job is to read job postings, "
        "normalize them, and add target companies to the database."
    )
    tools = [add_target_company]
    
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
    return agent_executor

from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from jobs_automation.agents.specialists.market_scout import build_market_scout_agent
from jobs_automation.agents.specialists.opportunity_matcher import build_opportunity_matcher_agent

class RegistryState(TypedDict):
    messages: list[Any]
    current_agent: str

def build_parent_graph(llm: Any):
    scout_agent = build_market_scout_agent(llm)
    matcher_agent = build_opportunity_matcher_agent(llm)

    def run_scout(state: RegistryState):
        result = scout_agent.invoke({"messages": state["messages"]})
        return {"messages": result["messages"]}

    def run_matcher(state: RegistryState):
        result = matcher_agent.invoke({"messages": state["messages"]})
        return {"messages": result["messages"]}

    def route_agent(state: RegistryState):
        return state["current_agent"]

    builder = StateGraph(RegistryState)
    builder.add_node("market_scout", run_scout)
    builder.add_node("opportunity_matcher", run_matcher)

    builder.add_conditional_edges(START, route_agent, {
        "market_scout": "market_scout",
        "opportunity_matcher": "opportunity_matcher"
    })
    
    # Simple handoff: if scout finishes, it could potentially route to matcher or END.
    # For now, we just end the graph after the agent finishes. In a real scenario,
    # the LLM output could be parsed to determine the next agent.
    builder.add_edge("market_scout", END)
    builder.add_edge("opportunity_matcher", END)

    return builder.compile()

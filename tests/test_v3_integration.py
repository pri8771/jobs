import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from tests.test_v3_specialists import FakeToolChatModel
from jobs_automation.agents.registry import build_parent_graph

def test_integration_market_scout():
    mock_tool_call = ToolCall(
        name="add_target_company",
        args={"company_name": "IntegrationCorp", "domain": "int.com"},
        id="call_999"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Added company IntegrationCorp")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    
    graph = build_parent_graph(llm)
    
    initial_state = {
        "messages": [HumanMessage(content="Find jobs")],
        "current_agent": "market_scout"
    }
    
    result = graph.invoke(initial_state)
    messages = result["messages"]
    assert "Company IntegrationCorp added successfully." in [m.content for m in messages if m.type == "tool"]

def test_integration_opportunity_matcher():
    mock_tool_call = ToolCall(
        name="evaluate_job_match",
        args={"job_title": "SWE", "description": "Needs python", "resume_id": "r999"},
        id="call_888"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Match is good")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    
    graph = build_parent_graph(llm)
    
    initial_state = {
        "messages": [HumanMessage(content="Match this job")],
        "current_agent": "opportunity_matcher"
    }
    
    result = graph.invoke(initial_state)
    messages = result["messages"]
    assert "85.0" in [m.content for m in messages if m.type == "tool"][0]

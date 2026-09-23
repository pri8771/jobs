import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from tests.test_v3_specialists import FakeToolChatModel
from jobs_automation.agents.specialists.resume_strategist import build_resume_strategist_agent
from jobs_automation.agents.specialists.application_operator import build_application_operator_agent
from jobs_automation.agents.specialists.recruiter_crm import build_recruiter_crm_agent
from jobs_automation.agents.specialists.interview_agent import build_interview_agent

def test_resume_strategist_agent():
    mock_tool_call = ToolCall(
        name="tailor_resume",
        args={"job_description": "Needs python", "resume_id": "r123"},
        id="call_1"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Resume tailored")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_resume_strategist_agent(llm)
    result = agent.invoke({"messages": [HumanMessage(content="Tailor resume")]})
    assert "Tailored resume variant content." in [m.content for m in result["messages"] if m.type == "tool"][0]

def test_application_operator_agent():
    mock_tool_call = ToolCall(
        name="prepare_application",
        args={"job_id": "j123", "candidate_data": {}},
        id="call_2"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Application prepared")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_application_operator_agent(llm)
    result = agent.invoke({"messages": [HumanMessage(content="Prepare app")]})
    assert "Application packet prepared" in [m.content for m in result["messages"] if m.type == "tool"][0]

def test_recruiter_crm_agent():
    mock_tool_call = ToolCall(
        name="draft_recruiter_reply",
        args={"inbound_message_id": "m123", "context": "thanks"},
        id="call_3"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Drafted")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_recruiter_crm_agent(llm)
    result = agent.invoke({"messages": [HumanMessage(content="Draft reply")]})
    assert "Draft reply for message m123" in [m.content for m in result["messages"] if m.type == "tool"][0]

def test_interview_agent():
    mock_tool_call = ToolCall(
        name="generate_interview_story_map",
        args={"role_title": "Engineer"},
        id="call_4"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Story map done")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_interview_agent(llm)
    result = agent.invoke({"messages": [HumanMessage(content="Story map")]})
    assert "Interview story map generated" in [m.content for m in result["messages"] if m.type == "tool"][0]

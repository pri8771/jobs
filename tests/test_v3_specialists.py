import pytest
from typing import Any
from pydantic import Field
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from jobs_automation.agents.specialists.market_scout import build_market_scout_agent
from jobs_automation.agents.specialists.opportunity_matcher import build_opportunity_matcher_agent

class FakeToolChatModel(BaseChatModel):
    responses: list[Any] = Field(default_factory=list)
    i: int = 0
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        response = self.responses[self.i]
        self.i += 1
        return ChatResult(generations=[ChatGeneration(message=response)])
        
    @property
    def _llm_type(self) -> str:
        return "fake-tool-chat-model"
        
    def bind_tools(self, tools, **kwargs):
        return self

def test_market_scout_agent():
    mock_tool_call = ToolCall(
        name="add_target_company",
        args={"company_name": "TestCorp", "domain": "testcorp.com"},
        id="call_123"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Added company TestCorp")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_market_scout_agent(llm)
    
    result = agent.invoke({"messages": [HumanMessage(content="Find a job at TestCorp")]})
    messages = result["messages"]
    
    assert len(messages) > 1
    assert "Company TestCorp added successfully." in [m.content for m in messages if m.type == "tool"]
    assert messages[-1].content == "Added company TestCorp"

def test_opportunity_matcher_agent():
    mock_tool_call = ToolCall(
        name="evaluate_job_match",
        args={"job_title": "Software Eng", "description": "Needs python", "resume_id": "r123"},
        id="call_456"
    )
    mock_responses = [
        AIMessage(content="", tool_calls=[mock_tool_call]),
        AIMessage(content="Match score is 85.0")
    ]
    llm = FakeToolChatModel(responses=mock_responses)
    agent = build_opportunity_matcher_agent(llm)
    
    result = agent.invoke({"messages": [HumanMessage(content="Evaluate this job")]})
    messages = result["messages"]
    
    assert len(messages) > 1
    tool_messages = [m.content for m in messages if m.type == "tool"]
    assert any("85.0" in m for m in tool_messages)
    assert messages[-1].content == "Match score is 85.0"

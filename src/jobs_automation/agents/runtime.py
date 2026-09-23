from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, START, END
import uuid

class AgentState(TypedDict):
    task_id: str
    task_type: str
    status: Literal["READY", "RUNNING", "NEEDS_REVIEW", "SUCCEEDED", "FAILED"]
    error_reason: str | None
    attempt: int
    context: dict

def execute_task(state: AgentState) -> dict:
    return {"status": "SUCCEEDED" if state["attempt"] >= 1 else "RUNNING", "attempt": state["attempt"] + 1}

def check_status(state: AgentState) -> str:
    if state["status"] == "SUCCEEDED":
        return "success"
    elif state["status"] == "FAILED":
        return "failure"
    elif state["status"] == "NEEDS_REVIEW":
        return "review"
    return "running"

def build_runtime_graph():
    builder = StateGraph(AgentState)
    builder.add_node("execute_task", execute_task)
    
    builder.add_edge(START, "execute_task")
    builder.add_conditional_edges(
        "execute_task",
        check_status,
        {
            "success": END,
            "failure": END,
            "review": END,
            "running": "execute_task"
        }
    )
    return builder.compile()

runtime_graph = build_runtime_graph()

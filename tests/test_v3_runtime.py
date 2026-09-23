import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from jobs_automation.db.base import Base
from jobs_automation.agents.runtime import build_runtime_graph
from jobs_automation.agents.checkpointer import SQLAlchemyCheckpointSaver

@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def test_runtime_graph_with_checkpointer(session_factory):
    checkpointer = SQLAlchemyCheckpointSaver(session_factory)
    graph = build_runtime_graph()
    graph.checkpointer = checkpointer

    thread_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id, "task_id": task_id}}

    initial_state = {
        "task_id": task_id,
        "task_type": "TEST",
        "status": "READY",
        "error_reason": None,
        "attempt": 0,
        "context": {}
    }

    # Run the graph
    for state in graph.stream(initial_state, config):
        pass

    # Fetch the state using the checkpointer
    saved_state = graph.get_state(config)
    assert saved_state.values["status"] == "SUCCEEDED"
    assert saved_state.values["attempt"] == 2

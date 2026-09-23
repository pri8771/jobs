import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from jobs_automation.db.base import Base
from jobs_automation.agents.memory import ScopedMemoryService
import jobs_automation.db.models  # ensure models are registered

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_store_and_retrieve_memory(session):
    service = ScopedMemoryService(session)
    entry = service.store("agent_1", "key_1", {"some": "data"})
    assert entry.agent_id == "agent_1"
    assert entry.memory_key == "key_1"
    assert entry.memory_value == {"some": "data"}

    retrieved = service.retrieve("agent_1", "key_1")
    assert retrieved is not None
    assert retrieved.memory_value == {"some": "data"}

def test_update_memory(session):
    service = ScopedMemoryService(session)
    service.store("agent_1", "key_1", {"some": "data"})
    service.store("agent_1", "key_1", {"some": "new_data"})

    retrieved = service.retrieve("agent_1", "key_1")
    assert retrieved.memory_value == {"some": "new_data"}

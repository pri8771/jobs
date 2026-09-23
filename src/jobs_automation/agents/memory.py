from typing import Any
import uuid
from sqlalchemy.orm import Session
from jobs_automation.db.models import AgentMemoryModel
from jobs_automation.agents.models import MemoryEntry

class ScopedMemoryService:
    def __init__(self, session: Session):
        self.session = session

    def store(self, agent_id: str, memory_key: str, memory_value: dict[str, Any]) -> MemoryEntry:
        model = self.session.query(AgentMemoryModel).filter_by(
            agent_id=agent_id, memory_key=memory_key
        ).first()

        if model:
            model.memory_value_json = memory_value
        else:
            model = AgentMemoryModel(
                agent_id=agent_id,
                memory_key=memory_key,
                memory_value_json=memory_value
            )
            self.session.add(model)
        
        self.session.flush()
        return MemoryEntry(
            id=model.id,
            agent_id=model.agent_id,
            memory_key=model.memory_key,
            memory_value=model.memory_value_json,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def retrieve(self, agent_id: str, memory_key: str) -> MemoryEntry | None:
        model = self.session.query(AgentMemoryModel).filter_by(
            agent_id=agent_id, memory_key=memory_key
        ).first()

        if not model:
            return None

        return MemoryEntry(
            id=model.id,
            agent_id=model.agent_id,
            memory_key=model.memory_key,
            memory_value=model.memory_value_json,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

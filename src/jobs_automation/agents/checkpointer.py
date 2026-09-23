import uuid
import json
from typing import Any, AsyncIterator, Iterator, Optional, Sequence, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple, ChannelVersions
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from jobs_automation.db.models import AgentCheckpointModel

class SQLAlchemyCheckpointSaver(BaseCheckpointSaver):
    """LangGraph checkpointer backed by SQLAlchemy AgentCheckpointModel."""
    
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        with self.session_factory() as session:
            query = select(AgentCheckpointModel).filter_by(thread_id=thread_id)
            if checkpoint_id:
                query = query.filter_by(checkpoint_id=checkpoint_id)
            else:
                query = query.order_by(desc(AgentCheckpointModel.created_at))
            
            model = session.execute(query).scalars().first()
            if not model:
                return None
                
            checkpoint = model.checkpoint_json
            metadata = model.metadata_json
            parent_config = None
            if model.parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": model.parent_checkpoint_id,
                    }
                }
                
            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
            )

    def list(self, config: RunnableConfig, *, filter: Optional[dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        with self.session_factory() as session:
            query = select(AgentCheckpointModel).filter_by(thread_id=thread_id).order_by(desc(AgentCheckpointModel.created_at))
            if limit:
                query = query.limit(limit)
                
            for model in session.execute(query).scalars().all():
                checkpoint = model.checkpoint_json
                metadata = model.metadata_json
                parent_config = None
                if model.parent_checkpoint_id:
                    parent_config = {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                            "checkpoint_id": model.parent_checkpoint_id,
                        }
                    }
                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                            "checkpoint_id": model.checkpoint_id,
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=parent_config,
                )

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: ChannelVersions) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        task_id = config["configurable"].get("task_id", "00000000-0000-0000-0000-000000000000")
        
        with self.session_factory() as session:
            model = AgentCheckpointModel(
                task_id=uuid.UUID(task_id),
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                checkpoint_json=checkpoint,
                metadata_json=metadata,
                parent_checkpoint_id=config["configurable"].get("checkpoint_id")
            )
            session.add(model)
            session.commit()
            
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": config["configurable"].get("checkpoint_ns", ""),
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(self, config: RunnableConfig, writes: Sequence[Tuple[str, Any]], task_id: str) -> None:
        pass # Not implementing pending writes for this simple setup

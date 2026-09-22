from __future__ import annotations

import datetime
import json
import os

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import InboundMessageModel, MessageLinkModel, TaskModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.engine import EmailIngestionEngine
from tests.test_gmail_adapter_bounded import CANDIDATE, FakeGmailService, _five_messages

SOURCE_SHA = os.environ["JOBS_SOURCE_SHA"]
SOURCE_TREE = os.environ["JOBS_SOURCE_TREE"]
DB_NAME = os.environ["JOBS_GMAIL_DB"]
url = URL.create(
    "postgresql+psycopg",
    username="pchordia",
    database=DB_NAME,
    query={"host": os.environ["JOBS_PG_SOCKET"], "port": os.environ["JOBS_PG_PORT"]},
)
db = create_engine(url)
init_db(db)
Factory = sessionmaker(bind=db)


def reset_database() -> None:
    Base.metadata.drop_all(db)
    Base.metadata.create_all(db)


def counts(session):
    return {
        "messages": len(session.scalars(select(InboundMessageModel)).all()),
        "links": len(session.scalars(select(MessageLinkModel)).all()),
        "tasks": len(session.scalars(select(TaskModel)).all()),
        "checkpoints": len(
            session.scalars(
                select(TaskModel).where(TaskModel.task_type == "email_checkpoint")
            ).all()
        ),
    }


output = {
    "source_sha": SOURCE_SHA,
    "source_tree": SOURCE_TREE,
    "database": DB_NAME,
    "dialect": db.dialect.name,
}

# Existing J20G01 retained scenario: missing fetch and cap incomplete are atomic;
# then a complete retry persists each of five provider IDs once.
session = Factory()
try:
    failing_ids = {"m2"}
    service = FakeGmailService(_five_messages(), page_size=5, failing_ids=failing_ids)
    engine = EmailIngestionEngine(
        session,
        GmailAdapter(service=service, verified_identities=[CANDIDATE]),
        candidate_emails=[CANDIDATE],
    )
    failed = engine.run_sweep(max_messages=10)
    session.expire_all()
    failed_state = counts(session)
    assert failed.errors == ["poll_incomplete: truncated_by_cap=False, missing_messages=1"]
    assert failed.messages_ingested == 0 and failed.batch_message_ids == []
    assert failed.checkpoint_advanced_to is None
    assert failed_state == {"messages": 0, "links": 0, "tasks": 0, "checkpoints": 0}

    capped = EmailIngestionEngine(
        session,
        GmailAdapter(
            service=FakeGmailService(_five_messages(), page_size=5),
            verified_identities=[CANDIDATE],
        ),
        candidate_emails=[CANDIDATE],
    ).run_sweep(max_messages=2)
    session.expire_all()
    capped_state = counts(session)
    assert capped.errors == ["poll_incomplete: truncated_by_cap=True, missing_messages=0"]
    assert capped.messages_ingested == 0 and capped.batch_message_ids == []
    assert capped.checkpoint_advanced_to is None
    assert capped_state == {"messages": 0, "links": 0, "tasks": 0, "checkpoints": 0}

    failing_ids.clear()
    retry = engine.run_sweep(max_messages=10)
    session.expire_all()
    ids = list(session.scalars(select(InboundMessageModel.provider_message_id)))
    retry_state = counts(session)
    assert retry.errors == [] and retry.messages_ingested == 5
    assert retry.messages_skipped_duplicate == 0
    assert sorted(ids) == ["m1", "m2", "m3", "m4", "m5"]
    assert len(ids) == len(set(ids)) == 5
    assert retry_state["messages"] == 5 and retry_state["checkpoints"] == 1
    output["atomic_failure_complete_retry"] = {
        "missing_fetch_errors": failed.errors,
        "missing_fetch_counts": failed_state,
        "missing_fetch_checkpoint": failed.checkpoint_advanced_to,
        "cap_errors": capped.errors,
        "cap_counts": capped_state,
        "cap_checkpoint": capped.checkpoint_advanced_to,
        "retry_ingested": retry.messages_ingested,
        "retry_skipped": retry.messages_skipped_duplicate,
        "retry_provider_ids": sorted(ids),
        "retry_counts": retry_state,
        "retry_checkpoint": retry.checkpoint_advanced_to,
    }
finally:
    session.close()

# Same retained prior-state assertion in a clean schema in this same disposable DB.
reset_database()
session = Factory()
try:
    prior = InboundMessageModel(
        provider_message_id="prior-committed",
        provider_thread_id="prior-thread",
        received_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        sender="prior@example.test",
        recipients_json=[CANDIDATE],
        direction="inbound",
        subject="Prior",
        headers_json={},
        body_text="Synthetic prior committed row",
        classification="JOB_ALERT",
        confidence=1.0,
    )
    checkpoint_payload = {"source": "prior", "marker": "must-survive", "nested": {"n": 1}}
    checkpoint = TaskModel(
        task_type="email_checkpoint",
        status="completed",
        due_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        payload_json=checkpoint_payload,
    )
    session.add_all([prior, checkpoint])
    session.commit()
    prior_id, checkpoint_id = prior.id, checkpoint.id
    checkpoint_due_before = checkpoint.due_at
    before = counts(session)

    failed = EmailIngestionEngine(
        session,
        GmailAdapter(
            service=FakeGmailService(_five_messages(), page_size=5, failing_ids={"m2"}),
            verified_identities=[CANDIDATE],
        ),
        candidate_emails=[CANDIDATE],
    ).run_sweep(max_messages=10)
    session.expire_all()
    after = counts(session)
    prior_after = session.get(InboundMessageModel, prior_id)
    checkpoint_after = session.get(TaskModel, checkpoint_id)
    assert failed.errors == ["poll_incomplete: truncated_by_cap=False, missing_messages=1"]
    assert before == after == {"messages": 1, "links": 0, "tasks": 1, "checkpoints": 1}
    assert prior_after is not None and prior_after.provider_message_id == "prior-committed"
    assert checkpoint_after is not None and checkpoint_after.payload_json == checkpoint_payload
    assert checkpoint_after.due_at == checkpoint_due_before
    output["prior_committed_state_preserved"] = {
        "errors": failed.errors,
        "before_counts": before,
        "after_counts": after,
        "prior_provider_message_id": prior_after.provider_message_id,
        "checkpoint_payload": checkpoint_after.payload_json,
        "checkpoint_due_at": checkpoint_after.due_at.isoformat(),
    }
finally:
    session.close()
    db.dispose()

print(json.dumps(output, indent=2, sort_keys=True))

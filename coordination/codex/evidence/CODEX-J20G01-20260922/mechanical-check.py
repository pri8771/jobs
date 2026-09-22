from __future__ import annotations

import datetime
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.db.models import InboundMessageModel, MessageLinkModel, TaskModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.engine import EmailIngestionEngine
from tests.test_gmail_adapter_bounded import CANDIDATE, FakeGmailService, _five_messages

BASE_SHA = "10a3a23924fdde6b040082ef030ad1286591b9a9"
DIFF_SHA256 = "7be7cd8a2d5a16326110aac5b567067479fd6ea4f39949c57a841c9408835c8b"


def new_session():
    db = create_engine("sqlite:///:memory:")
    init_db(db)
    return db, sessionmaker(bind=db)()


def counts(session):
    return {
        "messages": len(session.scalars(select(InboundMessageModel)).all()),
        "links": len(session.scalars(select(MessageLinkModel)).all()),
        "tasks": len(session.scalars(select(TaskModel)).all()),
        "checkpoints": len(session.scalars(select(TaskModel).where(TaskModel.task_type == "email_checkpoint")).all()),
    }


output = {"base_sha": BASE_SHA, "diff_sha256": DIFF_SHA256}

# Scenario 1: failed full fetch is an all-or-nothing sweep, then clean retry inserts five once.
db1, session1 = new_session()
try:
    failing_ids = {"m2"}
    service = FakeGmailService(_five_messages(), page_size=5, failing_ids=failing_ids)
    engine = EmailIngestionEngine(
        session1,
        GmailAdapter(service=service, verified_identities=[CANDIDATE]),
        candidate_emails=[CANDIDATE],
    )
    failed = engine.run_sweep(max_messages=10)
    session1.expire_all()
    failed_state = counts(session1)
    assert failed.errors == ["poll_incomplete: missing_messages=1"]
    assert failed.messages_ingested == 0 and failed.batch_message_ids == []
    assert failed.checkpoint_advanced_to is None
    assert failed_state == {"messages": 0, "links": 0, "tasks": 0, "checkpoints": 0}

    failing_ids.clear()
    retry = engine.run_sweep(max_messages=10)
    session1.expire_all()
    ids = list(session1.scalars(select(InboundMessageModel.provider_message_id)))
    retry_state = counts(session1)
    assert retry.errors == [] and retry.messages_ingested == 5
    assert retry.messages_skipped_duplicate == 0
    assert sorted(ids) == ["m1", "m2", "m3", "m4", "m5"]
    assert len(ids) == len(set(ids)) == 5
    assert retry_state["messages"] == 5 and retry_state["checkpoints"] == 1
    output["fresh_failure_then_retry"] = {
        "failure_errors": failed.errors,
        "failure_counts": failed_state,
        "failure_checkpoint": failed.checkpoint_advanced_to,
        "retry_ingested": retry.messages_ingested,
        "retry_skipped": retry.messages_skipped_duplicate,
        "retry_provider_ids": sorted(ids),
        "retry_counts": retry_state,
        "retry_checkpoint": retry.checkpoint_advanced_to,
    }
finally:
    session1.close(); db1.dispose()


# Scenario 2: rollback preserves unrelated committed rows and exact checkpoint payload.
db2, session2 = new_session()
try:
    prior = InboundMessageModel(
        provider_message_id="prior-committed",
        provider_thread_id="prior-thread",
        received_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        sender="prior@example.test",
        recipients_json=[CANDIDATE], direction="inbound", subject="Prior",
        headers_json={}, body_text="Synthetic prior committed row",
        classification="JOB_ALERT", confidence=1.0,
    )
    checkpoint_payload = {"source": "prior", "marker": "must-survive", "nested": {"n": 1}}
    checkpoint = TaskModel(
        task_type="email_checkpoint", status="completed",
        due_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        payload_json=checkpoint_payload,
    )
    session2.add_all([prior, checkpoint]); session2.commit()
    prior_id, checkpoint_id = prior.id, checkpoint.id
    checkpoint_due_before = checkpoint.due_at
    before = counts(session2)

    failed = EmailIngestionEngine(
        session2,
        GmailAdapter(
            service=FakeGmailService(_five_messages(), page_size=5, failing_ids={"m2"}),
            verified_identities=[CANDIDATE],
        ),
        candidate_emails=[CANDIDATE],
    ).run_sweep(max_messages=10)
    session2.expire_all()
    after = counts(session2)
    prior_after = session2.get(InboundMessageModel, prior_id)
    checkpoint_after = session2.get(TaskModel, checkpoint_id)
    assert failed.errors == ["poll_incomplete: missing_messages=1"]
    assert before == after == {"messages": 1, "links": 0, "tasks": 1, "checkpoints": 1}
    assert prior_after is not None and prior_after.provider_message_id == "prior-committed"
    assert checkpoint_after is not None and checkpoint_after.payload_json == checkpoint_payload
    assert checkpoint_after.due_at == checkpoint_due_before
    output["prior_state_preservation"] = {
        "failure_errors": failed.errors,
        "before_counts": before,
        "after_counts": after,
        "prior_message_id": str(prior_after.id),
        "checkpoint_id": str(checkpoint_after.id),
        "checkpoint_payload": checkpoint_after.payload_json,
        "checkpoint_due_at": checkpoint_after.due_at.isoformat(),
    }
finally:
    session2.close(); db2.dispose()

print(json.dumps(output, indent=2, sort_keys=True))

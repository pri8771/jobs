from __future__ import annotations

import json
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.db.models import InboundMessageModel, MessageLinkModel, TaskModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.engine import EmailIngestionEngine
from tests.test_gmail_adapter_bounded import CANDIDATE, FakeGmailService, _five_messages

CODE_SHA = "10a3a23924fdde6b040082ef030ad1286591b9a9"


def snapshot(session):
    messages = session.scalars(
        select(InboundMessageModel).order_by(InboundMessageModel.received_at)
    ).all()
    checkpoints = session.scalars(
        select(TaskModel).where(TaskModel.task_type == "email_checkpoint")
    ).all()
    return {
        "message_rows": len(messages),
        "provider_ids": [m.provider_message_id for m in messages],
        "message_links": session.scalar(select(func.count()).select_from(MessageLinkModel)),
        "task_rows": session.scalar(select(func.count()).select_from(TaskModel)),
        "checkpoint_rows": len(checkpoints),
        "checkpoint_due_at": checkpoints[-1].due_at.isoformat() if checkpoints else None,
        "lifecycle_eligible_rows": sum(m.classification != "JOB_ALERT" for m in messages),
        "classifications": {m.provider_message_id: m.classification for m in messages},
    }


engine = create_engine("sqlite:///:memory:")
init_db(engine)
session = sessionmaker(bind=engine)()
try:
    failed_adapter = GmailAdapter(
        service=FakeGmailService(_five_messages(), page_size=5, failing_ids={"m2"}),
        verified_identities=[CANDIDATE],
    )
    failed = EmailIngestionEngine(
        session, failed_adapter, candidate_emails=[CANDIDATE]
    ).run_sweep(max_messages=10)
    session.expire_all()
    after_failure = snapshot(session)
    failed_report = failed.poll_report
    failure_result = {
        "messages_polled": failed.messages_polled,
        "messages_ingested": failed.messages_ingested,
        "errors": failed.errors,
        "checkpoint_advanced_to": failed.checkpoint_advanced_to,
        "checkpoint_held_reason": failed.checkpoint_held_reason,
        "poll_complete": failed_report.complete if failed_report else None,
        "listed_count": failed_report.listed_count if failed_report else None,
        "fetched_count": failed_report.fetched_count if failed_report else None,
        "missing_message_ids": failed_report.missing_message_ids if failed_report else None,
        "database": after_failure,
    }

    retry_adapter = GmailAdapter(
        service=FakeGmailService(_five_messages(), page_size=5),
        verified_identities=[CANDIDATE],
    )
    retry = EmailIngestionEngine(
        session, retry_adapter, candidate_emails=[CANDIDATE]
    ).run_sweep(max_messages=10)
    session.expire_all()
    retry_report = retry.poll_report
    retry_result = {
        "messages_polled": retry.messages_polled,
        "messages_ingested": retry.messages_ingested,
        "messages_skipped_duplicate": retry.messages_skipped_duplicate,
        "errors": retry.errors,
        "checkpoint_advanced_to": retry.checkpoint_advanced_to,
        "checkpoint_held_reason": retry.checkpoint_held_reason,
        "poll_complete": retry_report.complete if retry_report else None,
        "listed_count": retry_report.listed_count if retry_report else None,
        "fetched_count": retry_report.fetched_count if retry_report else None,
        "missing_message_ids": retry_report.missing_message_ids if retry_report else None,
        "database": snapshot(session),
    }

    assert failure_result["poll_complete"] is False
    assert failure_result["missing_message_ids"] == ["m2"]
    assert failure_result["errors"] == []
    assert failure_result["checkpoint_advanced_to"] is None
    assert after_failure["message_rows"] == 4  # J20G-01 defect: partial transaction committed
    assert after_failure["lifecycle_eligible_rows"] > 0  # eligible for later worker lifecycle sweep
    assert retry_result["poll_complete"] is True
    assert retry_result["messages_ingested"] == 1
    assert retry_result["messages_skipped_duplicate"] == 4
    assert retry_result["database"]["message_rows"] == 5
    assert retry_result["database"]["checkpoint_rows"] == 1

    print(json.dumps({
        "code_sha": CODE_SHA,
        "after_missing_fetch": failure_result,
        "after_successful_retry": retry_result,
        "observed_defect": "missing listed message produced no sweep error and committed fetched subset",
    }, indent=2, sort_keys=True))
finally:
    session.close()
    engine.dispose()

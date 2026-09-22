from __future__ import annotations

import datetime
import json
import os

from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.ingestion.models import RawEmailMessage
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.timeline import build_timeline_export
from jobs_automation.worker import WorkerDaemon


def instant(value: datetime.datetime | None) -> datetime.datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.UTC)
    return value.astimezone(datetime.UTC)


url = URL.create(
    "postgresql+psycopg",
    username=os.environ.get("JOBS_PG_USER", os.environ.get("USER")),
    host=os.environ["JOBS_PG_SOCKET"],
    port=int(os.environ["JOBS_PG_PORT"]),
    database=os.environ["JOBS_REPLY_DB"],
)
engine = create_engine(url)
Base.metadata.create_all(engine)
factory = sessionmaker(bind=engine, expire_on_commit=False)
now = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
inbound_at = now - datetime.timedelta(days=4)
reply_at = now - datetime.timedelta(hours=1)
thread = "diag-thread-reply-link"
candidate = "candidate@diagnostic.invalid"

# Explicit prior state: this is a synthetic partial scenario, not golden/live proof.
with factory() as session:
    company = CompanyModel(normalized_name="Diagnosticco", domain="diagnostic.invalid")
    session.add(company)
    session.flush()
    job = JobModel(company_id=company.id, normalized_title="Diagnostic Engineer", status="active")
    session.add(job)
    session.flush()
    app = ApplicationModel(
        job_id=job.id,
        status="SUBMITTED",
        application_mode="manual",
        destination_domain="diagnostic.invalid",
        policy_decision="allowed",
        applied_at=inbound_at - datetime.timedelta(days=1),
        last_activity_at=inbound_at - datetime.timedelta(days=1),
    )
    session.add(app)
    session.commit()
    app_id, job_id, company_id = app.id, job.id, company.id

inbound = RawEmailMessage(
    provider_message_id="diag-inbound-1",
    provider_thread_id=thread,
    received_at=inbound_at,
    sender="Recruiter <recruiter@diagnostic.invalid>",
    recipients=[candidate],
    direction="inbound",
    subject="Opportunity at Diagnosticco - Engineer",
    body_text="I came across your profile and am reaching out regarding an opportunity at Diagnosticco.",
    raw_reference="synthetic://diag/inbound",
)
reply = RawEmailMessage(
    provider_message_id="diag-reply-1",
    provider_thread_id=thread,
    received_at=reply_at,
    sender=candidate,
    recipients=["recruiter@diagnostic.invalid"],
    direction="outbound",
    subject="Re: Opportunity at Diagnosticco - Engineer",
    body_text="Synthetic diagnostic reply; no message was sent.",
    raw_reference="synthetic://diag/reply",
)

first = WorkerDaemon(
    factory, email_adapter=MockEmailAdapter([inbound]), candidate_emails=[candidate]
).run_sweep(reconcile=False)
assert first["errors"] == [], first
with factory() as session:
    task = session.scalar(select(TaskModel).where(TaskModel.task_type == "UNANSWERED_RECRUITER"))
    assert task is not None and task.status == "pending"
    first_task_id = task.id
    app = session.get(ApplicationModel, app_id)
    initial_status, initial_closed_at = app.status, app.closed_at
    initial_interviews = session.scalar(
        select(func.count()).select_from(InterviewModel).where(InterviewModel.application_id == app_id)
    )

second = WorkerDaemon(
    factory, email_adapter=MockEmailAdapter([inbound, reply]), candidate_emails=[candidate]
).run_sweep(reconcile=False)
assert second["errors"] == [], second

# A new daemon and adapter simulate a duplicate poll after process restart.
third = WorkerDaemon(
    factory, email_adapter=MockEmailAdapter([inbound, reply]), candidate_emails=[candidate]
).run_sweep(reconcile=False)
assert third["errors"] == [], third

# Independent engine/sessionmaker supplies fresh-process-style durable readback.
engine.dispose()
fresh_engine = create_engine(url)
fresh_factory = sessionmaker(bind=fresh_engine, expire_on_commit=False)
with fresh_factory() as session:
    messages = list(session.scalars(select(InboundMessageModel).order_by(InboundMessageModel.received_at)))
    assert [message.provider_message_id for message in messages] == ["diag-inbound-1", "diag-reply-1"]
    by_provider = {message.provider_message_id: message for message in messages}
    inbound_row, reply_row = by_provider["diag-inbound-1"], by_provider["diag-reply-1"]

    inbound_links = list(session.scalars(select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == inbound_row.id)))
    reply_links = list(session.scalars(select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == reply_row.id)))
    assert len(inbound_links) == 1 and len(reply_links) == 1
    prior_link, reply_link = inbound_links[0], reply_links[0]
    assert (reply_link.application_id, reply_link.job_id, reply_link.company_id) == (app_id, job_id, company_id)
    assert reply_link.method == "thread_reply_attribution"
    assert reply_link.confidence == prior_link.confidence and reply_link.confidence >= 0.8

    events = list(session.scalars(select(ApplicationEventModel).where(ApplicationEventModel.application_id == app_id)))
    reply_events = [event for event in events if event.source_reference == "diag-reply-1"]
    assert len(reply_events) == 1
    reply_event = reply_events[0]
    assert (reply_event.event_type, reply_event.source, reply_event.actor) == (
        "CANDIDATE_REPLIED", "email_lifecycle", "candidate"
    )

    contacts = list(session.scalars(select(ContactModel)))
    assert len(contacts) == 1 and contacts[0].email == "recruiter@diagnostic.invalid"
    contact = contacts[0]
    assert reply_event.payload_json.get("contact_id") == str(contact.id)
    assert not session.scalar(select(ContactModel).where(ContactModel.email == candidate))

    app = session.get(ApplicationModel, app_id)
    assert app.status == initial_status
    assert app.closed_at == initial_closed_at is None
    assert instant(app.last_activity_at) == reply_at
    final_interviews = session.scalar(
        select(func.count()).select_from(InterviewModel).where(InterviewModel.application_id == app_id)
    )
    assert final_interviews == initial_interviews == 0

    tasks = list(session.scalars(select(TaskModel).where(TaskModel.task_type == "UNANSWERED_RECRUITER")))
    assert len(tasks) == 1 and tasks[0].id == first_task_id and tasks[0].status == "completed"
    assert (tasks[0].payload_json or {}).get("resolved_by_reply_id") == str(reply_row.id)
    assert not list(session.scalars(select(TaskModel).where(TaskModel.task_type == "NEEDS_REVIEW")))

    crm = RecruiterCRMService(session)
    application_ids = [row["provider_message_id"] for row in crm.get_timeline_for_application(app_id)]
    contact_ids = [row["provider_message_id"] for row in crm.get_timeline_for_contact(contact.id)]
    assert application_ids == ["diag-inbound-1", "diag-reply-1"]
    assert contact_ids == ["diag-inbound-1", "diag-reply-1"]
    export = build_timeline_export(
        session,
        app_id,
        identity={"git_sha": os.environ["SOURCE_BASE_SHA"], "package_version": "diagnostic"},
        now=now,
    )
    reply_source = next(row for row in export["sources"] if row["provider_message_id"] == "diag-reply-1")
    assert reply_source["link_method"] == "thread_reply_attribution"
    assert reply_source["link_confidence"] == reply_link.confidence

    output = {
        "source_base_sha": os.environ["SOURCE_BASE_SHA"],
        "source_state": "base_plus_dirty_candidate_reply_repair",
        "source_diff_sha256": os.environ["SOURCE_DIFF_SHA256"],
        "scenario": "synthetic partial seeded job/application; not golden or live proof",
        "worker_runs": {"first": first, "second": second, "duplicate_restart": third},
        "durable_counts": {
            "messages": len(messages),
            "reply_links": len(reply_links),
            "reply_events": len(reply_events),
            "contacts": len(contacts),
            "unanswered_tasks": len(tasks),
            "interviews": final_interviews,
        },
        "reply_link": {
            "method": reply_link.method,
            "confidence": reply_link.confidence,
            "application_id": str(reply_link.application_id),
            "job_id": str(reply_link.job_id),
            "company_id": str(reply_link.company_id),
        },
        "reply_event": {
            "type": reply_event.event_type,
            "source": reply_event.source,
            "actor": reply_event.actor,
            "contact_id": reply_event.payload_json.get("contact_id"),
        },
        "application": {
            "status": app.status,
            "closed_at": app.closed_at,
            "last_activity_at": app.last_activity_at,
        },
        "crm_application_provider_ids": application_ids,
        "crm_contact_provider_ids": contact_ids,
        "redacted_reply_source": reply_source,
        "assertions": "PASS",
    }
    print(json.dumps(output, indent=2, sort_keys=True, default=str))

fresh_engine.dispose()

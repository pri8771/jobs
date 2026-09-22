"""Safe same-thread attribution for synthetic outbound candidate replies."""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from jobs_automation.adapters.gmail import MockEmailAdapter
from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.ingestion.engine import EmailIngestionEngine
from jobs_automation.ingestion.models import (
    EmailClassification,
    EmailClassificationResult,
    RawEmailMessage,
)
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.lifecycle.engine import LifecycleEngine
from jobs_automation.lifecycle.timeline import build_timeline_export

NOW = datetime.datetime(2026, 9, 22, 12, 0, tzinfo=datetime.UTC)
CANDIDATE = "candidate@reply-diagnostic.invalid"
THREAD = "thread-candidate-reply"


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def _application(db: Session, *, status: str = "INTERVIEWING") -> ApplicationModel:
    company = CompanyModel(normalized_name=f"reply-diagnostic-{uuid.uuid4().hex}")
    db.add(company)
    db.flush()
    job = JobModel(company_id=company.id, normalized_title="Synthetic Reply Engineer")
    db.add(job)
    db.flush()
    app = ApplicationModel(
        job_id=job.id,
        status=status,
        application_mode="manual",
        destination_domain="reply-diagnostic.invalid",
        applied_at=NOW - datetime.timedelta(days=10),
        last_activity_at=NOW - datetime.timedelta(days=3),
    )
    db.add(app)
    db.flush()
    return app


def _prior(
    db: Session,
    app: ApplicationModel,
    *,
    thread: str = THREAD,
    confidence: float = 0.95,
    canary: bool = False,
    with_contact: bool = False,
    received_at: datetime.datetime | None = None,
) -> tuple[InboundMessageModel, ContactModel | None]:
    message = InboundMessageModel(
        provider_message_id=f"prior-{uuid.uuid4().hex}",
        provider_thread_id=thread,
        received_at=received_at or NOW - datetime.timedelta(days=2),
        sender="Recruiter <recruiter@reply-diagnostic.invalid>",
        recipients_json=[CANDIDATE],
        direction="inbound",
        subject="Synthetic recruiter outreach",
        headers_json={"_provider": {"canary": True}} if canary else {},
        body_text="Synthetic prior evidence only.",
        classification="RECRUITER_OUTREACH",
        confidence=0.95,
    )
    db.add(message)
    db.flush()
    db.add(
        MessageLinkModel(
            inbound_message_id=message.id,
            application_id=app.id,
            job_id=app.job_id,
            company_id=app.job.company_id,
            confidence=confidence,
            method="company_match",
        )
    )
    contact = None
    if with_contact:
        contact = ContactModel(
            company_id=app.job.company_id,
            name="Synthetic Recruiter",
            email="recruiter@reply-diagnostic.invalid",
            role="Recruiter",
            source="email",
            first_contact_at=message.received_at,
            last_contact_at=message.received_at,
        )
        db.add(contact)
        db.flush()
        db.add(
            ApplicationEventModel(
                application_id=app.id,
                event_type="RECRUITER_CONTACTED",
                occurred_at=message.received_at,
                source="email_lifecycle",
                source_reference=message.provider_message_id,
                actor="system",
                payload_json={"contact_id": str(contact.id)},
            )
        )
    db.flush()
    return message, contact


def _raw_reply(
    *, message_id: str, thread: str = THREAD, received_at: datetime.datetime = NOW
) -> RawEmailMessage:
    return RawEmailMessage(
        provider_message_id=message_id,
        provider_thread_id=thread,
        received_at=received_at,
        sender=CANDIDATE,
        recipients=["recruiter@reply-diagnostic.invalid"],
        direction="outbound",
        subject="Re: Synthetic recruiter outreach",
        body_text="Synthetic reply; no message was sent.",
        raw_reference=f"synthetic://{message_id}",
    )


def _ingest_and_process(db: Session, raw: RawEmailMessage) -> InboundMessageModel:
    summary = EmailIngestionEngine(
        session=db,
        adapter=MockEmailAdapter([raw]),
        candidate_emails=[CANDIDATE],
    ).run_sweep(reconcile=False)
    assert summary.errors == []
    reply = db.scalar(
        select(InboundMessageModel).where(
            InboundMessageModel.provider_message_id == raw.provider_message_id
        )
    )
    assert reply is not None
    LifecycleEngine(db).process_message(reply)
    db.commit()
    return reply


def _reply_event(
    db: Session, app: ApplicationModel, message_id: str
) -> ApplicationEventModel | None:
    return db.scalar(
        select(ApplicationEventModel).where(
            ApplicationEventModel.application_id == app.id,
            ApplicationEventModel.source_reference == message_id,
        )
    )


def test_unique_application_and_contact_records_stage_preserving_reply(session: Session) -> None:
    app = _application(session)
    prior, contact = _prior(session, app, with_contact=True)
    assert contact is not None
    task = TaskModel(
        application_id=app.id,
        job_id=app.job_id,
        task_type="UNANSWERED_RECRUITER",
        status="pending",
        payload_json={"thread_id": THREAD, "message_id": str(prior.id)},
    )
    session.add(task)
    session.commit()

    reply = _ingest_and_process(session, _raw_reply(message_id="candidate-reply-unique"))
    LifecycleAlertService(session).check_unanswered_recruiters(now=NOW)
    session.commit()

    link = session.scalar(
        select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == reply.id)
    )
    event = _reply_event(session, app, reply.provider_message_id)
    assert link is not None and link.application_id == app.id
    assert link.method == "thread_reply_attribution" and link.confidence == pytest.approx(0.95)
    assert event is not None and event.event_type == "CANDIDATE_REPLIED"
    assert event.source == "email_lifecycle" and event.actor == "candidate"
    assert event.payload_json["contact_id"] == str(contact.id)
    assert app.status == "INTERVIEWING" and app.last_activity_at == NOW
    assert task.status == "completed"
    assert task.payload_json["resolved_by_reply_id"] == str(reply.id)

    crm = RecruiterCRMService(session)
    assert [row["provider_message_id"] for row in crm.get_timeline_for_application(app.id)][
        -1
    ] == reply.provider_message_id
    assert [row["provider_message_id"] for row in crm.get_timeline_for_contact(contact.id)][
        -1
    ] == reply.provider_message_id
    source = next(
        row
        for row in build_timeline_export(session, app.id)["sources"]
        if row["provider_message_id"] == reply.provider_message_id
    )
    assert source["link_method"] == "thread_reply_attribution"


@pytest.mark.parametrize("contact_evidence", ["none", "ambiguous"])
def test_unique_application_without_unique_contact_does_not_guess_contact(
    session: Session, contact_evidence: str
) -> None:
    app = _application(session)
    _prior(session, app)
    if contact_evidence == "ambiguous":
        _prior(session, app, with_contact=True)
        prior, second_contact = _prior(session, app, with_contact=True)
        assert second_contact is not None
        second_contact.email = "second-recruiter@reply-diagnostic.invalid"
        prior.sender = "Second Recruiter <second-recruiter@reply-diagnostic.invalid>"
    session.commit()

    reply = _ingest_and_process(session, _raw_reply(message_id="candidate-reply-no-contact"))
    event = _reply_event(session, app, reply.provider_message_id)
    link = session.scalar(
        select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == reply.id)
    )
    assert link is not None and link.application_id == app.id
    assert event is not None and event.payload_json.get("contact_id") is None
    assert reply.provider_message_id in {
        row["provider_message_id"]
        for row in RecruiterCRMService(session).get_timeline_for_application(app.id)
    }
    contacts = session.scalars(select(ContactModel)).all()
    assert len(contacts) == (0 if contact_evidence == "none" else 2)
    for contact in contacts:
        assert reply.provider_message_id not in {
            row["provider_message_id"]
            for row in RecruiterCRMService(session).get_timeline_for_contact(contact.id)
        }


@pytest.mark.parametrize("case", ["missing", "multiple", "weak", "canary_only", "future_only"])
def test_ambiguous_or_untrusted_thread_evidence_never_auto_links(
    session: Session, case: str
) -> None:
    app = _application(session)
    if case == "multiple":
        other = _application(session)
        _prior(session, app)
        _prior(session, other)
    elif case == "weak":
        _prior(session, app, confidence=0.79)
    elif case == "canary_only":
        _prior(session, app, canary=True)
    elif case == "future_only":
        _prior(session, app, received_at=NOW + datetime.timedelta(minutes=1))
    session.commit()

    reply = _ingest_and_process(
        session, _raw_reply(message_id=f"candidate-reply-{case}", received_at=NOW)
    )
    links = session.scalars(
        select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == reply.id)
    ).all()
    events = session.scalars(
        select(ApplicationEventModel).where(
            ApplicationEventModel.source_reference == reply.provider_message_id
        )
    ).all()
    assert links == [] and events == []
    if case in {"multiple", "weak"}:
        assert (
            session.scalar(
                select(TaskModel).where(
                    TaskModel.task_type == "NEEDS_REVIEW", TaskModel.status == "pending"
                )
            )
            is not None
        )


def test_replay_is_idempotent_and_reply_time_never_regresses_activity(session: Session) -> None:
    app = _application(session, status="OFFER")
    _prior(session, app)
    app.last_activity_at = NOW + datetime.timedelta(hours=2)
    session.commit()
    raw = _raw_reply(message_id="candidate-reply-replay", received_at=NOW)

    first = _ingest_and_process(session, raw)
    _ingest_and_process(session, raw)

    assert (
        len(
            session.scalars(
                select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == first.id)
            ).all()
        )
        == 1
    )
    assert (
        len(
            session.scalars(
                select(ApplicationEventModel).where(
                    ApplicationEventModel.application_id == app.id,
                    ApplicationEventModel.source_reference == raw.provider_message_id,
                )
            ).all()
        )
        == 1
    )
    assert app.status == "OFFER"
    assert app.last_activity_at == NOW + datetime.timedelta(hours=2)


def test_persisted_inbound_candidate_reply_is_not_attributed(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _application(session)
    _prior(session, app)
    session.commit()
    raw = _raw_reply(message_id="candidate-reply-inbound")
    engine = EmailIngestionEngine(
        session=session,
        adapter=MockEmailAdapter([raw]),
        candidate_emails=[CANDIDATE],
    )
    monkeypatch.setattr(
        engine.classifier,
        "classify",
        lambda _raw: EmailClassificationResult(
            classification=EmailClassification.CANDIDATE_REPLY,
            confidence=0.99,
            direction="inbound",
            needs_review=False,
        ),
    )
    assert engine.run_sweep(reconcile=False).errors == []
    message = session.scalar(
        select(InboundMessageModel).where(
            InboundMessageModel.provider_message_id == raw.provider_message_id
        )
    )
    assert message is not None
    LifecycleEngine(session).process_message(message)
    session.commit()
    assert (
        session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == message.id)
        ).all()
        == []
    )
    assert _reply_event(session, app, raw.provider_message_id) is None


def test_spoofed_inbound_sender_containing_candidate_address_is_not_a_reply(
    session: Session,
) -> None:
    app = _application(session)
    prior, _ = _prior(session, app, with_contact=True)
    task = TaskModel(
        application_id=app.id,
        job_id=app.job_id,
        task_type="UNANSWERED_RECRUITER",
        status="pending",
        payload_json={"thread_id": THREAD, "message_id": str(prior.id)},
    )
    session.add(task)
    session.commit()
    raw = RawEmailMessage(
        provider_message_id="spoofed-inbound-candidate-address",
        provider_thread_id=THREAD,
        received_at=NOW,
        sender=f"{CANDIDATE}.evil@attacker.invalid",
        recipients=[CANDIDATE],
        direction="inbound",
        subject="Re: Synthetic recruiter outreach",
        body_text="Inbound attacker-controlled content.",
        raw_reference="synthetic://spoofed-inbound",
    )

    summary = EmailIngestionEngine(
        session=session,
        adapter=MockEmailAdapter([raw]),
        candidate_emails=[CANDIDATE],
    ).run_sweep(reconcile=False)
    assert summary.errors == []
    message = session.scalar(
        select(InboundMessageModel).where(
            InboundMessageModel.provider_message_id == raw.provider_message_id
        )
    )
    assert message is not None and message.direction == "inbound"
    assert message is not None
    LifecycleEngine(session).process_message(message)
    LifecycleAlertService(session).check_unanswered_recruiters(now=NOW)
    session.commit()

    assert (
        session.scalars(
            select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == message.id)
        ).all()
        == []
    )
    assert _reply_event(session, app, raw.provider_message_id) is None
    assert task.status == "pending"
    assert task.payload_json.get("resolved_by_reply_id") is None


def test_proven_outbound_declining_different_role_records_reply_before_divergence(
    session: Session,
) -> None:
    app = _application(session)
    _prior(session, app, with_contact=True)
    original_activity = app.last_activity_at
    session.commit()
    raw = _raw_reply(message_id="candidate-reply-different-role")
    raw.body_text = "Thanks, but I am not pursuing a different role."

    reply = _ingest_and_process(session, raw)
    event = _reply_event(session, app, raw.provider_message_id)
    assert event is not None and event.event_type == "CANDIDATE_REPLIED"
    assert event.payload_json.get("contact_id") is not None
    assert app.status == "INTERVIEWING"
    assert app.last_activity_at == NOW and app.last_activity_at > original_activity
    assert raw.provider_message_id in {
        row["provider_message_id"]
        for row in RecruiterCRMService(session).get_timeline_for_application(app.id)
    }
    assert (
        session.scalar(
            select(TaskModel).where(
                TaskModel.task_type == "NEEDS_REVIEW", TaskModel.status == "pending"
            )
        )
        is None
    )
    assert reply.direction == "outbound"

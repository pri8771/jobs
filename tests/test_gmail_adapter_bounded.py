"""V17-M01 / V17-M02: bounded, complete Gmail polling with provider-time semantics.

These tests drive the real ``GmailAdapter`` against an in-memory fake of the Gmail API
service object (list/get/getProfile), so pagination, per-message fetch accounting, label
derived direction and provider-time handling are exercised without any network or
credential. No mailbox is touched.
"""

from __future__ import annotations

import base64
import datetime
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.gmail import GmailAdapter, MockEmailAdapter
from jobs_automation.db.models import InboundMessageModel, MessageLinkModel, TaskModel
from jobs_automation.db.session import init_db
from jobs_automation.ingestion.engine import EmailIngestionEngine
from jobs_automation.ingestion.models import RawEmailMessage

CANDIDATE = "candidate@invalid"
NOW = datetime.datetime(2026, 9, 20, 12, 0, tzinfo=datetime.UTC)


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def _message(
    msg_id: str,
    *,
    sender: str,
    to: str,
    subject: str,
    body: str,
    internal: datetime.datetime,
    labels: list[str] | None = None,
    claimed_date: str | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    headers = [
        {"name": "From", "value": sender},
        {"name": "To", "value": to},
        {"name": "Subject", "value": subject},
    ]
    if claimed_date:
        headers.append({"name": "Date", "value": claimed_date})
    return {
        "id": msg_id,
        "threadId": thread_id or f"thread-{msg_id}",
        "internalDate": str(int(internal.timestamp() * 1000)),
        "labelIds": labels or ["INBOX"],
        "payload": {
            "mimeType": "text/plain",
            "headers": headers,
            "body": {"data": _b64(body)},
        },
    }


class _Executable:
    def __init__(self, result: Any) -> None:
        self._result = result

    def execute(self) -> Any:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeGmailService:
    """Minimal stand-in for the googleapiclient Gmail resource used by GmailAdapter."""

    def __init__(
        self,
        messages: list[dict[str, Any]],
        *,
        page_size: int = 2,
        failing_ids: set[str] | None = None,
        profile_address: str = CANDIDATE,
    ) -> None:
        self._messages = messages
        self._page_size = page_size
        self._failing_ids = failing_ids or set()
        self._profile_address = profile_address
        self.list_calls: list[dict[str, Any]] = []
        self.get_calls: list[str] = []

    # googleapiclient chaining: service.users().messages().list(...).execute()
    def users(self) -> FakeGmailService:
        return self

    def messages(self) -> FakeGmailService:
        return self

    def threads(self) -> FakeGmailService:
        return self

    def getProfile(self, userId: str) -> _Executable:  # noqa: N802
        return _Executable({"emailAddress": self._profile_address})

    def list(self, **kwargs: Any) -> _Executable:  # noqa: A003
        self.list_calls.append(dict(kwargs))
        start = int(kwargs.get("pageToken") or 0)
        requested = int(kwargs.get("maxResults") or self._page_size)
        size = min(self._page_size, requested)
        page = self._messages[start : start + size]
        result: dict[str, Any] = {
            "messages": [{"id": m["id"], "threadId": m["threadId"]} for m in page]
        }
        if start + size < len(self._messages):
            result["nextPageToken"] = str(start + size)
        return _Executable(result)

    def get(self, userId: str, id: str, format: str = "full") -> _Executable:  # noqa: A002
        self.get_calls.append(id)
        if id in self._failing_ids:
            return _Executable(RuntimeError("HttpError 500 while fetching message"))
        for message in self._messages:
            if message["id"] == id:
                return _Executable(message)
        return _Executable(RuntimeError("HttpError 404 message not found"))


def _five_messages() -> list[dict[str, Any]]:
    return [
        _message(
            f"m{i}",
            sender=f"recruiter{i}@employer.invalid",
            to=CANDIDATE,
            subject=f"Interview {i}",
            body="Let us talk.",
            internal=NOW - datetime.timedelta(hours=5 - i),
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# V17-M01: bounded pagination and completeness
# ---------------------------------------------------------------------------


def test_poll_pages_through_listing_and_fetches_every_listed_message() -> None:
    service = FakeGmailService(_five_messages(), page_size=2)
    adapter = GmailAdapter(service=service, verified_identities=[CANDIDATE], page_size=2)
    messages = adapter.poll_messages(query="from:employer.invalid", max_results=100)
    report = adapter.last_poll_report()
    assert report is not None
    assert [m.provider_message_id for m in messages] == ["m1", "m2", "m3", "m4", "m5"]
    assert report.pages_fetched == 3
    assert report.listed_count == 5 and report.fetched_count == 5
    assert report.complete is True and report.truncated_by_cap is False
    assert report.missing_message_ids == []
    assert report.adapter == "gmail" and report.synthetic is False
    assert len(service.get_calls) == 5


def test_poll_marks_cap_truncation_and_never_exceeds_cap() -> None:
    service = FakeGmailService(_five_messages(), page_size=2)
    adapter = GmailAdapter(service=service, page_size=2)
    messages = adapter.poll_messages(max_results=3)
    report = adapter.last_poll_report()
    assert report is not None
    assert len(messages) == 3
    assert report.truncated_by_cap is True
    assert report.complete is False
    assert all(int(call["maxResults"]) <= 2 for call in service.list_calls)


def test_poll_marks_missing_message_instead_of_silently_dropping_it() -> None:
    service = FakeGmailService(_five_messages(), page_size=5, failing_ids={"m3"})
    adapter = GmailAdapter(service=service)
    messages = adapter.poll_messages(max_results=10)
    report = adapter.last_poll_report()
    assert report is not None
    assert [m.provider_message_id for m in messages] == ["m1", "m2", "m4", "m5"]
    assert report.missing_message_ids == ["m3"]
    assert report.complete is False


def test_incomplete_poll_cannot_advance_checkpoint_past_lost_evidence(db_session: Session) -> None:
    service = FakeGmailService(_five_messages(), page_size=5, failing_ids={"m2"})
    adapter = GmailAdapter(service=service, verified_identities=[CANDIDATE])
    engine = EmailIngestionEngine(db_session, adapter, candidate_emails=[CANDIDATE])

    summary = engine.run_sweep(max_messages=10)
    assert summary.messages_ingested == 0
    assert summary.errors == ["poll_incomplete: truncated_by_cap=False, missing_messages=1"]
    assert summary.batch_message_ids == []
    assert summary.checkpoint_advanced_to is None
    assert summary.checkpoint_held_reason is not None
    assert "missing_messages=1" in summary.checkpoint_held_reason
    assert engine.get_last_checkpoint() is None
    assert summary.poll_report is not None and summary.poll_report.complete is False
    for model in (InboundMessageModel, MessageLinkModel, TaskModel):
        assert db_session.scalars(select(model)).all() == []

    # A cap-truncated prefix is also an atomic failure, not a partial ingest.
    capped = EmailIngestionEngine(
        db_session,
        GmailAdapter(service=FakeGmailService(_five_messages(), page_size=5)),
    )
    capped_summary = capped.run_sweep(max_messages=2)
    assert capped_summary.messages_ingested == 0
    assert capped_summary.errors == ["poll_incomplete: truncated_by_cap=True, missing_messages=0"]
    assert capped_summary.batch_message_ids == []
    assert capped_summary.checkpoint_advanced_to is None
    assert "truncated_by_cap=True" in (capped_summary.checkpoint_held_reason or "")
    for model in (InboundMessageModel, MessageLinkModel, TaskModel):
        assert db_session.scalars(select(model)).all() == []

    # A complete retry sees every listed message exactly once because no prefix survived.
    service._failing_ids.clear()
    retry = engine.run_sweep(max_messages=10)
    assert retry.errors == []
    assert retry.messages_ingested == 5
    assert retry.messages_skipped_duplicate == 0
    assert retry.checkpoint_advanced_to is not None
    assert sorted(db_session.scalars(select(InboundMessageModel.provider_message_id))) == [
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
    ]


class _MalformedListingService(FakeGmailService):
    def list(self, **kwargs: Any) -> _Executable:  # noqa: A003
        self.list_calls.append(dict(kwargs))
        # One valid stub plus a malformed listing item proves that a partial prefix is
        # rejected before it can be persisted.
        return _Executable({"messages": [{"id": "m1"}, "not-a-message-stub"]})


class _PayloadMismatchService(FakeGmailService):
    def get(self, userId: str, id: str, format: str = "full") -> _Executable:  # noqa: A002
        self.get_calls.append(id)
        for message in self._messages:
            if message["id"] == id:
                mismatched = dict(message)
                mismatched["id"] = "unexpected-provider-id"
                return _Executable(mismatched)
        return _Executable(RuntimeError("message not found"))


@pytest.mark.parametrize(
    ("service_factory", "expected_marker"),
    [
        (_MalformedListingService, "<malformed-listing>"),
        (_PayloadMismatchService, "<payload-id-mismatch>"),
    ],
)
def test_malformed_or_mismatched_gmail_evidence_aborts_before_all_writes(
    db_session: Session,
    service_factory: type[FakeGmailService],
    expected_marker: str,
) -> None:
    adapter = GmailAdapter(service=service_factory(_five_messages(), page_size=5))
    engine = EmailIngestionEngine(db_session, adapter, candidate_emails=[CANDIDATE])

    summary = engine.run_sweep(max_messages=10)

    assert summary.errors[0].startswith(
        "poll_incomplete: truncated_by_cap=False, missing_messages="
    )
    assert summary.messages_ingested == 0
    assert summary.batch_message_ids == []
    assert summary.checkpoint_advanced_to is None
    assert engine.get_last_checkpoint() is None
    assert summary.poll_report is not None
    assert expected_marker in summary.poll_report.missing_message_ids
    assert summary.poll_report.complete is False
    for model in (InboundMessageModel, MessageLinkModel, TaskModel):
        assert db_session.scalars(select(model)).all() == []


def test_complete_poll_persists_query_window_count_and_completeness(db_session: Session) -> None:
    service = FakeGmailService(_five_messages(), page_size=2)
    adapter = GmailAdapter(service=service, verified_identities=[CANDIDATE])
    engine = EmailIngestionEngine(db_session, adapter, candidate_emails=[CANDIDATE])
    summary = engine.run_sweep(query="from:employer.invalid", max_messages=10)
    assert summary.checkpoint_advanced_to is not None
    checkpoint = db_session.scalar(
        select(TaskModel).where(TaskModel.task_type == "email_checkpoint")
    )
    assert checkpoint is not None
    payload = checkpoint.payload_json
    assert payload["query"] == "from:employer.invalid"
    assert payload["max_results"] == 10
    assert payload["listed_count"] == 5 and payload["fetched_count"] == 5
    assert payload["ingested_count"] == 5
    assert payload["complete"] is True
    assert payload["adapter"] == "gmail"


def test_bounded_run_never_advances_the_incremental_checkpoint(db_session: Session) -> None:
    adapter = GmailAdapter(service=FakeGmailService(_five_messages(), page_size=5))
    engine = EmailIngestionEngine(db_session, adapter)
    summary = engine.run_sweep(
        max_messages=10,
        since_override=NOW - datetime.timedelta(days=1),
        advance_checkpoint=False,
    )
    assert summary.messages_ingested == 5
    assert summary.checkpoint_advanced_to is None
    assert summary.checkpoint_held_reason == "bounded_run_does_not_advance_checkpoint"
    assert engine.get_last_checkpoint() is None


# ---------------------------------------------------------------------------
# V17-M02: direction from SENT / verified identity; provider time vs claimed Date
# ---------------------------------------------------------------------------


def test_sent_reply_is_outbound_by_label_and_identity() -> None:
    reply = _message(
        "sent1",
        sender=f"Candidate Name <{CANDIDATE}>",
        to="Recruiter <recruiter1@employer.invalid>, hiring@employer.invalid",
        subject="Re: Interview 1",
        body="Tuesday works.",
        internal=NOW,
        labels=["SENT"],
    )
    adapter = GmailAdapter(service=FakeGmailService([reply]), verified_identities=[CANDIDATE])
    (message,) = adapter.poll_messages(max_results=5)
    assert message.direction == "outbound"
    assert message.provider_metadata["direction_basis"] == "gmail_sent_label"
    assert message.provider_metadata["identity_verified"] is True
    assert message.provider_metadata["sender_address"] == CANDIDATE
    assert message.recipients == ["recruiter1@employer.invalid", "hiring@employer.invalid"]

    # Identity alone (no SENT label, e.g. a copy in another label) still derives outbound.
    copy = dict(reply, id="sent2", labelIds=["INBOX"])
    adapter = GmailAdapter(service=FakeGmailService([copy]), verified_identities=[CANDIDATE])
    (message,) = adapter.poll_messages(max_results=5)
    assert message.direction == "outbound"
    assert message.provider_metadata["direction_basis"] == "verified_identity"


def test_inbound_message_from_unknown_sender_is_not_outbound_even_if_it_claims_so() -> None:
    forged = _message(
        "forged1",
        sender=f"Not The Candidate <spoof@{CANDIDATE.split('@')[1]}>",
        to=CANDIDATE,
        subject="Re: your reply",
        body="pretending",
        internal=NOW,
        labels=["INBOX"],
    )
    adapter = GmailAdapter(service=FakeGmailService([forged]), verified_identities=[CANDIDATE])
    (message,) = adapter.poll_messages(max_results=5)
    assert message.direction == "inbound"
    assert message.provider_metadata["direction_basis"] == "inbound_default"


def test_provider_time_is_authoritative_and_forged_future_date_is_kept_separately(
    db_session: Session,
) -> None:
    future_claim = "Mon, 01 Jan 2035 09:00:00 +0000"
    genuine = _message(
        "g1",
        sender="recruiter@employer.invalid",
        to=CANDIDATE,
        subject="Next steps",
        body="Hello",
        internal=NOW - datetime.timedelta(hours=2),
    )
    forged = _message(
        "f1",
        sender="attacker@employer.invalid",
        to=CANDIDATE,
        subject="Time travel",
        body="Hello",
        internal=NOW - datetime.timedelta(hours=1),
        claimed_date=future_claim,
    )
    adapter = GmailAdapter(service=FakeGmailService([genuine, forged], page_size=5))
    messages = {m.provider_message_id: m for m in adapter.poll_messages(max_results=10)}
    assert messages["f1"].received_at == NOW - datetime.timedelta(hours=1)
    assert messages["f1"].provider_metadata["claimed_date_utc"] == "2035-01-01T09:00:00+00:00"
    assert messages["f1"].provider_metadata["claimed_date_skew_seconds"] > 0
    assert messages["g1"].provider_metadata["claimed_date_utc"] is None

    engine = EmailIngestionEngine(db_session, adapter)
    summary = engine.run_sweep(max_messages=10)
    # The checkpoint follows provider time, not the forged header.
    assert summary.checkpoint_advanced_to == (NOW - datetime.timedelta(hours=1)).isoformat()
    stored = db_session.scalar(
        select(InboundMessageModel).where(InboundMessageModel.provider_message_id == "f1")
    )
    assert stored is not None
    assert stored.received_at.replace(tzinfo=datetime.UTC) == NOW - datetime.timedelta(hours=1)
    assert stored.headers_json["Date"] == future_claim
    assert stored.headers_json["_provider"]["claimed_date_utc"] == "2035-01-01T09:00:00+00:00"
    assert (
        stored.headers_json["_provider"]["internal_date_utc"]
        == (NOW - datetime.timedelta(hours=1)).isoformat()
    )


def test_mailbox_address_uses_profile_metadata_only() -> None:
    service = FakeGmailService([], profile_address="Owner <owner@invalid>")
    adapter = GmailAdapter(service=service)
    assert adapter.mailbox_address() == "owner@invalid"
    assert service.list_calls == [] and service.get_calls == []


def test_canary_identities_are_tagged_and_counted(db_session: Session) -> None:
    canary = RawEmailMessage(
        provider_message_id="canary-1",
        provider_thread_id="canary-thread",
        received_at=NOW,
        sender="unsubscriber+canary@invalid",
        recipients=[CANDIDATE],
        subject="Canary ping",
        body_text="synthetic",
    )
    genuine = RawEmailMessage(
        provider_message_id="real-1",
        provider_thread_id="real-thread",
        received_at=NOW,
        sender="recruiter@employer.invalid",
        recipients=[CANDIDATE],
        subject="Interview request",
        body_text="Can we talk?",
    )
    engine = EmailIngestionEngine(
        db_session,
        MockEmailAdapter([canary, genuine]),
        canary_identities=["unsubscriber+canary@invalid"],
    )
    summary = engine.run_sweep(max_messages=10)
    assert summary.canary_messages == 1
    tagged = db_session.scalar(
        select(InboundMessageModel).where(InboundMessageModel.provider_message_id == "canary-1")
    )
    assert tagged is not None and tagged.headers_json["_provider"]["canary"] is True
    untagged = db_session.scalar(
        select(InboundMessageModel).where(InboundMessageModel.provider_message_id == "real-1")
    )
    assert untagged is not None and "_provider" not in untagged.headers_json
    assert summary.poll_report is not None and summary.poll_report.synthetic is True


def test_canary_identity_matching_uses_exact_normalized_addresses(db_session: Session) -> None:
    """A display-name alias must match exactly without consuming lookalike addresses."""

    exact = RawEmailMessage(
        provider_message_id="exact-canary",
        provider_thread_id="exact-canary-thread",
        received_at=NOW,
        sender="Owner Canary <sarah.connor@viatris.com>",
        recipients=[CANDIDATE],
        subject="Canary ping",
        body_text="synthetic",
    )
    prefix_lookalike = exact.model_copy(
        update={
            "provider_message_id": "prefix-lookalike",
            "provider_thread_id": "prefix-lookalike-thread",
            "sender": "not-sarah.connor@viatris.com",
        }
    )
    suffix_lookalike = exact.model_copy(
        update={
            "provider_message_id": "suffix-lookalike",
            "provider_thread_id": "suffix-lookalike-thread",
            "sender": "sarah.connor@viatris.com.evil",
        }
    )
    engine = EmailIngestionEngine(
        db_session,
        MockEmailAdapter([exact, prefix_lookalike, suffix_lookalike]),
        canary_identities=["Configured Alias <sarah.connor@viatris.com>"],
    )

    summary = engine.run_sweep(max_messages=10)

    assert summary.canary_messages == 1
    rows = {
        message.provider_message_id: message
        for message in db_session.scalars(select(InboundMessageModel)).all()
    }
    assert rows["exact-canary"].headers_json["_provider"]["canary"] is True
    assert (rows["prefix-lookalike"].headers_json or {}).get("_provider", {}).get("canary") is not True
    assert (rows["suffix-lookalike"].headers_json or {}).get("_provider", {}).get("canary") is not True

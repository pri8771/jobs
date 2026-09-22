"""Bounded production ingestion runs with replay evidence (V17-M04 / V17-R05).

A bounded run is the only supported way to ingest genuine recruiting evidence for the V1.7
proof: it names the mailbox, the query, the window and the cap explicitly, it never moves
the incremental worker checkpoint, it tags owner-controlled canary aliases so their mail
is excluded from genuine evidence, and it records a secret-free audit row with the poll
completeness, the counts and logical-state digests taken before and after the run. A
replay re-executes the same recorded parameters and reports whether the logical state
(messages, links, events, tasks, interviews, contacts) stayed identical.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import subprocess
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation import __version__
from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.db.models import (
    ApplicationEventModel,
    AuditLogModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.ingestion.engine import EmailIngestionEngine, IngestionSweepSummary
from jobs_automation.ingestion.models import PollReport
from jobs_automation.lifecycle.alerts import LifecycleAlertService
from jobs_automation.lifecycle.engine import LifecycleEngine

logger = logging.getLogger(__name__)

BOUNDED_RUN_ACTION = "mailbox_ingestion_run"
MAX_BOUNDED_CAP = 500
RunStatus = Literal["SUCCESS", "INCOMPLETE", "FAILED", "DRY_RUN"]


class BoundedIngestionError(ValueError):
    """Raised for a request that violates the bounded-run contract."""


def code_identity() -> dict[str, Any]:
    """Git SHA and package version of the code that produced a run (no secrets)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        )
        git_sha = result.stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        git_sha = "unknown"
    return {"git_sha": git_sha, "package_version": __version__}


def mailbox_fingerprint(mailbox: str) -> dict[str, str]:
    """Bind a run to a mailbox without persisting the address itself."""
    normalized = mailbox.strip().lower()
    domain = normalized.partition("@")[2] if "@" in normalized else ""
    return {
        "mailbox_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "mailbox_domain": domain,
    }


class BoundedIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mailbox: str
    query: str
    window_start: datetime.datetime
    window_end: datetime.datetime
    cap: int = Field(ge=1, le=MAX_BOUNDED_CAP)
    dry_run: bool = False
    run_label: str | None = None
    replay_of_run_id: str | None = None

    def validated(self) -> BoundedIngestionRequest:
        if not self.mailbox.strip() or "@" not in self.mailbox:
            raise BoundedIngestionError("MAILBOX_REQUIRED")
        if not self.query.strip():
            raise BoundedIngestionError("QUERY_REQUIRED")
        if self.window_start.tzinfo is None or self.window_end.tzinfo is None:
            raise BoundedIngestionError("WINDOW_MUST_BE_TIMEZONE_AWARE")
        if self.window_start >= self.window_end:
            raise BoundedIngestionError("WINDOW_EMPTY")
        return self

    def provider_query(self) -> str:
        """Gmail query with the window bound explicitly; ``after:`` comes from since_override."""
        before_epoch = int(self.window_end.timestamp())
        return f"{self.query.strip()} before:{before_epoch}".strip()


class LogicalStateDigests(BaseModel):
    """Order-independent digests of the logical recruiting state (no private content)."""

    model_config = ConfigDict(extra="forbid")

    messages: str
    links: str
    events: str
    tasks: str
    interviews: str
    contacts: str
    counts: dict[str, int] = Field(default_factory=dict)


def _digest(rows: list[tuple[Any, ...]]) -> str:
    serialized = json.dumps(sorted(json.dumps(row, default=str) for row in rows))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_logical_state_digests(session: Session) -> LogicalStateDigests:
    messages = [
        (
            m.provider_message_id,
            m.provider_thread_id,
            m.received_at.isoformat(),
            m.direction,
            m.classification,
        )
        for m in session.scalars(select(InboundMessageModel)).all()
    ]
    links = [
        (
            str(link.inbound_message_id),
            str(link.application_id) if link.application_id else None,
            str(link.job_id) if link.job_id else None,
            link.method,
        )
        for link in session.scalars(select(MessageLinkModel)).all()
    ]
    events = [
        (str(e.application_id), e.event_type, e.source, e.source_reference, e.actor)
        for e in session.scalars(select(ApplicationEventModel)).all()
    ]
    tasks = [
        (
            t.task_type,
            t.status,
            str(t.application_id) if t.application_id else None,
            str((t.payload_json or {}).get("reason") or ""),
            str((t.payload_json or {}).get("provider_message_id") or ""),
        )
        for t in session.scalars(select(TaskModel)).all()
        if t.task_type != "email_checkpoint"
    ]
    interviews = [
        (
            str(i.application_id),
            i.round_type,
            i.scheduled_start.isoformat(),
            i.scheduled_end.isoformat(),
            i.timezone,
            i.status,
        )
        for i in session.scalars(select(InterviewModel)).all()
    ]
    contacts = [
        (
            hashlib.sha256((c.email or "").lower().encode("utf-8")).hexdigest(),
            c.role,
            c.first_contact_at.isoformat() if c.first_contact_at else None,
            c.last_contact_at.isoformat() if c.last_contact_at else None,
        )
        for c in session.scalars(select(ContactModel)).all()
    ]
    return LogicalStateDigests(
        messages=_digest(messages),
        links=_digest(links),
        events=_digest(events),
        tasks=_digest(tasks),
        interviews=_digest(interviews),
        contacts=_digest(contacts),
        counts={
            "messages": len(messages),
            "links": len(links),
            "events": len(events),
            "tasks": len(tasks),
            "interviews": len(interviews),
            "contacts": len(contacts),
        },
    )


class BoundedIngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: RunStatus
    adapter: str
    synthetic: bool
    mailbox_sha256: str
    mailbox_domain: str
    query: str
    provider_query: str
    window_start: str
    window_end: str
    cap: int
    dry_run: bool
    run_label: str | None = None
    replay_of_run_id: str | None = None
    started_at: str
    finished_at: str
    poll: PollReport | None = None
    complete: bool = False
    messages_polled: int = 0
    messages_ingested: int = 0
    messages_skipped_duplicate: int = 0
    canary_messages: int = 0
    review_tasks_created: int = 0
    lifecycle_transitions: int = 0
    interviews_scheduled: int = 0
    unanswered_alerts: int = 0
    stale_alerts: int = 0
    digests_before: LogicalStateDigests
    digests_after: LogicalStateDigests
    replay_identical: bool | None = None
    replay_matches_original: bool | None = None
    errors: list[str] = Field(default_factory=list)
    code_identity: dict[str, Any] = Field(default_factory=dict)

    def audit_metadata(self) -> dict[str, Any]:
        """Secret-free metadata persisted on the audit row (no address, no bodies)."""
        payload: dict[str, Any] = json.loads(self.model_dump_json())
        return payload


class BoundedIngestionRunner:
    """Run (or replay) one bounded ingestion + lifecycle pass and record its evidence."""

    def __init__(
        self,
        session: Session,
        adapter: EmailAdapter,
        *,
        candidate_emails: list[str] | None = None,
        canary_identities: list[str] | None = None,
        adapter_kind: str = "gmail",
        synthetic: bool = False,
        identity: dict[str, Any] | None = None,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.candidate_emails = list(candidate_emails or [])
        self.canary_identities = list(canary_identities or [])
        self.adapter_kind = adapter_kind
        self.synthetic = synthetic
        self.identity = identity or code_identity()

    def _verify_mailbox(self, request: BoundedIngestionRequest) -> None:
        """The live adapter must be bound to exactly the mailbox named in the request."""
        mailbox_address = getattr(self.adapter, "mailbox_address", None)
        if not callable(mailbox_address):
            return
        actual = str(mailbox_address() or "").strip().lower()
        if actual != request.mailbox.strip().lower():
            raise BoundedIngestionError("MAILBOX_MISMATCH")

    def run(self, request: BoundedIngestionRequest) -> BoundedIngestionResult:
        request = request.validated()
        self._verify_mailbox(request)
        started = datetime.datetime.now(datetime.UTC)
        run_id = str(uuid.uuid4())
        fingerprint = mailbox_fingerprint(request.mailbox)
        digests_before = compute_logical_state_digests(self.session)

        engine = EmailIngestionEngine(
            session=self.session,
            adapter=self.adapter,
            candidate_emails=self.candidate_emails,
            canary_identities=self.canary_identities,
        )
        summary: IngestionSweepSummary = engine.run_sweep(
            query=request.provider_query(),
            max_messages=request.cap,
            dry_run=request.dry_run,
            since_override=request.window_start,
            advance_checkpoint=False,
        )

        lifecycle_transitions = 0
        interviews_scheduled = 0
        unanswered_alerts = 0
        stale_alerts = 0
        errors = list(summary.errors)
        if not request.dry_run and not errors:
            try:
                lifecycle = LifecycleEngine(self.session)
                messages = self.session.scalars(
                    select(InboundMessageModel)
                    .where(
                        InboundMessageModel.id.in_(summary.batch_message_ids),
                        InboundMessageModel.classification != "JOB_ALERT",
                    )
                    .order_by(InboundMessageModel.received_at.asc())
                ).all()
                genuine_ids: list[uuid.UUID] = []
                thread_ids: set[str] = set()
                for message in messages:
                    if (message.headers_json or {}).get("_provider", {}).get("canary"):
                        continue  # canary mail never drives genuine lifecycle state
                    genuine_ids.append(message.id)
                    thread_ids.add(message.provider_thread_id or message.provider_message_id)
                    transition = lifecycle.process_message(message)
                    if transition:
                        lifecycle_transitions += 1
                        if transition.interview_scheduled:
                            interviews_scheduled += 1
                alerts = LifecycleAlertService(self.session)
                application_ids = {
                    app_id for app_id in self.session.scalars(
                        select(MessageLinkModel.application_id).where(
                            MessageLinkModel.inbound_message_id.in_(genuine_ids),
                            MessageLinkModel.application_id.is_not(None),
                        )
                    ) if app_id is not None
                }
                unanswered_alerts = len(alerts.check_unanswered_recruiters(thread_ids=thread_ids))
                stale_alerts = len(alerts.check_stale_applications(application_ids=application_ids))
                self.session.commit()
            except Exception as exc:  # pragma: no cover - defensive; surfaced as FAILED
                self.session.rollback()
                errors.append(f"lifecycle_pass_failed: {type(exc).__name__}")

        digests_after = compute_logical_state_digests(self.session)
        poll = summary.poll_report
        complete = bool(poll and poll.complete)
        if request.dry_run:
            status: RunStatus = "DRY_RUN"
        elif errors:
            status = "FAILED"
        elif not complete:
            status = "INCOMPLETE"
        else:
            status = "SUCCESS"

        replay_identical: bool | None = None
        replay_matches_original: bool | None = None
        if request.replay_of_run_id:
            replay_identical = digests_after == digests_before
            original = self._load_run(request.replay_of_run_id)
            if original is not None:
                recorded = original.get("digests_after") or {}
                replay_matches_original = all(
                    recorded.get(key) == getattr(digests_after, key)
                    for key in ("messages", "links", "events", "tasks", "interviews", "contacts")
                )
            else:
                errors.append("REPLAY_ORIGINAL_NOT_FOUND")
            if replay_identical is not True or replay_matches_original is not True:
                errors.append("REPLAY_LOGICAL_STATE_MISMATCH")
                status = "FAILED"

        result = BoundedIngestionResult(
            run_id=run_id,
            status=status,
            adapter=self.adapter_kind,
            synthetic=self.synthetic,
            mailbox_sha256=fingerprint["mailbox_sha256"],
            mailbox_domain=fingerprint["mailbox_domain"],
            query=request.query,
            provider_query=request.provider_query(),
            window_start=request.window_start.isoformat(),
            window_end=request.window_end.isoformat(),
            cap=request.cap,
            dry_run=request.dry_run,
            run_label=request.run_label,
            replay_of_run_id=request.replay_of_run_id,
            started_at=started.isoformat(),
            finished_at=datetime.datetime.now(datetime.UTC).isoformat(),
            poll=poll,
            complete=complete,
            messages_polled=summary.messages_polled,
            messages_ingested=summary.messages_ingested,
            messages_skipped_duplicate=summary.messages_skipped_duplicate,
            canary_messages=summary.canary_messages,
            review_tasks_created=summary.review_tasks_created,
            lifecycle_transitions=lifecycle_transitions,
            interviews_scheduled=interviews_scheduled,
            unanswered_alerts=unanswered_alerts,
            stale_alerts=stale_alerts,
            digests_before=digests_before,
            digests_after=digests_after,
            replay_identical=replay_identical,
            replay_matches_original=replay_matches_original,
            errors=errors,
            code_identity=dict(self.identity),
        )
        self._record(result)
        return result

    def _record(self, result: BoundedIngestionResult) -> None:
        """Persist the run evidence; a dry run is recorded too (as DRY_RUN) for traceability."""
        audit = AuditLogModel(
            action_type=BOUNDED_RUN_ACTION,
            entity_type="mailbox",
            actor="bounded_ingestion",
            result=result.status,
            external_reference=result.run_id,
            metadata_json=result.audit_metadata(),
        )
        self.session.add(audit)
        self.session.commit()

    def _load_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.session.scalar(
            select(AuditLogModel).where(
                AuditLogModel.action_type == BOUNDED_RUN_ACTION,
                AuditLogModel.external_reference == run_id,
            )
        )
        return dict(row.metadata_json) if row is not None else None

    def replay(
        self, run_id: str, mailbox: str, run_label: str | None = None
    ) -> BoundedIngestionResult:
        """Re-run the exact recorded parameters of a previous run against the same mailbox."""
        original = self._load_run(run_id)
        if original is None:
            raise BoundedIngestionError("REPLAY_RUN_NOT_FOUND")
        if original.get("mailbox_sha256") != mailbox_fingerprint(mailbox)["mailbox_sha256"]:
            raise BoundedIngestionError("REPLAY_MAILBOX_MISMATCH")
        if bool(original.get("synthetic")) != self.synthetic:
            raise BoundedIngestionError("REPLAY_ADAPTER_KIND_MISMATCH")
        request = BoundedIngestionRequest(
            mailbox=mailbox,
            query=str(original["query"]),
            window_start=datetime.datetime.fromisoformat(str(original["window_start"])),
            window_end=datetime.datetime.fromisoformat(str(original["window_end"])),
            cap=int(original["cap"]),
            dry_run=False,
            run_label=run_label or f"replay:{run_id}",
            replay_of_run_id=run_id,
        )
        return self.run(request)

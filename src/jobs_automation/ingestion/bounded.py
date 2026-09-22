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
BOUNDED_AUDIT_SCHEMA_VERSION = 2
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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_iso(value: datetime.datetime) -> str:
    """Canonical, non-secret representation used for replay request matching."""
    return value.astimezone(datetime.UTC).isoformat()


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


def _safe_request_metadata(request: BoundedIngestionRequest) -> dict[str, Any]:
    """Return the persisted replay contract without retaining a mailbox or query string."""
    fingerprint = mailbox_fingerprint(request.mailbox)
    immutable = {
        "mailbox_sha256": fingerprint["mailbox_sha256"],
        "query_sha256": _sha256_text(request.query.strip()),
        "provider_query_sha256": _sha256_text(request.provider_query()),
        "window_start": _utc_iso(request.window_start),
        "window_end": _utc_iso(request.window_end),
        "cap": request.cap,
    }
    request_sha256 = _sha256_text(
        json.dumps(immutable, sort_keys=True, separators=(",", ":"))
    )
    return {
        **immutable,
        "request_sha256": request_sha256,
        "dry_run": request.dry_run,
    }


def _safe_poll_metadata(poll: PollReport | None) -> dict[str, Any] | None:
    """Persist completeness accounting without query text or provider identifiers."""
    if poll is None:
        return None
    return {
        "adapter": poll.adapter,
        "synthetic": poll.synthetic,
        "max_results": poll.max_results,
        "pages_fetched": poll.pages_fetched,
        "listed_count": poll.listed_count,
        "fetched_count": poll.fetched_count,
        "missing_message_count": len(poll.missing_message_ids),
        "truncated_by_cap": poll.truncated_by_cap,
        "complete": poll.complete,
    }


def _safe_error_codes(errors: list[str]) -> list[str]:
    """Map possibly provider-derived error text to fixed, non-sensitive audit categories."""
    codes: set[str] = set()
    for error in errors:
        if error in {"POLL_INCOMPLETE", "INGESTION_ERROR", "LIFECYCLE_PASS_FAILED"}:
            codes.add(error)
        elif error.startswith("poll_incomplete:"):
            codes.add("POLL_INCOMPLETE")
        elif error.startswith("lifecycle_pass_failed:"):
            codes.add("LIFECYCLE_PASS_FAILED")
        elif error.startswith("REPLAY_"):
            codes.add(error.split(":", maxsplit=1)[0])
        else:
            codes.add("INGESTION_ERROR")
    return sorted(codes)


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
    request_sha256: str
    query_sha256: str
    provider_query_sha256: str
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
    application_id_sha256: list[str] = Field(default_factory=list)
    provider_message_id_sha256: list[str] = Field(default_factory=list)

    def audit_metadata(self) -> dict[str, Any]:
        """Secret-free, schema-versioned evidence used for replay and timeline binding.

        The result object can retain a query for its immediate caller, but persistence must
        never retain raw search text, provider query text, message identifiers, application
        identifiers, mailboxes, bodies, or provider exception text.
        """
        return {
            "schema_version": BOUNDED_AUDIT_SCHEMA_VERSION,
            "run_id": self.run_id,
            "status": self.status,
            "adapter": self.adapter,
            "synthetic": self.synthetic,
            "mailbox_sha256": self.mailbox_sha256,
            "mailbox_domain": self.mailbox_domain,
            "request_sha256": self.request_sha256,
            "query_sha256": self.query_sha256,
            "provider_query_sha256": self.provider_query_sha256,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "cap": self.cap,
            "dry_run": self.dry_run,
            "run_label_sha256": _sha256_text(self.run_label) if self.run_label else None,
            "replay_of_run_id": self.replay_of_run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "poll": _safe_poll_metadata(self.poll),
            "complete": self.complete,
            "messages_polled": self.messages_polled,
            "messages_ingested": self.messages_ingested,
            "messages_skipped_duplicate": self.messages_skipped_duplicate,
            "canary_messages": self.canary_messages,
            "review_tasks_created": self.review_tasks_created,
            "lifecycle_transitions": self.lifecycle_transitions,
            "interviews_scheduled": self.interviews_scheduled,
            "unanswered_alerts": self.unanswered_alerts,
            "stale_alerts": self.stale_alerts,
            "digests_before": self.digests_before.model_dump(),
            "digests_after": self.digests_after.model_dump(),
            "replay_identical": self.replay_identical,
            "replay_matches_original": self.replay_matches_original,
            "error_codes": _safe_error_codes(self.errors),
            "code_identity": {
                "git_sha": str(self.code_identity.get("git_sha") or "unknown"),
                "package_version": str(self.code_identity.get("package_version") or "unknown"),
            },
            "application_id_sha256": sorted(set(self.application_id_sha256)),
            "provider_message_id_sha256": sorted(set(self.provider_message_id_sha256)),
        }


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

    @staticmethod
    def _is_canary(message: InboundMessageModel) -> bool:
        return bool((message.headers_json or {}).get("_provider", {}).get("canary"))

    def _batch_messages(self, summary: IngestionSweepSummary) -> list[InboundMessageModel]:
        """Load only durable rows admitted by this exact sweep, in chronological order."""
        message_ids = list(dict.fromkeys(summary.batch_message_ids))
        if not message_ids:
            return []
        messages = self.session.scalars(
            select(InboundMessageModel).where(InboundMessageModel.id.in_(message_ids))
        ).all()
        return sorted(messages, key=lambda message: (message.received_at, str(message.id)))

    def _batch_application_ids(self, message_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not message_ids:
            return set()
        return {
            application_id
            for application_id in self.session.scalars(
                select(MessageLinkModel.application_id)
                .where(
                    MessageLinkModel.inbound_message_id.in_(message_ids),
                    MessageLinkModel.application_id.is_not(None),
                )
                .distinct()
            )
            if application_id is not None
        }

    @staticmethod
    def _digests_match(recorded: Any, observed: LogicalStateDigests) -> bool:
        if not isinstance(recorded, dict):
            return False
        return all(
            recorded.get(key) == getattr(observed, key)
            for key in ("messages", "links", "events", "tasks", "interviews", "contacts")
        ) and recorded.get("counts") == observed.counts

    def run(
        self, request: BoundedIngestionRequest, *, _validated_replay: bool = False
    ) -> BoundedIngestionResult:
        request = request.validated()
        if request.replay_of_run_id is not None and not _validated_replay:
            raise BoundedIngestionError("REPLAY_MUST_USE_REPLAY_API")

        self._verify_mailbox(request)
        started = datetime.datetime.now(datetime.UTC)
        run_id = str(uuid.uuid4())
        fingerprint = mailbox_fingerprint(request.mailbox)
        request_metadata = _safe_request_metadata(request)
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

        batch_messages = self._batch_messages(summary)
        batch_ids = [message.id for message in batch_messages]
        batch_application_ids = self._batch_application_ids(batch_ids)
        genuine_messages = [message for message in batch_messages if not self._is_canary(message)]

        lifecycle_transitions = 0
        interviews_scheduled = 0
        unanswered_alerts = 0
        stale_alerts = 0
        errors = list(summary.errors)
        if not request.dry_run and not errors:
            try:
                lifecycle = LifecycleEngine(self.session)
                for message in genuine_messages:
                    if message.classification == "JOB_ALERT":
                        continue
                    transition = lifecycle.process_message(message)
                    if transition:
                        lifecycle_transitions += 1
                        if transition.interview_scheduled:
                            interviews_scheduled += 1

                genuine_ids = [message.id for message in genuine_messages]
                admitted_application_ids = self._batch_application_ids(genuine_ids)
                admitted_thread_ids = {
                    message.provider_thread_id or message.provider_message_id
                    for message in genuine_messages
                }
                alerts = LifecycleAlertService(self.session)
                unanswered_alerts = len(
                    alerts.check_unanswered_recruiters(thread_ids=admitted_thread_ids)
                )
                stale_alerts = len(
                    alerts.check_stale_applications(application_ids=admitted_application_ids)
                )
                self.session.commit()
            except Exception as exc:  # pragma: no cover - defensive; surfaced as FAILED
                self.session.rollback()
                logger.warning("Bounded lifecycle pass failed with %s", type(exc).__name__)
                errors.append("LIFECYCLE_PASS_FAILED")

        digests_after = compute_logical_state_digests(self.session)
        poll = summary.poll_report
        complete = bool(poll and poll.complete)

        replay_identical: bool | None = None
        replay_matches_original: bool | None = None
        if request.replay_of_run_id:
            replay_identical = digests_after == digests_before
            original = self._load_run(request.replay_of_run_id)
            if original is None:
                errors.append("REPLAY_ORIGINAL_NOT_FOUND")
            elif original.get("schema_version") != BOUNDED_AUDIT_SCHEMA_VERSION:
                errors.append("REPLAY_EVIDENCE_SCHEMA_UNSUPPORTED")
            else:
                replay_matches_original = self._digests_match(
                    original.get("digests_after"), digests_after
                )
            if replay_identical is not True or replay_matches_original is not True:
                errors.append("REPLAY_LOGICAL_STATE_MISMATCH")

        if errors:
            status: RunStatus = "FAILED"
        elif request.dry_run:
            status = "DRY_RUN"
        elif not complete:
            status = "INCOMPLETE"
        else:
            status = "SUCCESS"

        result = BoundedIngestionResult(
            run_id=run_id,
            status=status,
            adapter=self.adapter_kind,
            synthetic=self.synthetic,
            mailbox_sha256=fingerprint["mailbox_sha256"],
            mailbox_domain=fingerprint["mailbox_domain"],
            query=request.query,
            provider_query=request.provider_query(),
            request_sha256=str(request_metadata["request_sha256"]),
            query_sha256=str(request_metadata["query_sha256"]),
            provider_query_sha256=str(request_metadata["provider_query_sha256"]),
            window_start=str(request_metadata["window_start"]),
            window_end=str(request_metadata["window_end"]),
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
            application_id_sha256=sorted(
                _sha256_text(str(application_id)) for application_id in batch_application_ids
            ),
            provider_message_id_sha256=sorted(
                _sha256_text(message.provider_message_id) for message in batch_messages
            ),
        )
        self._record(result)
        return result

    def _record(self, result: BoundedIngestionResult) -> None:
        """Persist the run evidence; a dry run is recorded too (as DRY_RUN) for traceability."""
        audit = AuditLogModel(
            action_type=BOUNDED_RUN_ACTION,
            entity_type="mailbox",
            actor="bounded_ingestion",
            input_hash=result.request_sha256,
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
        self,
        run_id: str,
        request: BoundedIngestionRequest,
        *,
        allow_stateful_replay: bool = False,
        run_label: str | None = None,
    ) -> BoundedIngestionResult:
        """Replay a caller-supplied request only when it matches safe recorded evidence.

        The caller supplies the complete request because raw query text is intentionally
        absent from the audit row.  A stateful replay needs an explicit authorization;
        a recorded dry-run is permanently replayed as dry-run even if a caller asks to
        apply it.
        """
        request = request.validated()
        original = self._load_run(run_id)
        if original is None:
            raise BoundedIngestionError("REPLAY_RUN_NOT_FOUND")
        required = {
            "schema_version",
            "mailbox_sha256",
            "query_sha256",
            "provider_query_sha256",
            "window_start",
            "window_end",
            "cap",
            "dry_run",
            "request_sha256",
        }
        if original.get("schema_version") != BOUNDED_AUDIT_SCHEMA_VERSION or not required.issubset(
            original
        ):
            raise BoundedIngestionError("REPLAY_EVIDENCE_SCHEMA_UNSUPPORTED")
        expected = _safe_request_metadata(request)
        if original.get("mailbox_sha256") != expected["mailbox_sha256"]:
            raise BoundedIngestionError("REPLAY_MAILBOX_MISMATCH")
        if original.get("adapter") != self.adapter_kind or bool(original.get("synthetic")) != self.synthetic:
            raise BoundedIngestionError("REPLAY_ADAPTER_KIND_MISMATCH")
        if any(
            original.get(field) != expected[field]
            for field in (
                "query_sha256",
                "provider_query_sha256",
                "window_start",
                "window_end",
                "cap",
                "request_sha256",
            )
        ):
            raise BoundedIngestionError("REPLAY_REQUEST_MISMATCH")
        if not isinstance(original.get("dry_run"), bool):
            raise BoundedIngestionError("REPLAY_EVIDENCE_SCHEMA_UNSUPPORTED")

        recorded_dry_run = bool(original["dry_run"])
        effective_dry_run = True if recorded_dry_run else request.dry_run
        if not effective_dry_run and not allow_stateful_replay:
            raise BoundedIngestionError("REPLAY_STATEFUL_REQUIRES_EXPLICIT_AUTHORIZATION")
        replay_request = request.model_copy(
            update={
                "dry_run": effective_dry_run,
                "run_label": run_label or request.run_label or f"replay:{run_id}",
                "replay_of_run_id": run_id,
            }
        )
        return self.run(replay_request, _validated_replay=True)

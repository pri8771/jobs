"""Follow-up reminders, unanswered recruiter alerts, and stale application monitoring."""

from __future__ import annotations

import datetime
import logging
import uuid
from collections.abc import Collection

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    InboundMessageModel,
    MessageLinkModel,
    TaskModel,
)

logger = logging.getLogger(__name__)


# Keep this in lockstep with the task provenance fields redacted by the V1.7
# timeline export.  A task that names durable canary evidence in any of these
# fields is historical reconciliation work: do not silently update, resolve,
# cancel, or reuse it for genuine traffic in the same provider thread.
_TASK_MESSAGE_PROVENANCE_KEYS = (
    "provider_message_id",
    "source_message_id",
    "message_id",
    "latest_message_id",
    "resolved_by_reply_id",
    "inbound_message_id",
)


class LifecycleAlertService:
    """Detects unanswered recruiter outreach and stale application pipelines with lifecycle-aware closure."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _is_canary(message: InboundMessageModel) -> bool:
        """Return whether durable provider metadata marks a message as test traffic."""
        provider_metadata = (message.headers_json or {}).get("_provider")
        return isinstance(provider_metadata, dict) and bool(provider_metadata.get("canary"))

    def _durable_canary_message_references(self) -> set[str]:
        """Return UUID and provider-id forms of all currently durable canaries.

        Alert tasks may have been created before a source message was reclassified.
        Resolve against persisted, durable marks rather than the current candidate
        thread so a later genuine message cannot mutate that historical task.
        """
        canary_messages = (
            message
            for message in self.session.scalars(select(InboundMessageModel)).all()
            if self._is_canary(message)
        )
        references: set[str] = set()
        for message in canary_messages:
            references.add(str(message.id))
            if message.provider_message_id:
                references.add(str(message.provider_message_id))
        return references

    @staticmethod
    def _task_references_durable_canary(task: TaskModel, references: Collection[str]) -> bool:
        """Whether a task carries historical durable-canary source provenance."""
        if not references:
            return False
        payload = task.payload_json if isinstance(task.payload_json, dict) else {}
        return any(
            str(reference) in references
            for key in _TASK_MESSAGE_PROVENANCE_KEYS
            if (reference := payload.get(key)) is not None
        )

    def _applications_with_canary_lifecycle_provenance(
        self, application_ids: Collection[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Return applications whose historical state needs canary reconciliation.

        A stale-state reminder is itself a product action. If a prior untagged message
        was later reclassified as canary, do not create a new reminder from that
        potentially contaminated state. Existing historical rows are left intact for
        explicit reconciliation rather than silently rewritten.
        """
        candidate_ids = set(application_ids)
        if not candidate_ids:
            return set()
        canary_messages = [
            message
            for message in self.session.scalars(select(InboundMessageModel)).all()
            if self._is_canary(message)
        ]
        if not canary_messages:
            return set()
        canary_message_ids = {message.id for message in canary_messages}
        canary_provider_ids = {message.provider_message_id for message in canary_messages}
        linked_applications = {
            application_id
            for application_id in self.session.scalars(
                select(MessageLinkModel.application_id).where(
                    MessageLinkModel.application_id.in_(candidate_ids),
                    MessageLinkModel.inbound_message_id.in_(canary_message_ids),
                )
            )
            if application_id is not None
        }
        event_applications = {
            application_id
            for application_id in self.session.scalars(
                select(ApplicationEventModel.application_id).where(
                    ApplicationEventModel.application_id.in_(candidate_ids),
                    ApplicationEventModel.source_reference.in_(canary_provider_ids),
                )
            )
            if application_id is not None
        }
        return linked_applications | event_applications

    def check_unanswered_recruiters(
        self,
        window_hours: int = 48,
        now: datetime.datetime | None = None,
        *,
        thread_ids: Collection[str] | None = None,
    ) -> list[TaskModel]:
        """Flags recruiter emails that have gone unanswered by the candidate beyond window_hours,

        and automatically closes/resolves stale pending tasks when a candidate reply arrives.

        ``thread_ids`` limits processing to threads explicitly admitted by a bounded
        ingestion batch. ``None`` preserves the worker's full-mailbox behavior; an
        empty collection processes no threads. Canary evidence is ignored in every
        mode, including the unscoped worker pass.
        """
        if now is None:
            now = utc_now()

        cutoff = now - datetime.timedelta(hours=window_hours)

        recruiter_classes = (
            "RECRUITER_OUTREACH",
            "RECRUITER_FOLLOW_UP",
            "SCREENING_REQUEST",
            "INTERVIEW_REQUEST",
        )

        # 1. Gather all active recruiter threads
        inbound_stmt = (
            select(InboundMessageModel)
            .where(
                InboundMessageModel.direction == "inbound",
                InboundMessageModel.classification.in_(recruiter_classes),
            )
            .order_by(InboundMessageModel.received_at.asc())
        )
        if thread_ids is not None:
            inbound_stmt = inbound_stmt.where(
                func.coalesce(
                    InboundMessageModel.provider_thread_id,
                    InboundMessageModel.provider_message_id,
                ).in_(thread_ids)
            )
        all_inbound = self.session.scalars(inbound_stmt).all()
        canary_message_references = self._durable_canary_message_references()

        # Group by thread
        threads: dict[str, list[InboundMessageModel]] = {}
        for msg in all_inbound:
            if self._is_canary(msg):
                continue
            thread_id = msg.provider_thread_id or msg.provider_message_id
            threads.setdefault(thread_id, []).append(msg)

        created_tasks: list[TaskModel] = []

        for thread_id, in_msgs in threads.items():
            latest_inbound = in_msgs[-1]

            # Find latest outbound reply in this thread
            reply_stmt = (
                select(InboundMessageModel)
                .where(
                    InboundMessageModel.provider_thread_id == thread_id,
                    InboundMessageModel.direction == "outbound",
                )
                .order_by(InboundMessageModel.received_at.desc())
            )
            latest_reply = next(
                (
                    reply
                    for reply in self.session.scalars(reply_stmt)
                    if not self._is_canary(reply)
                ),
                None,
            )

            # Check if reply is AFTER the latest inbound recruiter message
            has_valid_reply = (
                latest_reply is not None and latest_reply.received_at >= latest_inbound.received_at
            )

            # Query any existing pending tasks for this thread or message
            existing_tasks_stmt = select(TaskModel).where(
                TaskModel.task_type == "UNANSWERED_RECRUITER",
                TaskModel.status == "pending",
            )
            all_pending = self.session.scalars(existing_tasks_stmt).all()
            thread_pending_tasks = [
                t
                for t in all_pending
                if not self._task_references_durable_canary(t, canary_message_references)
                and (
                    (t.payload_json or {}).get("thread_id") == thread_id
                    or (t.payload_json or {}).get("message_id")
                    in [str(m.id) for m in in_msgs]
                )
            ]

            if has_valid_reply:
                # Candidate replied! Auto-resolve/close any pending unanswered alert tasks for this thread
                for task in thread_pending_tasks:
                    task.status = "completed"
                    updated_payload = dict(task.payload_json)
                    updated_payload["resolved_by_reply_id"] = (
                        str(latest_reply.id) if latest_reply else None
                    )
                    updated_payload["resolved_at"] = now.isoformat()
                    updated_payload["resolution_notes"] = (
                        f"Candidate replied via message {latest_reply.provider_message_id if latest_reply else ''}."
                    )
                    task.payload_json = updated_payload
                    logger.info("Resolved pending UNANSWERED_RECRUITER task %s due to candidate reply", task.id)
            else:
                # No valid reply yet. Has the latest recruiter message crossed the unanswered cutoff?
                if latest_inbound.received_at <= cutoff:
                    if thread_pending_tasks:
                        # Task already pending; update with latest message reference if needed, do not duplicate
                        existing_task = thread_pending_tasks[0]
                        updated_payload = dict(existing_task.payload_json)
                        updated_payload["latest_message_id"] = str(latest_inbound.id)
                        updated_payload["latest_subject"] = latest_inbound.subject
                        updated_payload["latest_received_at"] = latest_inbound.received_at.isoformat()
                        existing_task.payload_json = updated_payload
                    else:
                        # Check if a completed/cancelled task already exists for this exact message
                        exact_existing = [
                            t
                            for t in self.session.scalars(
                                select(TaskModel).where(
                                    TaskModel.task_type == "UNANSWERED_RECRUITER"
                                )
                            ).all()
                            if not self._task_references_durable_canary(
                                t, canary_message_references
                            )
                            and (t.payload_json or {}).get("message_id")
                            == str(latest_inbound.id)
                        ]
                        if not exact_existing:
                            task = TaskModel(
                                task_type="UNANSWERED_RECRUITER",
                                due_at=now,
                                status="pending",
                                payload_json={
                                    "thread_id": thread_id,
                                    "message_id": str(latest_inbound.id),
                                    "provider_message_id": latest_inbound.provider_message_id,
                                    "sender": latest_inbound.sender,
                                    "subject": latest_inbound.subject,
                                    "received_at": latest_inbound.received_at.isoformat(),
                                    "reason": f"Recruiter message from {latest_inbound.sender} has not been answered in {window_hours}h.",
                                },
                            )
                            self.session.add(task)
                            created_tasks.append(task)

        self.session.flush()
        return created_tasks

    def check_stale_applications(
        self,
        stale_days: int = 14,
        now: datetime.datetime | None = None,
        screening_stale_days: int = 21,
        *,
        application_ids: Collection[uuid.UUID] | None = None,
    ) -> list[TaskModel]:
        """Detects applications with no activity after stale_days without spamming follow-ups."""
        if now is None:
            now = utc_now()

        cutoff_submitted = now - datetime.timedelta(days=stale_days)
        cutoff_screening = now - datetime.timedelta(days=screening_stale_days)

        created_tasks: list[TaskModel] = []

        # 1. Submitted & Confirmed applications
        stmt = select(ApplicationModel).where(
            ApplicationModel.status.in_(("SUBMITTED", "CONFIRMED")),
            ApplicationModel.last_activity_at <= cutoff_submitted,
        )
        if application_ids is not None:
            stmt = stmt.where(ApplicationModel.id.in_(application_ids))
        apps = self.session.scalars(stmt).all()

        # 2. Screening stage with prolonged silence
        stmt_screening = select(ApplicationModel).where(
            ApplicationModel.status == "SCREENING",
            ApplicationModel.last_activity_at <= cutoff_screening,
        )
        if application_ids is not None:
            stmt_screening = stmt_screening.where(ApplicationModel.id.in_(application_ids))
        screening_apps = self.session.scalars(stmt_screening).all()

        contaminated_application_ids = self._applications_with_canary_lifecycle_provenance(
            [app.id for app in [*apps, *screening_apps]]
        )

        for app in apps:
            if app.id in contaminated_application_ids:
                continue
            existing = self.session.scalar(
                select(TaskModel).where(
                    TaskModel.task_type == "STALE_APPLICATION_FOLLOW_UP",
                    TaskModel.application_id == app.id,
                    TaskModel.status == "pending",
                )
            )
            if not existing:
                job_title = app.job.normalized_title if app.job else "Unknown Job"
                co_name = app.job.company_name if app.job else "Unknown Company"
                task = TaskModel(
                    application_id=app.id,
                    job_id=app.job_id,
                    task_type="STALE_APPLICATION_FOLLOW_UP",
                    due_at=now,
                    status="pending",
                    payload_json={
                        "application_id": str(app.id),
                        "job_title": job_title,
                        "company_name": co_name,
                        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                        "reason": f"Application to {job_title} at {co_name} has had no response in {stale_days} days.",
                    },
                )
                self.session.add(task)
                created_tasks.append(task)

        for app in screening_apps:
            if app.id in contaminated_application_ids:
                continue
            existing = self.session.scalar(
                select(TaskModel).where(
                    TaskModel.task_type == "STALE_SCREENING_FOLLOW_UP",
                    TaskModel.application_id == app.id,
                    TaskModel.status == "pending",
                )
            )
            if not existing:
                job_title = app.job.normalized_title if app.job else "Unknown Job"
                co_name = app.job.company_name if app.job else "Unknown Company"
                task = TaskModel(
                    application_id=app.id,
                    job_id=app.job_id,
                    task_type="STALE_SCREENING_FOLLOW_UP",
                    due_at=now,
                    status="pending",
                    payload_json={
                        "application_id": str(app.id),
                        "job_title": job_title,
                        "company_name": co_name,
                        "stage": "SCREENING",
                        "reason": f"Screening conversation for {job_title} at {co_name} has had no activity in {screening_stale_days} days.",
                    },
                )
                self.session.add(task)
                created_tasks.append(task)

        self.session.flush()
        return created_tasks

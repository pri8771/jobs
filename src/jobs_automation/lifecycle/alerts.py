"""Follow-up reminders, unanswered recruiter alerts, and stale application monitoring."""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import ApplicationModel, InboundMessageModel, TaskModel

logger = logging.getLogger(__name__)


class LifecycleAlertService:
    """Detects unanswered recruiter outreach and stale application pipelines with lifecycle-aware closure."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def check_unanswered_recruiters(
        self,
        window_hours: int = 48,
        now: datetime.datetime | None = None,
    ) -> list[TaskModel]:
        """Flags recruiter emails that have gone unanswered by the candidate beyond window_hours,

        and automatically closes/resolves stale pending tasks when a candidate reply arrives.
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
        all_inbound = self.session.scalars(inbound_stmt).all()

        # Group by thread
        threads: dict[str, list[InboundMessageModel]] = {}
        for msg in all_inbound:
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
            latest_reply = self.session.scalars(reply_stmt).first()

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
                if t.payload_json.get("thread_id") == thread_id
                or t.payload_json.get("message_id")
                in [str(m.id) for m in in_msgs]
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
                            if t.payload_json.get("message_id") == str(latest_inbound.id)
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
        apps = self.session.scalars(stmt).all()

        for app in apps:
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

        # 2. Screening stage with prolonged silence
        stmt_screening = select(ApplicationModel).where(
            ApplicationModel.status == "SCREENING",
            ApplicationModel.last_activity_at <= cutoff_screening,
        )
        screening_apps = self.session.scalars(stmt_screening).all()

        for app in screening_apps:
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

"""Follow-up reminders, unanswered recruiter alerts, and stale application monitoring."""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import ApplicationModel, InboundMessageModel, TaskModel


class LifecycleAlertService:
    """Detects unanswered recruiter outreach and stale application pipelines."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def check_unanswered_recruiters(
        self,
        window_hours: int = 48,
        now: datetime.datetime | None = None,
    ) -> list[TaskModel]:
        """Flags recruiter emails that have gone unanswered by the candidate beyond window_hours."""
        if now is None:
            now = utc_now()

        cutoff = now - datetime.timedelta(hours=window_hours)

        # Find threads with inbound recruiter messages older than cutoff
        recruiter_classes = (
            "RECRUITER_OUTREACH",
            "SCREENING_REQUEST",
            "INTERVIEW_REQUEST",
        )
        stmt = (
            select(InboundMessageModel)
            .where(
                InboundMessageModel.direction == "inbound",
                InboundMessageModel.classification.in_(recruiter_classes),
                InboundMessageModel.received_at <= cutoff,
            )
            .order_by(InboundMessageModel.received_at.desc())
        )
        messages = self.session.scalars(stmt).all()

        created_tasks: list[TaskModel] = []
        for msg in messages:
            # Check if there is an outbound reply in this thread
            reply_stmt = select(InboundMessageModel).where(
                InboundMessageModel.provider_thread_id == msg.provider_thread_id,
                InboundMessageModel.direction == "outbound",
                InboundMessageModel.received_at >= msg.received_at,
            )
            reply = self.session.scalar(reply_stmt)
            if not reply:
                # Check if task already exists for this message
                existing_task = self.session.scalar(
                    select(TaskModel).where(
                        TaskModel.task_type == "UNANSWERED_RECRUITER",
                        TaskModel.payload_json["message_id"].as_string() == str(msg.id),
                    )
                )
                if not existing_task:
                    task = TaskModel(
                        task_type="UNANSWERED_RECRUITER",
                        due_at=now,
                        status="pending",
                        payload_json={
                            "message_id": str(msg.id),
                            "sender": msg.sender,
                            "subject": msg.subject,
                            "received_at": msg.received_at.isoformat(),
                            "reason": f"Recruiter message from {msg.sender} has not been answered in {window_hours}h.",
                        },
                    )
                    self.session.add(task)
                    created_tasks.append(task)

        return created_tasks

    def check_stale_applications(
        self,
        stale_days: int = 14,
        now: datetime.datetime | None = None,
    ) -> list[TaskModel]:
        """Detects submitted applications with no activity after stale_days."""
        if now is None:
            now = utc_now()

        cutoff = now - datetime.timedelta(days=stale_days)

        active_statuses = ("SUBMITTED", "CONFIRMED")
        stmt = select(ApplicationModel).where(
            ApplicationModel.status.in_(active_statuses),
            ApplicationModel.last_activity_at <= cutoff,
        )
        apps = self.session.scalars(stmt).all()

        created_tasks: list[TaskModel] = []
        for app in apps:
            existing = self.session.scalar(
                select(TaskModel).where(
                    TaskModel.task_type == "STALE_APPLICATION_FOLLOW_UP",
                    TaskModel.application_id == app.id,
                    TaskModel.status == "pending",
                )
            )
            if not existing:
                job_title = app.job.title if app.job else "Unknown Job"
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

        return created_tasks

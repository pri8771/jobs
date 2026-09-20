"""Email ingestion engine coordinating polling, classification, deduplication, and checkpointing."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    TaskModel,
)
from jobs_automation.ingestion.classifier import EmailClassifier
from jobs_automation.ingestion.deduplication import JobDeduplicationService, normalize_string
from jobs_automation.ingestion.models import EmailClassification
from jobs_automation.ingestion.parsers import AlertParserRegistry


class IngestionSweepSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime.datetime
    completed_at: datetime.datetime
    messages_polled: int = 0
    messages_ingested: int = 0
    messages_skipped_duplicate: int = 0
    jobs_discovered_new: int = 0
    jobs_updated_existing: int = 0
    review_tasks_created: int = 0
    checkpoint_advanced_to: str | None = None
    is_reconciliation: bool = False
    errors: list[str] = Field(default_factory=list)


class EmailIngestionEngine:
    """Orchestrates periodic Gmail polling, message classification, job parsing,

    recruiter thread tracking, and incremental mailbox checkpointing.
    """

    def __init__(
        self,
        session: Session,
        adapter: EmailAdapter,
        candidate_emails: list[str] | None = None,
        safety_overlap_minutes: int = 15,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.classifier = EmailClassifier(candidate_emails=candidate_emails)
        self.parser_registry = AlertParserRegistry()
        self.dedup_service = JobDeduplicationService(session)
        self.safety_overlap_minutes = safety_overlap_minutes

    def get_last_checkpoint(self) -> datetime.datetime | None:
        stmt = (
            select(TaskModel)
            .where(TaskModel.task_type == "email_checkpoint")
            .order_by(TaskModel.due_at.desc())
        )
        task = self.session.execute(stmt).scalars().first()
        if task and task.due_at:
            return task.due_at
        return None

    def save_checkpoint(self, checkpoint_time: datetime.datetime) -> None:
        task = TaskModel(
            task_type="email_checkpoint",
            due_at=checkpoint_time,
            status="completed",
            payload_json={"checkpoint_utc": checkpoint_time.isoformat()},
        )
        self.session.add(task)
        self.session.flush()

    def run_sweep(
        self,
        reconcile: bool = False,
        query: str | None = None,
        max_messages: int = 200,
    ) -> IngestionSweepSummary:
        start_time = datetime.datetime.now(datetime.UTC)
        summary = IngestionSweepSummary(
            started_at=start_time,
            completed_at=start_time,
            is_reconciliation=reconcile,
        )

        last_checkpoint = self.get_last_checkpoint()
        since_dt: datetime.datetime | None = None

        if reconcile:
            # Look back 48 hours for full reconciliation pass
            since_dt = start_time - datetime.timedelta(hours=48)
        elif last_checkpoint:
            # Overlap window to prevent missed messages
            since_dt = last_checkpoint - datetime.timedelta(minutes=self.safety_overlap_minutes)

        since_str = since_dt.isoformat() if since_dt else None

        try:
            raw_messages = self.adapter.poll_messages(
                query=query,
                since_timestamp=since_str,
                max_results=max_messages,
            )
            summary.messages_polled = len(raw_messages)

            # Sort by received_at ascending to process chronologically
            raw_messages.sort(key=lambda m: m.received_at)

            newest_processed_time: datetime.datetime | None = last_checkpoint

            for raw_msg in raw_messages:
                # 1. Deduplication on provider_message_id
                existing_stmt = select(InboundMessageModel).where(
                    InboundMessageModel.provider_message_id == raw_msg.provider_message_id
                )
                if self.session.execute(existing_stmt).scalars().first():
                    summary.messages_skipped_duplicate += 1
                    continue

                # 2. Classify message
                classification_res = self.classifier.classify(raw_msg)

                # 3. Insert into inbound_message
                msg_model = InboundMessageModel(
                    provider_message_id=raw_msg.provider_message_id,
                    provider_thread_id=raw_msg.provider_thread_id or raw_msg.provider_message_id,
                    received_at=raw_msg.received_at,
                    sender=raw_msg.sender,
                    recipients_json=raw_msg.recipients,
                    direction=classification_res.direction,
                    subject=raw_msg.subject,
                    headers_json=raw_msg.headers,
                    body_text=raw_msg.body_text,
                    body_html_hash=None,
                    classification=classification_res.classification.value,
                    confidence=classification_res.confidence,
                    raw_reference=raw_msg.raw_reference,
                )
                self.session.add(msg_model)
                self.session.flush()
                summary.messages_ingested += 1

                # Update latest processed time
                if newest_processed_time is None or raw_msg.received_at > newest_processed_time:
                    newest_processed_time = raw_msg.received_at

                # 4. Handle Job Alerts
                if classification_res.classification == EmailClassification.JOB_ALERT:
                    postings = self.parser_registry.parse_alert_email(raw_msg)
                    for posting in postings:
                        job, is_new = self.dedup_service.ingest_posting(
                            posting, raw_msg.received_at
                        )
                        if is_new:
                            summary.jobs_discovered_new += 1
                        else:
                            summary.jobs_updated_existing += 1

                        # Link message to job
                        link = MessageLinkModel(
                            inbound_message_id=msg_model.id,
                            job_id=job.id,
                            company_id=job.company_id,
                            confidence=0.95,
                            method="alert_parser",
                        )
                        self.session.add(link)

                # 5. Handle Recruiting / Application lifecycle messages
                elif classification_res.classification in {
                    EmailClassification.APPLICATION_CONFIRMATION,
                    EmailClassification.INTERVIEW_REQUEST,
                    EmailClassification.INTERVIEW_CONFIRMATION,
                    EmailClassification.REJECTION,
                    EmailClassification.OFFER,
                    EmailClassification.RECRUITER_OUTREACH,
                }:
                    self._link_recruiting_message(msg_model, classification_res, summary)

                # 6. Ambiguous / Review required
                elif classification_res.needs_review:
                    task = TaskModel(
                        task_type="NEEDS_REVIEW",
                        status="pending",
                        payload_json={
                            "reason": classification_res.review_reason,
                            "provider_message_id": raw_msg.provider_message_id,
                            "subject": raw_msg.subject,
                            "sender": raw_msg.sender,
                        },
                    )
                    self.session.add(task)
                    summary.review_tasks_created += 1

            # 7. Advance checkpoint ONLY if sweep completed without exceptions
            if newest_processed_time and not reconcile:
                self.save_checkpoint(newest_processed_time)
                summary.checkpoint_advanced_to = newest_processed_time.isoformat()

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            summary.errors.append(str(e))

        summary.completed_at = datetime.datetime.now(datetime.UTC)
        return summary

    def _link_recruiting_message(
        self,
        msg: InboundMessageModel,
        res: Any,
        summary: IngestionSweepSummary,
    ) -> None:
        """Link recruiting lifecycle email to company and active application if found."""
        company_name = res.company_hint
        if not company_name:
            return

        norm_co = normalize_string(company_name)
        co_stmt = select(CompanyModel).where(func.lower(CompanyModel.normalized_name) == norm_co)
        company = self.session.execute(co_stmt).scalars().first()

        if not company:
            return

        # Check for active application with this company
        app_stmt = (
            select(ApplicationModel)
            .join(JobModel, ApplicationModel.job_id == JobModel.id)
            .where(JobModel.company_id == company.id)
            .order_by(ApplicationModel.last_activity_at.desc())
        )
        apps = self.session.execute(app_stmt).scalars().all()

        if len(apps) == 1:
            app = apps[0]
            link = MessageLinkModel(
                inbound_message_id=msg.id,
                job_id=app.job_id,
                application_id=app.id,
                company_id=company.id,
                confidence=res.confidence,
                method="company_match",
            )
            self.session.add(link)
            app.last_activity_at = msg.received_at
        elif len(apps) > 1:
            # Ambiguous: multiple applications with the same company -> NEEDS_REVIEW
            task = TaskModel(
                application_id=None,
                task_type="NEEDS_REVIEW",
                status="pending",
                payload_json={
                    "reason": f"Ambiguous application link: {len(apps)} plausible applications for {company_name}",
                    "inbound_message_id": str(msg.id),
                    "provider_message_id": msg.provider_message_id,
                },
            )
            self.session.add(task)
            summary.review_tasks_created += 1

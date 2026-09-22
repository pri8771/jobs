"""Email ingestion engine coordinating polling, classification, deduplication, and checkpointing."""

from __future__ import annotations

import datetime
import logging
import uuid
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
from jobs_automation.ingestion.models import EmailClassification, PollReport
from jobs_automation.ingestion.parsers import AlertParserRegistry

logger = logging.getLogger(__name__)


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
    checkpoint_held_reason: str | None = None
    poll_report: PollReport | None = None
    canary_messages: int = 0
    is_reconciliation: bool = False
    is_dry_run: bool = False
    errors: list[str] = Field(default_factory=list)
    # Internal membership for downstream bounded work, including replay duplicates.
    batch_message_ids: list[uuid.UUID] = Field(default_factory=list, exclude=True)


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
        canary_identities: list[str] | None = None,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.classifier = EmailClassifier(candidate_emails=candidate_emails)
        self.parser_registry = AlertParserRegistry()
        self.dedup_service = JobDeduplicationService(session)
        self.safety_overlap_minutes = safety_overlap_minutes
        # Owner-controlled test aliases: their mail is ingested but tagged as canary so it
        # never counts as genuine recruiting evidence (V17-M04).
        self.canary_identities = {
            identity.strip().lower() for identity in (canary_identities or []) if identity.strip()
        }

    def _is_canary(self, raw_msg: Any) -> bool:
        if not self.canary_identities:
            return False
        participants = {str(raw_msg.sender).lower()} | {str(r).lower() for r in raw_msg.recipients}
        sender_address = str((raw_msg.provider_metadata or {}).get("sender_address") or "").lower()
        if sender_address:
            participants.add(sender_address)
        return any(
            identity in participant
            for identity in self.canary_identities
            for participant in participants
        )

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

    def save_checkpoint(
        self,
        checkpoint_time: datetime.datetime,
        poll_report: PollReport | None = None,
        ingested_count: int | None = None,
    ) -> None:
        """Persist the checkpoint together with the query/window/count/completeness it rests on."""
        payload: dict[str, Any] = {"checkpoint_utc": checkpoint_time.isoformat()}
        if poll_report is not None:
            payload.update(
                {
                    "query": poll_report.query,
                    "since_timestamp": poll_report.since_timestamp,
                    "max_results": poll_report.max_results,
                    "pages_fetched": poll_report.pages_fetched,
                    "listed_count": poll_report.listed_count,
                    "fetched_count": poll_report.fetched_count,
                    "complete": poll_report.complete,
                    "adapter": poll_report.adapter,
                }
            )
        if ingested_count is not None:
            payload["ingested_count"] = ingested_count
        task = TaskModel(
            task_type="email_checkpoint",
            due_at=checkpoint_time,
            status="completed",
            payload_json=payload,
        )
        self.session.add(task)
        self.session.flush()

    def run_sweep(
        self,
        reconcile: bool = False,
        query: str | None = None,
        max_messages: int = 200,
        dry_run: bool = False,
        since_override: datetime.datetime | None = None,
        advance_checkpoint: bool = True,
    ) -> IngestionSweepSummary:
        """Poll, classify, persist and (when complete) checkpoint one sweep.

        ``since_override`` replaces the checkpoint-derived lower bound (bounded runs);
        ``advance_checkpoint=False`` keeps the incremental checkpoint untouched, which a
        bounded canary run must do so it can never move the worker's checkpoint past
        evidence it did not cover.
        """
        start_time = datetime.datetime.now(datetime.UTC)
        summary = IngestionSweepSummary(
            started_at=start_time,
            completed_at=start_time,
            is_reconciliation=reconcile,
            is_dry_run=dry_run,
        )

        last_checkpoint = self.get_last_checkpoint()
        since_dt: datetime.datetime | None = None

        if since_override is not None:
            since_dt = since_override
        elif reconcile:
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
            summary.poll_report = self.adapter.last_poll_report()
            if summary.poll_report is not None and summary.poll_report.missing_message_ids:
                # A listed message that could not be fetched invalidates the whole
                # sweep. Stop before classification or writes; the existing error
                # path rolls back and allows the overlap window to retry it.
                summary.checkpoint_held_reason = (
                    "poll_incomplete: "
                    f"missing_messages={len(summary.poll_report.missing_message_ids)}"
                )
                raise RuntimeError(summary.checkpoint_held_reason)

            # Sort by received_at ascending to process chronologically
            raw_messages.sort(key=lambda m: m.received_at)

            newest_processed_time: datetime.datetime | None = last_checkpoint

            for raw_msg in raw_messages:
                # 1. Deduplication on provider_message_id
                existing_stmt = select(InboundMessageModel).where(
                    InboundMessageModel.provider_message_id == raw_msg.provider_message_id
                )
                existing = self.session.execute(existing_stmt).scalars().first()
                if existing is not None:
                    summary.batch_message_ids.append(existing.id)
                    summary.messages_skipped_duplicate += 1
                    continue

                # 2. Classify message
                classification_res = self.classifier.classify(raw_msg)

                # 3. Insert into inbound_message. Provider facts (label ids, provider time,
                # claimed Date, direction basis, canary tag) travel under headers_json["_provider"]
                # so the claimed headers and the provider-observed facts stay distinguishable.
                headers_json: dict[str, Any] = dict(raw_msg.headers)
                provider_facts: dict[str, Any] = dict(raw_msg.provider_metadata or {})
                is_canary = self._is_canary(raw_msg)
                if is_canary:
                    provider_facts["canary"] = True
                    summary.canary_messages += 1
                if provider_facts:
                    headers_json["_provider"] = provider_facts
                msg_model = InboundMessageModel(
                    provider_message_id=raw_msg.provider_message_id,
                    provider_thread_id=raw_msg.provider_thread_id or raw_msg.provider_message_id,
                    received_at=raw_msg.received_at,
                    sender=raw_msg.sender,
                    recipients_json=raw_msg.recipients,
                    direction=classification_res.direction,
                    subject=raw_msg.subject,
                    headers_json=headers_json,
                    body_text=raw_msg.body_text,
                    body_html_hash=None,
                    classification=classification_res.classification.value,
                    confidence=classification_res.confidence,
                    raw_reference=raw_msg.raw_reference,
                )
                self.session.add(msg_model)
                self.session.flush()
                summary.messages_ingested += 1
                summary.batch_message_ids.append(msg_model.id)

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

            # 7. Advance checkpoint ONLY if the sweep completed without exceptions, the poll
            # was complete (every listed message fetched, no cap truncation), the run is
            # not a dry run, not a reconciliation and not a bounded run.
            poll_report = summary.poll_report
            if dry_run:
                self.session.rollback()
                summary.checkpoint_advanced_to = None
                logger.info(
                    "Dry-run sweep completed: session changes rolled back, zero rows persisted to database."
                )
            else:
                if poll_report is not None and not poll_report.complete:
                    summary.checkpoint_held_reason = (
                        "poll_incomplete: "
                        f"truncated_by_cap={poll_report.truncated_by_cap}, "
                        f"missing_messages={len(poll_report.missing_message_ids)}"
                    )
                    logger.warning(
                        "Checkpoint held at %s: %s",
                        last_checkpoint.isoformat() if last_checkpoint else None,
                        summary.checkpoint_held_reason,
                    )
                elif not advance_checkpoint:
                    summary.checkpoint_held_reason = "bounded_run_does_not_advance_checkpoint"
                elif newest_processed_time and not reconcile:
                    self.save_checkpoint(
                        newest_processed_time,
                        poll_report=poll_report,
                        ingested_count=summary.messages_ingested,
                    )
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

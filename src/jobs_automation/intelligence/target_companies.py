"""TargetCompanyService — management and relationship signal generation for target companies."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    ContactModel,
    JobModel,
    MessageLinkModel,
    TargetCompanyModel,
    TargetCompanyObservationModel,
)
from jobs_automation.ingestion.deduplication import JobDeduplicationService
from jobs_automation.intelligence.envelope import DerivedArtifactEnvelope, EvidenceRef
from jobs_automation.intelligence.opportunity_graph import OpportunityGraphService


class RelationshipSignal(DerivedArtifactEnvelope):
    artifact_type: Literal["relationship_signal"] = "relationship_signal"
    known_contacts: list[EvidenceRef] = Field(default_factory=list)
    prior_applications: list[EvidenceRef] = Field(default_factory=list)
    prior_responses: bool = False
    referral_paths: list[EvidenceRef] = Field(default_factory=list)


class TargetCompanyService:
    """Service for managing target company watchlists and computing relationship signals."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.dedupe_service = JobDeduplicationService(session)
        self.opp_graph_service = OpportunityGraphService(session)

    def add(
        self,
        canonical_name: str,
        domain: str | None = None,
        priority: int = 3,
        reason: str | None = None,
        role_families: list[str] | None = None,
        compensation_floor: float | None = None,
        location_constraints: dict[str, Any] | None = None,
        source_config: dict[str, Any] | None = None,
    ) -> TargetCompanyModel:
        """Add a target company. Watch status stays PAUSED initially."""
        company = self.dedupe_service.get_or_create_company(canonical_name, domain)

        target = TargetCompanyModel(
            company_id=company.id,
            canonical_name=canonical_name,
            domain=domain or company.domain,
            priority=priority,
            reason=reason,
            target_role_families=role_families or [],
            compensation_floor=compensation_floor,
            location_constraints=location_constraints or {},
            watch_status="PAUSED",
            source_config=source_config or {},
        )
        self.session.add(target)
        self.session.flush()
        return target

    def list(self, status: str | None = None) -> list[TargetCompanyModel]:
        """List target companies, optionally filtered by watch_status."""
        stmt = select(TargetCompanyModel)
        if status:
            stmt = stmt.where(TargetCompanyModel.watch_status == status)
        return list(self.session.scalars(stmt).all())

    def set_status(self, target_id: uuid.UUID, status: str) -> TargetCompanyModel:
        """Update watch status for a target company."""
        if status not in ("PAUSED", "ACTIVE", "ARCHIVED"):
            raise ValueError(f"Invalid watch status: {status}")

        target = self.session.get(TargetCompanyModel, target_id)
        if not target:
            raise KeyError(f"TargetCompanyModel not found: {target_id}")

        target.watch_status = status
        target.updated_at = utc_now()
        self.session.flush()
        return target

    def add_observation(
        self,
        target_id: uuid.UUID,
        type: str,
        source_type: str,
        source_reference: str,
        observed_at: datetime.datetime,
        confidence: float,
        payload: dict[str, Any],
        dedupe_key: str,
        job_id: uuid.UUID | None = None,
    ) -> tuple[TargetCompanyObservationModel, bool]:
        """Add an observation for a target company with unique dedupe_key check."""
        existing = self.session.scalars(
            select(TargetCompanyObservationModel).where(
                TargetCompanyObservationModel.target_company_id == target_id,
                TargetCompanyObservationModel.dedupe_key == dedupe_key,
            )
        ).first()

        if existing:
            return existing, False

        obs = TargetCompanyObservationModel(
            target_company_id=target_id,
            observation_type=type,
            source_type=source_type,
            source_reference=source_reference,
            observed_at=observed_at,
            confidence=confidence,
            normalized_payload=payload,
            dedupe_key=dedupe_key,
            job_id=job_id,
        )
        self.session.add(obs)
        self.session.flush()
        return obs, True

    def observations(
        self,
        target_id: uuid.UUID,
        since: datetime.datetime | None = None,
        status: str | None = None,
    ) -> list[TargetCompanyObservationModel]:
        """Fetch observations for a target company."""
        stmt = select(TargetCompanyObservationModel).where(
            TargetCompanyObservationModel.target_company_id == target_id
        )
        if since:
            stmt = stmt.where(TargetCompanyObservationModel.observed_at >= since)
        if status:
            stmt = stmt.where(TargetCompanyObservationModel.status == status)

        stmt = stmt.order_by(TargetCompanyObservationModel.observed_at.desc())
        return list(self.session.scalars(stmt).all())

    def relationship_signal(self, target_id: uuid.UUID) -> RelationshipSignal:
        """Derive evidence-backed relationship signal for a target company."""
        target = self.session.get(TargetCompanyModel, target_id)
        if not target:
            raise KeyError(f"TargetCompanyModel not found: {target_id}")

        known_contacts: list[EvidenceRef] = []
        prior_applications: list[EvidenceRef] = []
        referral_paths: list[EvidenceRef] = []
        prior_responses = False
        source_refs: list[EvidenceRef] = []

        if target.company_id:
            # 1. Contacts
            contacts = list(
                self.session.scalars(
                    select(ContactModel).where(ContactModel.company_id == target.company_id)
                ).all()
            )
            for c in contacts:
                ref = EvidenceRef(ref_type="contact", ref_id=str(c.id), note=f"Contact: {c.name}")
                known_contacts.append(ref)
                source_refs.append(ref)

            # 2. Applications & Messages
            jobs = list(
                self.session.scalars(
                    select(JobModel).where(JobModel.company_id == target.company_id)
                ).all()
            )
            job_ids = [j.id for j in jobs]
            if job_ids:
                apps = list(
                    self.session.scalars(
                        select(ApplicationModel).where(ApplicationModel.job_id.in_(job_ids))
                    ).all()
                )
                for app in apps:
                    ref = EvidenceRef(ref_type="application", ref_id=str(app.id), note=f"Status: {app.status}")
                    prior_applications.append(ref)
                    source_refs.append(ref)

                    # Check for inbound messages linked to these applications
                    msg_links = list(
                        self.session.scalars(
                            select(MessageLinkModel).where(
                                MessageLinkModel.application_id == app.id,
                            )
                        ).all()
                    )
                    if msg_links:
                        prior_responses = True
                        for ml in msg_links:
                            source_refs.append(
                                EvidenceRef(ref_type="message", ref_id=str(ml.inbound_message_id), note="Inbound response link")
                            )

            # 3. Referral paths from OpportunityGraphService
            try:
                paths = self.opp_graph_service.referral_paths_to_company(target.company_id)
                for p in paths:
                    ref = EvidenceRef(ref_type="edge", ref_id=p.evidence_ref, note=f"Referral via {p.contact_name}")
                    referral_paths.append(ref)
                    source_refs.append(ref)
            except Exception:
                pass

        return RelationshipSignal(
            artifact_type="relationship_signal",
            generated_at=utc_now(),
            generator="TargetCompanyService",
            generator_version="2.3",
            source_refs=source_refs,
            known_contacts=known_contacts,
            prior_applications=prior_applications,
            prior_responses=prior_responses,
            referral_paths=referral_paths,
            confidence="HIGH" if (known_contacts or prior_applications) else "LOW",
        )

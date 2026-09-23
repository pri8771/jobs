"""Opportunity Graph projection and evidence-backed query layer.

Projects relational truth from PostgreSQL into an in-memory graph representation
without introducing a separate graph database or changing the database schema.
Implements typed, evidence-preserving queries adhering to docs/V2_3_OPPORTUNITY_GRAPH_CONTRACT.md.
"""

from __future__ import annotations
from jobs_automation.evaluation.engine import OPEN_JOB_STATUSES
from jobs_automation.lifecycle.crm import RecruiterCRMService

import datetime
import hashlib
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobModel,
    MessageLinkModel,
    ResumeVariantModel,
)


class NodeType(StrEnum):
    COMPANY = "company"
    JOB = "job"
    JOB_SOURCE = "job_source"
    APPLICATION = "application"
    APPLICATION_EVENT = "application_event"
    CONTACT = "contact"
    MESSAGE = "message"
    INTERVIEW = "interview"
    RESUME_VARIANT = "resume_variant"
    APPLICATION_PACKET = "application_packet"


class Predicate(StrEnum):
    HAS_JOB = "HAS_JOB"
    OBSERVED_AT = "OBSERVED_AT"
    FOR_JOB = "FOR_JOB"
    USED_PACKET = "USED_PACKET"
    PACKET_HAS_RESUME = "PACKET_HAS_RESUME"
    USED_RESUME = "USED_RESUME"
    INTERVIEW_FOR_APPLICATION = "INTERVIEW_FOR_APPLICATION"
    EVENT_FOR_APPLICATION = "EVENT_FOR_APPLICATION"
    MESSAGE_LINKED_TO = "MESSAGE_LINKED_TO"
    CONTACT_ASSOCIATED_WITH = "CONTACT_ASSOCIATED_WITH"
    CONTACT_TOUCHED_APPLICATION = "CONTACT_TOUCHED_APPLICATION"
    RESUME_TARGETS_ROLE_FAMILY = "RESUME_TARGETS_ROLE_FAMILY"
    REFERRAL_PATH = "REFERRAL_PATH"


class EdgeStatus(StrEnum):
    ASSERTED = "ASSERTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INVALIDATED = "INVALIDATED"


class OpportunityNode(BaseModel):
    """Normalized node in the opportunity graph."""

    model_config = ConfigDict(extra="forbid")

    id: str
    node_type: NodeType
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)
    source_reference: str | None = None
    observed_at: datetime.datetime | None = None


class OpportunityEdge(BaseModel):
    """Evidence-backed directed relationship edge."""

    model_config = ConfigDict(extra="forbid")

    id: str
    subject_type: NodeType
    subject_id: str
    predicate: Predicate
    object_type: NodeType
    object_id: str
    source_type: str
    source_reference: str | None = None
    confidence: float = 1.0
    evidence_hash: str | None = None
    observed_at: datetime.datetime
    method: str
    inferred: bool
    valid_from: datetime.datetime
    valid_to: datetime.datetime | None = None
    status: EdgeStatus = EdgeStatus.ASSERTED
    created_at: datetime.datetime
    updated_at: datetime.datetime


class OpportunityGraph(BaseModel):
    """In-memory projection of the opportunity graph."""

    model_config = ConfigDict(extra="forbid")

    nodes: dict[str, OpportunityNode] = Field(default_factory=dict)
    edges: list[OpportunityEdge] = Field(default_factory=list)

    def get_node(self, node_id: str) -> OpportunityNode | None:
        return self.nodes.get(node_id)

    def edges_from(self, subject_id: str, predicate: Predicate | None = None) -> list[OpportunityEdge]:
        return [
            e for e in self.edges
            if e.subject_id == subject_id and (predicate is None or e.predicate == predicate)
        ]

    def edges_to(self, object_id: str, predicate: Predicate | None = None) -> list[OpportunityEdge]:
        return [
            e for e in self.edges
            if e.object_id == object_id and (predicate is None or e.predicate == predicate)
        ]


# --- Typed Query Result Models ---


class CompanyOpportunityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    company_id: str
    company_name: str
    job_title: str
    status: str
    remote_type: str | None = None
    location_text: str | None = None
    compensation_min: float | None = None
    compensation_max: float | None = None
    apply_url: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ref: str | None = None


class CompanyContactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact_id: str
    company_id: str
    company_name: str
    name: str
    email: str | None = None
    role: str | None = None
    first_contact_at: datetime.datetime | None = None
    last_contact_at: datetime.datetime | None = None
    evidence_ref: str | None = None


class ContactApplicationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact_id: str
    contact_name: str
    application_id: str
    job_id: str
    job_title: str
    company_name: str
    application_status: str
    touch_type: str
    evidence_ref: str | None = None


class ResumeOutcomeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_variant_id: str
    resume_family: str
    variant_name: str
    target_role_family: str | None = None
    total_applications: int = 0
    screenings: int = 0
    interviews: int = 0
    offers: int = 0
    rejections: int = 0
    conversion_rate: float = 0.0
    evidence_refs: list[str] = Field(default_factory=list)


class OpportunitySignalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    job_title: str
    company_id: str | None = None
    company_name: str
    job_status: str
    has_active_contact: bool = False
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    prior_applications_count: int = 0
    has_prior_response: bool = False
    signal_summary: str
    evidence_refs: list[str] = Field(default_factory=list)


class ReferralPathRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    company_name: str
    contact_id: str
    contact_name: str
    contact_role: str | None = None
    relationship_type: str
    confidence: float
    status: EdgeStatus
    evidence_ref: str | None = None


def _make_edge_id(subject_type: str, subject_id: str, predicate: str, object_type: str, object_id: str) -> str:
    raw = f"{subject_type}:{subject_id}->{predicate}->{object_type}:{object_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class OpportunityGraphService:
    """Projects relational PostgreSQL state into an evidence-backed Opportunity Graph."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def project_graph(self) -> OpportunityGraph:
        """Projects all relational entities and evidence links into a clean OpportunityGraph.

        Deduplicates edges deterministically and preserves entity provenance.
        """
        now = datetime.datetime.now(datetime.UTC)
        nodes: dict[str, OpportunityNode] = {}
        edge_map: dict[str, OpportunityEdge] = {}

        def add_node(node: OpportunityNode) -> None:
            nodes[node.id] = node

        def add_edge(
            subject_type: NodeType,
            subject_id: str,
            predicate: Predicate,
            object_type: NodeType,
            object_id: str,
            source_type: str,
            source_reference: str | None = None,
            confidence: float = 1.0,
            status: EdgeStatus = EdgeStatus.ASSERTED,
            valid_from: datetime.datetime | None = None,
            observed_at: datetime.datetime | None = None,
            method: str = "fk_projection",
            inferred: bool = False,
        ) -> None:
            edge_id = _make_edge_id(subject_type.value, subject_id, predicate.value, object_type.value, object_id)
            if edge_id in edge_map:
                return
            ev_hash = hashlib.sha256(
                f"{edge_id}:{source_type}:{source_reference or ''}:{confidence}".encode()
            ).hexdigest()
            edge_map[edge_id] = OpportunityEdge(
                id=edge_id,
                subject_type=subject_type,
                subject_id=subject_id,
                predicate=predicate,
                object_type=object_type,
                object_id=object_id,
                source_type=source_type,
                source_reference=source_reference,
                confidence=confidence,
                evidence_hash=ev_hash,
                observed_at=observed_at or valid_from or now,
                method=method,
                inferred=inferred,
                valid_from=valid_from or now,
                valid_to=None,
                status=status,
                created_at=now,
                updated_at=now,
            )

        # 1. Companies
        companies = self.session.scalars(select(CompanyModel)).all()
        for c in companies:
            cid = str(c.id)
            add_node(
                OpportunityNode(
                    id=cid,
                    node_type=NodeType.COMPANY,
                    label=c.normalized_name,
                    properties={"domain": c.domain, "aliases": c.aliases_json},
                    source_reference=f"company:{cid}",
                    observed_at=now,
                )
            )

        # 2. Jobs and Sources
        jobs = self.session.scalars(
            select(JobModel).options(joinedload(JobModel.sources), joinedload(JobModel.company))
        ).unique().all()
        for j in jobs:
            jid = str(j.id)
            add_node(
                OpportunityNode(
                    id=jid,
                    node_type=NodeType.JOB,
                    label=j.normalized_title,
                    properties={
                        "status": j.status,
                        "location_text": j.location_text,
                        "remote_type": j.remote_type,
                        "employment_type": j.employment_type,
                        "compensation_min": float(j.compensation_min) if j.compensation_min is not None else None,
                        "compensation_max": float(j.compensation_max) if j.compensation_max is not None else None,
                        "posted_at": j.posted_at.isoformat() if j.posted_at else None,
                    },
                    source_reference=f"job:{jid}",
                    observed_at=j.first_seen_at or now,
                )
            )
            if j.company_id:
                cid = str(j.company_id)
                add_edge(
                    subject_type=NodeType.COMPANY,
                    subject_id=cid,
                    predicate=Predicate.HAS_JOB,
                    object_type=NodeType.JOB,
                    object_id=jid,
                    source_type="relational_fk",
                    source_reference=f"job.company_id={cid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=j.first_seen_at,
                )

            for s in j.sources:
                sid = str(s.id)
                add_node(
                    OpportunityNode(
                        id=sid,
                        node_type=NodeType.JOB_SOURCE,
                        label=f"{s.provider}:{s.source_job_id or sid}",
                        properties={
                            "provider": s.provider,
                            "source_url": s.source_url,
                            "canonical_apply_url": s.canonical_apply_url,
                            "requisition_id": s.requisition_id,
                        },
                        source_reference=f"job_source:{sid}",
                        observed_at=s.first_seen_at or now,
                    )
                )
                add_edge(
                    subject_type=NodeType.JOB,
                    subject_id=jid,
                    predicate=Predicate.OBSERVED_AT,
                    object_type=NodeType.JOB_SOURCE,
                    object_id=sid,
                    source_type="relational_fk",
                    source_reference=f"job_source.job_id={jid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=s.first_seen_at,
                )

        # 3. Resume Variants
        variants = self.session.scalars(select(ResumeVariantModel)).all()
        for rv in variants:
            rvid = str(rv.id)
            add_node(
                OpportunityNode(
                    id=rvid,
                    node_type=NodeType.RESUME_VARIANT,
                    label=f"{rv.resume_family}:{rv.name} v{rv.version}",
                    properties={
                        "resume_family": rv.resume_family,
                        "name": rv.name,
                        "version": rv.version,
                        "target_role_family": rv.target_role_family,
                        "content_hash": rv.content_hash,
                    },
                    source_reference=rv.source_reference or f"resume_variant:{rvid}",
                    observed_at=rv.created_at or now,
                )
            )
            if rv.target_job_id:
                add_edge(
                    subject_type=NodeType.RESUME_VARIANT,
                    subject_id=rvid,
                    predicate=Predicate.FOR_JOB,
                    object_type=NodeType.JOB,
                    object_id=str(rv.target_job_id),
                    source_type="relational_fk",
                    source_reference=f"resume_variant.target_job_id={rv.target_job_id}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=rv.created_at,
                )

        # 4. Application Packets
        packets = self.session.scalars(select(ApplicationPacketModel)).all()
        for pkt in packets:
            pkt_id = str(pkt.id)
            add_node(
                OpportunityNode(
                    id=pkt_id,
                    node_type=NodeType.APPLICATION_PACKET,
                    label=f"packet:{pkt_id[:8]}",
                    properties={
                        "is_live_ready": pkt.is_live_ready,
                        "packet_hash": pkt.packet_hash,
                    },
                    source_reference=f"application_packet:{pkt_id}",
                    observed_at=pkt.created_at or now,
                )
            )
            if pkt.resume_variant_id:
                rvid = str(pkt.resume_variant_id)
                add_edge(
                    subject_type=NodeType.APPLICATION_PACKET,
                    subject_id=pkt_id,
                    predicate=Predicate.PACKET_HAS_RESUME,
                    object_type=NodeType.RESUME_VARIANT,
                    object_id=rvid,
                    source_type="relational_fk",
                    source_reference=f"application_packet.resume_variant_id={rvid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=pkt.created_at,
                )

        # 5. Applications
        applications = self.session.scalars(
            select(ApplicationModel)
            .options(
                joinedload(ApplicationModel.events),
                joinedload(ApplicationModel.interviews),
            )
        ).unique().all()
        for app in applications:
            appid = str(app.id)
            jid = str(app.job_id)
            add_node(
                OpportunityNode(
                    id=appid,
                    node_type=NodeType.APPLICATION,
                    label=f"app:{appid[:8]} ({app.status})",
                    properties={
                        "status": app.status,
                        "application_mode": app.application_mode,
                        "policy_decision": app.policy_decision,
                        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                        "last_activity_at": app.last_activity_at.isoformat() if app.last_activity_at else None,
                    },
                    source_reference=f"application:{appid}",
                    observed_at=app.applied_at or app.last_activity_at or now,
                )
            )
            add_edge(
                subject_type=NodeType.APPLICATION,
                subject_id=appid,
                predicate=Predicate.FOR_JOB,
                object_type=NodeType.JOB,
                object_id=jid,
                source_type="relational_fk",
                source_reference=f"application.job_id={jid}",
                confidence=1.0,
                status=EdgeStatus.ASSERTED,
                valid_from=app.applied_at or app.last_activity_at,
            )

            if app.packet_id:
                pkt_id = str(app.packet_id)
                add_edge(
                    subject_type=NodeType.APPLICATION,
                    subject_id=appid,
                    predicate=Predicate.USED_PACKET,
                    object_type=NodeType.APPLICATION_PACKET,
                    object_id=pkt_id,
                    source_type="relational_fk",
                    source_reference=f"application.packet_id={pkt_id}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=app.applied_at or app.last_activity_at,
                )

            # Application Events
            for ev in app.events:
                evid = str(ev.id)
                add_node(
                    OpportunityNode(
                        id=evid,
                        node_type=NodeType.APPLICATION_EVENT,
                        label=f"event:{ev.event_type}",
                        properties={
                            "event_type": ev.event_type,
                            "occurred_at": ev.occurred_at.isoformat(),
                            "source": ev.source,
                            "actor": ev.actor,
                        },
                        source_reference=ev.source_reference or f"application_event:{evid}",
                        observed_at=ev.occurred_at,
                    )
                )
                add_edge(
                    subject_type=NodeType.APPLICATION_EVENT,
                    subject_id=evid,
                    predicate=Predicate.EVENT_FOR_APPLICATION,
                    object_type=NodeType.APPLICATION,
                    object_id=appid,
                    source_type="relational_fk",
                    source_reference=f"application_event.application_id={appid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=ev.occurred_at,
                )

            # Interviews
            for iv in app.interviews:
                ivid = str(iv.id)
                add_node(
                    OpportunityNode(
                        id=ivid,
                        node_type=NodeType.INTERVIEW,
                        label=f"interview:{iv.round_type} ({iv.status})",
                        properties={
                            "round_type": iv.round_type,
                            "status": iv.status,
                            "scheduled_start": iv.scheduled_start.isoformat(),
                            "scheduled_end": iv.scheduled_end.isoformat(),
                        },
                        source_reference=f"interview:{ivid}",
                        observed_at=iv.scheduled_start,
                    )
                )
                add_edge(
                    subject_type=NodeType.INTERVIEW,
                    subject_id=ivid,
                    predicate=Predicate.INTERVIEW_FOR_APPLICATION,
                    object_type=NodeType.APPLICATION,
                    object_id=appid,
                    source_type="relational_fk",
                    source_reference=f"interview.application_id={appid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=iv.scheduled_start,
                )

        # 6. Contacts
        contacts = self.session.scalars(select(ContactModel)).all()
        contact_by_email: dict[str, ContactModel] = {}
        for ct in contacts:
            ctid = str(ct.id)
            if ct.email:
                contact_by_email[ct.email.lower()] = ct
            add_node(
                OpportunityNode(
                    id=ctid,
                    node_type=NodeType.CONTACT,
                    label=ct.name,
                    properties={
                        "email": ct.email,
                        "role": ct.role,
                        "source": ct.source,
                        "first_contact_at": ct.first_contact_at.isoformat() if ct.first_contact_at else None,
                        "last_contact_at": ct.last_contact_at.isoformat() if ct.last_contact_at else None,
                    },
                    source_reference=f"contact:{ctid}",
                    observed_at=ct.first_contact_at or now,
                )
            )
            if ct.company_id:
                cid = str(ct.company_id)
                add_edge(
                    subject_type=NodeType.CONTACT,
                    subject_id=ctid,
                    predicate=Predicate.CONTACT_ASSOCIATED_WITH,
                    object_type=NodeType.COMPANY,
                    object_id=cid,
                    source_type="relational_fk",
                    source_reference=f"contact.company_id={cid}",
                    confidence=1.0,
                    status=EdgeStatus.ASSERTED,
                    valid_from=ct.first_contact_at,
                )

        # 7. Messages and Message Links
        messages = self.session.scalars(
            select(InboundMessageModel).options(joinedload(InboundMessageModel.links))
        ).unique().all()
        for msg in messages:
            mid = str(msg.id)
            add_node(
                OpportunityNode(
                    id=mid,
                    node_type=NodeType.MESSAGE,
                    label=f"msg:{msg.subject[:32]}",
                    properties={
                        "sender": msg.sender,
                        "direction": msg.direction,
                        "classification": msg.classification,
                        "received_at": msg.received_at.isoformat(),
                    },
                    source_reference=msg.provider_message_id,
                    observed_at=msg.received_at,
                )
            )
            for lk in msg.links:
                target_type: NodeType | None = None
                target_id: str | None = None
                if lk.application_id:
                    target_type = NodeType.APPLICATION
                    target_id = str(lk.application_id)
                elif lk.job_id:
                    target_type = NodeType.JOB
                    target_id = str(lk.job_id)
                elif lk.company_id:
                    target_type = NodeType.COMPANY
                    target_id = str(lk.company_id)

                if target_type and target_id:
                    status = EdgeStatus.ASSERTED if lk.confidence >= 0.8 else EdgeStatus.REVIEW_REQUIRED
                    add_edge(
                        subject_type=NodeType.MESSAGE,
                        subject_id=mid,
                        predicate=Predicate.MESSAGE_LINKED_TO,
                        object_type=target_type,
                        object_id=target_id,
                        source_type="message_link",
                        source_reference=f"message_link:{lk.id}",
                        confidence=lk.confidence,
                        status=status,
                        valid_from=lk.created_at,
                        observed_at=lk.created_at,
                        method=getattr(lk, "method", "fk_projection"),
                        inferred=(lk.confidence < 0.8),
                    )

                    # If message is linked to application and matches a contact by sender email:
                    _, sender_address = RecruiterCRMService(self.session).parse_sender(msg.sender)
                    sender_address = (sender_address or "").lower()
                    for email, ct in contact_by_email.items():
                        if sender_address == email and lk.application_id:
                            add_edge(
                                subject_type=NodeType.CONTACT,
                                subject_id=str(ct.id),
                                predicate=Predicate.CONTACT_TOUCHED_APPLICATION,
                                object_type=NodeType.APPLICATION,
                                object_id=str(lk.application_id),
                                source_type="message_evidence",
                                source_reference=msg.provider_message_id,
                                confidence=lk.confidence,
                                status=status,
                                valid_from=msg.received_at,
                                observed_at=msg.received_at,
                                method="sender_address_match",
                                inferred=True,
                            )

        return OpportunityGraph(nodes=nodes, edges=list(edge_map.values()))

    # --- Typed Evidence-Preserving Queries ---

    def opportunities_for_company(self, company_id: uuid.UUID | str) -> list[CompanyOpportunityRecord]:
        """Lists open/discovered opportunities for a company with preserved evidence."""
        cid = uuid.UUID(str(company_id))
        company = self.session.get(CompanyModel, cid)
        company_name = company.normalized_name if company else "Unknown"

        jobs = self.session.scalars(
            select(JobModel)
            .where(JobModel.company_id == cid)
            .options(joinedload(JobModel.sources))
        ).unique().all()

        results: list[CompanyOpportunityRecord] = []
        for j in jobs:
            sources_data = [
                {
                    "provider": s.provider,
                    "source_url": s.source_url,
                    "canonical_apply_url": s.canonical_apply_url,
                }
                for s in j.sources
            ]
            results.append(
                CompanyOpportunityRecord(
                    job_id=str(j.id),
                    company_id=str(cid),
                    company_name=company_name,
                    job_title=j.normalized_title,
                    status=j.status,
                    remote_type=j.remote_type,
                    location_text=j.location_text,
                    compensation_min=float(j.compensation_min) if j.compensation_min is not None else None,
                    compensation_max=float(j.compensation_max) if j.compensation_max is not None else None,
                    apply_url=j.apply_url,
                    sources=sources_data,
                    evidence_ref=f"job:{j.id}",
                )
            )
        return results

    def contacts_for_company(self, company_id: uuid.UUID | str) -> list[CompanyContactRecord]:
        """Lists known recruiter / employee contacts for a company with evidence."""
        cid = uuid.UUID(str(company_id))
        company = self.session.get(CompanyModel, cid)
        company_name = company.normalized_name if company else "Unknown"

        contacts = self.session.scalars(
            select(ContactModel).where(ContactModel.company_id == cid)
        ).all()

        return [
            CompanyContactRecord(
                contact_id=str(c.id),
                company_id=str(cid),
                company_name=company_name,
                name=c.name,
                email=c.email,
                role=c.role,
                first_contact_at=c.first_contact_at,
                last_contact_at=c.last_contact_at,
                evidence_ref=f"contact:{c.id}",
            )
            for c in contacts
        ]

    def applications_with_contact(self, contact_id: uuid.UUID | str) -> list[ContactApplicationRecord]:
        """Finds applications where a contact was touched or associated."""
        ct_id = uuid.UUID(str(contact_id))
        contact = self.session.get(ContactModel, ct_id)
        if not contact:
            return []

        contact_email = contact.email.lower() if contact.email else None

        # Look up applications via linked messages
        query = (
            select(ApplicationModel, JobModel, CompanyModel, InboundMessageModel)
            .join(JobModel, ApplicationModel.job_id == JobModel.id)
            .outerjoin(CompanyModel, JobModel.company_id == CompanyModel.id)
            .join(MessageLinkModel, MessageLinkModel.application_id == ApplicationModel.id)
            .join(InboundMessageModel, MessageLinkModel.inbound_message_id == InboundMessageModel.id)
        )

        records: list[ContactApplicationRecord] = []
        seen_apps: set[uuid.UUID] = set()

        rows = self.session.execute(query).all()
        for app, job, comp, msg in rows:
            sender_lower = msg.sender.lower()
            if contact_email and contact_email in sender_lower:
                if app.id not in seen_apps:
                    seen_apps.add(app.id)
                    records.append(
                        ContactApplicationRecord(
                            contact_id=str(ct_id),
                            contact_name=contact.name,
                            application_id=str(app.id),
                            job_id=str(job.id),
                            job_title=job.normalized_title,
                            company_name=comp.normalized_name if comp else "Unknown",
                            application_status=app.status,
                            touch_type="inbound_message",
                            evidence_ref=msg.provider_message_id,
                        )
                    )

        # Also include applications for the contact's company if no direct touches found yet
        if not records and contact.company_id:
            company_apps = self.session.execute(
                select(ApplicationModel, JobModel, CompanyModel)
                .join(JobModel, ApplicationModel.job_id == JobModel.id)
                .join(CompanyModel, JobModel.company_id == CompanyModel.id)
                .where(CompanyModel.id == contact.company_id)
            ).all()
            for app, job, comp in company_apps:
                if app.id not in seen_apps:
                    seen_apps.add(app.id)
                    records.append(
                        ContactApplicationRecord(
                            contact_id=str(ct_id),
                            contact_name=contact.name,
                            application_id=str(app.id),
                            job_id=str(job.id),
                            job_title=job.normalized_title,
                            company_name=comp.normalized_name,
                            application_status=app.status,
                            touch_type="company_association",
                            evidence_ref=f"contact.company_id={contact.company_id}",
                        )
                    )

        return records

    def resume_outcomes_for_role_family(self, role_family: str) -> list[ResumeOutcomeRecord]:
        """Calculates resume variant outcomes and conversion metrics for a given role family.

        Follows exact evidence preservation without overclaiming causality.
        """
        variants = self.session.scalars(
            select(ResumeVariantModel).where(
                (ResumeVariantModel.target_role_family == role_family)
                | (ResumeVariantModel.resume_family == role_family)
            )
        ).all()

        results: list[ResumeOutcomeRecord] = []
        for rv in variants:
            # Query applications linked via packet or target_job_id
            apps = self.session.scalars(
                select(ApplicationModel)
                .join(ApplicationPacketModel, ApplicationModel.packet_id == ApplicationPacketModel.id)
                .where(ApplicationPacketModel.resume_variant_id == rv.id)
            ).all()

            total = len(apps)
            screenings = sum(1 for a in apps if a.status in ("SCREENING", "INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_DECLINED"))
            interviews = sum(1 for a in apps if a.status in ("INTERVIEWING", "OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_DECLINED"))
            offers = sum(1 for a in apps if a.status in ("OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_DECLINED"))
            rejections = sum(1 for a in apps if a.status == "REJECTED")

            conv = round(screenings / total, 3) if total > 0 else 0.0
            evidence_refs = [f"app:{a.id}" for a in apps]

            results.append(
                ResumeOutcomeRecord(
                    resume_variant_id=str(rv.id),
                    resume_family=rv.resume_family,
                    variant_name=rv.name,
                    target_role_family=rv.target_role_family,
                    total_applications=total,
                    screenings=screenings,
                    interviews=interviews,
                    offers=offers,
                    rejections=rejections,
                    conversion_rate=conv,
                    evidence_refs=evidence_refs,
                )
            )
        return results

    def open_opportunities_with_relationship_signal(self) -> list[OpportunitySignalRecord]:
        """Surfaces open jobs with warm recruiter contacts or prior positive application history."""
        # Find active / discovered jobs
        jobs = self.session.scalars(
            select(JobModel)
            .where(JobModel.status.in_(OPEN_JOB_STATUSES))
            .options(joinedload(JobModel.company))
        ).unique().all()

        signals: list[OpportunitySignalRecord] = []
        for j in jobs:
            comp_id = j.company_id
            comp_name = j.company.normalized_name if j.company else "Unknown"

            contacts_data: list[dict[str, Any]] = []
            has_contact = False
            if comp_id:
                cts = self.session.scalars(
                    select(ContactModel).where(ContactModel.company_id == comp_id)
                ).all()
                if cts:
                    has_contact = True
                    contacts_data = [
                        {"name": c.name, "role": c.role, "email": c.email, "id": str(c.id)}
                        for c in cts
                    ]

            # Prior applications for this company
            prior_apps_count = 0
            has_response = False
            ev_refs: list[str] = [f"job:{j.id}"]
            if comp_id:
                prior_apps = self.session.scalars(
                    select(ApplicationModel)
                    .join(JobModel, ApplicationModel.job_id == JobModel.id)
                    .where(JobModel.company_id == comp_id, JobModel.id != j.id)
                ).all()
                prior_apps_count = len(prior_apps)
                for pa in prior_apps:
                    ev_refs.append(f"app:{pa.id}")
                    if pa.status in ("SCREENING", "INTERVIEWING", "OFFER_RECEIVED"):
                        has_response = True

            # Synthesize factual signal summary
            parts = []
            if has_contact:
                parts.append(f"{len(contacts_data)} known contact(s)")
            if prior_apps_count > 0:
                parts.append(f"{prior_apps_count} prior application(s)")
                if has_response:
                    parts.append("positive prior response history")
            if not parts:
                parts.append("no known relationship signal")

            signals.append(
                OpportunitySignalRecord(
                    job_id=str(j.id),
                    job_title=j.normalized_title,
                    company_id=str(comp_id) if comp_id else None,
                    company_name=comp_name,
                    job_status=j.status,
                    has_active_contact=has_contact,
                    contacts=contacts_data,
                    prior_applications_count=prior_apps_count,
                    has_prior_response=has_response,
                    signal_summary="; ".join(parts),
                    evidence_refs=ev_refs,
                )
            )
        return signals

    def referral_paths_to_company(self, company_id: uuid.UUID | str) -> list[ReferralPathRecord]:
        """Identifies verified or potential referral connections to a company."""
        cid = uuid.UUID(str(company_id))
        company = self.session.get(CompanyModel, cid)
        comp_name = company.normalized_name if company else "Unknown"

        contacts = self.session.scalars(
            select(ContactModel).where(ContactModel.company_id == cid)
        ).all()

        paths: list[ReferralPathRecord] = []
        for c in contacts:
            # Verified contact at company
            status = EdgeStatus.ASSERTED if c.source in ("personal_referral", "user_confirmed") else EdgeStatus.REVIEW_REQUIRED
            conf = 1.0 if status == EdgeStatus.ASSERTED else 0.75
            paths.append(
                ReferralPathRecord(
                    company_id=str(cid),
                    company_name=comp_name,
                    contact_id=str(c.id),
                    contact_name=c.name,
                    contact_role=c.role,
                    relationship_type=c.source or "company_contact",
                    confidence=conf,
                    status=status,
                    evidence_ref=f"contact:{c.id}",
                )
            )
        return paths

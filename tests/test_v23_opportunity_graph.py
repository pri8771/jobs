"""Unit and adversarial tests for V2.3 Opportunity Graph projection."""

import datetime
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationModel,
    ApplicationPacketModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    InterviewModel,
    JobModel,
    JobSourceModel,
    MessageLinkModel,
    ResumeVariantModel,
)
from jobs_automation.intelligence.opportunity_graph import (
    EdgeStatus,
    NodeType,
    OpportunityGraphService,
    Predicate,
)


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_opportunity_graph_projection_and_stability() -> None:
    session = create_test_session()
    now = datetime.datetime.now(datetime.UTC)

    # 1. Company
    comp = CompanyModel(
        id=uuid.uuid4(),
        normalized_name="Acme Corp",
        domain="acme.com",
        aliases_json=["Acme Inc"],
    )
    session.add(comp)

    # 2. Job
    job = JobModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        normalized_title="Senior AI Engineer",
        status="discovered",
        location_text="Remote, US",
        remote_type="remote",
        first_seen_at=now,
    )
    session.add(job)

    # 3. Source
    source = JobSourceModel(
        id=uuid.uuid4(),
        job_id=job.id,
        provider="greenhouse",
        source_url="https://boards.greenhouse.io/acme/jobs/123",
        canonical_apply_url="https://boards.greenhouse.io/acme/jobs/123",
        first_seen_at=now,
    )
    session.add(source)

    # 4. Resume Variant
    rv = ResumeVariantModel(
        id=uuid.uuid4(),
        resume_family="ai_engineer",
        name="AI Engineer Tailored",
        version=1,
        target_role_family="ai_engineer",
        content_hash="abc123hash",
        created_at=now,
    )
    session.add(rv)

    # 5. Packet
    packet = ApplicationPacketModel(
        id=uuid.uuid4(),
        job_id=job.id,
        candidate_profile_version=1,
        resume_variant_id=rv.id,
        packet_hash="pkthash123",
        is_live_ready=True,
        created_at=now,
    )
    session.add(packet)

    # 6. Application
    app = ApplicationModel(
        id=uuid.uuid4(),
        job_id=job.id,
        status="SCREENING",
        packet_id=packet.id,
        applied_at=now,
        last_activity_at=now,
    )
    session.add(app)

    # 7. Contact
    contact = ContactModel(
        id=uuid.uuid4(),
        company_id=comp.id,
        name="Jane Recruiter",
        email="jane@acme.com",
        role="Lead Tech Recruiter",
        source="personal_referral",
        first_contact_at=now,
    )
    session.add(contact)

    # 8. Message & Link
    msg = InboundMessageModel(
        id=uuid.uuid4(),
        provider_message_id="msg_gmail_123",
        provider_thread_id="th_123",
        received_at=now,
        sender="jane@acme.com",
        subject="Interview Invitation: Senior AI Engineer",
        body_text="Hi, we would like to invite you for an interview.",
        classification="interview_invitation",
        confidence=0.95,
    )
    session.add(msg)

    link = MessageLinkModel(
        id=uuid.uuid4(),
        inbound_message_id=msg.id,
        application_id=app.id,
        company_id=comp.id,
        confidence=0.95,
        method="heuristic_email_match",
        created_at=now,
    )
    session.add(link)

    # 9. Interview
    iv = InterviewModel(
        id=uuid.uuid4(),
        application_id=app.id,
        round_type="technical_screen",
        scheduled_start=now + datetime.timedelta(days=2),
        scheduled_end=now + datetime.timedelta(days=2, hours=1),
        status="scheduled",
    )
    session.add(iv)

    session.commit()

    service = OpportunityGraphService(session)

    # Test projection stability
    graph1 = service.project_graph()
    graph2 = service.project_graph()

    assert len(graph1.nodes) == len(graph2.nodes)
    assert len(graph1.edges) == len(graph2.edges)

    # Verify node counts & types
    comp_node = graph1.get_node(str(comp.id))
    assert comp_node is not None
    assert comp_node.node_type == NodeType.COMPANY
    job_node = graph1.get_node(str(job.id))
    assert job_node is not None
    assert job_node.node_type == NodeType.JOB
    contact_node = graph1.get_node(str(contact.id))
    assert contact_node is not None
    assert contact_node.node_type == NodeType.CONTACT
    app_node = graph1.get_node(str(app.id))
    assert app_node is not None
    assert app_node.node_type == NodeType.APPLICATION

    # Verify edge predicates
    company_edges = graph1.edges_from(str(comp.id), Predicate.HAS_JOB)
    assert len(company_edges) == 1
    assert company_edges[0].object_id == str(job.id)
    assert company_edges[0].status == EdgeStatus.ASSERTED

    contact_edges = graph1.edges_from(str(contact.id), Predicate.CONTACT_ASSOCIATED_WITH)
    assert len(contact_edges) == 1
    assert contact_edges[0].object_id == str(comp.id)

    # Verify queries
    opps = service.opportunities_for_company(comp.id)
    assert len(opps) == 1
    assert opps[0].job_title == "Senior AI Engineer"
    assert opps[0].evidence_ref == f"job:{job.id}"

    contacts = service.contacts_for_company(comp.id)
    assert len(contacts) == 1
    assert contacts[0].name == "Jane Recruiter"

    contact_apps = service.applications_for_contact(contact.id)
    assert len(contact_apps) == 1
    assert contact_apps[0].application_id == str(app.id)

    outcomes = service.resume_outcomes_for_role_family("ai_engineer")
    assert len(outcomes) == 1
    assert outcomes[0].screenings == 1
    assert outcomes[0].total_applications == 1
    assert outcomes[0].conversion_rate == 1.0

    signals = service.open_opportunities_with_relationship_signal()
    assert len(signals) == 1
    assert signals[0].has_active_contact is True
    assert "1 known contact(s)" in signals[0].signal_summary

    referrals = service.referral_paths_to_company(comp.id)
    assert len(referrals) == 1
    assert referrals[0].contact_name == "Jane Recruiter"
    assert referrals[0].status == EdgeStatus.ASSERTED

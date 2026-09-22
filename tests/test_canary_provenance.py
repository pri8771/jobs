"""Regression coverage for historical durable-canary provenance quarantine."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.models import MockModelGateway
from jobs_automation.automation.auto_engine import ControlledAutoApplicationEngine
from jobs_automation.browser.assisted_engine import AssistedApplicationEngine
from jobs_automation.browser.mock_runner import MockBrowserRunner
from jobs_automation.core import CandidateProfileConfig, ConfigLoader, JobSearchConfig
from jobs_automation.core.policy_registry import (
    DefaultPolicyConfig,
    PolicyDecision,
    PolicyRegistryConfig,
)
from jobs_automation.db.canary_provenance import (
    CANARY_PROVENANCE_RECONCILIATION_REQUIRED,
    CanaryProvenanceReconciliationRequiredError,
    job_ids_with_durable_canary_provenance,
)
from jobs_automation.db.models import (
    ApplicationModel,
    CompanyModel,
    ContactModel,
    InboundMessageModel,
    JobEvaluationModel,
    JobModel,
    MessageLinkModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.evaluation.engine import JobEvaluationEngine
from jobs_automation.lifecycle.crm import RecruiterCRMService
from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def configs() -> tuple[CandidateProfileConfig, JobSearchConfig]:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile("config/candidate_profile.example.yaml")
    search, _ = loader.load_job_search("config/job_search.example.yaml")
    return profile, search


def _canary_message(*, provider_id: str, sender: str = "canary@example.test") -> InboundMessageModel:
    return InboundMessageModel(
        provider_message_id=provider_id,
        provider_thread_id=f"thread-{provider_id}",
        received_at=datetime.datetime.now(datetime.UTC),
        sender=sender,
        subject="Owner-controlled canary",
        headers_json={"_provider": {"canary": True}},
        body_text="This message is test traffic.",
        classification="JOB_ALERT",
    )


def _genuine_message(*, provider_id: str, sender: str) -> InboundMessageModel:
    return InboundMessageModel(
        provider_message_id=provider_id,
        provider_thread_id=f"thread-{provider_id}",
        received_at=datetime.datetime.now(datetime.UTC),
        sender=sender,
        subject="Genuine recruiter message",
        headers_json={},
        body_text="This is a genuine recruiting message.",
        classification="RECRUITER_OUTREACH",
    )


def _link_canary_to_job(
    session: Session,
    job: JobModel,
    *,
    through_application: bool = False,
) -> InboundMessageModel:
    message = _canary_message(provider_id=f"canary-{job.id}")
    session.add(message)
    session.flush()
    if through_application:
        application = ApplicationModel(job_id=job.id, status="SUBMITTED")
        session.add(application)
        session.flush()
        link = MessageLinkModel(
            inbound_message_id=message.id,
            application_id=application.id,
            confidence=1.0,
            method="historical_canary_application_link",
        )
    else:
        link = MessageLinkModel(
            inbound_message_id=message.id,
            job_id=job.id,
            confidence=1.0,
            method="historical_canary_job_link",
        )
    session.add(link)
    session.flush()
    return message


def test_durable_canary_provenance_covers_direct_and_application_links(
    db_session: Session,
) -> None:
    direct_job = JobModel(normalized_title="Direct canary role", status="discovered")
    app_linked_job = JobModel(normalized_title="Application canary role", status="discovered")
    genuine_job = JobModel(normalized_title="Genuine role", status="discovered")
    db_session.add_all([direct_job, app_linked_job, genuine_job])
    db_session.flush()

    _link_canary_to_job(db_session, direct_job)
    _link_canary_to_job(db_session, app_linked_job, through_application=True)
    db_session.commit()

    assert job_ids_with_durable_canary_provenance(db_session) == {
        direct_job.id,
        app_linked_job.id,
    }
    assert job_ids_with_durable_canary_provenance(db_session, {genuine_job.id}) == set()


def test_crm_omits_durable_canary_history_and_preserves_genuine_history(
    db_session: Session,
) -> None:
    crm = RecruiterCRMService(db_session)
    company = CompanyModel(normalized_name="CRM boundary company")
    db_session.add(company)
    db_session.flush()
    canary_job = JobModel(company_id=company.id, normalized_title="Canary application")
    genuine_job = JobModel(company_id=company.id, normalized_title="Genuine application")
    db_session.add_all([canary_job, genuine_job])
    db_session.flush()
    canary_application = ApplicationModel(job_id=canary_job.id, status="SUBMITTED")
    genuine_application = ApplicationModel(job_id=genuine_job.id, status="SUBMITTED")
    contact = ContactModel(
        company_id=company.id,
        name="Recruiter",
        email="recruiter@example.test",
        role="Recruiter",
        source="email",
    )
    db_session.add_all([canary_application, genuine_application, contact])
    db_session.flush()

    canary_message = _canary_message(
        provider_id="crm-canary", sender="Recruiter <recruiter@example.test>"
    )
    genuine_message = _genuine_message(
        provider_id="crm-genuine", sender="Recruiter <recruiter@example.test>"
    )
    db_session.add_all([canary_message, genuine_message])
    db_session.flush()
    db_session.add_all(
        [
            MessageLinkModel(
                inbound_message_id=canary_message.id,
                application_id=canary_application.id,
                confidence=1.0,
                method="historical_canary_link",
            ),
            MessageLinkModel(
                inbound_message_id=genuine_message.id,
                application_id=genuine_application.id,
                confidence=1.0,
                method="genuine_link",
            ),
        ]
    )
    db_session.commit()

    crm.record_touchpoint(contact, canary_message)
    assert contact.first_contact_at is None
    assert contact.last_contact_at is None
    crm.record_touchpoint(contact, genuine_message)
    assert contact.first_contact_at == genuine_message.received_at
    assert contact.last_contact_at == genuine_message.received_at

    assert crm.get_timeline_for_application(canary_application.id) == []
    assert [row["provider_message_id"] for row in crm.get_timeline_for_application(genuine_application.id)] == [
        "crm-genuine"
    ]
    assert [app.id for app in crm.get_applications_for_contact(contact.id)] == [
        genuine_application.id
    ]
    assert [row["provider_message_id"] for row in crm.get_timeline_for_contact(contact.id)] == [
        "crm-genuine"
    ]
    summary = crm.get_contact_summary(contact.id)
    assert summary is not None
    assert summary["applications_count"] == 1


def test_evaluation_batch_excludes_durable_canary_job_and_direct_path_fails_closed(
    db_session: Session,
    configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, search = configs
    company = CompanyModel(normalized_name="Evaluation boundary company")
    db_session.add(company)
    db_session.flush()
    canary_job = JobModel(
        company_id=company.id,
        normalized_title="Enterprise Automation Architect",
        location_text="Pittsburgh, PA",
        remote_type="hybrid",
        compensation_min=165000,
        compensation_max=195000,
        description_text="SAP BTP integrations, Python automation, enterprise systems.",
        status="discovered",
    )
    genuine_job = JobModel(
        company_id=company.id,
        normalized_title="Junior Support Technician",
        location_text="Miami, FL",
        remote_type="on_site",
        compensation_min=40000,
        compensation_max=50000,
        description_text="Password resets and desk support.",
        status="discovered",
    )
    db_session.add_all([canary_job, genuine_job])
    db_session.flush()
    _link_canary_to_job(db_session, canary_job)
    db_session.commit()

    engine = JobEvaluationEngine(db_session, profile, search)
    summary = engine.run_evaluation_batch()

    assert summary.total_evaluated == 1
    db_session.refresh(canary_job)
    assert canary_job.status == "discovered"
    assert db_session.scalars(
        select(JobEvaluationModel).where(JobEvaluationModel.job_id == canary_job.id)
    ).all() == []
    with pytest.raises(
        CanaryProvenanceReconciliationRequiredError,
        match=CANARY_PROVENANCE_RECONCILIATION_REQUIRED,
    ):
        engine.evaluate_job(canary_job)


def test_packet_assisted_and_auto_engines_stop_before_operational_work(
    db_session: Session,
    configs: tuple[CandidateProfileConfig, JobSearchConfig],
) -> None:
    profile, _ = configs
    job = JobModel(normalized_title="Canary execution boundary", status="shortlisted")
    db_session.add(job)
    db_session.flush()
    _link_canary_to_job(db_session, job)
    db_session.commit()

    with pytest.raises(
        CanaryProvenanceReconciliationRequiredError,
        match=CANARY_PROVENANCE_RECONCILIATION_REQUIRED,
    ):
        ApplicationPacketBuilder(db_session, profile, MockModelGateway()).build_packet(job)

    policy = PolicyEvaluator(
        PolicyRegistryConfig(
            version=1,
            default=DefaultPolicyConfig(
                decision=PolicyDecision.BLOCKED,
                reason="test_default_block",
            ),
        )
    )
    assisted = AssistedApplicationEngine(
        session=db_session,
        policy_evaluator=policy,
        browser_runner=MockBrowserRunner(),
        candidate_profile=profile,
    )
    with pytest.raises(
        CanaryProvenanceReconciliationRequiredError,
        match=CANARY_PROVENANCE_RECONCILIATION_REQUIRED,
    ):
        assisted.build_plan(job.id)

    auto = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=policy,
        candidate_profile=profile,
    )
    with pytest.raises(
        CanaryProvenanceReconciliationRequiredError,
        match=CANARY_PROVENANCE_RECONCILIATION_REQUIRED,
    ):
        auto.execute_auto_apply(job.id, mock_mode=True)

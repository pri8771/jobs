from __future__ import annotations

import datetime
import getpass
import uuid

from sqlalchemy import URL, create_engine, select, text
from sqlalchemy.orm import sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import (
    ApplicationEventModel, ApplicationModel, CompanyModel, ContactModel,
    InboundMessageModel, JobModel, MessageLinkModel,
)
from jobs_automation.lifecycle.crm import RecruiterCRMService

CODE_SHA = "10a3a23924fdde6b040082ef030ad1286591b9a9"
SOCKET = "/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd"
PORT = 56422
SCHEMA = f"codex_crm_pg_{uuid.uuid4().hex}"
URL_BASE = URL.create(
    "postgresql+psycopg", username=getpass.getuser(), database="postgres",
    query={"host": SOCKET, "port": str(PORT)},
)


def message(provider_id: str, sender: str, day: int) -> InboundMessageModel:
    return InboundMessageModel(
        provider_message_id=provider_id,
        provider_thread_id=f"thread-{provider_id}",
        received_at=datetime.datetime(2026, 1, day, tzinfo=datetime.UTC),
        sender=sender,
        recipients_json=["candidate@example.test"],
        direction="inbound", subject="Synthetic", headers_json={}, body_text="Synthetic only",
        classification="RECRUITER_OUTREACH", confidence=0.99,
    )


admin = create_engine(URL_BASE, isolation_level="AUTOCOMMIT")
engine = None
try:
    with admin.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{SCHEMA}"'))
    engine = create_engine(URL_BASE, connect_args={"options": f"-csearch_path={SCHEMA}"})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        company = CompanyModel(normalized_name="Synthetic PG Employer")
        session.add(company); session.flush()
        jobs = [JobModel(company_id=company.id, normalized_title=f"Role {n}", status="active") for n in range(3)]
        session.add_all(jobs); session.flush()
        apps = [ApplicationModel(job_id=j.id, status="SUBMITTED", application_mode="manual", destination_domain="example.test") for j in jobs]
        session.add_all(apps); session.flush()

        relink_msg = message("pg-relink", "Relink <relink@example.test>", 1)
        session.add(relink_msg); session.flush()
        session.add_all([
            MessageLinkModel(inbound_message_id=relink_msg.id, application_id=apps[0].id, job_id=jobs[0].id, company_id=company.id, confidence=.5, method="ambiguous"),
            MessageLinkModel(inbound_message_id=relink_msg.id, application_id=apps[1].id, job_id=jobs[1].id, company_id=company.id, confidence=.5, method="ambiguous"),
        ])

        primary = ContactModel(company_id=company.id, name="Primary", email="primary@example.test", role="Recruiter", source="email")
        secondary = ContactModel(company_id=company.id, name="Secondary", email="secondary@example.test", role="Recruiter", source="email")
        session.add_all([primary, secondary]); session.flush()
        alias_msg = message("pg-alias", "Secondary <secondary@example.test>", 2)
        event_msg = message("pg-event", "forwarder@example.test", 3)
        session.add_all([alias_msg, event_msg]); session.flush()
        session.add_all([
            MessageLinkModel(inbound_message_id=alias_msg.id, application_id=apps[0].id, job_id=jobs[0].id, company_id=company.id, confidence=1, method="test"),
            MessageLinkModel(inbound_message_id=event_msg.id, application_id=apps[1].id, job_id=jobs[1].id, company_id=company.id, confidence=1, method="test"),
            ApplicationEventModel(application_id=apps[1].id, event_type="RECRUITER_OUTREACH", source="email_lifecycle", source_reference=event_msg.provider_message_id, payload_json={"contact_id": str(secondary.id)}),
        ])
        session.commit()

        crm = RecruiterCRMService(session)
        corrected = crm.relink_message(relink_msg.id, apps[2].id, corrected_by="pg-dialect-check")
        crm.merge_contacts(primary.id, secondary.id, merged_by="pg-dialect-check")
        session.commit(); session.expire_all()

        links = session.scalars(select(MessageLinkModel).where(MessageLinkModel.inbound_message_id == relink_msg.id)).all()
        assert len(links) == 1
        assert links[0].id == corrected.id
        assert (links[0].application_id, links[0].job_id, links[0].company_id) == (apps[2].id, jobs[2].id, company.id)

        found_apps = {a.id for a in crm.get_applications_for_contact(primary.id)}
        timeline = crm.get_timeline_for_contact(primary.id)
        timeline_ids = {row["provider_message_id"] for row in timeline}
        assert found_apps == {apps[0].id, apps[1].id}, found_apps
        assert timeline_ids == {"pg-alias", "pg-event"}, timeline_ids
        print(f"PASS code_sha={CODE_SHA} schema={SCHEMA} relink=1 aliases=1 json_event_ref=1 apps={len(found_apps)} timeline={len(timeline)}")
finally:
    if engine is not None:
        engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
    admin.dispose()
    print(f"CLEANUP schema={SCHEMA} dropped=true")

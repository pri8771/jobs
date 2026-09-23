from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jobs_automation.db.base import Base
def create_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

import pytest
import uuid
from jobs_automation.db.models import ContactModel, InboundMessageModel, MessageLinkModel, ApplicationModel, JobModel, CompanyModel
from jobs_automation.intelligence.edges import backfill_message_link_contacts

def test_backfill_message_link_contacts():
    session = create_test_session()
    c_id = uuid.uuid4()
    comp = CompanyModel(id=c_id, normalized_name="ACME Corp")
    session.add(comp)
    
    ct_id = uuid.uuid4()
    contact = ContactModel(id=ct_id, name="Jordan", email="jordan@acme.com", company_id=c_id)
    session.add(contact)
    
    j_id = uuid.uuid4()
    job = JobModel(id=j_id, company_id=c_id, normalized_title="engineer", status="needs_review", location_text="Remote", remote_type="remote")
    session.add(job)
    
    a_id = uuid.uuid4()
    app = ApplicationModel(id=a_id, job_id=j_id, status="SCREENING")
    session.add(app)
    
    m_id = uuid.uuid4()
    msg = InboundMessageModel(id=m_id, provider_message_id="m1", provider_thread_id="th1", sender="Jordan <jordan@acme.com>", subject="Hello", direction="inbound", body_text="", classification="other", confidence=1.0, received_at=__import__("datetime").datetime.now(__import__("datetime").UTC))
    session.add(msg)
    session.flush()
    
    # Link missing contact_id
    link = MessageLinkModel(id=uuid.uuid4(), inbound_message_id=m_id, application_id=a_id, confidence=1.0, method="heuristic_email_match")
    session.add(link)
    session.commit()
    
    # Run backfill
    report = backfill_message_link_contacts(session)
    assert report.links_updated == 1
    
    # Idempotency
    report2 = backfill_message_link_contacts(session)
    assert report2.links_updated == 0
    assert report2.links_already_set == 1

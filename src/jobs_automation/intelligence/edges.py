import datetime
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from jobs_automation.db.models import MessageLinkModel, ContactModel, InboundMessageModel
from jobs_automation.lifecycle.crm import RecruiterCRMService

class BackfillReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    total_links_scanned: int = 0
    links_updated: int = 0
    links_already_set: int = 0
    ambiguous_senders_skipped: int = 0
    unresolved_senders: int = 0

def backfill_message_link_contacts(session: Session, dry_run: bool = False) -> BackfillReport:
    report = BackfillReport()
    
    # Pre-load all contacts to map email -> list of contacts
    contacts = session.scalars(select(ContactModel)).all()
    email_to_contacts: dict[str, list[ContactModel]] = {}
    for c in contacts:
        if c.email:
            em = c.email.lower()
            if em not in email_to_contacts:
                email_to_contacts[em] = []
            email_to_contacts[em].append(c)
            
    # Scan all message links
    links = session.scalars(
        select(MessageLinkModel).options(joinedload(MessageLinkModel.message))
    ).all()
    
    for link in links:
        report.total_links_scanned += 1
        
        if link.contact_id is not None:
            report.links_already_set += 1
            continue
            
        msg = link.message
        if not msg or msg.direction != "inbound":
            continue
            
        _, sender_email = RecruiterCRMService(session).parse_sender(msg.sender)
        sender_email = (sender_email or "").lower()
        
        if not sender_email or sender_email not in email_to_contacts:
            report.unresolved_senders += 1
            continue
            
        matched_contacts = email_to_contacts[sender_email]
        if len(matched_contacts) > 1:
            report.ambiguous_senders_skipped += 1
            continue
            
        # Match found
        if not dry_run:
            link.contact_id = matched_contacts[0].id
        report.links_updated += 1
        
    if not dry_run:
        session.commit()
        
    return report

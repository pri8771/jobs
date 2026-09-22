"""Offline boundaries for independent From/To/Cc fields and policy values."""
from jobs_automation.adapters.gmail import GmailAdapter
from jobs_automation.core.platforms import EmailPollingConfig
from jobs_automation.ingestion.engine import canonical_email_addresses

alias = 'owner+canary@example.com'
adapter = GmailAdapter(service=object())
for name, headers in (
    ('normal', [('From','recruiter@example.com'), ('To',alias)]),
    ('malformed_from', [('From','a@b.com;c@d.com'), ('To',alias)]),
    ('malformed_cc', [('From','recruiter@example.com'), ('To',alias), ('Cc','a@b.com;c@d.com')]),
):
    raw = adapter._parse_gmail_message_payload({
        'id':name, 'threadId':name, 'internalDate':'1790078400000',
        'payload':{'headers':[{'name':key,'value':value} for key,value in headers]},
    })
    print(name, {
        'recipients':raw.recipients,
        'canonical_participants':sorted(canonical_email_addresses([
            raw.sender,*raw.recipients,raw.provider_metadata['sender_address'],
        ])),
    })
for identities in ([alias], [alias, 'a@b.com;c@d.com']):
    config = EmailPollingConfig(canary_identities=identities)
    print('config_accepted', config.canary_identities, 'effective_policy', sorted(canonical_email_addresses(config.canary_identities)))

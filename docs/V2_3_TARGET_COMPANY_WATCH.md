# V2.3 Target Company Watch Contract

Artifact: A-V23-TARGET-COMPANY-WATCH

## Purpose

Track companies the user cares about and detect useful career opportunities/signals without turning the system into uncontrolled scraping or outreach.

## TargetCompany record

Minimum:
- id
- company_id or canonical company identity
- priority
- reason / strategy note
- target_role_families
- compensation_floor nullable
- location/remote constraints
- watch_status: ACTIVE | PAUSED | ARCHIVED
- created_at
- updated_at

## Observations

Store source-backed observations:
- new role
- role closed
- recruiter/contact signal
- company career-page update
- hiring-theme signal
- user-added note

Every observation includes:
- source type
- source reference/URL/message ID
- observed_at
- confidence
- normalized entities
- dedupe key

Do not store speculative facts as truth.

## Role watch

For each target company:
- query current public/approved sources,
- normalize jobs through existing ingestion/dedupe,
- match to target role families,
- surface new high-fit roles,
- suppress duplicates/already-applied roles.

## Relationship signal

Use existing contact/application/message evidence to answer:
- do we know a recruiter here?
- have we applied here before?
- did anyone respond before?
- is there a plausible referral path?

Do not auto-message contacts.

## Acceptance

- one target company can have multiple watched role families.
- duplicate observations collapse.
- already-known jobs do not create repeated alerts.
- source evidence is retained.
- relationship signal can be explained from source records.
- paused company creates no active alerts.

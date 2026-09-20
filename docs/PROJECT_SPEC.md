# Project Specification

## Product name

Working name: Jobs Automation

## Problem

Job searching is fragmented across job boards, alert emails, employer career sites, application forms, recruiter emails, interviews, and status updates. The same information is repeatedly entered and there is no durable, trustworthy record of the complete lifecycle.

## Product goal

Create a personal job-search operating system that turns incoming job opportunities into a structured pipeline:

Job alert or discovery
-> normalize
-> deduplicate
-> filter
-> score
-> review or prepare
-> apply
-> track communication
-> track interviews
-> track outcome
-> learn from results

## Primary user outcomes

The system should make it easy to answer:

- What new jobs arrived today?
- Which are actually worth applying to?
- Why did a job pass or fail the filter?
- Have I already seen or applied to this job?
- What resume and answers were used?
- What application state is each job in?
- What recruiter or employer messages are associated with it?
- What interviews are scheduled?
- Which applications need follow-up?
- What patterns are producing interviews and offers?

## Initial sources

1. LinkedIn
2. Indeed
3. ZipRecruiter
4. Dice
5. Employer career sites
6. Common ATS platforms discovered through job links
7. Gmail job/recruiting/application messages

The source list is extensible.

## Candidate profile

The application system must have one canonical candidate profile. It should contain reusable facts such as:

- names and contact fields
- location preferences
- target titles
- skills and technologies
- work history
- education
- portfolio/project links
- compensation preference
- work authorization and sponsorship answers
- willingness to relocate/travel
- demographic/self-identification answers only when explicitly provided
- reusable screening-question answers

Personal facts that are unknown remain unknown. The system must not guess them.

## Job filtering

Filtering is configurable and produces both a decision and explanation.

Suggested dimensions:

- target title / adjacent title
- required skills
- preferred skills
- seniority
- location and remote/hybrid/on-site
- compensation
- employment type
- sponsorship/work authorization compatibility
- travel requirement
- company preference/exclusion
- industry preference/exclusion
- years-of-experience mismatch
- clearance requirement
- must-have certifications
- duplicate / already applied
- freshness
- application effort
- source confidence

The filter should support:
- hard reject rules
- soft scoring
- must-review conditions

## Application preparation

For jobs that pass:

- capture full job description
- create a normalized qualification summary
- map candidate evidence to requirements
- choose the best base resume
- produce a tailored resume variant when useful
- produce optional cover letter
- prepare screening-question answers using the canonical candidate profile
- flag unknown or risky questions
- create an application packet with hashes/version IDs so the exact submitted material can be reconstructed

## Application execution

Execution is separate from discovery.

Modes:

1. Manual: user submits.
2. Assisted: system prepares fields/materials and opens the correct destination for review.
3. Auto-allowed: system can fill and submit through an approved adapter.
4. Blocked: system intentionally refuses because the platform, destination, or data is unsafe/unsupported.

No submit action happens without a policy decision.

## Lifecycle tracking

Minimum application states:

DISCOVERED
FILTERED_OUT
SHORTLISTED
PREPARING
READY_TO_APPLY
APPLYING
APPLIED
APPLICATION_CONFIRMED
RECRUITER_CONTACT
PHONE_SCREEN
INTERVIEW
FINAL_INTERVIEW
OFFER
REJECTED
WITHDRAWN
ACCEPTED
CLOSED
ERROR
NEEDS_REVIEW

State transitions must be event-based and timestamped.

## Email tracking

The system should ingest relevant Gmail messages and attach them to:

- source alert
- company
- job
- application
- interview
- offer

Examples include:
- job alerts
- application confirmations
- recruiter outreach
- scheduling emails
- rejection emails
- offer emails
- follow-ups
- assessments

Store provider IDs and normalized metadata; do not treat generated summaries as the raw record.

## Metrics

Eventually expose:

- jobs discovered
- jobs passing filters
- applications submitted
- response rate
- interview rate
- rejection rate
- offer rate
- source performance
- title/category performance
- company response time
- time from discovery to application
- resume variant performance
- reasons jobs are filtered out
- application funnel over time

## UX

MVP can be CLI/API-first. A dashboard may follow.

The user must always be able to:
- inspect the reason for a decision,
- override a decision,
- correct candidate facts,
- change a status,
- link/unlink an email,
- and see the audit log.

## Portability requirement

No critical project knowledge may exist only in an IDE-specific memory store. Rules, decisions, prompts, schemas, and current state live in Git.

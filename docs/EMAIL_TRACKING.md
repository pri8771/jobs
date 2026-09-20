# Email Monitoring and Recruiter Communication Rules

## Purpose

Email is the primary operating feed for both job discovery and application lifecycle tracking.

The system does not need real-time processing.

## Polling cadence

Default Gmail polling interval:

- every 4 hours
- configurable between roughly every 3 and 4 hours
- no push notifications required for MVP
- no minute-by-minute polling

The scheduler should perform a normal incremental mailbox sweep on each run.

Each sweep should:
1. query only messages newer than the last successful checkpoint, with a small overlap window for safety
2. deduplicate using Gmail message IDs
3. process job alerts
4. process recruiter/company communication
5. process application confirmations/status changes
6. link messages to existing companies/jobs/applications when confidence is sufficient
7. create NEEDS_REVIEW items for ambiguous messages
8. advance the mailbox checkpoint only after successful persistence

A broader reconciliation sweep may run once per day to catch missed or late-indexed messages.

## Message categories

At minimum classify:

- JOB_ALERT
- APPLICATION_CONFIRMATION
- RECRUITER_OUTREACH
- RECRUITER_FOLLOW_UP
- CANDIDATE_REPLY
- SCREENING_REQUEST
- ASSESSMENT_REQUEST
- INTERVIEW_REQUEST
- INTERVIEW_CONFIRMATION
- INTERVIEW_RESCHEDULE
- INTERVIEW_CANCELLED
- REJECTION
- OFFER
- BACKGROUND_CHECK
- ONBOARDING
- GENERAL_COMPANY_COMMUNICATION
- UNKNOWN_REVIEW_REQUIRED

## Thread-level tracking

Do not treat emails as unrelated individual records when Gmail indicates they belong to the same thread.

For every recruiting/application thread, retain:
- Gmail message ID
- Gmail thread ID
- sender
- recipients
- timestamp
- subject
- normalized body/reference
- direction: inbound or outbound
- company association
- contact/recruiter association
- job association
- application association
- classification
- confidence
- extraction/version metadata

Preserve all messages in chronological order.

Never overwrite prior communication just because a newer email arrived.

## Incoming and outgoing mail

Track both directions.

Examples:
- recruiter emails candidate
- candidate replies
- recruiter schedules screen
- candidate confirms
- hiring team sends interview details
- candidate sends thank-you/follow-up
- company sends rejection/offer

Outgoing mail matters for:
- follow-up timing
- avoiding duplicate replies
- understanding the full conversation
- knowing whether the candidate already answered a recruiter
- measuring response times

## Recruiter/contact records

When possible maintain a contact record containing:
- name
- email
- company
- title/role when known
- first-contact date
- last-contact date
- associated jobs
- associated applications
- thread IDs

One recruiter may be linked to multiple roles/applications.

A new role discussed in an existing recruiter thread must not automatically be merged into the old application.

## Linking priority

Link messages using strongest evidence first:

1. explicit requisition/job ID
2. known application confirmation/reference
3. exact job title + company
4. known recruiter/contact + existing thread
5. canonical application URL
6. subject/thread context
7. semantic inference as fallback

If multiple applications are plausible and confidence is insufficient, use NEEDS_REVIEW.

Do not guess.

## Lifecycle effects

High-confidence messages may create lifecycle events.

Examples:
- application confirmation -> APPLICATION_CONFIRMED
- recruiter outreach -> RECRUITER_CONTACT
- screening request -> PHONE_SCREEN / SCREENING
- interview confirmation -> INTERVIEW
- rejection -> REJECTED
- offer -> OFFER

The raw email remains the evidence.

A model summary must never replace the source message.

## Follow-up logic

The system should eventually create follow-up tasks based on the application/contact timeline.

Examples:
- recruiter asked a question and no candidate reply is detected
- candidate replied and recruiter has been silent for a configurable number of days
- application submitted with no response after a configured period
- interview completed and no thank-you/follow-up is recorded
- promised recruiter follow-up date has passed

Do not auto-send recruiter emails in the initial versions.

Drafting may be automated later, but sending should be a separate explicit capability.

## Job-alert email handling

Job-alert messages from LinkedIn, Indeed, ZipRecruiter, Dice, and other approved sources should be parsed during the same 4-hour mailbox sweep.

For each listed job:
- extract source
- job ID if available
- title
- company
- location
- compensation if present
- job URL
- application URL if distinct
- alert/search that produced it
- received timestamp

Then normalize, deduplicate, score, and route according to the project workflow.

## Reliability rules

- mailbox polling must be idempotent
- duplicate processing must not duplicate jobs, messages, events, or applications
- failed runs must not advance the checkpoint past uncommitted work
- retain a small overlap window between polling intervals
- daily reconciliation should detect any gaps
- processing one malformed email must not fail the entire mailbox batch

## Privacy

Use the narrowest practical Gmail scope.

Only retrieve/store content needed for job-search automation.

Do not alter, delete, archive, or send email in the initial ingestion version.

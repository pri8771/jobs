# Platform Constraints and Automation Policy

Last reviewed: 2026-09-20

Platform rules change. Re-check official terms before enabling any automatic submission adapter.

## LinkedIn

Use:
- profile
- job search
- job alerts
- saved/application tracking features
- manual/native Easy Apply
- outbound links to employer career sites

Current official LinkedIn terms prohibit automated means or scraping/data extraction unless expressly authorized. LinkedIn also applies Easy Apply daily/speed limits intended in part to curb bots.

Project policy:
- discovery from alert emails: allowed design path
- storing job data that arrived in the user's own email: allowed design path
- browser bot that drives LinkedIn and submits Easy Apply: disabled
- manual/native LinkedIn submission: supported
- external employer/ATS destination reached from a LinkedIn alert: evaluate under that destination's policy

Official references:
- https://www.linkedin.com/legal/jobs-terms-conditions
- https://www.linkedin.com/help/linkedin/answer/a8068422
- https://www.linkedin.com/help/linkedin/answer/a511279

## Indeed

Indeed's 2026 Terms and Job Seeker Guidelines explicitly prohibit third-party bots/automation for Indeed Apply and prohibit submitting job applications by automated means outside tools the site explicitly offers or approves.

Project policy:
- receive and parse Indeed alert emails
- score and prepare application materials
- manual/native Indeed Apply
- no third-party automated Indeed Apply
- external employer/ATS pages are evaluated separately

Official references:
- https://www.indeed.com/legal
- https://support.indeed.com/hc/en-us/articles/360028540531-Indeed-Job-Seeker-Guidelines
- https://support.indeed.com/hc/en-us/articles/204488890-Starting-Stopping-and-Managing-Job-Alerts

## ZipRecruiter

ZipRecruiter offers candidate profiles and 1-Click Apply. It also operates partner APIs, but the partner job APIs are primarily for posting/distributing jobs and receiving applications as an employer/ATS integration, not a blanket candidate-side auto-apply API.

Project policy:
- profile and alerts
- parse the user's alert emails
- use native 1-Click Apply manually unless a current approved candidate automation path is confirmed
- do not assume partner APIs authorize candidate-side automation
- re-check terms before building a submission adapter

Official references:
- https://www.ziprecruiter.com/job-seekers
- https://www.ziprecruiter.com/partner/documentation/job-api/
- https://www.ziprecruiter.com/partner/documentation/apply-webhook/

## Dice

Dice is the fourth initial board. It supports a technologist profile plus daily/weekly job alerts.

Project policy:
- profile and alerts
- parse alert emails
- assisted/manual applications initially
- re-check current candidate terms before enabling any automated submission adapter

Official reference:
- https://www.dice.com/support/candidate-help/finding-a-job/job-alerts-and-setting-them-up.html

## Employer career sites and ATS platforms

These are the primary eventual auto-apply target.

Potential ATS families:
- Greenhouse
- Lever
- Workday
- Ashby
- SmartRecruiters
- iCIMS
- Taleo / Oracle Recruiting
- SuccessFactors
- ADP Recruiting
- UKG

Do not assume all instances of an ATS have identical rules or forms.

Automation policy:
1. identify the destination and terms
2. classify as MANUAL_ONLY, ASSISTED, AUTO_ALLOWED, or BLOCKED
3. persist the policy result and reason
4. only then execute
5. never bypass CAPTCHA or anti-bot controls
6. if a form asks an unknown personal fact, move to NEEDS_REVIEW

## Email

Gmail ingestion is central because it is both portable and provider-agnostic. The system should prefer receiving platform-generated alerts/status emails rather than scraping board pages.

## Policy registry

Runtime should eventually use a versioned policy registry containing:
- platform
- domain
- adapter
- allowed capabilities
- evidence/reference
- date reviewed
- expiration/review date
- notes

Auto-submit must default to deny when there is no current allow decision.

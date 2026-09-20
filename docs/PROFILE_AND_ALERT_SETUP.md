# Profile and Job Alert Setup

## Phase objective

Before application automation, make the four source profiles consistent and create high-signal alerts that feed the same email inbox.

Initial platforms:
1. LinkedIn
2. Indeed
3. ZipRecruiter
4. Dice

## Canonical-first rule

Do not independently improvise profile content on each site.

First complete:
- config/candidate_profile.example.yaml -> private candidate profile
- config/job_search.example.yaml -> actual search configuration

Then use those values to populate each platform.

## Profile checklist

Keep consistent across platforms:
- headline / target role family
- location
- remote preference
- current and previous roles
- skills
- resume
- education
- portfolio/GitHub/website links
- compensation preference when supported
- open-to-work visibility preference

Record platform-specific differences in state/CURRENT.md or a future profile_sync table.

## Suggested alert families

Do not create dozens of near-identical alerts. Begin with a small set of high-value role families and expand based on results.

Example families:
- SAP BTP / SAP Integration / SAP Automation
- AI Automation / Applied AI / AI Platform
- Enterprise Integration / Platform Engineering
- Technical Product / Solutions / Automation leadership
- IT / Business Systems leadership where the technical scope matches

Each alert definition should specify:
- keywords/title
- location
- remote/hybrid/on-site
- minimum compensation when supported
- date posted
- seniority
- exclusions

## Email strategy

All alerts should land in the same Gmail account.

Preferred flow:
platform -> alert email -> Gmail query/label -> ingestion worker -> source parser -> normalized jobs

Suggested Gmail label:
Jobs/Alerts

Suggested follow-on labels:
Jobs/Applications
Jobs/Recruiters
Jobs/Interviews
Jobs/Offers
Jobs/Review

## LinkedIn

LinkedIn currently supports up to 20 job alerts and daily/weekly email/app notifications. Start with daily email for high-value searches.

Manual setup is preferred for profile and alert creation because authentication/MFA and current platform rules make browser automation unnecessary and brittle.

## Indeed

Create alerts from saved searches and ensure alert emails are enabled. Use native/manual application flow for Indeed Apply.

## ZipRecruiter

Complete the profile/resume because native 1-Click Apply relies on saved candidate information. Enable relevant match/alert emails.

## Dice

Complete the technologist profile. Dice supports keyword/filter job alerts and recommended-job alerts, with daily or weekly cadence.

## Verification checklist

For each platform:
- profile complete enough for matching
- correct resume uploaded
- target location correct
- alert created
- email alert enabled
- test alert received or existing alert located
- sender/domain recorded
- application/profile email notifications enabled
- source account marked verified

## What automation should do after setup

It should not repeatedly log into all four sites just to search.

It should:
1. consume alert emails
2. extract all included jobs
3. dedupe them across sources
4. enrich only when needed
5. score/filter
6. put qualified jobs in the application queue

This makes email the lowest-friction shared ingestion bus.

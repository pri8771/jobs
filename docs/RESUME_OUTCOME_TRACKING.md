# Resume Outcome Tracking

## Purpose

Jobs Automation must learn which resume strategies and exact resume versions are producing useful outcomes.

This is not optional analytics. Every real application must preserve enough information to answer:

- Which resume family was used?
- Which exact tailored resume version was submitted?
- Which job/role/company received it?
- Did the application receive a recruiter response?
- Did it reach screening?
- Did it reach an interview?
- Did it reach a final interview?
- Did it produce an offer?
- Was the offer accepted?
- How long did each stage take?
- Which resume families work best for which role families, industries, seniority levels, salary bands, sources, and companies?

## Attribution levels

Track performance at two distinct levels.

### 1. Resume family

Examples:
- Enterprise Automation & Solutions Architect
- Senior Software / AI Automation
- Senior iOS / Mobile Lead
- IT Applications & Infrastructure Manager

This answers strategic questions such as:

"Does Enterprise Automation positioning outperform AI Software positioning for $150K+ solutions roles?"

### 2. Exact submitted resume version

Every tailored resume used in a real application must be immutable and uniquely identifiable.

Track:
- resume_variant_id
- resume_family
- version
- parent/base variant
- job-specific tailoring target
- artifact_id
- SHA-256/content hash
- template/source version
- generated_at
- model/prompt version when AI tailoring was involved

This answers:

"Which exact resume did Microsoft receive?"

and:

"Did the revised V14 resume outperform V12?"

## Required application linkage

A real application must link to an immutable application packet.

The packet must link to:
- exact resume variant
- exact final resume artifact
- exact cover letter artifact if used
- exact answers submitted
- candidate profile version
- packet hash

Once an application is submitted, its resume linkage must never silently change even if a newer resume is created later.

## Outcome stages

At minimum measure:

1. SUBMITTED / APPLICATION_CONFIRMED
2. RECRUITER_RESPONSE
3. SCREEN / PHONE_SCREEN
4. INTERVIEW
5. FINAL_INTERVIEW
6. OFFER
7. ACCEPTED
8. REJECTED / CLOSED / WITHDRAWN

The event log remains authoritative.

Derived analytics may calculate:
- applications submitted
- recruiter response rate
- screen rate
- interview rate
- final-interview rate
- offer rate
- acceptance rate
- median time to first response
- median time to screen/interview/offer

## Dimensions

Performance should eventually be sliced by:

- resume family
- exact resume variant/version
- target role family
- normalized job title
- company
- industry
- source platform
- application destination / ATS
- compensation band
- seniority
- remote / hybrid / onsite
- location
- date range
- tailored vs base resume
- cover letter vs no cover letter

## Examples

Example A:

Enterprise Automation & Solutions Architect v12

- 24 applications
- 9 recruiter responses
- 6 screens
- 4 interviews
- 1 offer

Example B:

AI Automation v8

- 22 applications
- 3 recruiter responses
- 1 screen
- 0 interviews

This should inform future resume selection, but the system must account for sample size and job mix before drawing strong conclusions.

## Causality guardrail

Do not automatically claim that one resume caused better outcomes merely because conversion was higher.

Role mix, company quality, market conditions, compensation, application timing, source and sample size may differ.

Label performance as descriptive evidence unless controlled experimentation supports a stronger inference.

## Resume selection feedback loop

Later versions should allow the resume selector to use historical performance as one input.

Example:

For a new Senior Solutions Architect role:
- semantic fit says Enterprise Automation = 91
- historical screen rate for similar jobs using Enterprise Automation = 27%
- AI Automation family historical screen rate for same role cluster = 11%

The system may prefer Enterprise Automation, while still considering job-specific evidence and recency.

## Experimentation

Eventually support explicit experiments such as:

- family A vs family B
- summary A vs summary B
- 1-page vs 2-page
- skills emphasis variants
- tailored vs lightly tailored

Experiments must not fabricate qualifications.

Each experiment should record:
- hypothesis
- target population
- variants
- assignment method
- start/end dates
- sample size
- stage conversion metrics

## Near-term requirement

For V1.4-V1.6, the minimum requirement is:

- assign a resume family to every packet,
- assign an immutable resume variant/version,
- preserve the exact submitted artifact/hash,
- link the application permanently to that packet,
- record lifecycle outcomes through application events.

Advanced resume-performance analytics can be built after the first-real-application proof, but the data required for those analytics must be captured correctly from the first real application onward.

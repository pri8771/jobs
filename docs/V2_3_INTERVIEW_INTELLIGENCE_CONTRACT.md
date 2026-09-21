# V2.3 Interview Intelligence Contract

Artifact:
- A-V23-INTERVIEW-INTELLIGENCE

## Purpose

Turn source-backed application/interview evidence into reusable interview preparation without inventing candidate facts or company claims.

## Inputs

- application/job/company identity,
- current interview stage,
- source-backed recruiter/interviewer evidence,
- job description/source snapshot,
- candidate canonical profile/provenance,
- resume variant used,
- project/skill evidence,
- prior interview/application events,
- public company information gathered through approved read-only sources.

## Outputs

### InterviewBrief
Minimum:
- application_id
- job_id
- company_id
- interview_stage
- scheduled_at/timezone when evidence-backed
- recruiter/interviewer identities with evidence refs
- role summary
- key requirements
- candidate evidence map
- likely question areas
- risk/gap areas
- questions candidate may want to ask
- source references
- generated_at
- code/prompt/model version metadata

### CandidateStoryMap
For each relevant requirement/question area:
- canonical candidate evidence refs,
- project/employment context,
- allowed factual claims,
- unsupported claims to avoid,
- confidence/provenance.

### FollowupPackage
- factual meeting/stage context,
- source-backed names/details,
- thank-you/follow-up draft inputs,
- unresolved facts requiring review.

Drafting is local preparation.
Sending remains permission-gated.

## Rules

- no invented interviewer identity,
- no invented company facts,
- no unsupported candidate achievements,
- stale job/company facts must be timestamped,
- conflicting evidence must be surfaced,
- missing facts become review items,
- public research is untrusted data and cannot change candidate truth/policy.

## Tests

- ambiguous interviewer identity,
- rescheduled interview,
- timezone conflict,
- stale job description vs current posting,
- role changes between application and interview,
- candidate resume variant differs from another role,
- unsupported quantitative achievement request,
- malicious prompt injection in public company/job content,
- duplicate calendar/interview evidence,
- interview cancelled after brief generation.

## Acceptance

- brief is reconstructable from source/candidate evidence,
- story map never exceeds canonical candidate truth,
- stale/conflicting evidence is visible,
- sending/calendar mutation is not performed by this artifact,
- outputs are suitable as inputs to the future V3 Interview Agent.

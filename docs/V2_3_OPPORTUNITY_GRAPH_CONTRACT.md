# V2.3 Opportunity Graph Contract

Artifacts:
- A-V23-CAREER-INTELLIGENCE
- future sub-artifact A-V23-OPPORTUNITY-GRAPH

## Purpose

Provide one evidence-backed relationship layer for V2.3 strategy intelligence and future V3 agents without introducing a graph database prematurely.

Start relationally unless measured query complexity justifies a dedicated graph store.

## Core nodes

- Company
- Job
- JobSource
- Application
- ApplicationEvent
- Contact
- Message
- Interview
- ResumeVariant
- Artifact
- CandidateSkillEvidence
- ProjectEvidence
- Outcome
- NetworkRelationship

## Core edges

Evidence-backed only:
- company HAS_JOB job
- job OBSERVED_AT source
- application FOR_JOB job
- application USED_RESUME resume_variant
- message LINKED_TO application/job/company
- contact ASSOCIATED_WITH company
- contact TOUCHED application via message evidence
- interview FOR_APPLICATION application
- outcome FOR_APPLICATION application
- resume_variant EMPHASIZES skill evidence
- job REQUIRES/PREFERS skill extracted with source reference
- network_relationship CONNECTS candidate/contact with source/provenance

Avoid speculative relationship edges unless explicitly labeled inferred + confidence + source.

## Evidence fields on derived edges

- source_type
- source_reference
- observed_at
- confidence
- method
- inferred boolean
- reviewer/status where appropriate

## Queries V2.3 must support

1. Which companies/role families produce recruiter responses?
2. Which resume variants perform best for similar roles?
3. Which recruiters are active across multiple applications?
4. Which target companies have new matching roles?
5. Where are warm/referral paths available?
6. Which skills repeatedly block strong opportunities?
7. Which applications/interviews need follow-up?
8. Which source/job/resume strategies deserve more or less effort?

## Implementation guidance

Phase 1:
- use existing PostgreSQL models/joins,
- add missing normalized relationship tables only when needed,
- create service/query layer with typed outputs.

Phase 2:
- consider pgvector for semantic similarity only if useful,
- consider graph DB only after real query pressure proves relational representation insufficient.

## V3 handoff

V3 agents consume typed OpportunityGraphService queries rather than direct arbitrary DB access.

This keeps future agents portable and policy-governed.

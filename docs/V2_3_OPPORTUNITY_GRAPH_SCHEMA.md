# V2.3 Opportunity Graph Schema

Artifact: A-V23-OPPORTUNITY-GRAPH

## Design choice

Do not introduce Neo4j or another graph database for V2.3 by default.

The existing PostgreSQL domain model already represents many core relationships. Build an evidence-backed graph **projection/service** over relational truth, adding explicit edge persistence only for relationships not already captured cleanly.

## Node types

Minimum:
- company
- job
- contact
- application
- message_thread
- interview
- resume_variant
- candidate_evidence
- skill
- project
- target_company
- experiment

Potential later:
- recruiter_team
- referral_path
- public_content
- portfolio_asset

## Existing direct relationships

Prefer existing FKs/relations where available:
- company -> job
- job -> application
- application -> packet -> resume_variant
- application -> interview
- message -> message_link -> company/job/application
- contact -> company
- application -> application_event

Do not duplicate these into a generic edge table unless the graph service needs materialized snapshots for performance.

## Additional evidence-backed edge model

For relationships not already represented:

`OpportunityEdge`

Fields:
- id
- subject_type
- subject_id
- predicate
- object_type
- object_id
- source_type
- source_reference
- confidence
- evidence_hash nullable
- valid_from
- valid_to nullable
- status: ASSERTED | REVIEW_REQUIRED | INVALIDATED
- created_at
- updated_at

Examples:
- contact --RECRUITS_FOR--> role_family
- contact --REFERRED_CANDIDATE_TO--> company
- project --EVIDENCES--> skill
- resume_variant --TARGETS--> role_family
- company --IS_TARGET_COMPANY--> target_company record
- contact --KNOWN_BY--> candidate relationship record

## Provenance rule

No relationship edge exists without provenance.

Sources may include:
- email/provider message ID
- user confirmation
- application/job record
- public company/career page
- imported professional contact evidence

Model inference alone may propose REVIEW_REQUIRED edges but may not assert them as truth.

## Graph service queries

Provide typed queries such as:
- opportunities_for_company(company_id)
- contacts_for_company(company_id)
- applications_with_contact(contact_id)
- referral_paths_to_company(company_id)
- resume_outcomes_for_role_family(role_family)
- skills_evidenced_by_projects()
- open_opportunities_with_relationship_signal()

## Graph versioning

Graph projection should be rebuildable from underlying source truth where possible.

Derived scores belong in analytics/strategy services, not irreversible graph edges.

## V3 compatibility

Future agents consume typed graph queries; they do not directly write arbitrary edges.

Writes go through evidence/policy validation.

## Acceptance tests

- rebuild from relational fixtures yields stable graph.
- same source evidence does not duplicate edge.
- invalidated evidence removes/hides active edge.
- inferred relationship stays REVIEW_REQUIRED.
- user-confirmed relationship can become ASSERTED.
- graph queries preserve source references.

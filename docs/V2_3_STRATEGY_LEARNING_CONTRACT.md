# V2.3 Strategy Learning Contract

## Goal

Use real job-search outcomes to improve where the system spends effort without overstating weak evidence.

## Inputs

- jobs and role families
- sources
- companies
- resume families/variants
- application events
- recruiter responses
- screens/interviews/offers
- timing
- compensation/location/work arrangement
- explicit experiment assignments when present

## Required outputs

### Resume strategy
- response/screen/interview/offer rate by resume family/version
- similar-role comparisons
- sample sizes
- recency window

### Source strategy
- opportunity quality by source
- application conversion by source
- recruiter response by source
- effort/cost where measurable

### Role strategy
- role-family funnel
- compensation distribution
- location/work arrangement outcomes
- common reject/gap reasons

### Company strategy
- response time
- recruiter engagement
- repeat role patterns
- historical outcome

## Statistical guardrails

- show N for every rate,
- suppress/flag strong conclusions with very small N,
- label observational differences descriptive,
- experiments are separate from observational comparisons,
- do not claim a resume caused an outcome unless the experimental design supports it,
- account for recency where possible.

## Recommendation contract

Recommendations must state:
- evidence used,
- sample size,
- confidence/uncertainty,
- suggested action,
- reversible vs consequential nature.

Examples:
- "Prefer enterprise-automation resume for similar roles" only with supporting sample/evidence.
- "Gather more data" is valid when evidence is weak.

## Future worker slices

- build typed aggregation queries,
- add minimum-sample warning policy,
- add experiment-assignment persistence,
- add recommendation object with evidence references,
- add tests for sparse/confounded data.

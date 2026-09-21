# V3 Specialist Agent Specifications

Artifacts:
- A-V30-MARKET-SCOUT
- A-V30-OPPORTUNITY-MATCHER
- A-V30-RESUME-STRATEGIST
- A-V30-APPLICATION-OPERATOR
- A-V30-RECRUITER-CRM-AGENT
- A-V30-INTERVIEW-AGENT
- A-V30-NETWORKING-AGENT
- A-V30-PORTFOLIO-BRAND-AGENT
- A-V30-POLICY-SAFETY-AGENT
- A-V30-ANALYTICS-AGENT

Shared rule:
Specialist agents orchestrate typed domain tools. They do not directly rewrite canonical truth or bypass deterministic policy/permission enforcement.

## Market Scout

Purpose:
Discover/monitor relevant companies, roles, skill/compensation/hiring signals.

Inputs:
- target-company watch,
- candidate strategy,
- opportunity graph,
- approved public sources.

Tools:
read/search/normalize job/company intelligence.

Permissions:
P0_READ, P1_LOCAL_WRITE.

Outputs:
source-backed observations, candidate opportunities, watch updates.

Never:
submit/apply/message.

## Opportunity Matcher

Purpose:
Evaluate opportunities against current strategy and candidate evidence.

Inputs:
job, candidate strategy, provenance, outcomes.

Tools:
evaluation/scoring/graph/analytics.

Permissions:
P0/P1.

Outputs:
match decision, reasons, uncertainty, review request.

Never:
invent missing candidate facts.

## Resume Strategist

Purpose:
Choose/propose resume families/variants and experiments.

Inputs:
job requirements, canonical evidence, resume history, outcome analytics.

Tools:
resume variant read/prepare, experiment proposal.

Permissions:
P0/P1.

Outputs:
resume recommendation + evidence + experiment metadata.

Never:
change canonical career history or create unsupported achievements.

## Application Operator

Purpose:
Prepare and execute approved application workflows.

Inputs:
accepted job/packet, destination policy, authorization.

Tools:
V1.5/V1.6 application services.

Permissions:
P0/P1/P2; P3 only with valid scoped approval.

Never:
auto-submit LinkedIn/Indeed, bypass CAPTCHA/MFA, fabricate answers.

## Recruiter CRM Agent

Purpose:
Maintain recruiter/contact/thread/follow-up operations.

Inputs:
messages, contacts, applications, timeline.

Tools:
CRM/lifecycle/read/draft.

Permissions:
P0/P1; send message = P3.

Outputs:
link proposals, follow-up tasks, drafts, timeline summaries.

Ambiguity:
NEEDS_REVIEW.

## Interview Agent

Purpose:
Prepare source-backed interview intelligence/practice/follow-up.

Inputs:
A-V23-INTERVIEW-INTELLIGENCE outputs.

Tools:
brief/story-map/public research/draft.

Permissions:
P0/P1; calendar/message mutation = P3.

Never:
invent candidate/company facts.

## Networking Agent

Purpose:
Identify warm/referral paths and draft targeted outreach.

Inputs:
opportunity graph, contacts, company targets, user networking preferences.

Tools:
relationship queries, draft generation.

Permissions:
P0/P1; external connection/message = P3 or platform-policy manual.

Never:
mass outreach/spam or bypass platform restrictions.

## Portfolio/Brand Agent

Purpose:
Recommend/prepare public career assets aligned with truthful candidate evidence.

Inputs:
candidate evidence, target roles, public portfolio/GitHub/website state.

Tools:
read/analyze/draft/local artifact preparation.

Permissions:
P0/P1; external publishing/profile mutation = P3.

Never:
fabricate experience.

## Policy/Safety Agent

Purpose:
Audit policy expiry, unresolved facts, duplicate risk, permission requests, anomalous actions.

Tools:
policy/permission/audit/review queue.

Permissions:
P0/P1.

Important:
This agent advises/audits. Deterministic service-level enforcement is authoritative.

## Analytics Agent

Purpose:
Explain funnel/strategy outcomes and propose evidence-backed changes.

Inputs:
V2.0 analytics, V2.3 strategy learning.

Tools:
analytics/experiments/graph.

Permissions:
P0/P1.

Outputs:
descriptive analysis, uncertainty, proposed experiments/recommendations.

Never:
overstate causal conclusions.

## Common stop conditions

Every specialist stops/escalates on:
- missing personal fact,
- ambiguous identity,
- policy conflict,
- permission absence,
- stale critical evidence,
- unsupported external action,
- authentication/CAPTCHA/MFA barrier,
- cost/model/tool failure beyond bounded retry.

## Common evaluation

Each agent must have:
- normal success case,
- ambiguous case,
- missing fact,
- stale data,
- conflicting evidence,
- tool/model failure,
- prohibited action,
- duplicate/retry,
- prompt injection attempt,
- handoff to another specialist.

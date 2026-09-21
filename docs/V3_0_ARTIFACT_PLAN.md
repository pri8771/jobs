# V3.0 Artifact Plan — Autonomous Career Agent Network

## Goal

Coordinate specialized career agents over one shared, auditable artifact/event truth layer.

## Foundational artifacts

### A-V30-AGENT-RUNTIME
- task routing
- bounded agent execution
- retries/timeouts
- artifact inputs/outputs
- cancellation
- cost/model selection
- observability

### A-V30-PERMISSION-MODEL
Each action class:
- read-only
- local write
- external draft
- user-approved external write
- prohibited/blocked

Consequential actions remain human-governed.

### A-V30-SHARED-MEMORY
- career facts
- artifact references
- opportunity graph
- outcomes
- strategy history
- agent summaries with source links

Derived summaries never replace raw evidence.

## Specialist agent artifacts

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

Each agent must define:
- inputs
- tools
- permissions
- output artifacts
- stop conditions
- evaluation cases
- handoff rules

## V3.0 integration artifact

A-V30-CAREER-AGENT-NETWORK

Acceptance scenario:
User says "Find me a better job."

The system:
1. evaluates current strategy/outcomes,
2. discovers and ranks opportunities,
3. checks network/referral paths,
4. chooses evidence-backed resume strategy,
5. prepares application work,
6. executes only permitted actions,
7. tracks contacts/interviews/outcomes,
8. proposes next career actions,
9. asks the user only for consequential decisions or missing facts,
10. records all actions/evidence in the shared artifact graph.


## Prepared implementation contracts

- `docs/V3_PERMISSION_MODEL.md`
- `docs/V3_TOOL_PERMISSION_MATRIX.md`
- `docs/V3_RUNTIME_DATA_CONTRACTS.md`
- `docs/V3_SHARED_MEMORY_CONTRACT.md`
- `docs/V3_AGENT_HANDOFF_PROTOCOL.md`
- `docs/V3_SPECIALIST_AGENT_SPECS.md`
- `docs/V3_AGENT_EVAL_MATRIX.md`
- `docs/V3_INTEGRATION_ACCEPTANCE_SCENARIOS.md`
- `docs/FUTURE_SCHEMA_MIGRATION_PLAN_V16_V23_V30.md`

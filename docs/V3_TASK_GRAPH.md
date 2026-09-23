# V3 Task Graph - Agent Network

This document defines the highly granular, step-by-step tasks required for a "point-and-shoot" local model to implement the V3 Agent Runtime and Specialist Agents.

## 0. Foundations & Data Models
1. **V3-F01**: Create `migrations/versions/006_v3_agent_runtime_foundation.py`. Add `AgentTaskModel`, `AgentCheckpointModel`, `AgentMemoryModel`, `AgentTraceEventModel`. Run `alembic upgrade head`.
2. **V3-F02**: Create `src/jobs_automation/agents/models.py`. Define Pydantic schemas for `AgentTask`, `AgentStatus`, `MemoryEntry`, `TraceEvent`.
3. **V3-F03**: Update `src/jobs_automation/db/models.py` to expose the new models.

## 1. Permission & Memory Runtime
4. **V3-R01**: Create `src/jobs_automation/agents/permissions.py`. Implement `V3PermissionInterceptor` that wraps V2.3 `PermissionGate` and enforces `min(agent_ceiling, tool_req, policy, approval)`.
5. **V3-R02**: Create `src/jobs_automation/agents/memory.py`. Implement `ScopedMemoryService` that can store and retrieve `AgentMemoryModel` entries, maintaining the M0-M4 boundary.
6. **V3-R03**: Add unit tests for `permissions.py` in `tests/test_v3_permissions.py`.
7. **V3-R04**: Add unit tests for `memory.py` in `tests/test_v3_memory.py`.

## 2. Agent Runtime Core
8. **V3-RT01**: Create `src/jobs_automation/agents/runtime.py`. Implement `AgentRuntime`. Add `start_task(task_type, payload)`, `resume_task(task_id)`, `cancel_task(task_id)`.
9. **V3-RT02**: Implement retry and time/cost limits in `runtime.py`. Track attempts on `AgentTaskModel`.
10. **V3-RT03**: Create `src/jobs_automation/agents/tracing.py`. Implement `TraceEmitter` that logs tool execution boundaries to `AgentTraceEventModel`.
11. **V3-RT04**: Add unit tests for `runtime.py` covering failure scenarios and retry bounds.

## 3. Tool Facade (V3 Bridge)
12. **V3-TL01**: Create `src/jobs_automation/tools/facade.py`. Expose V2.3 `InterviewIntelligenceService`, `TargetCompanyService`, and `StrategyLearningService` as typed, transport-neutral tool functions (e.g. `get_interview_brief`, `add_target_company`).
13. **V3-TL02**: Add strict type-checking and docstrings to all functions in `facade.py` so agents understand inputs/outputs.
14. **V3-TL03**: Add unit tests for `facade.py`.

## 4. Specialist Agents (Scout & Matcher)
15. **V3-A01**: Create `src/jobs_automation/agents/specialists/market_scout.py`. Implement `MarketScoutAgent` class with permissions `P0_READ, P1_LOCAL_WRITE`. Uses `facade.py` tools to read job postings and normalize them.
16. **V3-A02**: Create `src/jobs_automation/agents/specialists/opportunity_matcher.py`. Implement `OpportunityMatcherAgent` class. Uses evaluation and graph tools to output `match decision`.
17. **V3-A03**: Add tests for `MarketScoutAgent` mocking the facade tools.
18. **V3-A04**: Add tests for `OpportunityMatcherAgent` mocking the facade tools.

## 5. Specialist Agents (Resume & Operator)
19. **V3-A05**: Create `src/jobs_automation/agents/specialists/resume_strategist.py`. Implement `ResumeStrategistAgent`. Uses tailoring and strategy tools.
20. **V3-A06**: Create `src/jobs_automation/agents/specialists/application_operator.py`. Implement `ApplicationOperatorAgent`. Binds strictly to `P2_EXTERNAL_PREP` and requires `P3` approval for submit tools.
21. **V3-A07**: Add tests for `ResumeStrategistAgent`.
22. **V3-A08**: Add tests for `ApplicationOperatorAgent`, ensuring it cannot bypass `P3` checks.

## 6. Specialist Agents (CRM & Interview)
23. **V3-A09**: Create `src/jobs_automation/agents/specialists/recruiter_crm.py`. Implement `RecruiterCRMAgent`. Reads lifecycle state, outputs drafted replies as `NEEDS_REVIEW` tasks.
24. **V3-A10**: Create `src/jobs_automation/agents/specialists/interview_agent.py`. Implement `InterviewAgent`. Generates interview briefs and story maps.
25. **V3-A11**: Add tests for CRM and Interview agents.

## 7. Hand-off & Integration
26. **V3-I01**: Create `src/jobs_automation/agents/registry.py`. Register all specialist agents.
27. **V3-I02**: Implement `AgentHandoffProtocol` in `runtime.py`. Allow one agent to yield `task.status = BLOCKED` and specify `next_agent`.
28. **V3-I03**: Create `src/jobs_automation/cli/agent_cli.py`. Add commands like `intel agents start <task_type>`, `intel agents status <task_id>`.
29. **V3-I04**: Create end-to-end fixture test `tests/test_v3_integration.py` demonstrating `MarketScout` finding a role and handing off to `OpportunityMatcher`.

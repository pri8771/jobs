# Prepared Work Queue — V1.6 to V3.0

Purpose:
Worker-ready downstream tasks prepared by ChatGPT while the single Antigravity implementation session works the current critical path.

This file is **not the active WORK_QUEUE** and does not authorize skipping phase gates.
When a phase opens, ChatGPT may promote the appropriate bounded tasks into `coordination/WORK_QUEUE.md`.

Story points measure complexity, not time.

## Promotion rules

A task is promoted only when:
- its dependency gate is open,
- it does not conflict with the active branch/batch,
- architecture/acceptance contract is stable enough,
- task size is SP1-SP5,
- live-action authority is not implied.

## V1.6 prepared tasks

| ID | SP | Task | Depends on | Output |
|---|---:|---|---|---|
| V16-E01 | 3 | typed scoped authorization record | G15 | model/service/tests |
| V16-E02 | 3 | deny-by-default expiring destination policy | G15 | policy model/service/tests |
| V16-E03 | 4 | immutable attempt ledger + idempotency | V16-E01 | durable state/tests |
| V16-E04 | 3 | immediate pre-submit packet/provenance integrity gate | V16-E01 | validator/tests |
| V16-E05 | 3 | kill switch, pacing, CAPTCHA/MFA/session routing | G15 | runtime guards/tests |
| V16-E06 | 4 | external confirmation validator | V16-E03 | confirmation evidence/tests |
| V16-E07 | 4 | transport-neutral ATS adapter contract | G15 | interface/test adapter |
| V16-E08 | 5 | first approved supported ATS transport | current policy approval | implementation/tests |
| V16-E09 | 4 | adversarial submission matrix automation | V16-E01..08 | regression suite |
| V16-PROOF | live | first externally confirmed system submit | G16A + owner authorization | redacted proof |

Reference:
- `docs/V1_6_SUBMISSION_CONTRACT.md`
- `docs/V1_6_ADVERSARIAL_TEST_MATRIX.md`
- `docs/AUTHORIZATION_GATES.md`

## V1.7 prepared tasks

| ID | SP | Task | Depends on |
|---|---:|---|---|
| V17-A01 | 2 | audit CRM artifact vs current accepted code | active V1.7 work surface |
| V17-A02 | 2 | audit interview/follow-up artifact vs current accepted code | V17-A01 |
| V17-T01 | 3 | multi-role recruiter/thread ambiguity adversarial cases | audit gaps |
| V17-T02 | 3 | correction/merge history adversarial cases | audit gaps |
| V17-T03 | 3 | interview time/reschedule/conflict cases | audit gaps |
| V17-T04 | 2 | lifecycle/follow-up truth table regression cases | audit gaps |
| V17-GATE | lead | milestone acceptance review | all accepted |

Do not rebuild accepted Lane 3 functionality without a demonstrated gap.

## V2.0 prepared tasks

### Control center
- V20-CC01 SP2 dashboard inventory/gap map
- V20-CC02 SP3 new-job/review inbox gap closure
- V20-CC03 SP3 application pipeline truth view
- V20-CC04 SP3 communication/interview/follow-up views
- V20-CC05 SP3 health/policy/kill-switch/backup view
- V20-CC06 SP3 safe non-secret config view

### Reliability
- V20-R01 SP3 migration upgrade/downgrade verification
- V20-R02 SP3 backup/restore drill
- V20-R03 SP4 parser regression corpus
- V20-R04 SP3 model/provider fail-closed behavior
- V20-R05 SP2 policy expiry reminders
- V20-R06 SP2 recovery runbooks

### Analytics
- V20-A01 SP3 immutable resume attribution query/service
- V20-A02 SP3 historical funnel semantics verification
- V20-A03 SP3 source/company/role/resume views
- V20-A04 SP3 time-to-stage
- V20-A05 SP2 sample-size/causal warnings

### Gmail/live runtime
- V20-G01 SP3 secret-free readiness report
- V20-G02 SP3 partial-fetch/checkpoint fail-closed behavior
- V20-G03 SP3 worker/readiness integration
- V20-LIVE live real read-only canary, user authorization required

### Integration
- V20-X01 SP5 deterministic end-to-end fixture
- V20-X02 SP4 failure-chain/replay cases
- V20-X03 SP2 machine-readable engineering campaign report
- V20-LIVE-CAMPAIGN live acceptance, user/external gates required

Reference:
- `docs/V2_0_END_TO_END_ACCEPTANCE_MATRIX.md`
- `docs/V2_0_INTEGRATION_ACCEPTANCE.md`

## V2.3 prepared tasks

### Opportunity graph
- V23-G01 SP4 schema/relationship audit
- V23-G02 SP4 graph projection/query service
- V23-G03 SP3 evidence traversal
- V23-G04 SP3 identity/dedupe/invalidation

### Strategy learning
- V23-S01 SP3 experiment persistence
- V23-S02 SP4 descriptive performance engine
- V23-S03 SP3 minimum-sample/uncertainty rules
- V23-S04 SP3 recommendation object

### Target-company watch
- V23-T01 SP2 watchlist model
- V23-T02 SP4 approved source adapters
- V23-T03 SP3 new/changed/closed dedupe
- V23-T04 SP3 relationship signal integration

### Interview intelligence
- V23-I01 SP3 typed InterviewBrief
- V23-I02 SP4 CandidateStoryMap
- V23-I03 SP2 FollowupPackage
- V23-I04 SP3 injection/stale/conflict regression suite

### Agent tools
- V23-TL01 SP5 stable transport-neutral typed tools
- V23-TL02 SP4 authorization context
- V23-TL03 SP3 idempotency/audit envelope
- V23-TL04 SP3 optional MCP wrapper after service contracts stabilize

## V3.0 prepared tasks

### Permission model
- V30-P01 SP3 action taxonomy
- V30-P02 SP4 scoped approval records
- V30-P03 SP4 deterministic policy interceptor
- V30-P04 SP4 human approval queue

### Shared memory
- V30-M01 SP4 memory classes/storage interface
- V30-M02 SP3 source/supersession/invalidation rules
- V30-M03 SP3 sensitivity/agent-scope enforcement
- V30-M04 SP3 restart/retrieval tests

### Runtime
- V30-R01 SP4 durable AgentTask/checkpoint schema
- V30-R02 SP3 specialist registry
- V30-R03 SP5 planner/router
- V30-R04 SP5 durable execution loop
- V30-R05 SP4 provider-neutral model router
- V30-R06 SP4 scoped memory/retrieval integration

### Evaluation/observability
- V30-E01 SP3 trace schema
- V30-E02 SP5 specialist golden eval suites
- V30-E03 SP4 policy violation regression suite
- V30-E04 SP4 quality/cost/latency/rework dashboard

### Specialists
Each specialist is separate SP3-SP5 implementation after platform foundations:
- Market Scout
- Opportunity Matcher
- Resume Strategist
- Application Operator
- Recruiter CRM Agent
- Interview Agent
- Networking Agent
- Portfolio/Brand Agent
- Policy/Safety Agent
- Analytics Agent

Reference:
- `docs/V3_SPECIALIST_AGENT_SPECS.md`

### Integration
- V30-X01 SP5 "Find me a better job" multi-agent engineering scenario
- V30-X02 SP4 interruption/restart scenario
- V30-X03 SP4 prompt injection/permission escalation scenario
- V30-X04 SP4 duplicate application race scenario
- V30-REAL live genuine real-world career workflow with appropriate approvals

Reference:
- `docs/V3_INTEGRATION_ACCEPTANCE_SCENARIOS.md`

## ChatGPT prep rule

While Antigravity is active:
- refine contracts,
- prepare tests/fixtures/runbooks,
- audit dependencies,
- keep these tasks worker-sized,
- do not implement conflicting production code on the worker's active surface,
- do not promote work across a closed gate.

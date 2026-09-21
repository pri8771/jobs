# Fable 5.1 Master Planning Brief — V2.3 ASAP, V3-Compatible

## Assignment

This is a **planning / architecture / decomposition pass**, not broad implementation.

Primary objective:

> Get **V2.3 genuinely working as fast as safely possible**.

Secondary objective:

> Design enough V3.0 contracts now that V2.3 does not create architectural dead ends.

Do **not** make broad V3 implementation part of the V2.3 critical path.

ChatGPT is the engineering/product lead and final acceptance authority.
Fable/Claude is the planning worker for this pass.

## Start from current truth

Before planning:
1. fetch current Git,
2. inspect current main, active branches/PRs, recent commits, proof evidence, CI, and heartbeat,
3. read the minimal startup set from `CLAUDE.md`,
4. use relevant prior Claude/Fable conversation/memory only to recover intent,
5. reconcile everything against Git.

Do not assume historical status in this brief is still current.

## Product target hierarchy

Critical capability path:
V1.4 → V1.5 → V1.6 → V1.7 → V2.0 → **V2.3**

V3.0:
- plan architecture now,
- implement later unless a small interface is required now to prevent V2.3 rework.

V2.3 must work without a multi-agent runtime.

## Planning principles

### Brownfield first

Audit what already exists before planning new code.
Prefer:
- repair,
- reuse,
- narrow integration,
- small additive migrations.

Avoid greenfield replacement of mature subsystems.

### Artifact-oriented

Each meaningful unit is an artifact with:
- inputs,
- outputs,
- invariants,
- failure states,
- tests,
- evidence,
- dependency gates.

### Tiny worker tasks

Make tasks detailed enough that Sonnet-class workers can execute them mechanically.

Default:
- SP1 preferred,
- SP2 allowed,
- SP3 only when genuinely indivisible,
- decompose SP4/SP5 implementation work.

### Engineering vs live proof

Keep separate:
- implementation/engineering acceptance,
- real/live proof.

Mocks, fixtures, CI, and tests never substitute for real proof.

## What V2.3 must already do

Without V3 agents, V2.3 should support a user asking:

> What are the best opportunities for me right now, why, who do I know there, which resume should I use, what should I do next, and what interviews/follow-ups do I have?

The answer must come from real evidence and expose uncertainty.

V2.3 should integrate:
- job/recruiting ingestion,
- discovery and dedupe,
- matching/evaluation,
- truthful packet preparation,
- safe application routing,
- application lifecycle,
- recruiter/contact history,
- interviews/follow-ups,
- operator control center,
- health/recovery,
- exact resume attribution/analytics,
- opportunity graph,
- strategy/outcome learning,
- target-company watch,
- interview intelligence,
- stable typed tool/service layer.

## Required planning outputs

Write durable repo-native planning artifacts. Avoid duplicate roadmaps.

At minimum produce or refine:

1. **Current brownfield audit**
   - what truly exists now,
   - what is accepted,
   - what is implemented but unaccepted,
   - what is absent,
   - live-proof gaps.

2. **Critical path to V2.3**
   - shortest safe path,
   - gates,
   - user/live boundaries,
   - explicit work deferred until after V2.3.

3. **Artifact graph**
   - remaining artifacts through V2.3,
   - required V3 compatibility contracts,
   - dependencies and parallelizable groups.

4. **Detailed worker task graph**
   - predominantly SP1/SP2,
   - detailed enough for Sonnet-class implementation.

5. **Model-routing plan**
   - cheapest capable model for each task,
   - suggested effort,
   - subagent suitability.

6. **Code/module map**
   - map each artifact/task to existing code anchors,
   - call out repair/reuse vs new module.

7. **Migration sequence**
   - additive schema steps,
   - upgrade/downgrade/test requirements,
   - no defaults that silently create authority/confirmation.

8. **Test/adversarial matrix**
   - by artifact.

9. **Live-proof matrix**
   - V1.4, V1.5, V1.6, V1.7, V2.0, V2.3.

10. **V2.3 acceptance campaign**
    - concrete end-to-end scenario(s),
    - real evidence required,
    - machine-verifiable outputs where possible.

11. **V3 compatibility check**
    - permissions,
    - typed tools,
    - durable task contract,
    - memory boundaries,
    - handoff/trace contracts,
    - prove V2.3 can support V3 without broad redesign.

12. **Canonical worker queue**
    - first tasks immediately executable after lead review.

## Task schema

Every implementation task must contain:
- ID
- artifact
- story points
- objective
- why
- inputs/dependencies
- primary code surfaces
- exact required behavior
- non-goals
- tests
- adversarial tests where relevant
- failure behavior
- expected output
- acceptance evidence
- parallelizable yes/no
- minimum recommended worker model
- suggested effort level

## V2.0 focus

V2.0 is the real operating-system integration milestone.

Audit and plan only real gaps in:
- control center,
- reliability/recovery,
- analytics,
- Gmail runtime,
- cross-subsystem integration,
- live acceptance.

Prefer repairing the current dashboard/analytics/worker/Gmail architecture.

## V2.3 focus

### Opportunity graph
Use canonical relational/event truth as authority.
Default to PostgreSQL/relational projection.
Evidence-backed edges; inferred relationships labeled.

### Strategy learning
Exact attribution, sample sizes, recency, uncertainty.
Do not turn observational N=1 into causal claims.

### Target-company watch
Approved/public sources, new/changed/closed roles, dedupe, recruiter/referral evidence.

### Interview intelligence
Typed InterviewBrief, CandidateStoryMap, FollowupPackage.
No invented candidate achievements or interviewer/company facts.

### Agent-ready tool layer
This is the key V3 bridge.
Build stable typed services/tools independent of Claude/ChatGPT/CrewAI/LangGraph/MCP.

Tools need:
- typed inputs/outputs,
- permission context where consequential,
- evidence references,
- idempotency/audit envelope,
- deterministic policy enforcement.

MCP can be a wrapper later, not the core architecture.

## V3 compatibility that must be designed now

Define/validate interfaces for:
- permission taxonomy and scoped approval,
- durable AgentTask/checkpoint contract,
- canonical-vs-derived memory boundary,
- artifact-based handoff,
- trace/evaluation envelope,
- specialist tool ceilings.

Do not broadly implement the agent runtime/specialists before V2.3 works unless lead explicitly advances them.

## Infrastructure restraint

For every new dependency, answer:
1. what present problem does it solve?
2. can the current Python/PostgreSQL/service stack solve it?
3. does it shorten the V2.3 critical path?
4. what operational burden does it add?

Default to current stack.

## Token/model efficiency

Follow `docs/MODEL_ROUTING_AND_TOKEN_EFFICIENCY.md`.

Use lower-cost subagents/models for bounded mechanical audits.
Reserve Fable 5.1 for architecture, safety, hard reconciliation, and synthesis.

Do not reread unchanged large files or duplicate planning prose.

## Heartbeat

During active implementation sessions:
- one session,
- one watcher,
- `FIVE_MIN_2026_09_21`,
- fixed 5-minute cadence,
- no 15-minute/hourly/proving transitions.

For this planning pass, do not create extra implementation watchers if an active worker already owns one.

## Live/action boundaries

No planning instruction self-authorizes:
- private candidate/resume use,
- Gmail OAuth/mailbox access,
- browser application action,
- application submission,
- external messages,
- calendar mutation,
- spending.

Mark these `USER_GATE`.
A gate blocks only its action, not safe planning/engineering elsewhere.

## Finish

Write the authoritative planning changes into Git.

Do not broad-implement V2/V3 in this pass.
Do not self-accept the plan.

Final handoff should be concise:
- exact main SHA,
- files created/updated,
- audited current state,
- critical path to V2.3,
- artifact/task counts,
- parallel groups,
- model allocation summary,
- first 5 worker tasks,
- live/user gates,
- V3 compatibility decisions,
- open lead decisions,
- `READY_FOR_LEAD_REVIEW`.

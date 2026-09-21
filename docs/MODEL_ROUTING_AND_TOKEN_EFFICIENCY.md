# Model Routing & Token Efficiency

Purpose: minimize cost/tokens without lowering correctness on consequential work.

## Core rule

Use the **lowest-cost model reasonably capable of the bounded task**.

Reserve the strongest model for work where mistakes compound across the project.

## Suggested routing

### Strongest planner/reasoner (Fable 5.1 or equivalent)

Use for:
- architecture and artifact decomposition,
- dependency/gate design,
- safety/policy reasoning,
- difficult brownfield reconciliation,
- conflicting evidence,
- V2.3/V3 compatibility design,
- final synthesis/review of delegated analyses.

Recommended effort:
- High/XHigh for normal architecture,
- highest available only for genuinely difficult cross-system decisions.

### Opus-class implementation model

Use for:
- difficult multi-module implementation,
- concurrency/idempotency,
- durable state machines,
- complex migrations/refactors,
- difficult integration/debugging,
- agent runtime/orchestration after V2.3.

Recommended effort:
- High/XHigh normally,
- maximum only for a demonstrated hard problem.

### Sonnet-class / lower-cost model

Default for well-specified:
- SP1/SP2 implementation,
- unit/regression tests,
- simple migrations,
- adapters against fixed interfaces,
- dashboard endpoints,
- analytics queries,
- CLI/service plumbing,
- docs and artifact-card updates,
- code inventories and checklist audits.

Recommended effort:
- Medium/High.

## Subagents

If the environment supports subagents:

Delegate independent mechanical work such as:
- file/symbol inventory,
- test inventory,
- module summaries,
- artifact consistency checks,
- CI evidence collection,
- simple static contract audits,
- boilerplate tests from an exact specification.

Use lower-cost subagents for these.

Do not delegate final authority for:
- candidate truth/provenance,
- submission authorization,
- idempotency/concurrency semantics,
- external-confirmation truth,
- prompt-injection boundaries,
- policy decisions,
- V2.3 service architecture,
- V3 permission/runtime architecture.

The parent planner remains responsible for synthesis.

## Parallelism

Parallelize only independent work with non-overlapping write surfaces.

Good examples:
- dashboard audit + analytics audit + Gmail readiness audit,
- opportunity graph audit + target-company-watch audit,
- test inventory + schema inventory.

Avoid parallel agents independently redesigning the same contract.

## Token-efficient reading

- Git diff/search before full-file reads.
- Batch related reads.
- Read only relevant line ranges.
- Do not reread unchanged roadmap files.
- Keep a compact working summary.
- Persist durable conclusions in canonical Git docs.
- Do not regenerate giant project summaries every turn.

## Token-efficient writing

Prefer:
- one canonical plan,
- small artifact cards,
- bounded task queue,
- links/references to existing contracts.

Avoid:
- multiple roadmaps containing the same prose,
- repeating acceptance criteria in every document,
- copying entire histories into new planning files.

## Brownfield rule

Before proposing new infrastructure:
1. search for existing implementation,
2. determine repair vs replacement,
3. reuse accepted interfaces,
4. add the minimum abstraction needed.

Do not introduce Neo4j, Temporal, LangGraph, CrewAI, Redis, Kafka, Kubernetes, MCP, pgvector, etc. without a concrete current requirement and clear V2.3 acceleration benefit.

## Context persistence

The repo is the portable memory.

Conversation memory is useful for intent but should not be repeatedly restated into prompts.

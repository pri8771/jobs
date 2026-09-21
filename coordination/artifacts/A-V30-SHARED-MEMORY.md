# A-V30-SHARED-MEMORY

- Type: memory / continuity
- Phase: V3.0
- Status: PROPOSED
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V23-AGENT-TOOLS, A-V30-PERMISSION-MODEL
- Downstream: A-V30-AGENT-RUNTIME, specialist agents, A-V30-CAREER-AGENT-NETWORK

## Purpose

Provide durable scoped agent continuity without allowing derived summaries to replace canonical domain truth.

## Contract

See:
- `docs/V3_SHARED_MEMORY_CONTRACT.md`

## Acceptance

- canonical truth remains authoritative,
- derived memory retains source references,
- stale/superseded memory is invalidated,
- memory cannot grant permissions,
- memory cannot convert inference into candidate truth,
- task restart can restore bounded working memory,
- sensitivity/agent scope enforced.

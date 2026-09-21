# A-V30-POLICY-SAFETY-AGENT

- Type: specialist agent / audit
- Phase: V3.0
- Status: PROPOSED
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: A-V30-PERMISSION-MODEL, A-V30-AGENT-RUNTIME
- Downstream: A-V30-CAREER-AGENT-NETWORK

## Purpose
Surface policy expiry, permission gaps, unresolved facts, duplicate/action risks and anomalous behavior.

## Core constraint
This agent does not replace deterministic enforcement.

## Acceptance
- cannot override policy interceptor,
- reports source/rationale,
- catches stale approval/policy and duplicate risk,
- prompt cannot grant permission,
- audit findings become review artifacts.

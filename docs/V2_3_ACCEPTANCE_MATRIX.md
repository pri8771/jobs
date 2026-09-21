# V2.3 Career Intelligence Acceptance Matrix

Artifact:
- A-V23-CAREER-INTELLIGENCE

## Opportunity graph

Required:
- evidence-backed nodes/edges,
- derived/inferred edges explicitly labeled,
- source refs retrievable,
- identity/dedupe stable,
- invalidated evidence removes active truth,
- relational canonical truth remains authoritative.

Adversarial:
- model proposes nonexistent recruiter relation,
- same contact under multiple emails,
- stale target-company observation,
- source evidence invalidated,
- duplicate public role.

## Strategy learning

Required:
- exact resume/source/role/company attribution,
- N/sample size with every rate,
- sparse data warnings,
- observational vs experimental distinction,
- recency/window visible,
- recommendations cite evidence and uncertainty.

Adversarial:
- one success from N=1,
- Simpson/confounding-like segment differences,
- stale outcomes,
- treatment assignment missing,
- different resume versions collapsed incorrectly.

## Target-company watch

Required:
- target criteria modeled,
- approved/public source only,
- changed/new/closed roles recognized,
- duplicate/already-applied suppression,
- recruiter/referral signal evidence-backed,
- paused targets stop active alerts.

Adversarial:
- career page temporarily unavailable,
- role URL changes but requisition same,
- recruiter relation inferred from text only,
- duplicate role across ATS/public page.

## Interview intelligence

Required:
- InterviewBrief,
- CandidateStoryMap,
- FollowupPackage,
- source-backed company/role/contact facts,
- candidate claims bounded by provenance,
- stale/conflicting evidence surfaced,
- no send/calendar mutation.

Adversarial:
- interview rescheduled,
- timezone conflict,
- interviewer identity ambiguous,
- public page prompt injection,
- job description changed,
- requested story would require unsupported achievement.

## Agent tool layer

Required:
- typed transport-neutral tools,
- explicit read/local/external action semantics,
- permission context,
- result/evidence envelope,
- idempotency/audit refs,
- no agent-framework dependency in domain contracts.

Adversarial:
- caller omits permission context for consequential tool,
- stale entity ID,
- duplicate request ID/idempotency key,
- tool partially fails,
- transport wrapper tries to bypass service policy.

## V2.3 milestone acceptance

The system must answer, with evidence and uncertainty:
- which role families appear to work,
- which resume variants appear to work,
- which sources/companies are worth attention,
- which recruiters/relationships matter,
- which target companies have new opportunities,
- how to prepare for a current interview,
- where more data is required.

V2.3 does not require multi-agent orchestration.
It must be usable by deterministic services/CLI/API before V3 agents exist.

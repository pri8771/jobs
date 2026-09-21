# V2.3 — Career Intelligence & Optimization

## Purpose

V2.3 turns the V2.0 operating system into a system that learns which opportunities and strategies are worth pursuing, and prepares the stable intelligence/tool layer required by V3.0 agents.

## Required artifacts

### A-V23-OPPORTUNITY-GRAPH
Normalized relationships across:
- company
- job
- contact
- application
- message/thread
- interview
- resume variant
- outcome
- skill/project evidence
- referral/network edge

Must preserve source evidence and avoid speculative relationship edges.

### A-V23-STRATEGY-LEARNING
- resume conversion by role cluster
- source/company response performance
- time-to-stage
- role/comp/location outcomes
- explicit experiment records
- minimum sample-size warnings
- descriptive-vs-causal guardrails

### A-V23-TARGET-COMPANY-WATCH
- target companies
- role search criteria
- new role observations
- hiring/recruiter signals
- dedupe against known jobs
- no unauthorized outreach

### A-V23-INTERVIEW-INTELLIGENCE
- company/role/contact brief
- candidate evidence map
- relevant project/story suggestions
- interview stage history
- follow-up draft package

### A-V23-AGENT-TOOLS
Stable typed services/tools for:
- jobs
- applications
- contacts
- timelines
- resume variants
- analytics
- review queue
- policy
- artifact evidence

The tool layer should be transport-neutral. MCP may wrap it later.

## Exit

The system can explain:
- which role families are working,
- which resume variants are working,
- which sources/companies are worth time,
- which recruiters/relationships matter,
- where the user should focus next,
while preserving uncertainty and evidence.

This milestone prepares, but does not yet require, multi-agent orchestration.

# V3 Specialist Agent Contract Template

Every V3 specialist agent must define this contract before implementation.

## Identity

- Agent ID:
- Name:
- Purpose:
- Owner/reviewer:

## Inputs

List exact artifact/event/tool inputs.

No agent may treat unverified summaries as canonical facts.

## Tools

List allowed typed tools/services.

Prefer stable Jobs Automation service interfaces over direct arbitrary database access.

## Permissions

Classify every tool/action:
- READ_ONLY
- LOCAL_WRITE
- EXTERNAL_DRAFT
- USER_APPROVED_EXTERNAL_WRITE
- BLOCKED

State which actions require explicit user approval.

## Output artifacts

Every meaningful run produces named artifacts/evidence.

Examples:
- opportunity shortlist
- resume recommendation
- interview brief
- outreach draft
- policy decision
- analytics recommendation

## Stop conditions

Must stop/escalate on:
- missing candidate fact
- ambiguous identity/link
- policy conflict
- unsupported external action
- authentication/MFA/CAPTCHA
- insufficient evidence
- cost/model limit where relevant

## Handoff rules

Define:
- which agent can consume the output,
- what evidence travels with it,
- whether human approval is required,
- how stale outputs expire.

## Memory

Specify:
- durable facts it may write,
- derived summaries,
- source references,
- retention/supersession rules.

Raw evidence remains authoritative.

## Evaluation cases

At least:
- normal success
- ambiguous input
- missing fact
- stale data
- conflicting evidence
- model/tool failure
- prohibited action
- duplicate/retry

## Observability

Record:
- run ID
- task/artifact IDs
- model/provider
- tools called
- input/output hashes where useful
- cost/tokens if available
- result/status
- evidence references

## Safety

No agent may:
- fabricate candidate facts,
- bypass platform restrictions,
- treat mock results as external success,
- perform consequential external actions outside its permission contract.

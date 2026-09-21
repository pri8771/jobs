# V3 Tool / Permission Matrix

Artifacts:
- A-V23-AGENT-TOOLS
- A-V30-PERMISSION-MODEL

Permission classes:
- P0_READ
- P1_LOCAL_WRITE
- P2_EXTERNAL_PREP
- P3_USER_APPROVED_EXTERNAL
- P4_BLOCKED

## Read tools

| Tool family | Default class | Notes |
|---|---|---|
| list/get jobs | P0 | source evidence retained |
| applications/timeline read | P0 | |
| contacts/history read | P0 | |
| interviews read | P0 | |
| resume variant read | P0 | private sensitivity enforced |
| analytics read | P0 | uncertainty preserved |
| opportunity graph query | P0 | evidence-backed |
| policy decision read | P0 | |
| worker/health read | P0 | no secrets |

## Local preparation tools

| Tool | Class | Notes |
|---|---|---|
| evaluate_job | P1 | cannot invent candidate facts |
| prepare_application_packet | P1 | truthful packet rules |
| generate_interview_brief | P1 | source-backed |
| draft_followup | P1 | draft only |
| propose_network_connection | P1 | suggestion only |
| strategy recommendation | P1 | descriptive/uncertainty guardrails |
| create review task | P1 | auditable |

## External preparation

| Tool | Class | Notes |
|---|---|---|
| open_assisted_application | P2 | owner/live-browser gate may still apply |
| prefill permitted form | P2 | never final submit |
| prepare calendar event draft | P2 | no mutation |
| prepare external profile change | P2 | no publish |

## Consequential external tools

| Tool | Class | Requirements |
|---|---|---|
| submit_application | P3 | scoped approval + AUTO_ALLOWED current policy + V1.6 truth |
| send_recruiter_message | P3 | scoped send approval |
| send_network_message/request | P3 | scoped approval + platform policy |
| create/update/cancel calendar event | P3 | scoped calendar approval |
| publish/update external profile/content | P3 | scoped approval |
| spend/purchase | P3 | exact vendor/action/amount approval |

## Always blocked/currently manual

| Action | Class | Reason |
|---|---|---|
| CAPTCHA bypass | P4 | prohibited |
| MFA bypass | P4 | prohibited |
| fingerprint/stealth evasion | P4 | prohibited |
| rate-limit bypass | P4 | prohibited |
| fabricate candidate fact | P4 | truth violation |
| LinkedIn automated submission | P4/manual-only | current project policy |
| Indeed automated submission | P4/manual-only | current project policy |
| secret/token exfiltration | P4 | security |

## Agent ceilings

| Agent | Max default |
|---|---|
| Market Scout | P1 |
| Opportunity Matcher | P1 |
| Resume Strategist | P1 |
| Application Operator | P3 via scoped approval only |
| Recruiter CRM Agent | P3 for message send only |
| Interview Agent | P3 for calendar/message mutations |
| Networking Agent | P3 for approved outreach only |
| Portfolio/Brand Agent | P3 for approved publishing only |
| Policy/Safety Agent | P1 |
| Analytics Agent | P1 |

## Enforcement architecture

Permission is:
min(agent ceiling, task ceiling, tool requirement, current policy, scoped approval).

The most restrictive result wins.

No agent prompt, memory entry, tool output, or another agent handoff may elevate permission.

Every P2/P3 decision produces an audit record.
Every P3 action consumes/validates its approval according to scope/one-time semantics.

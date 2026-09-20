# Tentative V3 Architecture and Infrastructure Plan

Status: TENTATIVE FUTURE DIRECTION

This document preserves the broader V3 design so the team does not lose the long-term architecture while current execution stays focused on the first real application milestone.

Do not implement this entire document now.

The immediate execution target is documented in coordination/WORK_QUEUE.md and docs/FIRST_REAL_APPLICATION_PLAN.md.

## Architectural principle

Jobs Automation should be a durable runtime system that continues to operate whether or not ChatGPT, Antigravity, Cursor, or Claude is open.

AI IDEs and assistants are development/control-plane clients, not production runtime dependencies.

The runtime owns:
- database state
- OAuth/API connections
- polling/scheduling
- workflow state
- browser execution
- policy enforcement
- audit logs
- model routing
- artifact storage

MCP sits on top of the Jobs OS for agent interoperability. MCP should not be the only runtime integration mechanism.

## V3 conceptual architecture

User
-> Dashboard / ChatGPT / notifications
-> Jobs API / Jobs MCP
-> workflow control plane
-> AI agent runtime
-> integrations/adapters
-> durable data

Long-running deterministic workflow orchestration:
- Temporal is the preferred future candidate once workflows span days/weeks and simple workers become awkward.

AI reasoning/orchestration:
- LangGraph is the preferred future candidate for stateful agent workflows, review points, and specialized agents.

Model gateway:
- LiteLLM-compatible gateway.

Local inference:
- Ollama or vLLM on available GPU nodes for cheap/private classification, extraction, embeddings, and other repetitive tasks.

Durable relational state:
- PostgreSQL.

Semantic retrieval:
- pgvector inside PostgreSQL before considering a separate vector database.

Artifact/object storage:
- MinIO or equivalent S3-compatible local object storage for resumes, PDFs, screenshots, packet manifests, confirmations, and research artifacts.

Browser execution:
- Playwright browser workers.
- Interactive visible browser profile on a trusted desktop for login/MFA/manual checkpoints.
- Never commit cookies or browser profiles.

Remote access:
- Tailscale is the preferred future private access layer.
- Avoid exposing the dashboard directly to the public internet.

Observability:
- structured logs first.
- OpenTelemetry/Grafana later if operational complexity warrants it.

CI:
- GitHub Actions.

## Practical infrastructure progression

### Current / V1.x

Keep it simple:
- Docker Compose
- FastAPI
- PostgreSQL
- Python worker
- Playwright
- GitHub Actions
- LiteLLM-compatible interface
- local filesystem artifacts initially

Do not introduce Temporal, MinIO, or a large agent framework before the real application flow works.

### V2

Add only when needed:
- pgvector
- MinIO
- Temporal
- Jobs MCP
- local inference service
- Tailscale
- stronger monitoring

### V3

Potential services:
- jobs-api
- jobs-dashboard
- postgres + pgvector
- temporal
- temporal-worker(s)
- llm-gateway
- local-llm runtime
- minio
- browser-runner
- backup service
- observability stack
- jobs-mcp

## Accounts / external connections likely required

### Required for near-term real system

GitHub
- Already in use.
- Source, CI, agent coordination.

Google Cloud project
- Required for runtime Gmail OAuth.
- Later Calendar OAuth.
- Use a dedicated project such as Jobs Automation.
- Runtime should have its own OAuth credentials rather than depending on ChatGPT's connector.

Gmail
- Required for job alerts and recruiter/application communication.
- Start read-only.
- Runtime owns the OAuth token securely outside Git.

LinkedIn
- Candidate profile + alerts + networking.
- Submission remains manual-only under current project policy.

Indeed
- Candidate profile + alerts/discovery.
- Indeed Apply remains manual-only under current project policy.

ZipRecruiter
- Candidate profile + alerts/discovery.

Dice
- Candidate profile + tech job alerts/discovery.

Candidate resume/source material
- Required for real applications.
- Store sensitive source files outside Git or in a deliberately private artifact store.

### Strongly recommended before browser-heavy operation

Password manager
- 1Password, Bitwarden, or self-hosted Vaultwarden.
- Human credentials remain managed by the human/browser, not embedded in prompts/code.

Dedicated browser profile
- Jobs Automation browser profile on trusted desktop.
- Persist authenticated sessions locally.
- User handles MFA/CAPTCHA when required.

### Later

Google Calendar
- Interview scheduling/reminders.

Tailscale
- Private access to dashboard/browser workers.

Cloud LLM API account(s)
- Optional but recommended for high-quality tailoring/research.
- Keep provider-neutral through LiteLLM.
- ChatGPT subscription is not a runtime API credential.

Local model runtime
- Ollama or vLLM.
- Use available GPUs for low-cost/private tasks.

Search API
- Later autonomous company/market research.
- Behind a SearchProvider adapter.
- Candidate providers: Brave, Tavily, Exa, Serper or future equivalent.

Notifications
- Optional Slack, Pushover, or email notifications.

## MCP strategy

Eventually create one main Jobs MCP server.

Its purpose is to let ChatGPT, Claude, Antigravity, and other agents interact with the Jobs OS through a stable capability surface.

Potential read tools:
- list_new_jobs
- search_jobs
- get_job
- get_application
- list_applications
- get_application_timeline
- get_recruiter
- get_email_thread
- list_interviews
- get_review_queue
- get_daily_brief
- get_funnel
- check_policy

Potential controlled write tools:
- shortlist_job
- reject_job
- prepare_packet
- approve_packet
- mark_manual_submission
- draft_recruiter_email
- create_followup
- resolve_review
- approve_application
- schedule_interview

High-risk actions such as:
- submit_application
- send_email
- withdraw_application
- accept_offer

must have stronger authorization/approval checks.

Do not create many MCP servers unless there is a real isolation need. Prefer one Jobs MCP on top of stable internal APIs.

## ATS reality

Do not assume an applicant can obtain arbitrary Greenhouse/Lever/Ashby/SmartRecruiters API credentials.

Official ATS application APIs generally use credentials controlled by employer/ATS customers or approved partners.

Therefore the candidate-side execution strategy is destination-specific:

- MANUAL_ONLY
- ASSISTED
- AUTO_ALLOWED
- BLOCKED

Generic application automation may require:
- visible browser automation,
- user-authenticated sessions,
- explicit destination policy approval,
- external confirmation evidence.

Never classify an application as submitted based only on local simulated output.

## Future V3 agent organization

Possible specialized agents:
- Career Director
- Market Scout
- Opportunity Matcher
- Company Researcher
- Resume Strategist
- Application Operator
- Browser Operator
- Policy/Safety Agent
- Recruiter CRM Agent
- Networking Agent
- LinkedIn Network Growth Agent
- Interview Agent
- Follow-Up Agent
- Offer Agent
- Market Analytics Agent
- Portfolio Agent
- Brand Agent
- Audit Agent
- Cost/Model Router

The agents should invoke deterministic services rather than owning durable truth themselves.

## LinkedIn network growth — intentionally open-ended

A future V2/V3 capability should help expand the user's professional LinkedIn circle in a targeted, useful way rather than maximizing raw connection count.

Potential objectives:
- discover relevant recruiters and hiring managers at target companies,
- identify peers in target role families,
- identify alumni/former-coworker/referral paths,
- suggest high-value connection targets associated with active jobs,
- draft individualized connection requests and follow-ups,
- record relationship state and history,
- measure whether networking creates recruiter replies, referrals, interviews, or other useful outcomes.

Guardrails:
- no bulk spam,
- no indiscriminate connection farming,
- no automated mass messaging,
- human-governed consequential outreach,
- follow LinkedIn platform restrictions and current policy.

Exact implementation is deliberately deferred until after the first-real-application proof.

## V3 memory architecture

Project/development memory:
- Git
- coordination/CONTEXT.md
- coordination/WORK_QUEUE.md
- coordination/AI_SYNC.md
- state/DECISIONS.md
- architecture/code/docs

Career runtime memory:
- PostgreSQL
- candidate evidence
- jobs
- companies
- contacts
- applications
- communication
- interviews
- outcomes
- policies
- preferences

Semantic memory:
- pgvector
- job descriptions
- career evidence
- research
- summarized communication
- interview notes

Binary/document artifacts:
- MinIO/object storage

## Long-term V3 experience

The system should eventually support an instruction as broad as:

"Find me a better job."

It should already know:
- truthful career evidence
- preferred role families
- target compensation
- applications already made
- recruiters/contacts
- interviews
- active opportunities
- successful resume positioning
- market trends
- policy/automation boundaries

It should organize and execute safe approved work, ask only when user judgment or missing facts are required, and keep a complete audit trail.

## Current implementation instruction

This document is intentionally future-facing.

Do not begin implementing the full V3 architecture until the current near-term milestone has demonstrated one real, externally confirmed application workflow.

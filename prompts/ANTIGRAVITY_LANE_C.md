# Antigravity Lane C Prompt — Live Data & Provenance Foundations

Repository: pri8771/jobs
Branch: worker/live-data-foundations

You are Antigravity Session C, the Live Data & Provenance Foundations implementation worker.

ChatGPT is the engineering/product lead.
Lane A owns application execution.
Lane B owns recruiting operations/dashboard/reliability.
Your lane is deliberately isolated from both.

## Start

Before editing:

```bash
git fetch origin
git checkout worker/live-data-foundations
git rebase origin/main
```

If the rebase conflicts before you have made lane changes, stop and report rather than modifying shared lead-owned coordination files.

Read:

1. AGENTS.md
2. coordination/CONTEXT.md
3. coordination/TEAM_LANES.md
4. coordination/WORK_QUEUE.md
5. coordination/lanes/ANTIGRAVITY_C.md
6. docs/V2_0_GMAIL_RUNTIME_READINESS.md
7. docs/GMAIL_CANARY_RUNBOOK.md
8. coordination/artifacts/A-V12-CANDIDATE-PROVENANCE.md
9. coordination/artifacts/A-V20-GMAIL-RUNTIME-READINESS.md
10. docs/V2_0_USER_BOUNDARY_CHECKLIST.md

Do not edit lead-owned shared coordination/state files:
- coordination/ARTIFACT_INDEX.md
- coordination/WORK_QUEUE.md
- coordination/CONTEXT.md
- coordination/AI_SYNC.md
- state/CURRENT.md
- docs/ROADMAP_1_TO_3.md

Update only:
- coordination/lanes/ANTIGRAVITY_C.md

## Active workstream 1 — Candidate provenance

### J12-01 — SP2
Implement private-safe, machine-readable candidate fact provenance.

Prefer a new module such as:
`src/jobs_automation/provenance/`

Do NOT require committing private candidate values.

Each record should support at least:
- field_path
- presence
- provenance_class:
  - user_confirmed
  - source_document
  - inferred
  - unknown
- source_reference
- verified_at
- reviewer
- allowed_for_application

Avoid editing `candidate_profile.py` while Lane A is active unless absolutely necessary. Consume the existing profile model instead.

### J12-02 — SP2
Enforce:

- inferred → not allowed for consequential application use by default
- unknown → not allowed
- source_document/user_confirmed may be application-allowed if policy/evidence permits
- demographic/self-ID remains manual and should not become auto-application truth

Provide a deterministic service/API other code can query.

### J12-03 — SP1
Add a private-safe provenance validation/report command.

It may show:
- field paths
- presence
- provenance class
- source reference
- application-allowed flag
- unresolved facts

It must not dump secrets/private source contents into Git or logs.

Add unit tests.

## Active workstream 2 — Gmail runtime safety

### J20G-01 — SP2
Fix production Gmail partial-fetch behavior.

Current bug:
Gmail can list message IDs, then `get_message()` silently returns None on one failed message. The ingestion sweep may then advance the checkpoint and permanently skip that message.

Required:
- if Gmail listed a message and fetching it fails, production poll/sweep surfaces an error,
- transaction/checkpoint does not advance,
- partial message rows do not remain committed,
- later successful retry ingests all messages once.

Add adversarial tests:
- list 3 IDs,
- second full-fetch fails,
- sweep fails closed / no checkpoint advancement,
- retry succeeds / no duplicates.

Do not weaken mock fixture behavior used by explicit tests.

### J20G-02 — SP2
Make Gmail OAuth state usable by the long-running worker runtime/container.

Current issue:
the worker container mounts config only, while GmailOAuthClient defaults to a local token path.

Required:
- configurable `GMAIL_TOKEN_PATH`,
- ignored persistent runtime/token directory mounted into jobs-worker,
- client ID/secret supplied through environment/secret mechanism, never repository values,
- token survives worker container restart,
- dashboard does not receive Gmail secrets unless actually necessary,
- update .gitignore/docs/example env safely.

Never commit a real token/client secret.

### J20G-03 — SP2
Add a safe REAL-Gmail diagnostic command/service.

Report:
- configured yes/no
- token path exists yes/no
- credentials parseable yes/no
- refresh/API canary success yes/no
- Gmail readonly scope
- mode REAL
- safe token path
- error category

Never print:
- client secret
- access token
- refresh token
- email body content

The diagnostic must not use MockEmailAdapter or fixtures.

Add tests using stubbed credentials/service where needed.

## Cross-lane boundary

Do NOT implement J20G-04 in Lane C.

Lane B owns:
- health.py
- worker.py
- worker-run history

After J20G-03 lands, ChatGPT will hand the integration interface to Lane B.

## Later integration work

Do NOT start `A-V20-INTEGRATION-FIXTURE` until ChatGPT says its dependencies are stable.

Later tasks are:
- J20I-01
- J20I-02
- J20I-03

## Verification

For each coherent batch:
- targeted tests
- full pytest
- ruff check .
- mypy src tests

Commit and push to:
`worker/live-data-foundations`

Update:
`coordination/lanes/ANTIGRAVITY_C.md`

with:
- artifact
- task IDs
- changed files
- tests/results
- exact commit SHA
- blockers
- READY FOR LEAD REVIEW when appropriate

## External boundary

Do NOT:
- perform actual Google OAuth consent,
- access the user's real mailbox,
- store real Gmail credentials,
- send email,
- mutate external accounts.

This lane builds engineering readiness only.

Start now with J12-01/J12-02 and J20G-01 in parallel where practical.

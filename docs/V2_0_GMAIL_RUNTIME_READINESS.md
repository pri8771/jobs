# V2.0 Gmail Runtime Readiness Contract

Artifact: A-V20-GMAIL-RUNTIME-READINESS

## Purpose

Make the long-running Jobs Automation worker capable of using real read-only Gmail safely and observably, without silent message loss or secrets in Git.

This artifact prepares the runtime. It does not perform user OAuth by itself.

## Lead audit findings

### 1. Container OAuth state is not currently wired

`GmailOAuthClient` expects:
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- token at `gmail_token_path` (default `.local/gmail_token.json`)

Current Docker worker mounts only `./config:/app/config:ro`.

Therefore a token created on the host is not automatically available/persisted inside the worker container.

### 2. Silent per-message fetch failure can skip mail

`GmailAdapter.poll_messages()` lists Gmail message IDs, then calls `get_message()`.

`get_message()` catches all exceptions and returns `None`.

If one listed message fails to fetch:
- the adapter silently omits it,
- the ingestion sweep can still complete,
- the checkpoint can advance past the missing message.

This can create permanent message loss.

### 3. Runtime status has no Gmail-specific diagnostic

Current health/status can say database/adapters/policy are healthy but does not prove:
- Gmail token exists,
- token can refresh,
- Gmail API can answer a harmless request,
- worker container can access the token,
- latest ingestion was real rather than mock.

## Required fixes

### J20G-01 SP2 — fail closed on partial Gmail fetch

For a production Gmail poll:
- if Gmail lists a message and its full fetch fails, the poll/sweep must surface an error,
- the ingestion transaction/checkpoint must not advance,
- next run retries through the overlap/reconciliation path.

Do not silently drop listed messages.

Add tests:
- list returns 3 IDs; second get fails -> sweep errors + no checkpoint advance + no partial committed rows.
- next successful run ingests all 3 once.

### J20G-02 SP2 — runtime OAuth/container wiring

Provide documented configurable runtime paths without committing secrets.

Recommended container pattern:
- set `GMAIL_TOKEN_PATH=/app/.local/gmail_token.json`
- mount a local ignored `.local/` or dedicated secrets/runtime directory read-write into the worker,
- provide client ID/secret through runtime environment/secret mechanism, not repository values.

Do not mount OAuth material into dashboard unless required.

Token file must remain ignored by Git.

### J20G-03 SP2 — Gmail diagnostic command/service

Add a harmless read-only diagnostic that reports:
- configured: yes/no
- token file present: yes/no
- token parseable/refreshable: yes/no
- API identity/profile call or bounded list succeeds: yes/no
- scope = Gmail readonly
- runtime path being used (safe path only, no token contents)
- mode = REAL, never mock

It must not print client secret, access token, refresh token, or email bodies.

### J20G-04 SP2 — health + worker evidence

Integrate Gmail readiness with:
- health service,
- worker-run history,
- dashboard operational status.

Expose:
- Gmail ready/unavailable
- last successful real Gmail ingestion
- last error
- last reconciliation

Registered/mock adapters do not count as real Gmail ready.

## OAuth user boundary

Interactive OAuth remains a user action.

Recommended sequence when engineering is ready:
1. user supplies/sets OAuth client configuration locally,
2. run one explicit interactive OAuth command outside scheduled worker,
3. store token in ignored runtime location,
4. run diagnostic,
5. run bounded dry-run canary,
6. review,
7. run bounded persisted canary,
8. only then enable normal worker use.

## Acceptance

A-V20-GMAIL-RUNTIME-READINESS is accepted when:
- partial fetch cannot silently advance checkpoint,
- container/runtime token persistence is configured safely,
- diagnostic proves real Gmail adapter readiness without exposing secrets,
- health/worker evidence distinguishes REAL Gmail from mock/unavailable,
- tests/CI green.

Full A-V20-LIVE-INGESTION additionally requires the user's actual OAuth and live canary.

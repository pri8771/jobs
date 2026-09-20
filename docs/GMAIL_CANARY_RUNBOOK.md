# Gmail Read-Only Canary Runbook

Artifact:
- A-V12-GMAIL-CANARY

## Goal

Prove Jobs Automation can read real Gmail job/recruiting messages using runtime-owned OAuth, with no mock/fixture contamination and no mailbox mutation.

This runbook does not authorize OAuth setup by itself.

## Google Cloud setup

User-interactive steps:
1. Create/select dedicated Google Cloud project for Jobs Automation.
2. Enable Gmail API.
3. Configure OAuth consent.
4. Create desktop/local OAuth client appropriate for the runtime.
5. Authorize the runtime with read-only Gmail scope.

Start with the narrowest practical read scope.

## Secret handling

Never commit:
- OAuth client secret,
- authorization code,
- access token,
- refresh token,
- downloaded credential JSON,
- browser session.

Use local ignored secret path or secret store.

Document only:
- expected environment variable/path names,
- account alias/hint,
- last verified timestamp.

## Runtime diagnostics before canary

Must verify:
- credential config present,
- token readable,
- selected adapter is real GmailAdapter,
- mock fixtures disabled,
- dry-run supported,
- database reachable,
- mailbox checkpoint state known.

## Canary execution

First run should be:
- read-only,
- bounded time window or message count,
- dry-run first,
- no labels/archive/send/delete,
- no worker scheduling yet.

Evidence should record:
- provider = Gmail,
- account hint,
- query/window,
- messages discovered,
- messages parsed,
- classifications,
- job alerts parsed,
- duplicates skipped,
- unresolved/ambiguous messages,
- checkpoint unchanged during dry-run,
- mock/fixture mode = false.

## Review gate

Before enabling persistent writes:
- inspect sample parsed messages,
- confirm classifications,
- confirm job links/dedup behavior,
- confirm outbound/inbound recognition,
- confirm no private unrelated mail is unnecessarily persisted.

## First write-enabled canary

After dry-run approval:
- use small bounded window,
- persist normalized messages/jobs,
- verify exact provider message IDs,
- verify checkpoint advancement only on success,
- rerun same window and prove idempotency.

## Failure/recovery

If parsing is wrong:
- stop scheduled worker,
- identify affected rows by run/provider IDs,
- preserve raw external evidence,
- correct parser/link logic,
- use controlled rollback/cleanup according to audit policy,
- rerun canary.

If OAuth fails:
- fail closed,
- never substitute fixtures,
- leave reconciliation due.

## Acceptance

A-V12-GMAIL-CANARY can be accepted when:
- real Gmail OAuth works,
- read-only canary succeeds,
- no mock path is involved,
- dry-run is nonpersistent,
- write-enabled bounded canary is idempotent,
- ingestion evidence is independently reviewable,
- user-interactive OAuth boundary is respected.

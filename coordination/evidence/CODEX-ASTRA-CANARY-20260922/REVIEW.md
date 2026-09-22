# Independent Jobs exact-tree review — 2026-09-22

Recommendation: **REWORK_REQUIRED**. This is a mechanical review recommendation, not formal acceptance or live-gate proof. Review stopped after a concrete reproduced boundary failure, as assigned; remaining areas do not receive a blanket clean verdict.

## Identity and scope

- Exact candidate HEAD: `7685f811ec5e41df789e6df82f948669e5e35fe2`
- Exact candidate tree: `2f30edc8552198e96446b47f64e70f1d71a00cdc`
- Source repair commit: `d337424e8fde6f2a54e99ac7a1d02aed1878cc60`
- Source repair tree: `a8b83849ba8dd095b2dfb3928cdec09bc24b4b26`
- Base: `bc93a8a0bd381f9f675440b62c91aaf3b8406795`
- Worktree: `/tmp/jobs-v17-cli-gate-20260922`
- Initial status clean. Final source HEAD/tree unchanged and `git diff --check` clean; untracked `uv.lock` appeared during root verification and was left untouched.
- Read AGENTS.md, existing review, provenance closure, ingestion and policy source, bounded validator, adapter payload parsing, and relevant worker/lifecycle/alerts/CRM/dashboard/analytics/health diffs and tests. Full verification belongs to root and was not duplicated.

## P1: independent malformed header erases a valid recipient canary alias

Primary introduced defect: `src/jobs_automation/ingestion/engine.py:40-43` calls strict Python 3.13 `getaddresses` once for the entire participant list. A malformed raw From causes that function to return no addresses, including otherwise valid To recipients. The real `GmailAdapter` preserves the raw From in `RawEmailMessage.sender` (`src/jobs_automation/adapters/gmail.py:282-283,329-334`). Both fresh classification (`ingestion/engine.py:175-181`) and historical reclassification (`ingestion/engine.py:66-68,94-103`) feed that raw field into the shared canonicalizer.

Reproduced entirely offline using the real adapter payload parser and SQLite: `From: a@b.com;c@d.com`, `To: owner+canary@example.com`, configured alias `owner+canary@example.com`. The adapter returns recipients `['owner+canary@example.com']` and sender_address `''`. Central canonical participants become `[]`; fresh `_is_canary` is False; historical policy match is False; historical reclassification count is 0 and durable canary tag stays False. Consequently the fresh canary early return at `ingestion/engine.py:370-374` is bypassed, and downstream quarantine relies on a durable tag that never exists.

This contradicts the prior review's claim at `docs/V1_7_CLI_GATE_REVIEW_20260922.md:55` that the case is unreachable with adapter data. Canary matching explicitly includes recipient aliases; incoming traffic addressed to that alias need not have an owner-controlled From.

Related causal boundaries reproduced:

- `GmailAdapter` also parses To and Cc together (`gmail.py:284-288`); with normal From, valid canary To, and malformed Cc, `raw.recipients == []`. Fixing only the central parser leaves that path open. This adapter aggregation predates this repair, but matters to the claimed complete canary boundary.
- `EmailPollingConfig` accepts `[valid_alias, 'a@b.com;c@d.com']`, and current effective canonical policy is empty. Invalid policy should fail closed rather than silently disable canary recognition.

Smallest recommended production repair: parse independent participant/header values separately, including Gmail To/Cc, and validate each configured identity independently as exactly one canonical address. Retain exact-match semantics, case/display-name normalization, historical one-way tags, and lookalike exclusions. Add only focused regression coverage proving this actual adapter-to-ingestion failure and policy fail-closed behavior; then run required full checks and independent exact-tree review.

## Reproduction artifacts

From the reviewed worktree:

```sh
.venv/bin/python /tmp/jobs-astra-canary-header-20260922/reproduce.py
.venv/bin/python /tmp/jobs-astra-canary-header-20260922/boundary_cases.py
```

Observed outputs are retained as `output.txt` and `boundary_output.txt` alongside the scripts. Scripts perform no network, credential, mailbox, model, scheduler, or persistent runtime access. They create SQLite only in memory. No source/test files were changed. These are mechanical engineering evidence, never G14-G17 live proof.

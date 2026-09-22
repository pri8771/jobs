# DD2 V1.7 bounded ingestion repair review — 2026-09-22

## Review boundary

This is an independent-review preparation record for an implementation branch. It
is **not** a ChatGPT lead verdict, a merge authorization, or evidence that any
V1.7 live gate passed. It opens no Gmail, candidate, employer, or production
execution authority.

- project/repository: Jobs Automation / `pri8771/jobs`
- artifact and submission: DD2 bounded Gmail-ingestion, lifecycle, replay, and
  timeline repair on `codex/jobs-v17-cli-gate-20260922`
- reviewer actual identity/role: Codex subagent
  `/root/jobs_final_independent_review`, independent read-only source reviewer;
  it did not modify the reviewed worktree
- code SHA + relevant production tree/dependency/schema identity:
  `bc93a8a0bd381f9f675440b62c91aaf3b8406795`, tree
  `fa744608a4aa74111cff15758c0b7461ea18f6c8`; bounded-audit schema version 2;
  no dependency-lock change is included
- starting worker candidate: `dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`
  (first parent `113c584d731bee4c46e2d54d6048344991e6e16d`, integrated main
  parent `1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`)
- canonical contract read from: `origin/main@1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`,
  `coordination/WORK_QUEUE.md` and `coordination/codex/HANDOFF_TEMPLATES.md`

## Reviewed paths

`src/jobs_automation/adapters/gmail.py`,
`src/jobs_automation/ingestion/engine.py`,
`src/jobs_automation/ingestion/bounded.py`,
`src/jobs_automation/ingestion/readiness.py`,
`src/jobs_automation/lifecycle/alerts.py`,
`src/jobs_automation/lifecycle/timeline.py`, and
`src/jobs_automation/cli/main.py`, with their focused tests. The final delta
also changes `tests/test_bounded_ingestion.py`.

## Checks actually executed

The integrating coordinator executed on the exact final SHA in clean isolated
worktree `/tmp/jobs-v17-cli-gate-20260922`:

```text
uv run pytest -q
# exit 0 — 439 passed, 2 skipped in 50.17s

uv run ruff check .
# exit 0 — All checks passed

MYPYPATH=src uv run mypy src
# exit 0 — Success: no issues found in 74 source files

git diff --check
# exit 0 — no output
```

The independent reviewer separately executed:

```text
./.venv/bin/python -m pytest -q tests/test_bounded_ingestion.py tests/test_timeline_replay_scope.py
# exit 0 — 26 passed
```

It also performed scoped Ruff/mypy checks and a fresh in-memory canary-only
run plus explicit replay. Earlier worker-reported counts are not credited as
independent evidence here.

## Positive and adverse coverage

The repaired code keeps the bounded execution path fail-closed for malformed
or incomplete Gmail polls, binds readiness/timeline evidence to the matching
mailbox/application, scopes lifecycle and alerts to the admitted batch, and
requires explicit stateful replay authorization.

The final independent reproduction used a canary-only batch and explicit
replay. Both operational audits could succeed, but both had
`application_id_sha256=[]`; the linked application's timeline had
`genuine_evidence.source_count=0`, `canary_excluded_count=2`, and `replay=null`.
The regression also confirms the two canary provider-message hashes cannot
appear in bounded proof metadata. This preserves the separate readiness gate
without allowing operational canary traffic to become recruiting proof.

## Finding and repair

**REWORK_FOUND, repaired before this review:** the earlier integration derived
application and provider-message proof associations from all batch messages
before excluding canaries. A canary-linked recruiter batch could therefore
attach a successful replay record to an application despite no genuine source
evidence.

The repair at `bc93a8a` derives both association lists exclusively from
`genuine_messages`, then locks that invariant with the canary-only regression.
The independent reviewer found no remaining implementation blocker in the
final delta.

## Live-proof disposition

No real mailbox was read, no candidate/private content was accessed, and no
real recruiting event, timeline, interview, follow-up, or restart proof was
produced. G14, G15, G16, and G17 remain **UNPASSED** under the canonical queue.
Fixture, adapter, and in-memory replay tests above are engineering evidence
only and do not replace G17's genuine authorized production-path proof.

## Recommendation and requested authority

- recommendation: **RECOMMEND_ACCEPT** for the bounded implementation repair
  at `bc93a8a` only; the overall V1.7 milestone remains **REVIEW_BLOCKED** on
  its live gates
- formal acceptance authority and requested action: ChatGPT lead should
  independently accept or rework this exact source SHA. Any engineering
  acceptance must explicitly preserve the G14–G17 blockers and must not imply
  a main merge or live-action release.
- next bounded independent task: after the lead verdict, retain this branch
  unchanged and await a separate scoped genuine-evidence/access grant before
  any G17 operation. Do not invoke Gmail or create a new worker/watch stream.

# Jobs bounded-ingestion repair — prepared, not handed off

State: **OWNER_APPROVAL_REQUIRED_FOR_FABLE_HANDOFF**. These are local owner-authorized fixes, not a worker assignment, integration or acceptance. ChatGPT remains formal acceptance authority; Fable remains integration owner. Author/test operator: Codex, therefore these are author checks, not independent acceptance.

- Artifact: Jobs V17-M04 / V17-R05, two bounded SP2 concerns: batch isolation and replay proof semantics. Minimum/ceiling: genuinely live V1.7; later plans remain parked.
- Canonical contract: `main@1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`, `CODEX_START.md`, `docs/FABLE_V17_LIVE.md`, native queue and `coordination/codex/HANDOFF_TEMPLATES.md`.
- Expected implementation base: `claude/serene-brown-g6uij0@dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`. Base was fetched and remained unchanged before commit. Remote worker process/dirty state remains UNKNOWN; its worktree was not touched.
- Local repair: `codex/jobs-bounded-repair-20260922@3d9cc95d03b0b8c146d10423060d97ee9736212c`. Separate clean worktree; no upstream configured and no repair ref pushed.

## Change and evidence

`ingestion/engine.py` retains internal batch UUID membership, including deduplicated messages, without adding it to serialized sweep reports. `ingestion/bounded.py` processes only batch messages, excludes canaries, and scopes alerts to affected threads/applications. Thread-scoped alerts may read that thread's existing history to avoid false unanswered alerts; they cannot touch unrelated threads. Default global alert callers retain their prior behavior.

A replay with changed state, a mismatch against the recorded state, or a missing original now records FAILED plus stable errors. The existing CLI's FAILED path returns nonzero. Positive restart/replay behavior remains covered.

Before the production edit, the initial regressions failed on unrelated lifecycle mutation, unrelated alerts and false-success replay; restart/replay passed. Nine new synthetic regressions now cover empty/nonempty isolation, duplicate membership, scoped reply closure, canary exclusion, missing original, changed replay, historical drift and restart/replay.

Exact-source full suite: **437 passed, 1 skipped**, exit 0. The skip is the cross-host local-form redirect case: this Mac cannot bind `127.0.0.2`; no host configuration was changed to bypass it. The dedicated Jobs PostgreSQL role/password-rotation test and headless Chromium local forms passed. Ruff and mypy (74 source files) pass. No employer page, real mailbox or private profile was used.

Evidence: [manifest](../codex/evidence/20260922-repair/manifest.json), [full checks](../codex/evidence/20260922-repair/jobs-complete-checks.txt), [commands and exits](../codex/evidence/20260922-repair/jobs-final-checks.json), [environment/tree identity](../codex/evidence/20260922-repair/jobs-repair-environment.json). The dedicated ephemeral Jobs database is stopped; test data was never shared with SwarmAI.

## Review and next boundary

Recommendation for the original worker source remains **REWORK_FOUND**. Repair acceptance is **REVIEW_BLOCKED** pending an independent reviewer/ChatGPT verdict; Codex does not independently accept its own code. Preserve prior P0A/V1.5 acceptance. No G14–G17 or V1.7 live gate is passed by these fixtures.

After explicit owner approval only: route this exact diff/evidence to the existing Fable session and ChatGPT lead, refetch current worker base, reconcile any competing edits non-destructively, and request an acknowledgement before calling it assigned/running. Apply only the five changed source/test files; no coordination-branch application snapshot merge. Current write surface: `src/jobs_automation/ingestion/{engine,bounded}.py`, `src/jobs_automation/lifecycle/alerts.py`, `tests/test_bounded_ingestion{_scope,_alert_scope}.py`.

Done means independent review of the actual integrated SHA and required live proof under existing exact grants. Next live frontier remains approved genuine inputs/eligible host and later bounded browser/application/mailbox authority. This packet grants none of those actions. Native heartbeat stays one owned five-minute implementation stream; publication alone is not meaningful progress or a fresh ACK.

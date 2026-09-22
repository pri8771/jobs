# COMP-3A bounded.py composition return — 2026-09-22

Implementer: **Claude**, owner-assigned Jobs V1.7 implementation owner (`CLAUDE_JOBS_V17_RACE_20260922.md`). At startup I found no competing Jobs source writer (no COMP-3A branch or worktree existed; the last Jobs source push was engine 0a319d0).

**READY_FOR_LEAD_REVIEW** (within the released COMP-3A scope), plus **one exact held dependency** for which a patch is prepared and awaits release.

## Candidate

- Source: `claude/jobs-comp3a-bounded-20260922@212b76280677ac61d878abaec580d798199b84fc`
- Tree: `233fd37dce56b5c13d68ffbf9a547063eb1efa52`
- History (never rewritten): 54e255a (initial, reviewed) → de29999 (review rework) → 212b762 (delta re-review minors)
- Parent: accepted engine `0a319d07df4d679de7b32f84fbd9faf215037881` (disposition §15)
- Draft PR: https://github.com/pri8771/jobs/pull/31 (stacked on PR30)
- Worktree: `/Users/pchordia/Downloads/swarm_codex/review/jobs-comp3a-bounded-20260922`
- Changed files (allowed scope only): `src/jobs_automation/ingestion/bounded.py`, `tests/test_bounded_ingestion.py`, `tests/test_bounded_ingestion_scope.py`, new `tests/test_bounded_reference_scopes.py`.

## How bounded.py was composed (deliberately, not wholesale)

I ran a three-way merge with base `dd2e0de`, control `0a319d0` and reference `2969ac28`, which is canary `eec0ae3`'s bounded.py plus the accepted PR27 patch. The control delta is two hunks, and both conflict. Each resolves to reference semantics that subsume it:

1. **Control's batch-id lifecycle query** (current batch, non-JOB_ALERT, skip durable canary). It is subsumed by `_batch_messages` (exact current batch, chronological `received_at, id`) and the genuine set, which excludes runtime and durable canaries. The lifecycle set is genuine minus JOB_ALERT.
2. **Control's pre-computed alert scopes.** They are subsumed by `admitted_thread_ids` from lifecycle-eligible messages, `alert_application_ids` resolved **after** lifecycle from lifecycle-eligible links, and `proof_application_ids` resolved separately after lifecycle from all genuine messages, including JOB_ALERT.
3. **Control's inline replay mismatch flag.** It is subsumed by V3 error-first status (`REPLAY_LOGICAL_STATE_MISMATCH` → FAILED). Control's `REPLAY_ORIGINAL_NOT_FOUND` becomes a stronger V3 rejection **before any poll**: `REPLAY_RUN_NOT_FOUND`, with direct runs carrying a replay id rejected as `REPLAY_MUST_USE_REPLAY_API`.

The merged file is byte-identical to `2969ac28`'s bounded.py except for two narrow additions. The first:

- `replay()` also accepts `str` and immediately raises `REPLAY_REQUEST_REQUIRED` before any poll or side effect.
- The held CLI still calls `replay(run_id, mailbox)`. V3 audit rows intentionally omit raw query text, so such a replay cannot be reconstructed. The addition makes that path fail closed instead of crashing, and keeps `mypy src tests` clean without touching the CLI.

Second addition, from independent review: the reference commits historical canary reclassification before it verifies the bound mailbox. Now `_reconcile_persisted_canaries` verifies the mailbox only when tags would change, before committing them, and rolls back on any error. A run the adapter cannot serve therefore leaves no durable tag. Independent verifiers classed this as inherited from the accepted reference, not a COMP-3A defect. It is kept as a disclosed, test-backed safety improvement (run and replay paths, red on 54e255a). The lead may revert it.

All engine APIs that V3 bounded.py imports exist on accepted 0a319d0. So do the held `alerts.py` scope kwargs. No held file was modified.

## Required regressions (§15) → tests

1. JOB_ALERT in proof, out of lifecycle and both alert scopes: `test_proof_and_alert_scopes_are_distinct_and_batch_confined[False/True]`.
2. Lifecycle-created or repaired link visible to post-lifecycle stale scope: `test_lifecycle_link_is_resolved_after_processing_for_alerts_and_proof[False/True]`.
3. Proof IDs separate from alert IDs: same as item 1.
4. Runtime and durable canaries excluded: reference tests plus the canary tests (`test_canary_mail_is_tagged_…`, `test_dry_run_duplicate_canaries_…`, `test_preexisting_canary_duplicates_…`).
5. Outside-batch messages and links excluded: reference test and the control scope tests.
6. Dry run stays non-mutating with truthful proof selection: the `dry_run=True` parametrization plus the existing dry-run tests.
7. Reclassified-canary replay gives `REPLAY_EVIDENCE_CANARY_RECLASSIFIED` with **0 new list calls**: `test_replay_canonicalizes_policy_before_any_poll_of_legacy_canary`, plus the same-policy test.
8. Malformed or legacy evidence fails before poll: `test_replay_rejects_malformed_v3_evidence_before_polling` (0 polls) and `test_replay_rejects_legacy_audit_rows_without_safe_request_schema`.
9. Policy fingerprint mismatch fails before poll: **new** `test_replay_policy_fingerprint_mismatch_fails_before_any_poll` (0 polls).
10. An ordinary run records strict valid V3 audit: `test_bounded_run_records_secret_free_evidence_…` (`is_valid_bounded_audit_metadata`).

New control-side regressions:
- `test_missing_original_is_rejected_before_any_poll` (both routes, 0 polls, no rows).
- `test_legacy_mailbox_only_replay_fails_closed_before_any_poll`.

## Disclosed test changes

- Control scope tests ported to the V3 replay API. Stateful replays pass `allow_stateful_replay=True`, as V3 requires.
- Conflict unions keep the stricter assertions from both sides (for example, control's no-task/no-link/durable-tag checks plus the reference's `POLL_INCOMPLETE` codes).
- Reference-test typing: helpers annotated, and classes patched via their home modules. They are the same class objects.
- **Three strict xfails** (`raises=AssertionError`), each of which fails for exactly its held reason and becomes a hard failure once fixed. The installed-entrypoint run, restart, timeline and fail-closed legacy replay legs are enforced separately:
  - `test_installed_entrypoints_restart_and_replay_bounded_batch`: the held CLI lacks the V3 `--apply-replay`/request replay.
  - `test_reclassified_canary_audit_is_not_timeline_replay_evidence` and `test_fresh_canary_run_is_not_application_timeline_replay`: the timeline assertions were split out of the accepted canary tests without weakening them. The control `timeline.py` still exports a reclassified-canary bounded audit as replay evidence. The canary exclusion lives in `db/canary_provenance.py`, which is absent on 0a319d0, together with the canary timeline.

## Verification (evidence: `/tmp/claude-jobs-comp3a-evidence-20260922/`)

| Check | Result |
|---|---|
| Red before, on exact parent 0a319d0 (candidate tests copied onto `git archive`) | scope file **6 failed / 2 passed**; bounded and reference files fail to import the V3 API (`BOUNDED_AUDIT_SCHEMA_VERSION`). The earlier accepted reference red (3 fail / 1 pass) is reused |
| Focused bounded/replay/reference/Gmail | **76 passed, 3 strict xfailed** (settled on 212b762) |
| Full pytest, owned PostgreSQL 56422 (socket-only, pchordia, proof integration exercised) | **571 passed, 1 existing host skip (playwright), 3 strict xfailed** in 61s; new remaining proof DBs/roles: **0** (`settled-final/`). Earlier settled runs: 54e255a 568/1/2, de29999 570/1/3 |
| `mypy src tests` | clean, 119 files |
| Ruff `src tests`; format on changed files; `git diff --check` | clean |
| Blob hashes before and after the suites | identical; the commit contains exactly those blobs |
| `uv.lock` | none generated |
| Hosted CI | stacked target; NO RUN is not a green claim |

Intermediate failures are kept in `first/` and `second/`: the full-suite run before test porting (7 replay failures), the mypy run with 7 legacy replay call errors, and an extra `export["replay"]` assertion that I added and then withdrew. One environmental note: running from `/tmp` trips the proof tool's temp-path guard (`test_real_proof_integration`), so candidate checks run from the review worktree.

## Independent review

Round 1, on 54e255a: a 3-lens exact-tree review with adversarial verification of every finding.
- **Spec: RECOMMEND_ACCEPT.** Only the 4 allowed files changed. bounded.py differs from 2969ac28 only by the claimed replay branch. Every §15 V3 item and frozen semantics 1–6 was traced in code. Regressions 1–10 were mapped and mutation-checked.
- **Control: RECOMMEND_ACCEPT.** Checkpoint, incomplete-poll, dry-run and lifecycle-rollback behaviour is preserved. The control hunks are subsumed and none are lost. Held CLI and timeline callers work on V3 rows. The CLI `--replay-run` fails closed.
- **Tests: RECOMMEND_REWORK.** It raised (a) the whole installed-entrypoint test was xfailed, and (b) the reference fresh-canary `export["replay"] is None` assertion had been dropped. Finding (b) was adversarially refuted as a non-defect but is tracked anyway.
- Control also reproduced (c), the mailbox check running after reclassification. That was refuted as a COMP-3A defect because it is inherited.

Rework de29999 fixed (a), (b) and (c).

Round 2, a delta re-review of 54e255a..de29999: **RECOMMEND_ACCEPT**, with (a), (b) and (c) verified resolved and three minors raised. 212b762 addressed all three (any-error rollback; a contract-valid replay-path regression that truly reaches the mailbox check; installed run id bound to the persisted audit).

A final independent confirm of de29999..212b762 is pending at the time of writing; see the next checkpoint.

## Exact held dependency — patch prepared, awaiting release

**COMP-3A-CLI.** Port only the accepted `eec0ae3` `ingest_mailbox` command into `src/jobs_automation/cli/main.py`:
- the request is validated before config, database or OAuth side effects;
- `--apply-replay` is explicit and exclusive of `--dry-run`;
- `replay(run_id, request, allow_stateful_replay=…)`;
- configured `platforms.email.canary_identities` are merged.

No other CLI function changes.

- Proposal source: `claude/jobs-comp3a-cli-proposal-v3-20260922@9b591fa50bab8e1d1391600aeef4c5af6588fd65`, tree `613755aed129ebd4cfb0ae717965427abaed4442`, stacked on the final candidate. It supersedes cd9b987 and bb1a3ed. **Not a candidate until released.**
- Its checks (`/tmp/claude-jobs-comp3a-cli-proposal-v3-evidence-20260922/`): full owned PG **572 passed / 1 host skip / 2 strict xfails** (timeline only). The installed restart/replay test passes, and the ambiguous `--replay-run` fails closed. mypy clean (119), Ruff clean, cleanup 0.
- `main.py` has inherited formatting drift outside the ported function (lines ~885/1090/1155/1466). I left it untouched.

**Requested disposition:** accept COMP-3A at 212b762, and release/accept COMP-3A-CLI at 9b591fa in the same verdict. Then name the timeline/`canary_provenance` composition packet that clears the remaining strict xfail.

No live Gmail/OAuth, employer/browser/application, model/provider, scheduler, spend, deployment or main-merge action occurred. G14–G17 remain UNPASSED.

# Accepted Jobs source composition diagnostic

Status: COMPOSITION_REWORK_FOUND — stopped at first nontrivial semantic conflict. Read-only mechanical recommendation, no acceptance or source change.

## Exact identity

- Integration starting input: b67fc523863babd3e195ee71a05f00fa0f2f7e79, tree0338b7ef26bb727536175d975513976a068a9720.
- Canary input: b2688eeabb5ca996767b27b78d0004678eeee756, accepted tree6644f340b98eae517ae08ccde38a28da5f2c52a9.
- One common ancestor: dd2e0deb15ce0ff8983c4ed502e3e17206db2e80.
- Isolated worktree remains /tmp/jobs-astra-composition-20260922 on codex/jobs-accepted-composition-20260922 at b67fc523. Clean before/after.
- `git merge-tree --write-tree b67fc523... b2688ee...` returned exit1 and diagnostic tree3657a0ba92bbc83fdd727dee778442a407490ba9. The tree contains conflict markers and is NOT a buildable/review-ready composition. It was not checked out, committed or merged.
- Full exact delta lists: control-delta.txt (16 commits) and canary-delta.txt (10 commits); diff-stat and merge stage blobs retained. No manual reimplementation, checkout, resolution, index mutation or source write occurred.

## First semantic conflict: bounded ingestion alert admission

File: src/jobs_automation/ingestion/bounded.py. Raw conflicted content: bounded-merge-candidate.txt; accepted input excerpts: bounded-control.txt and bounded-canary.txt.

The control-center input derives lifecycle/alert scope from persisted messages in the current batch AFTER excluding classification JOB_ALERT. It skips current header-flagged canaries, adds remaining message IDs/thread IDs, processes lifecycle, then resolves application IDs from those remaining message links for bounded stale alerts.

The canary input first resolves the full batch, removes runtime and durable-provenance canaries, derives admitted_application_ids from all those genuine messages BEFORE lifecycle, then skips JOB_ALERT only inside the lifecycle loop. It subsequently derives alert thread IDs from all genuine messages and uses the earlier application IDs for stale alerts.

This is not just duplicate code or disjoint additions: the selected message set and timing differ. A genuine JOB_ALERT with an application link is outside the control input's alert scope and inside the canary input's scope. Simply choosing canary content, choosing control content, concatenating both, or sharing one ambiguous `genuine_ids` list changes/drops one accepted input's admission behavior. A mechanical union is therefore not certified under the composition contract.

Smallest lead disposition: freeze separate lifecycle/alert eligibility versus audit/proof admission sets, retaining full durable-canary exclusion and current-batch confinement, and explicitly choose the intended JOB_ALERT and post-lifecycle-link eligibility. Root should then implement only that released composition resolution and test both accepted invariants; do not infer this recommendation as permission.

The same file also has a replay/status conflict where the old post-poll original lookup/failure status branch meets the canary line's validated V3 replay metadata, current-canary check and final error-first status calculation. The raw union contains a duplicate else. This later hunk is recorded but was not resolved or independently classified after the first semantic stop; V3 preflight/zero-new-poll semantics must remain required.

## Complete conflict inventory from merge-tree

| File | Classification in this bounded pass |
| --- | --- |
| src/jobs_automation/ingestion/bounded.py | First nontrivial admission-set/timing conflict, described above; stop reached |
| src/jobs_automation/ingestion/engine.py | Git content conflict; semantics not assessed after stop |
| src/jobs_automation/lifecycle/alerts.py | Git content conflict; semantics not assessed after stop |
| src/jobs_automation/lifecycle/crm.py | Git content conflict; semantics not assessed after stop |
| tests/test_bounded_ingestion.py | Git content conflict; semantics not assessed after stop |
| tests/test_gmail_adapter_bounded.py | Git content conflict; semantics not assessed after stop |
| tests/test_health.py | Git content conflict; semantics not assessed after stop |
| tests/test_worker.py | Git content conflict; semantics not assessed after stop |

Git also auto-combined automation/auto_engine.py, cli/main.py, dashboard/server.py, health.py, lifecycle/engine.py, worker.py and tests/test_dashboard.py. A clean textual merge is not proof that both accepted behaviors survived; full path mapping remains outstanding. No conflict is declared mechanically resolved.

## Scope and next step

No tests run: there is no resolved composition candidate. Full integration validation specified by the lead is still outstanding. Request the smallest composition conflict disposition rather than opening broader J20-01 work. G14-G17 stay unpassed. No application/mailbox/provider/browser/model/scheduler action, spend, deploy, main merge or Fable dispatch.

Native raw diagnostic artifacts and SHA256SUMS: `../evidence/CODEX-ASTRA-COMPOSITION-20260922/`. Lead disposition requested; no merge candidate was created.

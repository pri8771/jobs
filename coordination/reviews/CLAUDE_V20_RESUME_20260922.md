# Claude V2.0 resume checkpoint — Jobs — 2026-09-22

Owner resumed three-project V2.0 work in the current Claude session (~17:55Z). No live, mailbox, browser, application, model, scheduler, spend, merge or deploy action taken.

## Verdict read (no re-review)

- Lead `e74785c` **ACCEPTED — REFERENCE_ONLY** `2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a` / tree `9e34b5c8e56ca501f84f6b0f7451aead34cf412e` (PR27). It explicitly does not certify b67 compatibility, composition, `engine.py` resolution or the other held conflicts.
- Accepted canary `b2688ee` (lead `326fd558`) and separate control-center `b67fc523` remain un-composed.

## New non-mutating evidence

`git merge-tree --write-tree --name-only` from common ancestor `dd2e0deb`:

| Left | vs `b67fc523` | Conflicted files |
|---|---|---|
| `b2688ee` | same 8 | bounded.py, engine.py, lifecycle/alerts.py, lifecycle/crm.py, tests/test_bounded_ingestion.py, tests/test_gmail_adapter_bounded.py, tests/test_health.py, tests/test_worker.py |
| `2969ac28` | same 8 | identical list |

The accepted reference patch settles the `bounded.py` semantics but leaves the same textual conflict set. `/tmp/jobs-astra-composition-20260922` is still clean at `b67fc523` (0 status lines). Nothing was composed.

## Hosted CI now executes (repos public)

The owner made the repos public, and a rerun of `35757522343` (PR26, exact `b2688ee`) now gets real runners and steps:

- Ruff: pass.
- `mypy src tests`: **fail, 22 errors** (tests/test_cli.py 15, tests/test_worker.py 7: untyped test defs and `Model | None` assignments).
- The Alembic chain check and pytest were skipped as a consequence.

The local accepted evidence (“mypy 75 clean”) covered `src` only, but the CI-configured gate includes `tests`. Main comparison rerun `35678124379` (exact `1a4efbb0`) is **fully green**: Ruff, `mypy src tests`, the Alembic chain and pytest with the Postgres service all pass. The 22 test-typing errors therefore **enter in the V1.7 branch lineage**; both files carry about 660 changed lines relative to main. They are not inherited debt. This is a CI-gate finding, not a product defect. It needs a lead disposition, for example a bounded test-typing packet before any composition is called CI-clean. No fix was applied.

Operator error, disclosed: I first reran `35759901989` believing it was main CI. It is the scheduled **Worker Heartbeat Monitor** (`contents: read`, writes only a step summary). I cancelled it at once. Nothing was written. With the repo public, that existing `*/15` read-only schedule will now execute where billing used to block it.

## Blockers (smallest first)

1. **Lead release of the next dependency/conflict packet**, i.e. the `engine.py` canary APIs b67 lacks, before any composition. Needs the native Jobs lead.
2. **Lead disposition of the hosted `mypy src tests` gate.** Needs the native Jobs lead.
3. **G14–G17 scoped owner grants.** A V2.0-narrowed request accompanies this checkpoint. Status: REQUESTED, NOT GRANTED.

G14–G17 remain UNPASSED. No V1.7 or V2.0 live claim is made.

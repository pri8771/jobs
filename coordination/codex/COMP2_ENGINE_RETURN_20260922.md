# COMP-2 engine composition return — 2026-09-22

READY_FOR_LEAD_REVIEW. Draft PR30: https://github.com/pri8771/jobs/pull/30

- Source: `0a319d07df4d679de7b32f84fbd9faf215037881`
- Tree: `f98b225bceb687238a8bbea59ce08934750cf7f5`
- Parent: accepted COMP-2B `bfc507903452d32d979cfb7b8c78f5ac916fa305`
- Release: `641ade3bdbb9a3d204719db3d913d7e9a1264f4e`, V17_ACTIVE_DISPOSITION section 14.
- Worktree: `/Users/pchordia/Downloads/swarm_codex/review/jobs-comp2-engine-20260922`

## Scope and preservation

Only engine.py and two authorized test files changed. Ported accepted canary helpers, exact-address matching, durable historical tagging, runtime membership including dry runs and duplicates, and explicit opt-in safe error categories. Fresh canaries stop before job, ordinary link, review-task and candidate-activity effects.

Independent review compared ASTs: helpers/constructor/matching/tagging match accepted eec0ae3; control checkpoint methods, incomplete-poll preflight, post-loop checkpoint/commit, candidate-reply attribution, recruiting attribution and discovery branches match bfc5079. This is a deliberate merge, not wholesale replacement.

Initial focused run found one stale timeline assertion. Accepted eec0ae3 already requires no application association for fresh canaries. The test now preserves unchanged activity, verifies no MessageLink, zero application sources, and two durably tagged stored rows. Independent diagnosis confirmed no timeline production dependency. Held V3 audit/hash/replay assertions were not ported. An intermediate missing test import was corrected before settled checks; no production workaround or assertion weakening.

## Verification

- Focused Gmail/engine/bounded/candidate-reply suite: 56 passed.
- Full suite: 545 passed, 1 existing host-dependent skip.
- Owned socket-only PostgreSQL on 56422 exercised the proof integration; no remaining proof databases or roles, cleanup 0.
- Ruff clean; full `mypy src tests` clean in 118 files; all three changed files formatted; diff check clean.
- New/extended regressions on exact parent: 19 failed, 12 passed. Some failures concern missing new APIs; this is not a claim of 19 distinct production defects.
- Independent exact-tree review: RECOMMEND_ACCEPT for this released scope, no actionable findings. Reviewer did not duplicate the settled suites.
- `uv.lock` removed before commit. Candidate worktree clean and pushed.
- Hosted CI: stacked PR target has no matching trigger in the inherited main-only workflow. NO RUN is not green. No workflow edits or main merge.

Retained local evidence: `/tmp/jobs-comp2-engine-evidence-20260922/` (baseline-red.log, full-pytest.log, postgres.json, settled-summary.json, verify.py). Baseline worktree `/tmp/jobs-comp2-engine-baseline-20260922` contains only copied regression tests against bfc5079; it is not a candidate.

## Disposition requested

Accept/rework this exact engine scope. If accepted, name the next bounded downstream composition task and its file ownership. bounded.py V3/reference, db/canary_provenance.py, lifecycle/alerts/CRM, worker/dashboard/CLI remain held until released. This engine packet does not establish their integration or genuine G14–G17 proof.

No live Gmail/OAuth, employer browser/application, model/provider, scheduler, spend, deploy, Fable/Claude dispatch or main merge occurred.

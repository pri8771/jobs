# COMP-2A exact source return — 2026-09-22

READY_FOR_LEAD_REVIEW; independent recommendation only. Release44c4655, review rule1463b49.

- Source `1b9efdda418baa059903215349e27493cf709f3a`
- Tree `cb57c3fe973cd8e837838d1a095d334cc2cba321`
- Parent `b67fc523863babd3e195ee71a05f00fa0f2f7e79`
- Branch `codex/jobs-comp2a-prerequisites-20260922`
- Worktree `/Users/pchordia/Downloads/swarm_codex/review/jobs-comp2a-prerequisites-20260922`

Only released Gmail/platforms/config-test/Gmail-test files changed. platforms.py matches accepted eec0ae3 byte-for-byte; Gmail parser matches accepted method AST while preserving control pagination/completeness/time/outbound logic. All prior test ASTs are unchanged. Independent exact-tree review: RECOMMEND_ACCEPT, no findings.

## Evidence

- New regressions before repair:8failed23passed; repaired focused set31passed.
- Full pytest530passed1existing hostskip, including owned socket-only PostgreSQL56422 proof integration. Before/after proof databases and roles empty; cleanup0.
- Ruffall clean, source-only mypy74files clean, changed-file formatting/diff clean.
- Full mypy27 inherited errors across the five files enumerated by1463b49. Baseline before any COMP2A edits and current log are byte-identical (`diff -u`exit0). Zero new errors. Full integration CI remains blocked, not green.
- Initial /tmp worktree fullrun528passed1skip2failed because real-proof guard intentionally refuses profile paths under /tmp. Moved the exact same Git tree to the stable review path, refreshed only the isolated editable install, then reranfullsuccessfully. No path guard or test weakening.
- uv.lock untracked/generated and removed before commit and return.

Logs: `/tmp/jobs-comp2a-evidence-20260922/`; settled full/PG logs in `stable-path/`; baseline typing `/tmp/jobs-comp2a-baseline-mypy-20260922.log`. Source/fixture checks are ENGINEERING, never G14-G17 live proof.

## Next dependency

Request exact-SHA COMP2A disposition. COMP-2B-TYPING only activates after acceptance; five named test files only. Engine/V3/provenance and all other conflict scopes remain held until typing is accepted. Dynamic resume owner requirement is recorded separately; verified fact paths and desired proof job remain unsupplied. No mailbox/browser/application/model/scheduler/spend/deploy/main merge.

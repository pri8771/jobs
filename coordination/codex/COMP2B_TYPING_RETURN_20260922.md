# COMP-2B typing return — 2026-09-22

READY_FOR_LEAD_REVIEW. Draft PR29: https://github.com/pri8771/jobs/pull/29

Source `bfc5079`; tree `4c3bfa242b34912066c0470efb8745f5ae22b3ad`; parent accepted COMP-2A `1b9efdda418baa059903215349e27493cf709f3a`. Release and COMP-2A acceptance: `d45f82b18802976a956fe2e9a73f015aa9f1968d`.

Only the five released test files changed. Precise annotations, five non-null assertions, a TypedDict/cast for the owned Node harness result, and the same classifier lambda installed via pytest monkeypatch remove the inherited typing errors. No production, CI configuration, exclusions, skips or test deletion. Formatting expanded three formerly dense files.

Independent mechanical review recommends acceptance of the exact tree: all29testfunctions and145existingassertions retained. Normalized AST comparison shows no further behavior changes; monkeypatch also restores the same instance attribute at teardown.

Validation:
- exact accepted-parent baseline reproduced27errors in5files (`/tmp/jobs-comp2b-mypy-red-20260922.log`);
- `uv run mypy src tests`: clean118files;
- focused five-file suite:46passed;
- full suite:530passed,1existinghostskip;
- real owned socket-only PostgreSQL56422 proof integration, zero remaining proof databases/roles;
- Ruffall, changed-fileformat and diff checks clean;
- generated untrackeduv.lock removed before commit.

Full/PG evidence: `/tmp/jobs-comp2b-evidence-20260922/`. Source worktree: `/Users/pchordia/Downloads/swarm_codex/review/jobs-comp2b-typing-20260922`. Hosted exact-head CI pending readback; no green claim until observed.

Request formal exact-SHA disposition. Engine composition remains held until this repair is accepted; no mailbox/browser/application/model/scheduler/spend/deploy/main merge. None of these checks pass G14-G17 live gates.

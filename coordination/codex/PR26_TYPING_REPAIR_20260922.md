# PR26 exact-tree typing repair — READY_FOR_LEAD_REVIEW

Authority: `V17_ACTIVE_DISPOSITION_20260922.md`, lead commits `4e4ea28` / `a4003c8`.

Base: `b2688eeabb5ca996767b27b78d0004678eeee756`, tree `6644f340b98eae517ae08ccde38a28da5f2c52a9`.
New source: `eec0ae3` on `codex/jobs-v17-cli-gate-20260922` / Jobs PR26.
Exact tree: `b41f35ff4e816c3df52521e328d60d598a4bc408`.

The hosted command `mypy src tests` reproduced 22 errors in two test files (113 files checked), although earlier src-only mypy was clean. The repair adds precise fixture/helper types, keeps SQLAlchemy reload values separate from constructed non-optional values, and retains non-null assertions. The counting adapter now declares the actual adapter signature/defaults and forwards the same arguments. No production source, CI configuration, ignores, skips or assertions changed. Ruff formatting normalized the existing mixed line endings in the allowed worker test file to LF; use `git diff --ignore-space-at-eol` for the semantic review.

## Validation on exact reviewed contents

- `uv run mypy src tests`: PASS, 113 files.
- `uv run pytest -q tests/test_cli.py tests/test_worker.py`: 26 passed.
- Full pytest with `PROOF_TEST_PG_ADMIN_URL` pointing to the existing owned socket-only PostgreSQL on port 56422: 490 passed / 1 pre-existing host skip, 74.32 seconds. Real PostgreSQL proof integration executed; this is synthetic engineering evidence, not G14.
- PostgreSQL before/after proof database and role inventories: empty; new remaining databases 0, roles 0. No shared service lifecycle changes.
- `uv run ruff check .`: PASS.
- `uv run ruff format --check tests/test_cli.py tests/test_worker.py`: PASS.
- `git diff --check`: PASS.
- Generated untracked `uv.lock` removed before commit; it is not in the candidate.

Local check artifacts: `/tmp/jobs-pr26-typing-evidence-20260922/` (`checks.json`, `full-check.json`, `full-pytest.log`, `postgres.json`, verifier script and check logs). Baseline failure also appears in hosted run `35757522343`.

## Independent mechanical review

Non-implementer review recommendation: RECOMMEND_ACCEPT, no findings, formal acceptance reserved for the lead. Exact tracked tree independently computed as `b41f35ff4e816c3df52521e328d60d598a4bc408`.

All 26 test functions / 125 assertions remain: CLI 11 tests/52 assertions; worker 15/73. AST comparison matches after removing type annotations/type imports and normalizing reload variable names; adapter forwarding was reviewed separately.

- CLI SHA256 `3c6c00caff7b514c4c99ac9bea60af9b84b7317406f87a7399c81d0d5860614d`.
- Worker SHA256 `5d7712b2173667bd9fb78a4b9e3ef428e74cd7fd50acdb06fadb27ac594a5e24`.

Candidate pushed to PR26. Hosted rerun is pending readback at this checkpoint; do not claim green until actual steps execute. COMP-2 remains queued pending formal typing disposition. G14-G17 remain UNPASSED; no main merge or live actions.

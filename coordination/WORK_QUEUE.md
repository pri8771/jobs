# Active Work Queue

Owner directive:
**No version is COMPLETE until one real non-mock production-path example passes.**

## P0 — Lane 1 V1.4 proof-tool integrity review

Branch:
- `worker/v14-real-proof`

PR:
- #8

Worker implementation:
- `8f8c21f88512aa32521c78285b72dc9da298672e`

Current action:
1. ChatGPT lead reviews actual RP14-T1..T7 diff against `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`.
2. Verify proof tests + CI.
3. Use worker-pc for bounded independent review if capacity is free and useful.
4. Accept or write bounded rework.
5. Do NOT run private-data proof before P0A lead acceptance.

After P0A acceptance:
- validate real private profile + exact resume mapping,
- import/revalidate OpenSesame job/questions,
- run production packet proof,
- emit runtime redacted candidate + separate verifier receipt,
- independent proof audit,
- only then V1.4 COMPLETE.

## P1 — Lane 2 V1.5 application safety review

Branch:
- `worker/v15-assisted-application`

PR:
- #2

Current action:
1. ChatGPT lead reviews A-R15-06..09 implementation and adversarial tests.
2. Preserve A-R15-01..05 accepted behavior.
3. Require green CI on current implementation head after any rebase.
4. Accept or write bounded rework.

No V1.6.
No real application action.

## Lane 3

Latest repair batch has been lead-accepted and merged:
- PR #3
- merge `be765ea42856bc695fc1eece9c1da396b4f162d4`

Do not reopen completed repair tasks.

Blocked future item:
- J20G-04 waits for Lane 1 later Gmail readiness.

Until that dependency exists, keep Lane 3 idle or assign only a clearly unblocked, non-conflicting V2.0 integration/reliability task after explicit lead reprioritization. Do not create filler work.

## Heartbeat

Canonical rule for active lanes:
- `FIVE_MIN_2026_09_21`
- `ACTIVE_5M`
- every 5 minutes while active
- one watcher per lane
- no transitions

If an old DAYWATCH watcher is still running:
1. stop it once,
2. pull latest main,
3. launch exactly one fixed-5m watcher.

Visible progress:
- GitHub issue #7

## Safety

No live Gmail OAuth/mailbox access, browser application action, submission, external messaging, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped authorization.

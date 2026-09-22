# A-V15-CLEAN-INTEGRATION

- Type: integration / assisted-application safety
- Phase: V1.5
- Status: **ACCEPTED**
- Owner: Fable/Claude + ChatGPT
- Reviewer: ChatGPT
- Dependencies: A-V14-P0A-INTEGRITY ACCEPTED
- Downstream: A-V15-BROWSER-SAFETY-CONTRACT, A-V15-ASSISTED-APPLICATION, A-V15-LIVE-ASSISTED-PROOF

## Purpose

Integrate the already-developed assisted-browser safety implementation into the single-worker V1.7 campaign without historical heartbeat/coordination churn.

## Accepted evidence

- Exact consolidated V1.5 source: `47fefd1b0ca354360353577685f6619a94f00f42`.
- PR #12 integrated to `main` as `7c0fa73bf350392a88b47442455359a43cf926b0`.
- Lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

Lead review accepted the semantic snapshot/destination binding, exact upload mapping/readback, prefill-only boundary, real local Playwright engineering-form coverage, and installed-entrypoint review stop. Fable reported 395 tests for the consolidated exact head plus Ruff/mypy green.

Hosted Actions were blocked before executable steps (`CI_BLOCKED_ACCOUNT`) and are not called green. The documented lead engineering exception was applied to engineering acceptance only.

## Boundary

This integration acceptance does not satisfy G15. **G15 remains UNPASSED** until an accepted genuine G14 packet is used in a scoped owner-authorized visible-browser prefill/upload run with genuine post-fill evidence and a stop before submit.
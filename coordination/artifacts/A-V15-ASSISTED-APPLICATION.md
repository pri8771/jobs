# A-V15-ASSISTED-APPLICATION

- Type: implementation / live evidence
- Phase: V1.5
- Status: **ACCEPTED (engineering)**
- Owner: Fable/Claude
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED, A-V15-BROWSER-SAFETY-CONTRACT ACCEPTED (engineering)
- Downstream: A-V15-LIVE-ASSISTED-PROOF, V1.6 engineering

## Purpose

Carry an accepted packet into a visible assisted-browser flow without corrupting provenance or crossing unknown/user-only boundaries, while guaranteeing the assisted path stops before submission.

## Accepted source

- Exact consolidated source: `47fefd1b0ca354360353577685f6619a94f00f42`.
- Integrated through PR #12 as `7c0fa73bf350392a88b47442455359a43cf926b0`.
- Lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

## Lead acceptance

The reviewed implementation closes the earlier assisted-browser residuals and verifies:
- semantic page/form/destination identity and immediate pre-write reinspection;
- exact accepted packet, answers/provenance and linked artifact integrity at browser use;
- field-level and page-level untrusted-content defenses;
- exact locator-bound text/select writes with readback;
- resume/cover-letter field-specific upload mapping and byte/hash evidence;
- unknown/ambiguous file inputs stay manual and are never defaulted to resume;
- truthful partial-prefill state and persistent post-fill evidence;
- consent/attestation, EEO/self-ID and unresolved consequential fields remain manual/blocking;
- assisted execution always ends at `REVIEW_REQUIRED` and never promotes itself to submitted state;
- URL text, caller receipts, runner flags, mock state and arbitrary evidence cannot establish external confirmation;
- real local headless Playwright engineering forms receive no submit POST from the assisted path;
- installed `assisted-apply` entrypoint stops for review even when legacy auto-confirm input is present.

Fable's exact-head handoff reports 395 tests including real Playwright engineering-form coverage plus Ruff/mypy green. Hosted Actions were `CI_BLOCKED_ACCOUNT` before executable steps and are not called green; the documented lead engineering exception was applied after code/test review.

## Live gate

**G15 remains UNPASSED.** A genuine live example requires:
1. an accepted genuine G14 packet;
2. this accepted V1.5 engineering;
3. a scoped owner grant naming the real visible-browser page/session;
4. actual safe prefill/uploads and genuine post-fill evidence;
5. **STOP BEFORE SUBMIT**.

This engineering artifact authorizes no live employer-page prefill or submission by itself. V1.6 engineering may now proceed independently, but live G16 remains separately gated.
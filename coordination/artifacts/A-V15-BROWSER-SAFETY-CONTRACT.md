# A-V15-BROWSER-SAFETY-CONTRACT

- Type: contract / safety / implementation guidance
- Phase: V1.5
- Status: **ACCEPTED (engineering)**
- Owner: Fable/Claude + ChatGPT
- Reviewer: ChatGPT; owner authorization remains required for live execution
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V15-ASSISTED-APPLICATION, A-V15-LIVE-ASSISTED-PROOF, V1.6 engineering

## Purpose

Define and verify a safe assisted-browser runtime contract before any genuine application prefill begins.

## Accepted source

- Exact consolidated V1.5 implementation: `47fefd1b0ca354360353577685f6619a94f00f42`.
- Integrated through PR #12 as `7c0fa73bf350392a88b47442455359a43cf926b0`.
- Lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

## Accepted engineering contract

Lead review verified:
- exact accepted packet/artifact identity is revalidated at the browser boundary;
- inspect-before-write and immediate reinspection are required;
- the semantic form snapshot binds final destination, form action, stable exact locator, control name/type/required state, labels/help/options and field classification;
- meaningful form or destination changes block writes;
- exact field-specific file-upload mapping is required; duplicate/unknown/ambiguous file controls remain manual and never receive a default resume;
- selected resume/cover-letter bytes and hashes are revalidated and post-fill evidence records actual attachment/readback identity;
- intended-vs-actual field evidence and partial outcomes are truthful;
- external page/form content remains untrusted data, never policy or authority;
- consent/attestation, EEO/self-ID and unresolved consequential answers remain manual/blocking as appropriate;
- assisted execution is prefill-only and ends at `REVIEW_REQUIRED`;
- URL keywords, caller receipts, runner flags, mocks, arbitrary evidence and local success state cannot establish submission;
- trusted structured external confirmation is a separate boundary;
- real local headless Playwright engineering-form coverage records zero submit POSTs from the assisted path and the installed assisted entrypoint stops for review.

Fable's consolidated exact-head handoff reports 395 tests including real headless Playwright engineering forms plus Ruff and mypy green. Hosted Actions were blocked before executable steps (`CI_BLOCKED_ACCOUNT`) and are not called green. The lead applied the documented engineering exception after actual code/test review.

## Live boundary

Engineering acceptance does **not** authorize real employer-page interaction. **G15 remains UNPASSED** until there is an accepted genuine G14 packet and a scoped owner grant for the real visible-browser page/session. A G15 run must capture genuine post-fill evidence and **STOP BEFORE SUBMIT**.

LinkedIn/Indeed submission remains MANUAL_ONLY. No CAPTCHA/MFA/anti-bot bypass is permitted.
# A-V15-BROWSER-SAFETY-CONTRACT

- Type: contract / safety / implementation guidance
- Phase: V1.5
- Status: READY
- Owner: ChatGPT
- Reviewer: ChatGPT lead review / user boundary for live execution
- Dependencies: none for design; implementation waits for A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V15-ASSISTED-APPLICATION

## Purpose

Define a safe assisted-browser runtime contract before real application prefill begins.

## Output

- `docs/V1_5_BROWSER_SAFETY_CONTRACT.md`

## Current code audit evidence

Reviewed on current `main`:
- `src/jobs_automation/browser/base.py`
- `src/jobs_automation/browser/assisted_engine.py`
- `src/jobs_automation/browser/playwright_runner.py`
- `src/jobs_automation/browser/mock_runner.py`

Key gaps captured by the contract:
- no inspect-before-prefill gate,
- no per-fill provenance,
- unresolved questions are not enforced as a stop,
- implicit latest-packet selection,
- no upload hash verification at browser boundary,
- separate ephemeral prefill/review browser contexts,
- visible session closes after a short fixed wait,
- local/mock/generic evidence can currently contribute to submitted-state semantics.

## Acceptance criteria

- contract documents exact accepted-packet requirement,
- inspect-before-write behavior,
- field classification taxonomy,
- per-field provenance,
- manual-barrier behavior,
- persistent visible-session requirement,
- upload-integrity check,
- pre-submit manifest,
- external-confirmation boundary,
- mock isolation,
- adversarial acceptance tests.

## Evidence

- `docs/V1_5_BROWSER_SAFETY_CONTRACT.md`
- bounded follow-on Antigravity tasks in `coordination/WORK_QUEUE.md`

## Risks

Do not implement or execute this artifact ahead of the V1.4 packet-safety acceptance gate unless ChatGPT explicitly reprioritizes a non-conflicting preparation slice.


## Additional security task

- J15-11 SP2 — Treat all external form/page content as untrusted data; add prompt-injection resistance and adversarial tests.

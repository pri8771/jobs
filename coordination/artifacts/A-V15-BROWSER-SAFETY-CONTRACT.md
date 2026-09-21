# A-V15-BROWSER-SAFETY-CONTRACT

- Type: contract / safety / implementation guidance
- Phase: V1.5
- Status: IN_PROGRESS
- Owner: ChatGPT / Antigravity Lane A implementation
- Reviewer: ChatGPT lead review / user boundary for live execution
- Dependencies: A-V14-PACKET-SAFETY ENGINEERING_ACCEPTED
- Downstream: A-V15-ASSISTED-APPLICATION

## Purpose

Define and verify a safe assisted-browser runtime contract before real application prefill begins.

## Worker evidence reviewed

Initial worker batch:
- `3d17fa8`

Current repaired batch:
- `ed875775122f0d390af6ab15beb378904af2a476` on `worker/v15-assisted-application`

Lead reviewed the branch code and adversarial tests.

Current batch materially repairs:
- external-confirmation truth: local `receipt_text` / `auto_confirm` alone cannot create SUBMITTED,
- field-level prompt-injection detection and POLICY_BLOCKED behavior,
- consent/attestation prefill blocking,
- distinct cover-letter hash/provenance and tamper/missing-required behavior,
- immediate pre-write form-fingerprint revalidation.

Worker-reported local verification:
- targeted adversarial tests: 27 passed,
- full pytest: 132 passed,
- Ruff: clean,
- mypy: no new errors.

GitHub evidence:
- the branch commit has no GitHub Actions/check result of its own,
- PR #2 remains draft and is currently non-mergeable against newer main,
- therefore this artifact is not engineering-accepted yet.

## Task-scope lead acceptance from `ed87577`

- A-R15-01 SP2 — LEAD_ACCEPTED
- A-R15-02 SP2 — LEAD_ACCEPTED for field-level prompt-injection scope
- A-R15-03 SP1 — LEAD_ACCEPTED
- A-R15-04 SP2 — LEAD_ACCEPTED for hash/provenance/tamper scope
- A-R15-05 SP2 — LEAD_ACCEPTED

These task acceptances do not accept the overall V1.5 artifact.

## Remaining residuals — P1 after V1.4 REAL_PROOF

Authoritative audit:
- `docs/LANE_A_REAUDIT_2.md`

Tasks:
- A-R15-06 SP2 — page-level prompt-injection signal/warning semantics outside individual form fields.
- A-R15-07 SP2 — actual cover-letter upload wiring + field-specific file mapping; no generic cross-attachment.
- A-R15-08 SP2 — recompute/revalidate accepted packet identity, answers/provenance, and linked resume/artifact identity immediately before browser use.
- A-R15-09 SP1 — unknown file inputs remain manual/unfilled and never default to resume.

These residuals must not delay A-V14-REAL-PROOF, which is the owner-designated P0 completion gate.

## Acceptance criteria

- exact accepted packet integrity and answer provenance verified at browser boundary,
- inspect-before-write behavior,
- safe field classification including unknown file inputs,
- per-field provenance,
- manual-barrier behavior,
- persistent visible-session requirement,
- resume and cover-letter upload integrity with field-specific mapping,
- pre-submit manifest,
- form-change detection immediately before write,
- typed externally sourced confirmation boundary,
- mock isolation,
- field-level and page-level external prompt-injection resistance,
- adversarial acceptance tests,
- green integrated CI on current main.

## Risks / boundaries

- No live application/form execution is authorized by this engineering artifact.
- External application content is attacker-controlled input from the agent perspective.
- V1.4 REAL_PROOF is packet preparation only and does not authorize browser prefill/submission.

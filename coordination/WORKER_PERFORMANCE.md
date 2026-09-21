# Worker Performance Ledger

Story-point rubric:
- docs/WORKER_STORY_POINTS.md

Story points measure complexity/uncertainty, not time.

## Summary

Only attempted tasks are counted. READY / NOT_ATTEMPTED tasks are excluded until a worker batch exists.

| SP | Attempted | Lead Accepted | First-Pass Accepted | Rework Tasks | Accepted Points |
|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 4 | 3 | 2 | 4 |
| 2 | 24 | 19 | 11 | 13 | 38 |
| 3 | 7 | 2 | 2 | 5 | 6 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 |

## V1.4 first-pass task audit — commit 10fd61d

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| J14-01 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Missing resume fails closed |
| J14-02 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Exact variant source resolution works |
| J14-03 | 3 | REWORK | 10fd61d | yes | 1 | Resume family identity needed repair |
| J14-04 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Packet -> ResumeVariant linkage implemented |
| J14-05 | 3 | REWORK | 10fd61d | yes | 1 | Historical artifact immutability needed repair |
| J14-06 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Candidate-specific runtime literals removed |
| J14-07 | 2 | REWORK | 10fd61d | yes | 1 | Live readiness needed explicit mock/test-origin rejection |
| J14-08 | 3 | REWORK | 10fd61d | yes | 1 | Quantitative claims needed exact canonical evidence |
| J14-09 | 1 | LEAD_ACCEPTED | 10fd61d | yes | 0 | EEO/self-ID always unresolved/manual |
| J14-10 | 3 | REWORK | 10fd61d | yes | 1 | Manifest inherited family/origin/immutability gaps |
| J14-11 | 1 | REWORK | 10fd61d | yes | 1 | Residual adversarial coverage needed |

## V1.4 bounded residual tasks

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| R14-01 | 2 | LEAD_ACCEPTED | 1410bf7 | yes / merged green | 1 | Immutable/content-addressed storage verified |
| R14-02 | 2 | LEAD_ACCEPTED | 1410bf7 | yes / merged green | 1 | Exact selected resume-family attribution |
| R14-03 | 2 | LEAD_ACCEPTED | 1410bf7 | yes / merged green | 1 | Mock/test packets cannot be live-ready |
| R14-04 | 2 | LEAD_ACCEPTED | 1410bf7 | yes / merged green | 1 | Unsupported quantitative claims fail closed |

Engineering merge: `8a0cdb4` with green main CI.
V1.4 version completion remains blocked on A-V14-REAL-PROOF.

## V1.5 first-pass task audit — initial commit 3d17fa8

Worker-reported first-pass verification:
- targeted assisted tests: 17 passed
- full pytest: 118 passed
- Ruff: clean
- mypy: clean

GitHub evidence at first review:
- no branch CI/check result on the implementation commit,
- branch required rebase/repair against newer main.

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| J15-00 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Explicit packet ID/job/live-ready checks exist; accepted packet integrity still needs stronger boundary revalidation |
| J15-01 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Inspection/classification exists; pre-write fingerprint later repaired; packet integrity residual remains |
| J15-02 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Auth/EEO/consent/unknown classification mechanics implemented |
| J15-03 | 3 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Machine-readable pre-submit review manifest implemented |
| J15-04 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Resume bytes/hash rechecked immediately before upload |
| J15-07 | 3 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Persistent Playwright page/context implemented |
| J15-08 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Unresolved/unknown-required/auth gates halt prefill |
| J15-09 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Local receipt text could satisfy submission confirmation |
| J15-10 | 1 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Mock runner evidence rejected for real submission truth |
| J15-11 | 2 | NOT_ATTEMPTED | — | — | 0 | Added after first branch base |

## V1.5 bounded rework audit — commit ed875775

Worker-reported local verification:
- `tests/test_assisted_safety_adversarial.py`: 27 passed
- full pytest: 132 passed
- Ruff: clean
- mypy: no new errors

GitHub evidence at lead review:
- no GitHub Actions/check result exists for `ed875775`,
- PR #2 is draft and non-mergeable against newer main,
- task-scope acceptance below does not equal artifact/integration acceptance.

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| A-R15-01 | 2 | LEAD_ACCEPTED | ed875775 | no branch CI | 1 | Caller receipt/auto-confirm alone cannot prove SUBMITTED; runner-observed evidence required |
| A-R15-02 | 2 | LEAD_ACCEPTED | ed875775 | no branch CI | 1 | Field-level prompt-like content becomes POLICY_BLOCKED; page-level text remains separate residual A-R15-06 |
| A-R15-03 | 1 | LEAD_ACCEPTED | ed875775 | no branch CI | 1 | Consent/attestation/legal acknowledgement blocks prefill |
| A-R15-04 | 2 | LEAD_ACCEPTED | ed875775 | no branch CI | 1 | Distinct cover-letter hash/provenance and missing-required/tamper handling; actual browser upload wiring remains A-R15-07 |
| A-R15-05 | 2 | LEAD_ACCEPTED | ed875775 | no branch CI | 1 | Re-inspection/fingerprint mismatch blocks immediately before write |

## V1.5 post-real-proof residuals

These are READY but deliberately not attempted before A-V14-REAL-PROOF.

| Task ID | SP | Status | Owner | Artifact | Lead notes |
|---|---:|---|---|---|---|
| A-R15-06 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT | Page-level prompt-injection signal/warning semantics; field-level-only detection is insufficient |
| A-R15-07 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT / A-V15-ASSISTED-APPLICATION | Wire actual cover-letter file upload; field-specific mapping; eliminate generic cross-attachment |
| A-R15-08 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT / A-V15-ASSISTED-APPLICATION | Recompute/revalidate packet hash, answers/provenance, ResumeVariant/artifact linkage at browser boundary |
| A-R15-09 | 1 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT | Unknown file inputs remain manual/unfilled; never default to resume |

Authoritative details:
- `docs/LANE_A_REAUDIT_2.md`

## Lane B bounded repair audit — commit 33d18b4

Worker-reported local verification:
- full pytest: 126 passed
- Ruff: clean
- mypy: clean

GitHub evidence at lead review:
- no branch CI/check result on repair commit,
- final integration requires rebase + green GitHub CI.

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| B-R17-01 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Missing lifecycle classes emitted conservatively |
| B-R17-02 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Rejection after accepted/onboarding preserves state + review |
| B-R20-01 | 3 | REWORK | 33d18b4 | no branch CI | 1 | Dimensional history repaired; headline funnel still needed history repair |
| B-R20-02 | 2 | REWORK | 33d18b4 | no branch CI | 1 | Dimensional denominator repaired; headline funnel still needed real-submission semantics |
| B-R20-03 | 1 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Neutral descriptive sample-size wording |
| B-R20-04 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Gmail health defaults fail-safe pending typed Lane C readiness |
| B-R20-06 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Dashboard writes require loopback or operator token |

## Lane B remaining work

| Task ID | SP | Status | Owner | Artifact | Lead notes |
|---|---:|---|---|---|---|
| B-R17-03 | 2 | READY | Antigravity Lane B | A-V17-CRM-EVIDENCE | Background-check semantics must not fabricate OFFER_RECEIVED |
| B-R20-07 | 1 | READY | Antigravity Lane B | A-V20-ANALYTICS / A-V20-CONTROL-CENTER | Simulation/test rows never count as real submissions |
| B-R20-08 | 2 | READY | Antigravity Lane B | A-V20-ANALYTICS | Evidence-backed final-interview/acceptance metrics |
| B-R20-05 / J20-14 | 3 | READY | Antigravity Lane B | A-V20-WORKER-RUN-HISTORY | Crash-durable begin/finalize worker-run semantics |

J20G-04 remains blocked on Lane C J20G-03.

## Interpretation

- Bounded SP1-SP2 work performs well when acceptance criteria include explicit adversarial cases.
- Cross-cutting trust/evidence semantics are the main source of rework even with green local test suites.
- Keep delegating the bulk of SP1-SP2 and most well-specified SP3 work.
- Split residual cross-cutting defects into narrow artifact-backed SP1-SP2 tasks rather than reissuing broad tasks.
- Do not infer long-term productivity rates from this still-small sample.

## Rules

- Antigravity reports completion; ChatGPT owns LEAD_ACCEPTED/REWORK.
- CI success is necessary but not sufficient.
- A real blocker reported promptly is not counted as task failure.
- >SP5 must be decomposed before assignment.

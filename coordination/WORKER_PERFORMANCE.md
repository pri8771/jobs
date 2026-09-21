# Worker Performance Ledger

Story-point rubric:
- docs/WORKER_STORY_POINTS.md

Story points measure complexity/uncertainty, not time.

## Summary

| SP | Attempted | Lead Accepted | First-Pass Accepted | Rework Tasks | Accepted Points |
|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 3 | 3 | 1 | 3 |
| 2 | 20 | 15 | 11 | 9 | 30 |
| 3 | 7 | 2 | 2 | 5 | 6 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 |

## V1.4 first-pass task audit — commit 10fd61d

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| J14-01 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Missing resume fails closed |
| J14-02 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Exact variant source resolution works |
| J14-03 | 3 | REWORK | 10fd61d | yes | 1 | ResumeVariant exists, but resume_family identity is semantically wrong |
| J14-04 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Packet -> ResumeVariant linkage implemented |
| J14-05 | 3 | REWORK | 10fd61d | yes | 1 | Storage writes/read-back verify, but same target path may overwrite historical bytes |
| J14-06 | 2 | LEAD_ACCEPTED | 10fd61d | yes | 0 | Candidate-specific runtime literals removed from drafter/mock content |
| J14-07 | 2 | REWORK | 10fd61d | yes | 1 | Gateway fails closed by default, but packet live-readiness does not reject explicit mock/test origin |
| J14-08 | 3 | REWORK | 10fd61d | yes | 1 | Provenance added, but quantitative years/duration can still be model-asserted without exact evidence |
| J14-09 | 1 | LEAD_ACCEPTED | 10fd61d | yes | 0 | EEO/self-ID always unresolved/manual |
| J14-10 | 3 | REWORK | 10fd61d | yes | 1 | Manifest exists, but inherits family/origin/immutability gaps |
| J14-11 | 1 | REWORK | 10fd61d | yes | 1 | 99 tests/CI green, but missing adversarial coverage for residual defects |

## V1.4 bounded residual tasks

| Task ID | SP | Status | Owner | Artifact | Lead notes |
|---|---:|---|---|---|---|
| R14-01 | 2 | LEAD_ACCEPTED | Antigravity Lane A | A-V14-PACKET-SAFETY | Accepted in 1410bf7 / merged 8a0cdb4; immutable/content-addressed storage verified |
| R14-02 | 2 | LEAD_ACCEPTED | Antigravity Lane A | A-V14-PACKET-SAFETY | Accepted in 1410bf7 / merged 8a0cdb4; exact selected resume-family attribution |
| R14-03 | 2 | LEAD_ACCEPTED | Antigravity Lane A | A-V14-PACKET-SAFETY | Accepted in 1410bf7 / merged 8a0cdb4; mock/test packets not live-ready |
| R14-04 | 2 | LEAD_ACCEPTED | Antigravity Lane A | A-V14-PACKET-SAFETY | Accepted in 1410bf7 / merged 8a0cdb4; unsupported quantitative claims fail closed |

## V1.5 first-pass task audit — commit 3d17fa8

Worker-reported local verification:
- targeted assisted tests: 17/17 passed
- full pytest: 118/118 passed
- Ruff: clean
- mypy: clean

GitHub evidence at lead review:
- commit had no GitHub status/check result of its own,
- branch was 1 commit ahead / 11 commits behind current main,
- final acceptance therefore requires rebase/repair and green integrated CI.

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| J15-00 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Explicit ID/job/live-ready checks exist, but exact accepted packet hash/provenance is not revalidated before browser use |
| J15-01 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Inspect/classification exists, but packet-answer provenance integrity and pre-write form-change enforcement are incomplete |
| J15-02 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Auth/EEO/consent/unknown field classification implemented; overall artifact still gated by residuals |
| J15-03 | 3 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Machine-readable pre-submit review manifest and persisted audit metadata implemented |
| J15-04 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Resume bytes/hash are rechecked immediately before upload |
| J15-07 | 3 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Playwright page/context is reused across inspect, prefill and review; integration remains subject to repaired batch CI |
| J15-08 | 2 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Unresolved packet questions and unknown-required/auth barriers stop before prefill |
| J15-09 | 2 | REWORK | 3d17fa8 | no branch CI | 1 | Arbitrary local receipt text containing confirmation-like tokens can still satisfy external-confirmation validator |
| J15-10 | 1 | LEAD_ACCEPTED | 3d17fa8 | no branch CI | 0 | Mock runner evidence is explicitly rejected for real submission truth |
| J15-11 | 2 | NOT_ATTEMPTED | — | — | 0 | Added on main after worker branch base; external-form prompt-injection resistance must be implemented after rebase |

## V1.5 bounded residual tasks

| Task ID | SP | Status | Owner | Artifact | Lead notes |
|---|---:|---|---|---|---|
| A-R15-01 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT / A-V15-ASSISTED-APPLICATION | Revalidate exact packet hash + answer provenance before browser use |
| A-R15-02 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT | Recheck form fingerprint immediately before first write |
| A-R15-03 | 2 | READY | Antigravity Lane A | A-V15-ASSISTED-APPLICATION | Free-form/local receipt text alone cannot prove SUBMITTED |
| A-R15-04 | 1 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT | Unknown file inputs must not default to resume |
| A-R15-05 | 2 | READY | Antigravity Lane A | A-V15-BROWSER-SAFETY-CONTRACT | Rebase + implement J15-11 prompt-injection resistance |

## Lane B bounded repair audit — commit 33d18b4

Worker-reported local verification:
- full pytest: 126 passed
- Ruff: clean
- mypy: clean

GitHub evidence at lead review:
- repair commit had no GitHub status/check result of its own,
- branch was 3 commits ahead / 18 commits behind current main,
- final integration requires rebase + green GitHub CI.

| Task ID | SP | Status | Worker commit | CI first push | Rework cycles | Lead notes |
|---|---:|---|---|---|---:|---|
| B-R17-01 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Classifier emits missing lifecycle classes; fallback remains review; end-to-end tests added |
| B-R17-02 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Rejection after OFFER_ACCEPTED/ONBOARDING preserves state and creates review task |
| B-R20-01 | 3 | REWORK | 33d18b4 | no branch CI | 1 | Source/role/resume historical outcomes repaired, but headline funnel summary still uses current status rather than ever-reached history |
| B-R20-02 | 2 | REWORK | 33d18b4 | no branch CI | 1 | Dimensional analytics real-submission denominator repaired, but headline funnel still counts status rows/simulation incorrectly |
| B-R20-03 | 1 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Replaced statistical-robustness claim with descriptive N/sample-size wording |
| B-R20-04 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Removed heuristic Gmail credential readiness; defaults NOT_INTEGRATED pending typed Lane C interface |
| B-R20-06 | 2 | LEAD_ACCEPTED | 33d18b4 | no branch CI | 0 | Dashboard writes require loopback or configured operator token; tests cover deny/allow paths |

## Lane B remaining residual

| Task ID | SP | Status | Owner | Artifact | Lead notes |
|---|---:|---|---|---|---|
| B-R20-07 | 2 | READY | Antigravity Lane B | A-V20-ANALYTICS / A-V20-CONTROL-CENTER | Repair `get_funnel_summary()` to use real-submission + historical ever-reached stage semantics; add simulation and terminal-state regression tests |

B-R20-05 / A-V20-WORKER-RUN-HISTORY remains deferred and unaccepted; J20G-04 remains blocked on Lane C J20G-03.

## Interpretation so far

Latest accepted evidence:
- V1.4 residual batch R14-01..R14-04: 4/4 SP2 rework tasks lead-accepted after one bounded repair cycle.
- Main CI passed after merge 8a0cdb4.
- V1.5 first pass shows good results on bounded SP1-SP3 mechanics, but cross-cutting trust-boundary semantics still require lead adversarial review: packet immutability/provenance and external evidence were the main misses.
- Lane B's bounded repair batch closed five of seven assigned residuals cleanly; the remaining analytics defect is now reduced to one SP2 top-level funnel repair instead of reopening the full analytics work.

Current evidence suggests:
- SP1-SP2 bounded work is relatively strong when acceptance criteria are explicit.
- SP3 work improves when the contract is narrow and testable; J15-03/J15-07 were accepted first pass, while broader historical-analytics semantics still needed another decomposition.
- Semantic security/evidence boundaries deserve dedicated adversarial cases even when the broader test suite is green.
- Do not infer long-term productivity rates from this small sample.
- Continue delegating the bulk of SP1-SP2 work and most well-specified SP3 work.
- When a cross-cutting SP3 is partially correct, split the residual into a narrow SP1-SP2 task rather than reissuing the whole task.

## Rules

- Antigravity reports completion; ChatGPT owns LEAD_ACCEPTED/REWORK.
- CI success is necessary but not sufficient.
- A real blocker reported promptly is not counted as task failure.
- >SP5 must be decomposed before assignment.

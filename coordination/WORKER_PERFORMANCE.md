# Worker Performance Ledger

Story-point rubric:
- docs/WORKER_STORY_POINTS.md

Story points measure complexity/uncertainty, not time.

## Summary

| SP | Attempted | Lead Accepted | First-Pass Accepted | Rework Tasks | Accepted Points |
|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 1 | 1 | 1 | 1 |
| 2 | 9 | 8 | 4 | 5 | 16 |
| 3 | 4 | 0 | 0 | 4 | 0 |
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

## Interpretation so far

Latest accepted evidence:
- V1.4 residual batch R14-01..R14-04: 4/4 SP2 rework tasks lead-accepted after one bounded repair cycle.
- Main CI passed after merge 8a0cdb4.

Initial evidence suggests:
- SP1-SP2 bounded work is relatively strong when acceptance criteria are explicit.
- Cross-cutting SP3 tasks need tighter semantic contracts and adversarial acceptance tests.
- Do not infer long-term rates from this small sample.
- Continue delegating the bulk of SP1-SP2 work.
- For SP3+, ChatGPT should provide stronger artifact contracts and split tasks further when semantics span persistence + policy + provenance.

## Rules

- Antigravity reports completion; ChatGPT owns LEAD_ACCEPTED/REWORK.
- CI success is necessary but not sufficient.
- A real blocker reported promptly is not counted as task failure.
- >SP5 must be decomposed before assignment.

# A-V15-ASSISTED-APPLICATION

- Type: implementation / live evidence
- Phase: V1.5
- Status: IN_PROGRESS
- Owner: Antigravity Lane A
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ENGINEERING_ACCEPTED, A-V15-BROWSER-SAFETY-CONTRACT engineering acceptance, later user approval for consequential live evidence
- Downstream: A-V16-FIRST-REAL-SUBMISSION

## Purpose

Prove that an accepted packet can be carried into a visible assisted browser flow without corrupting provenance or crossing unknown/user-only boundaries.

## Worker batches reviewed

Initial:
- `3d17fa8`

Current repaired batch:
- `ed875775122f0d390af6ab15beb378904af2a476`

Task-scope lead acceptance in current batch:
- A-R15-01 external-confirmation hardening
- A-R15-02 field-level prompt-injection blocking
- A-R15-03 consent/attestation prefill barrier
- A-R15-04 cover-letter hash/provenance + tamper/missing-required handling
- A-R15-05 immediate pre-write form-fingerprint revalidation

Worker reported 132 full tests passing, 27 targeted assisted-safety tests passing, clean Ruff, and no new mypy errors. The branch commit itself has no GitHub Actions/check result and PR #2 is currently draft/non-mergeable against newer main, so overall artifact acceptance remains pending.

## P0 sequencing

A-V14-REAL-PROOF outranks remaining V1.5 work.

Lane A should rebase/pull current main and, if the real private profile and actual resume mapping exist on its machine, run the V1.4 proof immediately using:
- `scripts/import_v14_proof_job.py`
- `scripts/run_v14_real_proof.py`
- `scripts/verify_v14_real_proof.py`

No browser prefill/submission is part of V1.4 real proof.

## Remaining V1.5 residuals after V1.4 proof

See `docs/LANE_A_REAUDIT_2.md`:
- A-R15-06 SP2 page-level prompt-injection inspection/security evidence.
- A-R15-07 SP2 real cover-letter file-upload wiring + field-specific mapping.
- A-R15-08 SP2 accepted packet hash/answer/provenance/resume-link integrity revalidation immediately before browser use.
- A-R15-09 SP1 unknown file inputs must stay manual/unfilled rather than defaulting to resume.

## Acceptance criteria

- exact accepted packet used; no implicit latest-packet selection for a real run
- packet hash/current answer/provenance integrity validated before browser use
- dedicated persistent browser context/profile as appropriate
- inspect form before any write/prefill
- form fields explicitly classified
- known fields mapped with provenance
- arbitrary/unknown file inputs never receive the resume by default
- ambiguous/unknown required fields block or remain manual
- unresolved consequential packet questions block progress
- EEO/self-ID left manual
- exact accepted resume/cover-letter artifact hashes verified immediately before upload
- field-specific upload mapping prevents cross-attachment
- one persistent visible browser context spans inspect/prefill/review
- meaningful form change after inspection blocks write/requires reinspection
- pre-submit review manifest generated
- external page/form content treated only as untrusted data, never agent instruction
- user controls final submit in assisted mode
- real external confirmation captured before submitted state
- free-form/local/mock/generic receipt evidence cannot satisfy real submission state
- application lifecycle/audit updated truthfully

## Evidence required

Engineering acceptance:
- adversarial tests for all remaining residual safety cases
- full pytest, Ruff, mypy
- green integrated GitHub CI on current main/rebased branch
- lead review

Version completion additionally requires its own real non-mock V1.5 example under the owner completion policy. That later proof must not be confused with the non-consequential V1.4 packet proof.

## Boundary

No live browser/application action is authorized by this artifact's current engineering state. V1.6 remains blocked until V1.5 engineering and completion gates are satisfied.

## Worker report — Fable, 2026-09-22 (state: READY_FOR_LEAD_REVIEW, not accepted)

F145-07: the V1.5 browser code and adversarial tests from `worker/v15-assisted-application`
`ddb4f84` were ported onto the single-worker branch `claude/serene-brown-g6uij0` without
heartbeat/coordination churn. F145-08..11 (FR15-01..03 repairs, real local Playwright
engineering-form tests, installed entrypoint test) are summarised in the addendum of
`docs/V1_5_BROWSER_SAFETY_CONTRACT.md`. Exact SHA and independent check results are in the
handoff and heartbeat. G15 (live visible prefill) remains blocked on this host: no accepted
real packet, no owner browser grant, no owner machine.

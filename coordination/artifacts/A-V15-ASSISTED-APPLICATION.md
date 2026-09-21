# A-V15-ASSISTED-APPLICATION

- Type: implementation / live evidence
- Phase: V1.5
- Status: IN_PROGRESS
- Owner: Antigravity Lane A
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED, A-V15-BROWSER-SAFETY-CONTRACT accepted for engineering, A-PROOF-JOB-SELECTION user approved for live evidence
- Downstream: A-V16-FIRST-REAL-SUBMISSION

## Purpose

Prove that an accepted packet can be carried into a visible assisted browser flow without corrupting provenance or crossing unknown/user-only boundaries.

## Worker batch reviewed

- `3d17fa8` on `worker/v15-assisted-application`

The batch is substantial and useful but not artifact-accepted. See:
- `docs/LANE_A_V15_REAUDIT.md`

First-pass accepted implementation slices:
- J15-02
- J15-03
- J15-04
- J15-07
- J15-08
- J15-10

Residual worker tasks:
- A-R15-01 exact packet integrity/provenance
- A-R15-02 form-change enforcement
- A-R15-03 external-confirmation hardening
- A-R15-04 safe file-input classification
- A-R15-05 J15-11 external prompt-injection resistance

## Acceptance criteria

- exact accepted packet used; no implicit latest-packet selection for a real run
- packet hash/current answer/provenance integrity validated before browser use
- dedicated persistent authenticated browser profile
- inspect form before any write/prefill
- form fields explicitly classified
- known fields mapped with provenance
- arbitrary/unknown file inputs never receive the resume by default
- ambiguous/unknown required fields block or remain manual
- unresolved consequential packet questions block progress
- EEO/self-ID left manual
- exact accepted resume artifact hash verified immediately before upload
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
- adversarial tests for all residual safety cases
- full pytest, Ruff, mypy
- green integrated GitHub CI
- lead review of repaired branch

Live-evidence acceptance additionally requires:
- user-approved exact proof job
- browser inspection/preflight manifest
- field classification + mapping manifest
- provenance for each filled field
- uploaded artifact hash match
- manual barrier list
- final review manifest
- external confirmation evidence
- audit/application event records

## Prepared contracts

- `docs/V1_5_FAST_START.md`
- `docs/V1_5_BROWSER_SAFETY_CONTRACT.md`
- `docs/LANE_A_V15_REAUDIT.md`
- `coordination/artifacts/A-V15-BROWSER-SAFETY-CONTRACT.md`

## Boundary

No live browser/application action is authorized by this artifact's current engineering state. V1.6 remains blocked until V1.5 is lead-accepted.

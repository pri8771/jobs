# A-V15-ASSISTED-APPLICATION

- Type: implementation / live evidence
- Phase: V1.5
- Status: READY
- Owner: Antigravity Lane A
- Reviewer: ChatGPT
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED, A-V15-BROWSER-SAFETY-CONTRACT READY, A-PROOF-JOB-SELECTION user approved
- Downstream: A-V16-FIRST-REAL-SUBMISSION

## Purpose

Prove that an accepted packet can be carried into a visible assisted browser flow without corrupting provenance or crossing unknown/user-only boundaries.

## Acceptance criteria

- exact accepted packet used; no implicit latest-packet selection for a real run
- dedicated persistent authenticated browser profile
- inspect form before any write/prefill
- form fields explicitly classified
- known fields mapped with provenance
- ambiguous/unknown required fields block or remain manual
- unresolved consequential packet questions block progress
- EEO/self-ID left manual
- exact accepted resume artifact hash verified immediately before upload
- one persistent visible browser context spans inspect/prefill/review
- pre-submit review manifest generated
- user controls final submit in assisted mode
- real external confirmation captured before submitted state
- mock/local/generic receipt evidence cannot satisfy real submission state
- application lifecycle/audit updated truthfully

## Evidence required

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
- `coordination/artifacts/A-V15-BROWSER-SAFETY-CONTRACT.md`

## Current readiness notes

Lead pre-audit of current browser code found it is useful scaffolding but not live-ready. Current `AssistedApplicationEngine` does not enforce inspect-before-prefill, exact accepted packet selection, provenance/barrier gates, or external-evidence-only submission truth. Current Playwright flow uses separate ephemeral contexts and closes the visible session after a short fixed wait. See the browser safety contract for the worker-ready repair slices.

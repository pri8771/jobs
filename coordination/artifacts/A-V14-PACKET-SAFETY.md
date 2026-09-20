# A-V14-PACKET-SAFETY

- Type: implementation / acceptance
- Phase: V1.4
- Status: IN_PROGRESS
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: V1.1 accepted
- Downstream: A-V15-ASSISTED-APPLICATION

## Purpose

Produce a truthful, immutable, independently inspectable application packet pipeline safe enough for real use.

## Scope

Includes J14-01..J14-11 from WORK_QUEUE.

## Non-goals

- live browser interaction
- live submission
- Gmail OAuth
- new ATS adapters
- V2/V3 infrastructure

## Acceptance criteria

1. exact resume source mapping
2. fail closed on missing resume
3. immutable ResumeVariant persistence
4. packet -> ResumeVariant linkage
5. actual artifact bytes written and hash verified
6. no runtime hard-coded candidate claims
7. no silent mock/model fallback
8. screening-answer provenance
9. EEO/self-ID always manual
10. inspectable packet manifest
11. pytest/ruff/mypy/CI green

## Evidence required

- commit SHA(s)
- migration
- tests
- CI
- artifact read-back hash evidence
- missing-resume fail-closed evidence
- model/mock fail-closed evidence
- provenance evidence
- EEO/manual evidence
- packet manifest

## Source paths

- src/jobs_automation/preparation/
- src/jobs_automation/adapters/models.py
- src/jobs_automation/db/models.py
- migrations/versions/
- tests/test_preparation.py
- docs/V1_4_REPAIR_GUIDE.md

## Current notes

Lead rejected prior packet implementation. Current worker sprint is the repair.

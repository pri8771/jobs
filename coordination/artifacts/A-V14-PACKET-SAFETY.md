# A-V14-PACKET-SAFETY

- Type: implementation / acceptance
- Phase: V1.4
- Status: ACCEPTED
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

## Evidence provided for review

- Migration: `migrations/versions/002_resume_variant_attribution.py` (applied and verified)
- Tests: 99 unit tests passing (`tests/test_artifact_store.py`, `tests/test_preparation.py`, `tests/test_packet_safety_adversarial.py`)
- Linter / Types: `ruff check .` clean, `mypy src tests` clean across 90 source files
- Artifact Storage & Read-Back: `ArtifactStore` atomic write with mandatory read-back SHA-256 verification
- Fail-Closed: Missing resume source raises `FileNotFoundError`; wrong variant cannot load unmapped variant source
- Model Gateway: `LiteLLMModelGateway(fallback_mock=False)` fails closed; `MockModelGateway` generic synthetic only
- Screening Provenance: Every resolved answer cites exact field paths in `answer_provenance_json`; unsupported model claims rejected
- EEO / Demographic: All 4 EEO self-identification questions strictly route to unresolved
- Sample Proof Packet Manifest: `artifacts/packets/manifest_3395ca7b-fc9b-4207-b08f-8f98459f8347.json` (hash `c6e352aa...`)

## Source paths

- src/jobs_automation/core/candidate_profile.py
- src/jobs_automation/storage/artifact_store.py
- src/jobs_automation/preparation/packet_builder.py
- src/jobs_automation/preparation/tailoring.py
- src/jobs_automation/adapters/models.py
- src/jobs_automation/db/models.py
- migrations/versions/002_resume_variant_attribution.py
- tests/test_preparation.py
- tests/test_artifact_store.py
- tests/test_packet_safety_adversarial.py
- docs/V1_4_REPAIR_GUIDE.md

## Current notes

Repair J14-01 through J14-11 complete and verified (99 unit tests passing, SHA-256 read-back verified, migration 002 applied). Ready for ChatGPT lead re-audit.

User requested immediate STOP at 2026-09-20 20:11 ET; execution paused before proceeding to V1.5.


## Lead re-audit — residual rework

Lead reviewed commit `10fd61d` and current CI.

Most original J14 repairs are materially correct and retained.

Four bounded residual tasks remain:

- R14-01 SP2 — ArtifactStore currently overwrites the same target path via os.replace; make historical artifact bytes immutable/content-addressed and add a two-build regression test.
- R14-02 SP2 — ResumeVariant.resume_family currently uses target.primary_headline rather than the actual selected resume family; add explicit family mapping and tests.
- R14-03 SP2 — packet readiness does not yet enforce generation origin; explicit MockModelGateway/test content must never be considered live-ready.
- R14-04 SP2 — model-assisted quantitative claims (for example years of Python) need exact canonical evidence; skill presence alone is insufficient.

After these pass with green CI, A-V14 can be accepted immediately.


## Final lead acceptance

Accepted after re-audit of Lane A commit `1410bf7`, merge PR #1, and green main CI on merge commit `8a0cdb4`.

V1.4 is no longer an active worker artifact.

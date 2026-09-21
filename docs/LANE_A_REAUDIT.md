# Lane A Re-Audit — V1.5 Assisted Application

Reviewed commit:
- `3d17fa8`

Overall:
The V1.5 implementation is substantial and most of the original safety contract is present. Keep the implementation. Do not rewrite it.

The artifact is NOT yet accepted because the following bounded residuals remain.

## A-R15-01 — external confirmation must be observed external evidence (SP2)

Current `is_valid_external_confirmation()` can accept caller-supplied `receipt_text` merely because it contains words such as:
- confirmation
- received
- application id
- ref
- receipt

That is not independent external evidence.

This also affects MANUAL_ONLY recording because `auto_confirm=True` can construct a local BrowserSessionResult and pass arbitrary receipt text.

Required:
- a boolean `auto_confirm` means only "the user says they attempted/submitted"; it is NOT evidence,
- caller-provided free-text alone can never create SUBMITTED,
- valid evidence must be observed/captured from an external source:
  - browser confirmation page observed by the browser runner,
  - ATS/employer account state,
  - confirmation email/provider message,
  - structured external receipt carrying source/provenance,
- a locally-entered note may be stored as a note but results in SUBMISSION_UNCONFIRMED until external evidence exists.

Tests:
1. receipt_text="application received ref 123" passed by caller -> NOT submitted.
2. auto_confirm=True with no observed external evidence -> SUBMISSION_UNCONFIRMED.
3. structured browser evidence with source=external + non-mock -> may confirm.
4. external confirmation email/provider ID -> may confirm through the later evidence ingestion path.

## A-R15-02 — prompt-injection resistance J15-11 (SP2)

The new J15-11 contract landed after the initial A implementation.

External page/form/job text is untrusted data.

Required:
- detect prompt-like page/field text such as "ignore previous instructions", "if you are an AI", "system prompt", "output exactly",
- preserve it as untrusted evidence/security signal,
- it must never modify policy, permissions, candidate truth, packet readiness, field provenance, or submission state,
- required suspicious questions follow ordinary provenance/manual-review behavior,
- optional/hidden suspicious content does not execute as instructions.

Add adversarial tests from docs/V1_5_BROWSER_SAFETY_CONTRACT.md.

## A-R15-03 — consent barrier must block prefill until manual review (SP1)

`compute_barriers()` creates `consent_manual:...`, but current `blocking_barriers` excludes it.

Contract requires new consent/attestation/legal acknowledgement to be a manual barrier.

Required:
- CONSENT_MANUAL is blocking before automated prefill,
- create review task,
- no consent checkbox/signature/attestation autofill.

EEO may remain unfilled/manual and does not need to prevent filling unrelated safe fields unless required form behavior makes it unavoidable.

## A-R15-04 — cover-letter upload mapping/hash provenance (SP2)

Current build plan primarily wires resume into `file_uploads`.
For any discovered cover-letter file input:
- map exact cover-letter artifact,
- verify bytes/hash immediately before upload,
- use the cover-letter hash in FieldFillProvenance,
- do not accidentally use resume_sha for cover-letter fields,
- if a required cover-letter input exists but packet artifact is absent -> review/block.

Tests:
- resume + cover letter fields get distinct artifacts/hashes,
- tampered cover letter fails closed.

## A-R15-05 — revalidate form fingerprint before write/review (SP2)

The code computes an inspection fingerprint but does not prove the form is unchanged when writing.

Required:
- after initial inspection and before first write, ensure current form structure matches inspected fingerprint,
- if material structure changes -> stop/reinspect rather than writing against stale selectors,
- before final review/confirmation evidence, retain the run/form fingerprint in evidence.

Test:
- inspection fields change before prefill -> no write.

## Keep

Keep the existing good work:
- explicit packet ID
- packet/job binding
- live-ready gate
- unresolved-question gate
- artifact hash verification
- field taxonomy/provenance
- auth/unknown-required barriers
- one persistent Playwright page/context
- review manifest
- mock isolation
- SUBMISSION_UNCONFIRMED state

## Exit

After A-R15-01..05:
- targeted tests
- full pytest
- Ruff
- mypy
- push to existing PR #2
- lane heartbeat -> READY FOR CHATGPT V1.5 RE-REVIEW

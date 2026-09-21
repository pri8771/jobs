# Lane A Re-Audit 2 — Post-Real-Proof V1.5 Residuals

Priority rule:
These residuals are real, but they are **P1 after A-V14-REAL-PROOF**.
Do not delay the V1.4 real proof to implement them.

Reviewed:
- Lane A commit `ed875775122f0d390af6ab15beb378904af2a476`

## Keep

The first V1.5 rework materially improved:
- external confirmation gating,
- consent/manual barriers,
- cover-letter hash provenance,
- form fingerprint revalidation,
- field-level prompt-injection detection.

## A-R15-06 — page-level prompt-injection inspection (SP2)

Current detector inspects only discovered FormField:
- name
- label
- placeholder
- options

It does not inspect general page text / adjacent explanatory text / hidden page content.

The real OpenSesame application contains AI-directed text outside the normal candidate-data model. External page text is attacker-controlled data.

Required:
- browser inspection returns a bounded page-security signal derived from visible/accessible page text around the form,
- detect prompt-like text outside individual field labels,
- never feed that text back as instructions,
- preserve it as untrusted security evidence,
- optional/non-required page injection should create a security warning, not necessarily block safe unrelated prefill,
- required question/field containing injection-like text remains manual/policy-blocked,
- page text can never authorize submission or change candidate facts/policy.

Tests:
1. page-level "ignore previous instructions" outside input label -> security signal, no instruction execution.
2. optional page-level injection + otherwise safe form -> safe fields may still be prepared, warning retained.
3. required field with injection text -> manual/policy block.
4. page injection cannot set live-ready/submitted/authorization state.

## A-R15-07 — actual cover-letter file upload wiring (SP2)

Current code records distinct cover-letter hash provenance, but `build_plan()` does not populate a cover-letter entry in `file_uploads`.

Therefore the browser runtime can have correct metadata without actually having the cover-letter file available to upload.

Required:
- when packet.cover_letter_artifact_id exists, resolve and add exact cover-letter artifact to file_uploads,
- use field-aware upload mapping so resume field gets resume file and cover-letter field gets cover-letter file,
- required cover-letter field + missing artifact -> blocking review,
- optional cover-letter field + missing artifact -> leave manual/unfilled with clear evidence,
- reverify cover-letter bytes immediately before upload,
- do not allow generic input[type=file] fallback to attach the wrong artifact to the wrong upload field.

Tests:
- required resume + required cover letter attach distinct paths/bytes/hashes,
- cover-letter missing required -> no prefill/upload,
- tampered cover letter -> blocked,
- two file inputs cannot cross-attach resume/cover letter.

## Exit

After the V1.4 REAL_PROOF is accepted, finish A-R15-06/07 before calling V1.5 COMPLETE.

The owner completion rule also applies to V1.5:
V1.5 eventually requires its own real non-mock example before COMPLETE.

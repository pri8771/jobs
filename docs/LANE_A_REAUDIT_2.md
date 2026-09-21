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

Task-scope accepted in this batch:
- A-R15-01 through A-R15-05 as currently defined in WORK_QUEUE / lane status.

Overall V1.5 is still IN_PROGRESS. The following residuals remain after real-proof priority work.

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
- do not allow generic `input[type=file]` fallback to attach the wrong artifact to the wrong upload field.

Tests:
- required resume + required cover letter attach distinct paths/bytes/hashes,
- cover-letter missing required -> no prefill/upload,
- tampered cover letter -> blocked,
- two file inputs cannot cross-attach resume/cover letter.

## A-R15-08 — accepted-packet integrity/provenance revalidation (SP2)

The runtime requires an explicit packet ID and validates job linkage/live-ready state plus artifact hashes, but it still trusts the persisted packet's `packet_hash`, `answers_json`, and provenance fields without recomputing or cross-checking the immutable packet identity immediately before browser use.

Required:
- recompute/verify the accepted packet identity using the same canonical packet-hash contract as packet preparation,
- verify screening answers have matching persisted provenance and no answer was added/changed after the accepted packet hash was produced,
- verify the linked ResumeVariant/artifact identities belong to the same accepted packet,
- fail closed before inspection/prefill when packet identity/provenance is inconsistent,
- record an auditable rejection reason without leaking private answer contents.

Tests:
1. mutate `answers_json` after packet creation -> blocked before browser write.
2. mutate answer provenance after packet creation -> blocked.
3. swap linked ResumeVariant/artifact identity -> blocked.
4. unchanged accepted packet -> passes this gate.

## A-R15-09 — unknown file-input classification must fail manual (SP1)

Current field classification treats any `field_type == "file"` as FILE_ARTIFACT and defaults to the resume unless the field text contains "cover". An unknown file input must never receive a resume merely because it is a file control.

Required:
- only positively identified resume/CV inputs map to resume,
- only positively identified cover-letter inputs map to cover letter,
- unknown required file input -> UNKNOWN_REQUIRED/manual blocking review,
- unknown optional file input -> UNKNOWN_OPTIONAL/manual/unfilled,
- no generic file input gets an artifact by default.

Tests:
- required `input[type=file]` labeled "Work sample" -> blocks/manual, no resume attachment,
- optional unknown file input -> left unfilled,
- positively identified resume and cover-letter inputs still map correctly.

## Exit

After A-V14-REAL-PROOF is accepted, finish A-R15-06..A-R15-09 before V1.5 engineering acceptance.

Then the owner completion rule also applies to V1.5:
V1.5 requires its own real non-mock example before V1.5 may be called COMPLETE.

# V1.5 Assisted Browser Safety Contract

Artifact: `A-V15-BROWSER-SAFETY-CONTRACT`

Status: prepared in advance. This contract does not authorize live browser execution.

## Purpose

Define the minimum safe runtime behavior for V1.5 assisted application execution before any real job form is opened or prefilled.

The contract is based on a lead review of the current browser layer on `main`.

## Current readiness findings

The existing browser/assisted implementation is useful scaffolding but is not yet live-ready:

1. `AssistedApplicationEngine.execute()` goes directly to `prefill_form()` and does not call `inspect_form()` first, so there is no authoritative field inventory/classification before data is written into a form.
2. `build_plan()` copies candidate-profile values directly into `prefill_data` without attaching per-field provenance.
3. `unresolved_questions` are carried in the plan but are not enforced as a stop condition before prefill or submission-state recording.
4. If no packet ID is supplied, the engine selects the latest packet for the job rather than requiring the exact lead-accepted packet.
5. Resume upload uses an artifact `storage_uri`, but the assisted layer does not independently verify that the bytes/hash match the accepted packet immediately before upload.
6. `PlaywrightBrowserRunner.prefill_form()` and `open_interactive_session()` launch separate ephemeral browser contexts. The visible session therefore does not preserve a single authenticated/prefilled browser context.
7. `open_interactive_session()` waits only five seconds and then closes the browser, so it does not provide a durable human review session.
8. `execute()` can mark an application `SUBMITTED` from `auto_confirm` or `session_res.submitted`, and can synthesize a generic local receipt string. V1.5/V1.6 require external confirmation evidence before real submitted state.
9. `MockBrowserRunner` defaults to `interactive_submitted=True` and returns a fabricated mock confirmation. That is acceptable for tests only and must never satisfy real evidence gates.
10. There is no explicit manual-barrier classification for login, MFA, CAPTCHA, consent, EEO/self-ID, unknown required fields, or policy conflicts before prefill.

## Required runtime contract

### 1. Exact accepted packet

V1.5 must require an explicit packet ID.

Before browser work:
- packet exists,
- packet belongs to the selected job,
- packet is the exact accepted V1.4 packet,
- resume variant/artifact IDs match the packet manifest,
- artifact bytes exist,
- read-back SHA-256 matches the persisted expected hash.

Do not silently select the latest packet.

### 2. Inspect before write

Every real assisted run must call `inspect_form()` before any field is filled.

The inspection artifact must capture:
- URL,
- detected ATS,
- field selector/name/label/type,
- required/optional,
- available options,
- file inputs,
- page/form fingerprint sufficient to detect a meaningful form change during the same run.

If no form is found, stop.

### 3. Field classification

Every discovered field must be classified into one of:

- `SAFE_CANONICAL` — direct mapping to verified canonical candidate data.
- `PACKET_ANSWER` — exact accepted packet answer with provenance.
- `FILE_ARTIFACT` — immutable accepted artifact upload.
- `EEO_MANUAL` — demographic/self-identification; never auto-filled.
- `AUTH_BARRIER` — login, MFA, verification, CAPTCHA.
- `CONSENT_MANUAL` — legal consent/attestation requiring user action.
- `UNKNOWN_REQUIRED` — required field with no safe mapping.
- `UNKNOWN_OPTIONAL` — optional field with no safe mapping.
- `POLICY_BLOCKED` — filling/action not permitted by current policy.

Only the first three classes are eligible for automatic prefill.

### 4. Provenance on every fill

Each planned fill must include:
- discovered field identity,
- canonical field or packet-answer key,
- source/provenance reference,
- value hash or redacted representation suitable for audit,
- classification,
- confidence/mapping method,
- whether human review is still required.

No free-form model output may create a new candidate fact.

### 5. Manual-barrier gate

Before any prefill, compute a barrier list.

Hard stop before prefill if:
- policy = BLOCKED or MANUAL_ONLY for the intended automated action,
- authentication/consent state makes field inspection unreliable,
- required field is `UNKNOWN_REQUIRED`,
- packet has unresolved consequential questions,
- form materially changed after inspection.

EEO/self-ID fields may remain visible for the user but must not be filled by the system.

### 6. Single persistent visible session

Real V1.5 must use one persistent visible browser context for:
- authentication already present in the dedicated local profile,
- inspection,
- prefill,
- file upload,
- human review.

The system must not fill in one browser instance and then open a fresh instance for review.

The visible session stays open until the user closes/completes it or a defined timeout/cancellation occurs.

Cookies/profile state remain local and outside Git.

### 7. Upload integrity

Immediately before upload:
- read the exact artifact bytes,
- recompute SHA-256,
- compare to the accepted packet manifest,
- reject mismatch/missing file,
- record the verified hash in the preflight manifest.

### 8. Pre-submit review artifact

Before the user can submit, generate a machine-readable review manifest containing:
- job/company/title/requisition,
- destination URL/domain/ATS,
- policy decision/version,
- packet ID/hash,
- resume variant/artifact/hash,
- cover-letter artifact/hash if used,
- every discovered form field,
- every planned/actual filled value reference and provenance,
- every manual/unfilled field,
- barrier list,
- form fingerprint,
- browser-run ID/timestamps.

### 9. Submission truthfulness

V1.5 assisted mode stops before system-triggered submission.

If the user manually submits in the visible browser, local confirmation alone is not enough to record `SUBMITTED`.

The application may transition to a submitted/confirmed state only after external evidence such as:
- confirmation page/reference,
- ATS/employer account application state,
- confirmation email,
- equivalent external receipt.

A generic local string like `Application submitted via assisted browser` is not evidence.

Ambiguous outcome -> `SUBMISSION_UNCONFIRMED` / review, never blind retry.

### 10. Mock isolation

Mock browser output must be explicitly marked test/simulation evidence.

No mock confirmation URL, mock receipt, `interactive_submitted=True`, or local simulated result may satisfy a real application evidence gate.

## Acceptance tests

At minimum:

- no explicit packet ID -> blocked,
- unaccepted/wrong-job packet -> blocked,
- missing or hash-mismatched resume -> blocked,
- `inspect_form()` not successful -> no prefill,
- EEO field discovered -> manual/unfilled,
- unknown required field -> review/block,
- unresolved packet question -> review/block,
- form changes between inspection and prefill -> re-inspect/review,
- mock runner cannot create real `SUBMITTED`,
- `auto_confirm=True` without external evidence cannot create real `SUBMITTED`,
- generic receipt text cannot satisfy confirmation,
- persistent visible session uses same browser context for inspect/prefill/review,
- exact uploaded file hash is present in preflight evidence.

## Worker implementation slices

These should remain dependency-blocked until `A-V14-PACKET-SAFETY` is accepted:

- `J15-00` SP2 — require exact accepted packet; remove implicit latest-packet selection for real runs.
- `J15-01` SP2 — form inspection + field classification + provenance mapping.
- `J15-02` SP2 — manual-barrier classifier.
- `J15-03` SP3 — pre-submit review manifest.
- `J15-04` SP2 — upload read-back/hash verification.
- `J15-07` SP3 — persistent single visible Playwright session for inspect/prefill/review.
- `J15-08` SP2 — enforce unresolved/unknown-required stop conditions before prefill/submission state.
- `J15-09` SP2 — external-evidence gate; remove generic/local receipt as real submission proof.
- `J15-10` SP1 — ensure mock browser evidence can never satisfy real submission state.

## Non-goals

This contract does not:
- authorize opening a real application,
- authorize OAuth/login/MFA handling,
- authorize submission,
- change LinkedIn/Indeed MANUAL_ONLY policy,
- define V1.6 automatic submit behavior beyond preserving the evidence boundary.

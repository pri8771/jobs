# Lane A Re-Audit — V1.5 Assisted Application

Lead re-audit of:
- `3d17fa8` — V1.5 assisted application/browser safety implementation

## Overall

The batch adds substantial useful V1.5 safety infrastructure, but **A-V15-BROWSER-SAFETY-CONTRACT and A-V15-ASSISTED-APPLICATION are not accepted yet**.

Keep the implementation. Repair the bounded gaps below, rebase on current `main`, rerun the full verification suite, and return for lead review.

The branch was one commit ahead and eleven commits behind `main` at review time. It therefore predates the newly added J15-11 external-form prompt-injection requirement.

## First-pass accepted implementation slices

The following worker slices are lead-accepted as implemented in this batch, subject to integration with the residual repairs:

- **J15-02 SP2** — manual barrier classification for authentication, EEO/self-ID, consent and unknown fields.
- **J15-03 SP3** — machine-readable pre-submit review manifest and persisted audit metadata.
- **J15-04 SP2** — resume artifact SHA-256 verification immediately before upload.
- **J15-07 SP3** — one Playwright page/context is reused across inspect, prefill and review instead of opening independent contexts.
- **J15-08 SP2** — unresolved packet questions and unknown required/auth barriers stop before prefill.
- **J15-10 SP1** — mock browser evidence cannot satisfy the real submission gate.

Worker-reported local verification is useful, but GitHub CI did not run on commit `3d17fa8`; final integration still requires green CI after the repaired batch is rebased/merged.

## A-R15-01 — Exact accepted packet integrity is incomplete (SP2)

Related original tasks:
- J15-00
- J15-01

Current runtime checks packet existence, target job, `is_live_ready`, unresolved questions and resume bytes, but it does not verify that the packet's current answer/provenance payload is still the exact accepted packet represented by `packet_hash`.

`classify_field()` will treat a matching key in `packet.answers_json` as `PACKET_ANSWER` even if the corresponding provenance record is absent or the packet payload was mutated after packet creation.

Required:
- validate packet integrity before browser work,
- recompute/verify the deterministic packet hash or validate against an immutable accepted manifest,
- every `PACKET_ANSWER` eligible for fill must have an accepted provenance record,
- missing/malformed provenance or packet-hash mismatch fails closed,
- do not create new candidate truth at browser time.

Acceptance tests:
1. mutate a packet answer after packet creation -> blocked before inspect/prefill,
2. remove answer provenance while retaining the answer -> blocked/unfilled,
3. valid unchanged packet + provenance -> eligible for normal classification.

## A-R15-02 — Form-change protection is not enforced (SP2)

The code computes a fingerprint after initial inspection, and the helper detects structure changes, but the runtime never re-inspects/compares the form immediately before first write.

The V1.5 contract explicitly requires a material form change between inspection and prefill to re-inspect or route to review.

Required:
- re-inspect or otherwise verify the authoritative form fingerprint immediately before first field/file write,
- mismatch -> no write + review/reinspection,
- record both expected and observed fingerprints in safe audit evidence.

Acceptance tests:
1. inspection A then form B before prefill -> zero writes and REVIEW_REQUIRED/BLOCKED,
2. unchanged form -> proceeds,
3. changed required/options structure cannot be ignored.

## A-R15-03 — Free-form receipt text can falsely create SUBMITTED (SP2)

Related original task:
- J15-09

`is_valid_external_confirmation()` currently accepts arbitrary caller-provided `receipt_text` whenever the string contains terms such as `confirmation`, `received`, `application id`, `ref`, or `receipt`.

That is still local assertion, not external evidence. The same weakness exists in the MANUAL_ONLY recording path.

Required:
- free-form/caller-supplied receipt text alone must never prove real submission,
- accepted evidence must have a typed external provenance such as browser-captured confirmation URL/page evidence, ATS account state, confirmation email/provider message ID, or another explicit externally sourced evidence object,
- receipt text may annotate already-valid external evidence but cannot create validity,
- ambiguous outcome remains `SUBMISSION_UNCONFIRMED`.

Acceptance tests:
1. `receipt_text='confirmation 123'` + auto-confirm + no external evidence -> not SUBMITTED,
2. `receipt_text='application received'` + no external evidence -> not SUBMITTED,
3. MANUAL_ONLY path has the same protection,
4. structured non-simulated external confirmation evidence -> accepted.

## A-R15-04 — Unknown file inputs default to resume upload (SP1)

Current field classification treats every file input as `FILE_ARTIFACT`; unless its text contains `cover`, it defaults to the resume artifact.

A required `work_sample`, `transcript`, `portfolio_document`, or other upload could therefore receive the resume incorrectly.

Required:
- only positively recognized resume/CV and cover-letter inputs may map to those accepted artifacts,
- unknown required file input -> `UNKNOWN_REQUIRED` / manual review,
- unknown optional file input -> `UNKNOWN_OPTIONAL`, left untouched,
- provenance must name the exact artifact role.

Acceptance tests:
1. required `work_sample` file input -> halt/manual,
2. optional unknown file input -> untouched,
3. recognized resume input -> exact accepted resume only,
4. recognized cover-letter input -> exact accepted cover-letter only when available and verified.

## A-R15-05 — J15-11 prompt-injection resistance was not implemented (SP2)

The worker branch predates J15-11 on `main`.

External job/application text is untrusted data. A legitimate ATS page may itself contain AI-targeted instructions.

Required:
- rebase on current `main`,
- implement J15-11 from `docs/V1_5_BROWSER_SAFETY_CONTRACT.md`,
- page/body/label/hidden/accessibility text cannot alter policy, permissions, candidate truth, tool behavior or answers,
- suspicious prompt-like content may produce a security/audit signal but is not executed as instruction,
- required suspicious questions still follow normal provenance/manual-review rules.

Use the five J15-11 acceptance cases already defined in the safety contract.

## Verification required after repair

- rebase current `main` cleanly,
- targeted adversarial tests for A-R15-01..05,
- existing assisted-browser tests,
- full `pytest`,
- `ruff check .`,
- `mypy src tests`,
- GitHub CI green on the integrated/reviewable commit.

## Non-goals / safety boundary

This rework does not authorize:
- opening or prefilling a real application,
- submitting an application,
- login/MFA/CAPTCHA handling,
- treating the researched proof-job shortlist as user approval,
- weakening MANUAL_ONLY policy.

## Lead status

**REWORK — bounded residuals A-R15-01..A-R15-05.**

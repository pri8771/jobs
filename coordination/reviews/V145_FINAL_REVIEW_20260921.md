# Final V1.4/V1.5 review — 2026-09-21

Verdict: **REWORK; no real-life milestone accepted**. Preserve Fable's clean-port work. This is a bounded corrective review, not another roadmap.

## Reviewed sources

- Main at review start: `43766560522cd8afcd505463391f4013dd4b70b3`.
- Fable clean port: `3444076de27573ec57d9c8ae60876aece8e646d9` on `claude/serene-brown-g6uij0`, based directly on `927b33c...`.
- Schema support: `70ef7adc62ab2e9846721e8174a306273f28cbaa`, parent `3444076...`.
- V1.5 source: `ddb4f848a97dec87033cfdef7ca33642480d99bc` on `worker/v15-assisted-application`.
- Wider next-round planning remains draft PR #10. It is not the scope of this V1.4/V1.5 closure assignment.

The new branch starts at schema support `70ef7adc...`, so it already contains Fable's clean port and the proposed schema correction. It additionally contains an independently tested DB identity helper and this frozen assignment. It is a candidate integration branch, NOT an accepted deployment. Main and Fable's branch were not overwritten.

## Evidence and limitations

Fable reports 205 pytest passes on Python 3.12/SQLite, Ruff, mypy, and 16 former xfail probes. Exact reviewed SHA `3444076...` has zero GitHub check-runs. The lead did not independently rerun that full suite: this runtime could read the private repository through the connector but could not clone it because GitHub DNS resolution failed. PostgreSQL/real browser/private-profile tests were not run here.

The lead independently ran **19 isolated tests** of the new `scripts/proof_database_identity.py` helper on SQLAlchemy 2.0.50, and compiled that helper/test module. The helper is NOT yet wired into the production runner/verifier. No full-repository Ruff/mypy claim is made for the helper batch.

Three old behaviors were reproduced with exact reviewed expressions/functions in isolation, not a full installed application:
1. `str(SQLAlchemy URL)` changes the password to `***` on serialization.
2. changing form labels/options leaves the existing fingerprint unchanged.
3. a query string containing `confirmation` triggers the runner's submitted/confirmation-URL conditions without a submit action.

These observations do not establish any REAL_PROOF_PASS. No private candidate data, mailbox, account creation, application prefill/submission or external message was used.

## Frozen blockers and required acceptance cases

### FR14-01 — Candidate schema and runtime validation must agree

At Fable `3444076...`, `coordination/proofs/v14_real_proof.schema.json` still allowed extra properties and required `result=REAL_PROOF_PASS`, while the actual producer emitted `REAL_PROOF_CANDIDATE`. Support `70ef7adc...` corrects that declarative shape and adds tests.

Remaining task: adopt the support, require the same schema/type/required-field behavior in the actual verifier entry point, and run the tests without an optional dependency skip. Format validation must actually execute. An AST key comparison alone does not test runtime values. Fix the dependency location appropriately if runtime validation needs jsonschema.

Tests: actual producer-shaped candidate accepted structurally; self-PASS/self-FAIL, extra/nested private fields, malformed ID/timestamp/count/type and missing required field rejected with bound failure evidence. No malformed input may escape into a traceback instead of the intended failure result. Receipt filenames must not use untrusted path components, and committed reasons must be sanitized categories rather than raw credentials/private paths.

### FR14-02 — The real runner serializes a masked PostgreSQL URL

Source: `scripts/run_v14_real_proof.py` builds `db_url` using `str(bind.engine.url)` / `str(bind.url)` and persists it in the private bundle. The verifier then uses `local_data['database_url']` to connect. SQLAlchemy 2.x masks passwords in `str(URL)`, so the true production path can fail even when handwritten SQLite verifier tests pass.

The new helper offers the intended safe boundary:
- write `database_identity(bind.engine.url)` to the PRIVATE bundle;
- obtain the actual connection credential from the trusted runtime AppSettings/environment, not the evidence JSON;
- resolve and compare with `resolve_runtime_database(reference, configured_url)`;
- pass the URL object to the engine, or render the real credential ONLY at the private engine call if its signature requires a string;
- never log or persist the credential;
- retain existing mandatory persisted DB/row/source validation.

Do not simply write an unmasked password into the proof bundle. Do not let an untrusted bundle choose an arbitrary environment-variable name or remote host. Legacy masked bundles require regeneration or explicit trusted runtime reconciliation, never a secret guessed from evidence.

Tests: actual producer/exporter/consumer roundtrip on password-protected PostgreSQL; password rotation keeps target identity; wrong DB/host/user/driver blocks; no password in report/log/receipt; missing runtime credential remains blocked.

Primary documentation: https://docs.sqlalchemy.org/20/core/engines.html#sqlalchemy.engine.URL.render_as_string

### FR14-03 — Recompute from persisted answers, not just stored packet_hash

Source: `verify_database_linkage()` reads packet.packet_hash and row IDs but does not read `packet.answers_json`, `packet.answer_provenance_json`, or `packet.unresolved_questions_json`. Those fields exist on ApplicationPacketModel. `_build_proof_database()` in the current verifier tests omits these fields even though its manifest includes an answer.

This is a verified static omission. It must receive an actual mutation regression before being called closed; the lead did not execute a full DB exploit here.

Fix: independently load DB answers/provenance/unresolved fields, recompute canonical packet identity from DB components, compare every component with the manifest/exported evidence and verify counts. Bind the parsed canonical profile/version and selected genuine resume mapping, not merely the existence of a file plus its self-supplied digest. Check persisted ResumeVariant.version against the redacted version, actual source byte count, correct artifact types and manifest identity. Do not widen the allowed source class by relabeling a path.

Tests: mutate only DB answers, only provenance, only unresolved questions, profile version/content, selected resume mapping, resume version or byte count while retaining old stored hashes; verification must reject. Update fixture builders to produce internally consistent data through production services; do not delete the adversarial assertion or repair every hash in the test to hide the mutation.

### FR14-04 — Add a real producer-to-consumer engineering integration test

The existing verifier happy path hand-creates a candidate YAML containing only a name, resume text files and matching DB rows. Such unit fixtures are legitimate engineering tests but cannot establish compatibility of the real importer, ConfigLoader, packet builder, exporter and verifier.

Add a test that actually calls the production services on valid canonical engineering inputs and the supported PostgreSQL stack. Engineering test evidence stays in a separate test namespace and must never be published as REAL_PROOF. Do not remove source-origin checks to make synthetic data count as private. After P0A lead acceptance, the actual genuine-profile run supplies the real positive proof.

Any differing required key, masked URL, metadata key, schema output or DB dialect must fail this test before the next lead handoff. A SQLite-only run is insufficient evidence of production PostgreSQL compatibility.

### FR15-01 — Form snapshot must bind semantics and the actual destination

Sources: `compute_form_fingerprint()` includes name/type/selector/required but omits labels, placeholders, options and form action; Playwright `inspect_form()` reports requested URL rather than binding the actual navigated destination. The engine's second inspection compares only that limited fingerprint.

Fix: one canonical snapshot includes actual origin/action/form identity, inspected stable field identity, name/type, relevant labels/help/placeholder, option identities and required/manual/security classification. Recheck and reclassify immediately before writing. A changed label/action/option or new injection warning must not be hidden behind an unchanged name/type.

Tests: label-only, option-only, action/redirect and injection-text mutations invalidate prefill. Inspection failure is not a clean safety result. A benign stable form still progresses. Escape selectors safely or use actual inspected locators; no need to build a universal ATS framework.

### FR15-02 — Execute exact inspected upload mappings and record actual results

Source: Playwright prefill re-queries several broad resume/cover selectors and always returns success=True, even when attempted fields fail. The manifest is built before write, so planned values alone are not proof of actual prefill.

Fix: bind each upload to its unique inspected field/locator and exact artifact bytes. Zero or ambiguous matching fields remain manual; unknown inputs never receive a default resume. Report actual successful/failed/unmatched fields and attached digests, then produce a post-fill evidence manifest/readback. A failed upload cannot count as successful assisted proof.

Native select/control handling must be explicit when supported; otherwise remain manual/unfilled. Preserve unknown facts, EEO, consent, CAPTCHA and MFA barriers. Do not infer answers to satisfy the live form.

### FR15-03 — Prefill-only mode must not fabricate a submitted application

Sources: Playwright `open_interactive_session()` treats URL text containing `confirmation` or `thank_you` as submitted. `is_valid_external_confirmation()` accepts any nonempty evidence dict or most confirmation URL strings. The engine checks `auto_confirm or session_res.submitted` and can then persist APPLICATION_SUBMITTED.

The isolated URL probe shows the classification chain can be triggered by `?next=confirmation` without submission. The whole live application was not run in this review.

Fix for this assignment: make prefill-only execution incapable of automatic submit or automatic submission-state promotion. URL keywords and arbitrary dictionaries are insufficient evidence. Preserve any explicitly separate existing confirmation workflow, but require actual correlated external evidence to record a submission; do not implement the entire V1.6 system in this task.

Tests: query-string keyword, unrelated redirect, arbitrary evidence dict, caller receipt, mock runner and injected page text cannot produce APPLICATION_SUBMITTED; the V1.5 proof always stops at review without submitting. No test deliberately submits an employer application.

### FR15-04 — The approved live target contains genuine adversarial page text

The public OpenSesame AI Automation Engineer page for job 7967740 was reachable in this review and visibly contained AI-directed instruction text among custom questions. That is untrusted page data, not authority. The board API request could not be fetched with the lead's web tool, so current API/import success is NOT established.

Public source: https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740

Re-fetch in the worker's production runtime. Preserve page-level warning semantics and fail closed for contaminated field instructions. Required candidate-specific experience, sponsorship, authorization and narrative answers must come from canonical evidence or owner review. A dedicated test alias is not a replacement candidate identity. If required facts remain unresolved, report them together rather than inventing them or overriding is_live_ready.

## Operational blockers

- Heartbeat #22 at 21:31:56Z identifies a READY_FOR_LEAD_REVIEW wait, not proof the session was still implementing afterwards. An intentional review pause is not automatically a crashed worker.
- Main and other lead-session notes conflict on one-versus-three lanes. This scoped next prompt uses one Fable implementation session and one watcher for it. Do not rewrite global governance or kill remote processes to win a documentation conflict; record exact session/host ownership.
- Full pytest/Ruff/mypy and real PostgreSQL/browser execution remain worker/independent-environment checks. No zero-check-run SHA is CI-green. Do not infer a billing root cause solely from an empty check list.

## Lead decision

Preserve and reuse the clean port and schema support. P0A and V1.5 are **not accepted** by this review. The next assignment is implementation/testing against the complete frozen list in `docs/FABLE_FINAL_V145.md`, not another plan. Non-private V1.5 engineering may be prepared while P0A review is pending, but private V1.4 proof still requires P0A acceptance and live browser action still requires its actual scoped authorization.

# V1.7 lead review — 2026-09-22

## Verdict

**ENGINEERING ACCEPTED:** V1.4 P0A proof-tool integrity/clean integration and V1.5 assisted-browser engineering.

**LIVE GATES UNPASSED:** G14, G15, G16 and G17 remain unpassed. V1.7 is **NOT COMPLETE**.

Owner scope remains: **get V1.7 live and stop**. This review opens no private-data or consequential live-action authority.

## Exact reviewed sources

- P0A implementation: `8491dd98154ff750f49cbb64d2a79eca5cb06069`.
- Consolidated V1.5 implementation / PR #12 exact head: `47fefd1b0ca354360353577685f6619a94f00f42`.
- Integrated to `main` by PR #12 as merge commit `7c0fa73bf350392a88b47442455359a43cf926b0`.

## P0A findings closed

Lead review verified the consolidated implementation for:
- closed runtime candidate schema and candidate/receipt separation;
- runtime schema execution and schema-hash binding;
- credential-safe database identity and mandatory runtime-target matching;
- independent persisted Job/JobSource/packet/answer/provenance/artifact/profile/resume re-derivation;
- canonical Greenhouse source/question binding;
- canonical candidate-profile fingerprint and exact selected-resume byte/hash binding;
- generation-origin truth and fail-closed behavior for missing/tampered evidence;
- sanitized failure receipts and path-safe handling of untrusted proof IDs;
- production-path integration tests covering importer -> runner -> verifier on SQLite and password-protected PostgreSQL, including stale/mutated credentials and persisted-data mutations.

## V1.5 findings closed

Lead review verified the consolidated assisted-browser implementation for:
- semantic form snapshots bound to destination, form action, exact locators, labels/help/options and field classification;
- immediate reinspection before writes and blocking on meaningful form/destination changes;
- exact field-specific upload mapping with unknown/ambiguous file fields remaining manual;
- artifact byte/hash readback and truthful intended-vs-actual post-fill evidence;
- partial-result truthfulness;
- prefill-only assisted execution ending at `REVIEW_REQUIRED`;
- rejection of URL-keyword, runner, caller, mock or arbitrary evidence as submission confirmation;
- trusted structured external-confirmation boundary;
- local real-Playwright engineering-form coverage proving no submit POST from the assisted path and installed-entrypoint review-stop behavior.

## Validation evidence and CI exception

Fable's exact-head worker-host handoff reports **395 tests**, including real PostgreSQL producer-to-consumer proof-path validation and real headless Playwright engineering forms, with Ruff and mypy green. Earlier P0A-only handoff reported 323 tests before the V1.5 batch was added.

Hosted GitHub Actions for the reviewed exact code was **not green**: the job was blocked before executable steps began by the existing runner/account startup condition. This is recorded as `CI_BLOCKED_ACCOUNT`, not as a passing check and not as a code-test failure.

A bounded read-only `worker-pc` validation independently confirmed exact HEAD `47fefd1b0ca354360353577685f6619a94f00f42`, but the non-interactive harness denied every Python invocation, including a trivial `python -c`, so it contributes **zero test counts** and must not be represented as independent pytest evidence.

Under `coordination/V17_LEAD_HANDOFF.md`, the documented lead engineering exception for observed `CI_BLOCKED_ACCOUNT` is applied to these engineering artifacts only. It does not bypass protected checks and does not waive any live proof.

## Live-gate state

- **G14 — UNPASSED.** P0A engineering is accepted, but no genuine private profile + exact selected resume + current real job has been run through the production packet path with runtime candidate and independently validated receipt. `coordination/proofs/` contains no accepted runtime proof bundle.
- **G15 — UNPASSED.** V1.5 engineering is accepted, but no scoped owner grant has authorized a real visible-browser prefill/upload run using an accepted G14 packet. Any future G15 run must stop before submit.
- **G16 — UNPASSED.** V1.6 engineering/live authorization remains incomplete; no exact owner-approved job/packet/method system submission and correlated external confirmation exists.
- **G17 — UNPASSED.** No scoped bounded genuine recruiting evidence set has been authorized and proven through production ingestion/lifecycle/replay.

## Next bounded work

1. Fable pulls/synchronizes latest `main` while preserving the single owned five-minute watcher.
2. Do **not** run G14 on the current Fable host unless the approved genuine private profile, exact selected resume bytes, current real job/source and eligible connectivity are actually present and authorized.
3. While G14 is blocked on those inputs, continue only the independent V1.6 engineering explicitly permitted by `docs/FABLE_V17_LIVE.md`: authorization/idempotency/preflight/confirmation/hygiene/eligible-transport correctness, especially unsafe fallback/retry/confirmation semantics.
4. Return the next coherent engineering batch for lead review. Live G15/G16/G17 remain closed until their exact grants and prerequisites exist.
5. After accepted engineering plus genuine G14/G15/G16/G17: mark V1.7 COMPLETE, **STOP**, and await new owner scope.

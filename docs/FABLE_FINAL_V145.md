# Fable final V1.4/V1.5 execution assignment

**Implement this assignment; do not write another roadmap.**

User = product owner. ChatGPT = lead and acceptance authority. Fable = implementation worker. Immediate scope is V1.4 and V1.5 only. The V2.3 hardening plan in draft PR #10 remains future inventory; do not expand this run to V1.6/V2/V3.

## 1. Prepared starting point

Use `lead/jobs-v145-final-campaign-20260921` as a candidate starting point, after fetching and reconciling any newer actual implementation. It contains:
- Fable clean port `3444076de27573ec57d9c8ae60876aece8e646d9`;
- schema support `70ef7adc62ab2e9846721e8174a306273f28cbaa`;
- `scripts/proof_database_identity.py` and its 19 isolated tests;
- this execution assignment and the consolidated lead review.

This branch does **not** represent accepted P0A or accepted V1.5. The DB helper is tested in isolation and still needs production integration. Preserve existing local work. Make a clean worktree/branch from the candidate or port only absent changes; never force-reset a dirty checkout. Compare current main once, preserve newer source changes and record the chosen baseline. Do not repeatedly rebase for heartbeat-only or planning-only commits.

Read only:
1. current root guidance and this assignment;
2. `coordination/reviews/V145_FINAL_REVIEW_20260921.md`;
3. the active task's relevant code/tests and latest lead verdict.

Check relevant prior Claude/Fable memory for intent if available; Git defines code/status. Do not invent missing memory access.

## 2. Review verdict and autonomy

Current verdict on `3444076...`: **REWORK**. P0A is not accepted. No genuine V1.4/V1.5 proof has been accepted.

Lead authorization for this implementation round:
- finish all non-private V1.4 corrective engineering below;
- publish its coherent review handoff;
- while that review is pending, continue the independently testable V1.5 clean port and safety corrections in the same implementation session, rather than stopping all useful work after the first schema fix;
- do not use private profile/resume proof inputs before actual P0A acceptance;
- do not perform live application-page prefill before actual V1.5 engineering acceptance and scoped owner authorization;
- never self-mark ACCEPTED, REAL_PROVEN or COMPLETE.

Review waits are gates, not permission to fabricate success. Record READY_FOR_LEAD_REVIEW and continue only the safe engineering explicitly listed here. An available new lead acceptance can open the next gate; do not assume the lead is continuously online.

## 3. One early readiness report

Before major edits, report all missing prerequisites together using only authorized metadata:
- Python/dependencies, actual CLI commands, PostgreSQL and driver;
- genuine profile source/mapping availability and the exact selected resume variant;
- browser availability and whether a visible session can run on this machine;
- current proof job/API availability;
- P0A acceptance, private-input grant and prefill authorization status;
- CI/independent validation capability.

Never scan or read private profile contents while that gate is closed. Use already-approved metadata or report NOT_CHECKED_PENDING_GATE. A missing fact/file is a blocker, not an invitation to synthesize it. Do not use a different resume just to make the selector pass.

The OpenSesame job 7967740 public page was reachable during lead review and contains AI-directed injection text. Reverify current API/page state on the actual worker runtime. An old source snapshot or a web-viewed page is not a successful production import. Preserve all required questions and manual/unknown states.

## 4. Frozen small-task queue

Each task is SP1/SP2 complexity, not a time promise. Reuse verified equivalent changes instead of doing them twice. Complete every invariant of the parent artifact; do not satisfy one check by removing another.

| Task | Artifact | SP | Required output / finish test |
|---|---|---:|---|
| F145-00 | execution readiness | 1 | clean baseline, one session/heartbeat owner, one combined prerequisite/blocker report |
| F145-01 | A-V14-P0A-INTEGRITY | 1 | schema support adopted; candidate-only closed schema and real verifier validation agree; required tests cannot skip |
| F145-02 | A-V14-P0A-INTEGRITY | 2 | DB identity helper wired into actual producer/consumer; trusted runtime credentials remain usable and secret-free in evidence |
| F145-03 | A-V14-P0A-INTEGRITY | 2 | DB answers/provenance/unresolved fields independently re-derived and compared with manifest and packet identity |
| F145-04 | A-V14-P0A-INTEGRITY | 2 | parsed profile/version/source fingerprint + selector/variant/source bytes and artifact types/version/counts bound end to end |
| F145-05 | A-V14-P0A-INTEGRITY | 1 | all malformed/tampered inputs fail through safe candidate-bound receipt handling; no path traversal/raw credential leakage |
| F145-06 | A-V14-CLEAN-INTEGRATION | 2 | production-service positive integration on PostgreSQL plus adversarial cases; full checks and coherent P0A review handoff |
| F145-07 | A-V15-CLEAN-INTEGRATION | 1 | port only relevant existing V1.5 code/tests from historical source; no history/heartbeat churn or broad rewrite |
| F145-08 | A-V15-BROWSER-SAFETY-CONTRACT | 2 | canonical actual-form semantic snapshot; label/option/action/redirect/injection changes halt writes |
| F145-09 | A-V15-ASSISTED-APPLICATION | 2 | unique inspected field-to-artifact mapping, exact bytes, actual post-fill/upload results and truthful partial/manual outcomes |
| F145-10 | A-V15-ASSISTED-APPLICATION | 2 | prefill-only path cannot submit or promote submitted state; URL keywords/arbitrary evidence dicts rejected |
| F145-11 | A-V15-ASSISTED-APPLICATION | 2 | real Playwright local engineering form tests, installed entrypoint and full merged V1.4/V1.5 regressions |
| F145-12 | A-V14-REAL-PROOF | live gate | after P0A acceptance and allowed private use: real current job + genuine selected profile/resume → production packet → independent receipt |
| F145-13 | A-V15-LIVE-ASSISTED-PROOF | live gate | after required acceptances and prefill grant: real visible page + accepted real packet → actual safe prefill/uploads → review stop |
| F145-14 | integrated milestone handoff | 1 | final tested source identity, both proof references or exact unresolved external gates, clean startup/runbook and lead-review request |

The full required behavior and mutation cases for FR14-01..04 and FR15-01..04 are in the consolidated review. These are the frozen acceptance conditions; they are not optional suggestions.

### F145-02 integration details

Use `database_identity(session_bind.engine.url)` for the PRIVATE reference. In the verifier, load the actual approved runtime database config, then `resolve_runtime_database(reference, runtime_url)`. Connect with the resulting URL object; if the existing factory requires str, render credentials only at that private call with no logging/persistence. Keep all existing persisted-DB validation. Missing/mismatched DB or masked legacy credential remains a rejection. Validate the real password-protected PostgreSQL path, not only SQLite string parsing.

### F145-03/04 integrity details

Do not merely compare stored packet_hash strings. Compute from persisted answers/provenance/artifact identifiers and compare to the manifest, then to independent evidence. Parse the actual canonical profile after its input gate opens; bind its normalized fingerprint/version and selected source mapping to the production packet. In engineering tests use valid canonical synthetic profiles and clearly label the fixture namespace; never export a fixture as REAL_PROOF.

Mutating only DB answers, provenance, unresolved list, profile identity/version, selected resume, variant.version or byte count must fail. Keep raw profile/resume data and exact local paths out of committed evidence.

### F145-08/09 browser details

Use actual inspected form/field identity and current destination. Include labels/help/placeholder, options and form action in semantic revalidation. Use safely escaped or actual captured locators; do not search again with broad file-name substrings and pick the first match. Duplicate or unknown file fields remain manual. Readback after writing distinguishes intended values from successfully filled values. Native/custom controls are supported explicitly or left manual, never guessed.

Do not weaken is_live_ready, unknown-answer, EEO, consent, CAPTCHA or MFA barriers to pass the real job. If required canonical answers are unavailable, emit one consolidated review request and continue allowed engineering. A warning in body text must never become an application answer.

### F145-10 browser submission details

For this run the only live browser capability is prefill-to-review, and only after its actual grant. `auto_confirm` is not authority. No automated submit click/Enter, no URL-substring confirmation, no arbitrary evidence dict causing APPLICATION_SUBMITTED. Preserve separately scoped legitimate manual-confirmation functionality only when independently correlated external evidence is verified. Do not build broad V1.6 submission automation to repair this V1.5 boundary.

## 5. Testing ladder — fail fast, prove the complete path

1. Run the 19 helper tests (already isolated-tested by lead); wire the helper and add actual producer/consumer tests.
2. Run schema/importer/runner/verifier, preparation/artifact and full P0A adversarial tests.
3. Run against actual PostgreSQL using the configured synchronous driver and current migrations. Zero-migration/SQLite-only success does not prove the production DB path.
4. Run actual Playwright on a controlled local engineering form covering two upload fields, unknown/ambiguous field, dynamic label/action/options, injection, redirect and no-submit behavior. This is ENGINEERING evidence, not the employer live checkpoint.
5. Run installed CLI/API entrypoints using documented commands, not only direct unit methods.
6. Run full pytest, Ruff, format checks, mypy and required migrations on the combined source. Report pre-existing formatting failures separately, never as globally clean. No broad formatting churn without need.
7. Run exact-head CI when available. If unavailable, provide observed infrastructure evidence plus a clean independent full validation run. An empty check list alone does not diagnose account billing. Do not claim CI-green or silently skip a required test.
8. Only after actual lead gates open, run genuine V1.4 then V1.5 proof.

A positive engineering integration must call real production constructors/importer/builder/exporter/validation components. It must not hand-author DB/proof JSON to imitate those outputs. It may use clearly synthetic engineering inputs in an isolated test namespace; its result remains engineering-only. Do not disable source-origin/private-input protections to manufacture a REAL_PROOF_PASS from fixtures.

## 6. Live proof artifacts

### V1.4

Use current real approved public job, genuine canonical private profile and the exact selected genuine resume bytes. Run actual importer, packet builder and exporter. Candidate must be REAL_PROOF_CANDIDATE; only the separate verifier emits its bound PASS/FAIL receipt. Bind runtime code/dependency/schema identity, source fetch/question digests, DB rows, profile fingerprint, variant and artifact bytes. No application submission.

Unknown questions remain explicit. Packet preparation success must not pretend the packet is submission-ready. V1.5 still enforces its own readiness contract.

### V1.5

Use a real accepted packet and authorized visible browser against the current permitted application destination. Inspect and classify before writes, revalidate immediately before writes, fill only allowed facts, attach the exact accepted files, independently record successful readbacks and stop before final submission.

Evidence must show real session mode, actual destination/form snapshot, packet/variant/artifact hashes, actual filled/unfilled/manual fields, security warnings, post-fill review manifest and no submit performed. Redact field values and private content in committed copies. An empty-page screenshot, headless fixture or planned prefill manifest does not satisfy the live checkpoint.

Owner-controlled test account/alias permission applies only to its actual bounded provider-canary scope. It is not permission for job submission or a substitute for real candidate/recruiting facts. Account creation is unnecessary for these milestones unless a specific permitted real path requires it.

## 7. Review cadence and one-shot intent

Do not return after only fixing the schema. Finish the complete allowed engineering queue for both milestones and prepare every real-proof prerequisite.

Publish a coherent P0A handoff as soon as it is ready; while its review is pending, continue F145-07..11 non-private V1.5 engineering. Do not cross private/live gates without acceptance. Once all safe work is done, a genuinely unavailable approval/private input/browser/provider is an explicit blocked outcome, not another feature-planning task.

No new features in this round. Newly discovered failures may enter only when they violate an existing safety or acceptance condition; add a reproducing test and the smallest repair. Do not rewrite the roadmap or start V1.6/V2/V3.

## 8. Heartbeat, ownership and efficiency

One Fable implementation session and one watcher for that session, epoch FIVE_MIN_2026_09_21 / ACTIVE_5M / five minutes while active. Do not create subagent watchers or pretend a local process check proves another host is stopped. Record session/host, actual code branch/SHA and heartbeat branch explicitly. Use the existing supported watcher command after verifying ownership; stop the owned watcher when the session intentionally stops. READY_FOR_LEAD_REVIEW plus an intentional pause is not continued implementation activity.

The repo contains competing lane directives from other lead contexts. For this assignment do not reopen lanes or overwrite global governance. Preserve other work and report an ownership conflict rather than deleting processes or restoring stale documentation. ChatGPT remains the lead.

Use cheap available subagents for mechanical inventory/test-writing/formatting; the parent integrates. Strong reasoning reviews schema, identity, proof, privacy and browser authority. No fixed commercial model names or effort labels are assumed available. Use targeted reads/diffs, not all V2.3/V3 planning files on every turn.

## 9. Exact final handoff

Report:
- candidate branch and exact source commit plus source/dependency/schema identity;
- each F145 task: done / failed / externally blocked, with evidence;
- exact focused/full test commands, counts, exit codes and sanitized logs;
- which validation was independent and which was worker-reported;
- V1.4 candidate + separate receipt references or exact missing gate;
- V1.5 actual visible-browser/post-fill/no-submit evidence or exact missing gate;
- remaining required candidate answers/mappings/authorization, consolidated;
- heartbeat ownership/final state;
- READY_FOR_LEAD_REVIEW.

Workers do not mark milestones accepted. The desired finish is both V1.4 and V1.5 genuinely demonstrated and ready for final lead acceptance. If an external prerequisite makes that impossible, the only acceptable partial finish is all safe engineering complete plus a precise actionable blocker—not a false success or another broad plan.

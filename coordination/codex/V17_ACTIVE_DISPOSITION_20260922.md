> **Latest owner assignment — 2026-09-22:** Claude is the next Jobs Automation implementation owner; target accepted LIVE V1.7. Read `coordination/codex/OWNER_RACE_V17_20260922.md` and `coordination/codex/CLAUDE_JOBS_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# Jobs V1.7 active disposition package — 2026-09-22

Authority:
- Latest owner goal reset: `coordination/codex/OWNER_TARGET_V17_20260922.md` (owner record ebae569).
- Target is **accepted V1.7, then STOP**.
- V2.0/V2.3/V2.7/V3 are deferred.
- ChatGPT remains lead and formal engineering/live/milestone acceptance authority.
- **Codex is the current direct implementation integrator for this pass.**
- Claude/Fable is paused/handed off and is not dispatched by this package.

This package lifts the prior owner pause only for the offline engineering work explicitly released below. It does not grant any live/account/mailbox/browser/application/model/scheduler/spend/deploy/main-merge action.

## 1. Execution ownership and watcher

Current direct implementation worker for this pass: **Codex**.

Claude/Fable:
- paused for implementation;
- retained only as historical/source context unless the owner explicitly reactivates it;
- no Fable/Claude dispatch is authorized by this package.

Existing watcher/heartbeat ownership is preserved exactly as already recorded:
- `FIVE_MIN_2026_09_21` / `ACTIVE_5M`;
- publication branch `worker/v14-real-proof`;
- no ownership transfer to Codex is implied;
- **no new timer, heartbeat, scheduler, cron, or automation is created or changed**.

Codex works directly on released source tasks and returns exact-SHA evidence. Existing watcher status must remain truthfully reported by its existing owner; this package does not fabricate or restart it.

## 2. Immediate active assignment — PR26 hosted mypy repair

### Exact starting source

Actual Jobs PR26:
https://github.com/pri8771/jobs/pull/26

Base exact candidate:
`b2688eeabb5ca996767b27b78d0004678eeee756`
tree `6644f340b98eae517ae08ccde38a28da5f2c52a9`
branch `codex/jobs-v17-cli-gate-20260922`

Hosted run:
`35757522343`, latest job `106870677780`.

Observed hosted behavior:
- setup/container/checkout/Python/install: PASS;
- Ruff: PASS;
- `mypy src tests`: FAIL;
- Alembic + pytest skipped because mypy failed.

Exact mypy failure inventory:
- `tests/test_cli.py`: 15 errors;
- `tests/test_worker.py`: 7 errors;
- total: 22 errors across 113 checked files.

The errors are test typing only: missing annotations and Optional ORM results assigned to non-Optional variables. This is a real hosted CI failure, not an infrastructure-start failure.

### Allowed files

Production source changes are **not authorized** for this assignment.

Allowed files only:
- `tests/test_cli.py`
- `tests/test_worker.py`

No workflow, pyproject/mypy config, ignore, exclude, per-module override, CI command, or source typing relaxation may be changed.

### Required repair behavior

Fix typing honestly without changing test semantics:
- add precise parameter/return annotations to currently untyped test helpers/functions;
- narrow/assert ORM `session.get` / scalar results before assigning/using values that tests require to exist;
- use existing model types and standard typing constructs;
- do not add `# type: ignore`, `Any` merely to silence errors, broad casts that bypass the invariant, or mypy exemptions unless a specific existing API truly requires a narrow cast and the test proves the runtime invariant first;
- do not weaken assertions, skip tests, remove cases, or alter production behavior.

### Required validation

Before handoff:
1. `mypy src tests` must pass exactly under the hosted command/config.
2. Focused:
   - `pytest -q tests/test_cli.py tests/test_worker.py`
3. Full pytest.
4. Ruff over source/tests.
5. Format/diff check for the two touched tests.
6. Push exact new PR26 head and allow hosted Actions to rerun.
7. Hosted result must be classified truthfully:
   - green if all actual steps execute/pass;
   - code failure if an executed code step fails;
   - infrastructure blocked only if runner never executes relevant steps.

Return exact new SHA/tree, diff, commands/exits, hosted run/job IDs, and READY_FOR_LEAD_REVIEW. Do not self-accept.

**This is the one active next engineering assignment now.**

## 3. V1.6 hosted-form transport policy — frozen lead proposal

This is a project safety/eligibility policy for V1.7 engineering. It is **not legal advice, ToS clearance, employer authorization, or a live-action grant**.

### Single supported hosted-form route

For V1.7, engineering may target **one candidate-facing employer/ATS hosted web-form route only: the employer-provided Greenhouse candidate application form in a visible browser flow**.

Explicitly out of V1.7 live transport scope unless separately re-authorized:
- LinkedIn submission;
- Indeed submission;
- generic browser submission to arbitrary ATS families;
- employer/private ATS APIs;
- undocumented endpoints;
- reverse-engineered submission calls;
- credential/API-token acquisition from an employer;
- any anti-bot/CAPTCHA/MFA bypass.

If the exact desired employer does not provide an eligible Greenhouse candidate-facing form, the truthful state is:
`BLOCKED_NO_ELIGIBLE_TRANSPORT`
until the lead/owner explicitly approves another route.

### Five frozen transport questions

1. **Destination policy / ToS eligibility**
   - Before engineering/live use, record the exact candidate-facing form and current destination-policy review.
   - If automation eligibility is unclear, disputed, blocked, or explicitly prohibited, stop with `BLOCKED_NO_ELIGIBLE_TRANSPORT`.
   - Owner approval cannot override a destination restriction.
   - This is an internal safety rule, not a legal determination.

2. **Scoped authorization**
   - No submit authority is blanket.
   - Required before any real submit: exact owner-approved job/requisition + account/session alias + exact packet/hash + exact method/route + current policy reference + unexpired approval.
   - Consequential unresolved answers block submission.

3. **Bot challenge / verification**
   - CAPTCHA, MFA, anti-bot challenge, identity verification, unexpected login challenge, or comparable barrier is a terminal automation halt.
   - Route to manual owner review.
   - No bypass, solver, stealth workaround, retry storm, fingerprint evasion, or alternate endpoint.

4. **Employer/ATS API**
   - No employer ATS submission API may be used without explicit employer-side authority/credentials establishing that API access.
   - A public job-board token/read endpoint is not submission authority.
   - For the V1.7 route above, the intended transport is the visible candidate-facing hosted form, not an employer API.

5. **Confirmation signal**
   - Local click success, HTTP success, navigation, thank-you URL text, or adapter return value is insufficient.
   - `SUBMITTED` requires correlated external evidence tied to the exact attempt/job/candidate, such as a provider-generated confirmation/reference, employer account application state, or correlated application-confirmation email.
   - Ambiguous outcome becomes `SUBMISSION_UNCONFIRMED`; do not blind-retry.

These answers freeze the engineering policy only. They do not authorize G15 or G16.

## 4. Formal V1.7 artifact dispositions

### A-V17-CRM-EVIDENCE

Disposition: **SEMANTIC REVIEW SATISFIED / FINAL ARTIFACT ACCEPTANCE PENDING INTEGRATED EXACT-HEAD CI**.

Prior lead review already accepted the actual semantic repair set (multi-role/thread divergence and rejection contradiction handling). No new CRM rewrite is authorized without a concrete failing regression.

Remaining acceptance work:
- current V1.7 composed candidate;
- exact-head full tests/Ruff/`mypy src tests`;
- green hosted CI;
- preserve manual correction/merge audibility and provider evidence.

Status remains LEAD_REVIEW until that integration/CI condition is met.

### A-V17-INTERVIEW-FOLLOWUP

Disposition: **SEMANTIC REVIEW SATISFIED / FINAL ARTIFACT ACCEPTANCE PENDING INTEGRATED EXACT-HEAD CI**.

Existing reviewed implementation/test coverage is the reuse baseline for:
- interview scheduling/timezone/reschedule/cancel;
- repeated-sweep idempotency;
- follow-up dedupe/replied-thread handling;
- safe lifecycle terminal transitions.

No rebuild is authorized without a concrete failing case.

Status remains LEAD_REVIEW until current composed exact-head validation and hosted CI pass.

### A-V12-CANDIDATE-PROVENANCE

Disposition: **SUPERSEDED / SATISFIED BY THE ACCEPTED P0A + PACKET PROVENANCE CONTRACT; NO PARALLEL IMPLEMENTATION**.

The accepted A-V14-P0A-INTEGRITY source `8491dd98154ff750f49cbb64d2a79eca5cb06069` already requires:
- canonical candidate-profile fingerprint;
- exact selected resume bytes/hash/version/source binding;
- persisted answer/provenance/unresolved-field recomputation;
- fail-closed tamper/missing evidence;
- private raw values kept out of committed proof.

V1.7 work must reuse that canonical provenance/fingerprint path. Unknown/inferred consequential facts cannot become application truth. Do not create a second provenance database/model merely because A-V12 remains an older artifact row.

This disposition does not pass G14; G14 still needs genuine approved profile/resume/job inputs and host permission.

### Synthetic golden fixture

The accepted synthetic golden fixture remains engineering regression evidence only. For V1.7 it may support integrated regression coverage, but it does not substitute for G14-G17 and is not itself a V1.7 live gate.

## 5. Composition — COMP-2 queued release after PR26 typing review

COMP-2 is the **next composition conflict**, but it is not the active task until the PR26 typing repair has an exact-SHA lead verdict.

Inputs remain:
- accepted control/local-origin line `b67fc523863babd3e195ee71a05f00fa0f2f7e79`;
- accepted canary line `b2688eeabb5ca996767b27b78d0004678eeee756`;
- accepted reference semantics patch `2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a` is REFERENCE_ONLY;
- common ancestor `dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`.

### COMP-2 scope

When activated after typing acceptance, open **only the `src/jobs_automation/ingestion/engine.py` dependency conflict** required to make the accepted canary bounded/V3 APIs executable on the control composition base.

Expected production file:
- `src/jobs_automation/ingestion/engine.py`

Expected focused tests:
- `tests/test_gmail_adapter_bounded.py`
- `tests/test_bounded_ingestion.py`
- `tests/test_canary_provenance.py`
- only one additional narrowly required existing test file if an engine behavior is directly exercised there.

Required engine API/behavior closure:
- `canonical_email_addresses`;
- `persisted_message_matches_canary_policy`;
- `reclassify_persisted_canary_messages`;
- `IngestionSweepSummary.batch_canary_provider_message_ids`;
- the accepted `safe_errors` constructor/behavior contract required by bounded execution;
- malformed independent header handling;
- invalid canary identity fail-closed behavior;
- incomplete-poll atomicity from the accepted control line;
- no regression to checkpoint semantics or ordinary genuine ingestion.

Do not resolve lifecycle/alerts/CRM/worker/dashboard conflicts in COMP-2.

### V1.7-only composition validation

For COMP-2 and later composition, validation scope is the V1.7 critical path only:
- Gmail bounded pagination/completeness;
- header/direction/provider-time semantics;
- canary durable/runtime quarantine;
- V3 bounded audit/replay and zero-new-poll preflight;
- accepted bounded reference semantics;
- CRM/interview/follow-up regressions needed for G17;
- V1.6/V1.7 safety integration relevant to G16/G17;
- full pytest, Ruff, `mypy src tests`, migrations/PostgreSQL as affected.

Do **not** require V2.0 control-center-only acceptance checks merely because they exist on the control branch, except where needed to prove no accepted safety regression in a touched shared file.

## 6. Exact-SHA review before main merge

Formal rule:

**Candidate-branch exact-SHA engineering review and acceptance may precede any merge to `main`.**

Main merge is not currently authorized and is not a prerequisite for:
- reviewing an exact candidate SHA;
- accepting an isolated engineering artifact;
- reviewing a composed V1.7 candidate.

Any acceptance must name exact SHA/tree and scope. It does not imply main merge.

When/if a main merge is later authorized, the merged result must be re-identified and checked for composition/merge drift before claiming that main contains the accepted candidate.

## 7. G14 relationship to composition

G14 is independent of the b67/b268 composition.

When the owner supplies:
- approved genuine private candidate profile path;
- exact selected resume bytes/path;
- one current real job URL;
- private-use authority;
- eligible execution host/network permission;

then G14 may proceed from the already accepted main proof path, subject to that exact scoped grant.

**Do not wait for COMP-2/COMP-3 composition to begin G14 once its inputs/host authorization exist.**

Until those owner inputs/grants arrive, G14 remains UNPASSED and no private proof is run.

## 8. Closed authorities

This package does not authorize:
- live Gmail/OAuth/mailbox reads;
- real employer page prefill;
- application submit;
- employer API use;
- model/provider calls;
- external messaging;
- public actions;
- scheduler/timer changes;
- spend;
- deployment;
- main merge.

G14-G17 remain UNPASSED.

## 9. Immediate expected handoff

Codex now performs only the PR26 two-file typing repair.

Expected starting SHA:
`b2688eeabb5ca996767b27b78d0004678eeee756`

Expected changed files:
- `tests/test_cli.py`
- `tests/test_worker.py`

Expected next state:
`READY_FOR_LEAD_REVIEW` with a new exact PR26 head SHA/tree and hosted CI evidence.

COMP-2 remains queued and becomes executable only after the typing candidate receives a lead disposition.


## 10. PR26 typing repair verdict and COMP-2 activation

### PR26 typing repair

**ACCEPTED** exact source:
- SHA `eec0ae3d9b50979b74294dd9ee0561172eff54b0`
- tree `b41f35ff4e816c3df52521e328d60d598a4bc408`

Changed files only:
- `tests/test_cli.py`
- `tests/test_worker.py`

Hosted validation:
- run `35771627731`
- job `106894485077`
- Ruff: PASS
- `mypy src tests`: PASS
- Alembic migration chain: PASS
- Pytest: PASS
- job conclusion: SUCCESS

Local source-bound validation:
- baseline 22 mypy errors reproduced;
- candidate `mypy src tests`: clean, 113 files;
- 26 focused tests pass;
- full 490 pass / 1 existing host-specific skip;
- owned PostgreSQL proof integration cleanup0;
- Ruff/format/diff clean;
- independent non-implementer AST review retained 26 tests / 125 assertions.

No production behavior or CI strictness was changed.

### COMP-2 is now ACTIVE

Current direct integrator: **Codex**.

Starting composition inputs:
- control/local-origin accepted line: `b67fc523863babd3e195ee71a05f00fa0f2f7e79`
- accepted canary/CLI/replay line now with typing-only successor: `eec0ae3d9b50979b74294dd9ee0561172eff54b0`
- reference-only bounded semantics: `2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a`
- common ancestor for control/canary source lineage: `dd2e0deb15ce0ff8983c4ed502e3e17206db2e80`

**Active scope: resolve only COMP-2, the `src/jobs_automation/ingestion/engine.py` composition dependency conflict.**

Expected production file:
- `src/jobs_automation/ingestion/engine.py`

Expected focused tests:
- `tests/test_gmail_adapter_bounded.py`
- `tests/test_bounded_ingestion.py`
- `tests/test_canary_provenance.py`
- at most one additional directly affected existing test file if strictly required by an engine API behavior.

Required integrated engine behavior:
1. preserve accepted control-line incomplete-poll atomicity/checkpoint behavior;
2. preserve canonical per-field email parsing from the accepted canary line;
3. preserve `canonical_email_addresses`;
4. preserve `persisted_message_matches_canary_policy`;
5. preserve `reclassify_persisted_canary_messages`;
6. preserve `IngestionSweepSummary.batch_canary_provider_message_ids`;
7. preserve the accepted `safe_errors` constructor/behavior required by bounded execution;
8. malformed independent From/To/Cc fields cannot suppress a valid canary alias;
9. invalid configured canary identities remain fail-closed through the existing config contract;
10. genuine ingestion/checkpoint/deduplication behavior must not regress.

Composition rule:
- start in an isolated integration worktree from the accepted control line;
- import/resolve only the engine dependency closure required by the accepted canary bounded/V3 API;
- do not resolve lifecycle/alerts/CRM/worker/dashboard conflicts in this pass;
- if preserving both accepted engine behaviors requires modifying another held production conflict file, STOP and return `COMP-2_REWORK_FOUND` with the exact dependency instead of broadening scope.

V1.7-only validation:
- focused engine/Gmail/bounded/canary tests;
- malformed-header regression;
- incomplete-poll/missing-message/cap-truncation atomicity;
- historical canary reclassification behavior that is engine-owned;
- full pytest;
- Ruff;
- `mypy src tests`;
- affected PostgreSQL/migration checks when needed;
- no V2.0-only control-center acceptance matrix required for this task.

Return:
- exact base/input SHAs;
- exact conflict resolution diff;
- source SHA/tree;
- commands/exits;
- any conflicts/dependencies encountered;
- `READY_FOR_LEAD_REVIEW` or `COMP-2_REWORK_FOUND`.

No main merge, Fable/Claude dispatch, live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, or other live action.

### Dynamic resume clarification

Owner clarification in `DYNAMIC_RESUME_CLARIFICATION_20260922.md` is acknowledged as current product intent:
- resumes may be tailored per job from verified candidate facts;
- exact generated resume bytes must be bound to each application/packet;
- automatic JD-to-resume generation is not currently implemented.

This clarification does not authorize model/private-data work and does not expand COMP-2.


## 11. COMP-2 dependency disposition — prerequisite split

**COMP-2_REWORK_FOUND confirmed** from native diagnostic `824f240` / `coordination/codex/COMP2_DEPENDENCY_REWORK_20260922.md`.

The clean control composition base remains:
`b67fc523863babd3e195ee71a05f00fa0f2f7e79`

No source/index edits from the failed COMP-2 attempt are accepted.

### Confirmed dependency blockers

Engine-only integration cannot satisfy the released malformed-neighbor and policy requirements because:

1. `src/jobs_automation/adapters/gmail.py` on the control line parses To/Cc in a combined strict call. A malformed Cc can erase a valid To alias, and a malformed To can erase a valid Cc alias before `EmailIngestionEngine` receives the recipients.
2. `src/jobs_automation/core/platforms.py` on the control line does not define `email.canary_identities`; the strict model rejects even a valid alias as `extra_forbidden`.
3. Full canary provenance/V3/reference tests additionally depend on held `bounded.py` and `db/canary_provenance.py` behavior. Those are **not** opened by this prerequisite.
4. Wholesale copying canary `engine.py` is prohibited because it would drop accepted control-line candidate-reply/outbound attribution behavior, including `_link_candidate_reply`.

## COMP-2A — ACTIVE prerequisite: Gmail parser + canary config schema only

**State: RELEASED TO CODEX / OFFLINE ENGINEERING ONLY.**

Starting base:
`b67fc523863babd3e195ee71a05f00fa0f2f7e79`

Reference behavior source:
`eec0ae3d9b50979b74294dd9ee0561172eff54b0`

Allowed production files only:
- `src/jobs_automation/adapters/gmail.py`
- `src/jobs_automation/core/platforms.py`

Allowed focused tests:
- `tests/test_gmail_adapter_bounded.py`
- `tests/test_config.py`
- at most one new/adjacent focused test file if needed solely to prove these two production contracts.

### Required Gmail behavior

Port only the accepted recipient-header parsing behavior needed for this dependency:
- parse `To` and `Cc` **independently**;
- one malformed header must not erase valid addresses from the other header;
- preserve provider-observed time vs claimed Date separation;
- preserve existing SENT/verified-identity outbound direction semantics;
- preserve all control-line pagination/completeness behavior;
- no mailbox/network access in tests.

Required regressions:
- malformed Cc + valid To canary alias => valid To survives;
- malformed To + valid Cc canary alias => valid Cc survives;
- malformed From does not erase valid recipient aliases;
- ordinary valid multi-recipient parsing unchanged;
- no direction/time regression.

### Required config behavior

Port only the accepted canary policy schema:
- add `EmailPollingConfig.canary_identities: list[str]` defaulting to empty;
- each configured entry must parse to exactly one email address;
- malformed/multiple-address identity fails validation;
- preserve `extra="forbid"` and all existing provider/polling validation;
- do not add runtime Gmail access, OAuth, or worker behavior.

Required regressions:
- valid single alias accepted;
- display-name single alias accepted if it resolves to exactly one address;
- malformed identity rejected;
- multiple-address single entry rejected;
- unrelated unknown config keys remain rejected.

### Explicit non-scope

Do **not** modify:
- `src/jobs_automation/ingestion/engine.py`;
- `src/jobs_automation/ingestion/bounded.py`;
- `src/jobs_automation/db/canary_provenance.py`;
- lifecycle/alerts/CRM/worker/dashboard/CLI;
- migrations;
- CI configuration.

This prerequisite does not claim:
- COMP-2 engine resolution;
- V3 bounded/replay integration;
- durable provenance composition;
- reference-patch integration;
- G14-G17 progress.

### Validation

Run:
- focused Gmail/config tests;
- full pytest;
- Ruff;
- `mypy src tests`;
- diff/format check;
- hosted CI on exact candidate if a PR/head is used.

Return exact SHA/tree and READY_FOR_LEAD_REVIEW or COMP-2A_REWORK_FOUND.

## Queued after COMP-2A acceptance — COMP-2 engine API preparation

If and only if COMP-2A is accepted, reactivate the engine-only conflict with:
- production file `src/jobs_automation/ingestion/engine.py`;
- preserve control candidate-reply/outbound attribution;
- add accepted canary engine helpers/runtime membership/safe_errors/reclassification;
- preserve incomplete-poll atomicity/checkpoint semantics.

At that stage, integrated V3/reference claims remain deferred until their own explicit `bounded.py`/provenance scope is opened. Engine acceptance must not claim full composition.

No Fable/Claude dispatch, live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, or main merge.


## 12. COMP-2A inherited mypy blocker — sequencing disposition

Reported COMP-2A worktree:
- isolated base: `b67fc523863babd3e195ee71a05f00fa0f2f7e79`;
- released production files only:
  - `src/jobs_automation/adapters/gmail.py`
  - `src/jobs_automation/core/platforms.py`
- released focused tests only:
  - `tests/test_gmail_adapter_bounded.py`
  - `tests/test_config.py`

Current reported focused state:
- baseline regressions: 8 failed / 23 passed;
- repaired focused set: 31 passed;
- Ruff clean;
- source-only mypy (74 source files) clean.

A separate pre-existing integration typing blocker was reproduced **before COMP-2A edits**:
`uv run mypy src tests` reports 27 errors in:
- `tests/test_crm_corrections.py`
- `tests/test_bounded_ingestion_scope.py`
- `tests/test_candidate_reply_attribution.py`
- `tests/test_auto_application.py`
- `tests/test_dashboard_health_badge.py`

The COMP-2A candidate must not edit those files or weaken mypy/CI to hide them.

### COMP-2A review rule

Submit COMP-2A exactly within its released four-file scope.

Formal review may disposition the bounded Gmail/config prerequisite on exact-SHA evidence if:
1. the candidate changes only the released files;
2. the 27 full-mypy errors are proven byte-for-byte/category-for-category inherited from the exact b67 baseline;
3. the candidate introduces **zero new** `mypy src tests` errors outside that inherited set;
4. focused Gmail/config tests pass;
5. full pytest passes;
6. Ruff passes;
7. source-only mypy passes;
8. any PostgreSQL/integration evidence required by the candidate completes cleanly.

If accepted, the verdict must state:
- COMP-2A behavior accepted;
- full integration CI remains blocked by inherited test typing;
- no hosted-green claim until the separate typing repair lands.

Do not call the inherited typing errors a COMP-2A product regression.

## COMP-2B-TYPING — queued, conditional on COMP-2A acceptance

**Not active until COMP-2A exact-SHA disposition.**

If COMP-2A is accepted, create the next isolated candidate **on top of the accepted COMP-2A SHA**.

Allowed files only:
- `tests/test_crm_corrections.py`
- `tests/test_bounded_ingestion_scope.py`
- `tests/test_candidate_reply_attribution.py`
- `tests/test_auto_application.py`
- `tests/test_dashboard_health_badge.py`

No production source changes.

Required repair:
- fix all inherited typing errors honestly;
- preserve test behavior/assertions;
- add precise annotations and non-Optional narrowing/assertions where runtime invariants require existence;
- no broad `Any` solely to silence mypy;
- no `# type: ignore` unless an unavoidable third-party typing defect is demonstrated and narrowly documented;
- no test deletion/skip/assertion weakening;
- no mypy config, CI workflow, exclude, override, or command relaxation.

Required validation:
1. reproduce the exact inherited 27-error baseline on the accepted COMP-2A parent;
2. `mypy src tests` => clean;
3. focused pytest for all five touched test files;
4. full pytest;
5. Ruff;
6. format/diff check;
7. hosted CI on exact head if available.

Return exact SHA/tree and READY_FOR_LEAD_REVIEW.

## Composition hold

COMP-2 engine work remains held until:
1. COMP-2A is formally dispositioned; and
2. the five-file typing repair is accepted with full `mypy src tests` green.

Do not begin `engine.py`, `bounded.py`, provenance, lifecycle, worker, dashboard, or other held conflict work in parallel.

No live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, Fable/Claude dispatch, or main merge.


## 13. COMP-2A formal verdict and COMP-2B typing activation

### COMP-2A

**ACCEPTED** exact source:
- SHA `1b9efdda418baa059903215349e27493cf709f3a`
- tree `cb57c3fe973cd8e837838d1a095d334cc2cba321`
- base `b67fc523863babd3e195ee71a05f00fa0f2f7e79`

Accepted scope only:
- `src/jobs_automation/adapters/gmail.py`
- `src/jobs_automation/core/platforms.py`
- `tests/test_gmail_adapter_bounded.py`
- `tests/test_config.py`

Accepted behavior:
- To/Cc recipient headers are parsed independently, so one malformed neighboring header cannot erase valid recipients from the other;
- ordinary recipient ordering/address parsing remains stable;
- control-line pagination/completeness/provider-time/direction semantics are preserved;
- `EmailPollingConfig.canary_identities` exists with empty default;
- every configured canary entry must resolve to exactly one email address;
- malformed/multi-address entries fail validation;
- `extra="forbid"` and existing provider/polling validation remain intact.

Evidence:
- baseline focused: 8 failed / 23 passed;
- repaired focused: 31 passed;
- full exact-tree: 530 passed / 1 existing host skip;
- owned PostgreSQL proof integration cleanup0;
- Ruff clean;
- source-only mypy74 clean;
- format/diff clean;
- independent exact-tree review recommends acceptance.

Full `mypy src tests` is **not green** on this line because of 27 inherited errors in unrelated tests. Baseline and candidate logs are byte-identical; COMP-2A adds zero new errors. Therefore this acceptance does not claim hosted/full integration CI green.

### COMP-2B-TYPING — ACTIVE

Current direct integrator: **Codex**.

Starting parent:
`1b9efdda418baa059903215349e27493cf709f3a`

Allowed files only:
- `tests/test_crm_corrections.py`
- `tests/test_bounded_ingestion_scope.py`
- `tests/test_candidate_reply_attribution.py`
- `tests/test_auto_application.py`
- `tests/test_dashboard_health_badge.py`

No production source changes.

Goal:
- reproduce the exact 27 inherited errors on the accepted COMP-2A parent;
- fix them honestly with precise annotations and non-Optional narrowing/assertions;
- preserve behavior and assertions;
- no broad `Any` solely to silence mypy;
- no `# type: ignore` unless a specific unavoidable third-party typing defect is independently demonstrated and narrowly documented;
- no skip/delete/assertion weakening;
- no mypy config/CI command/exclude/override relaxation.

Required validation:
1. baseline `mypy src tests` => exact 27 errors;
2. candidate `mypy src tests` => clean;
3. focused pytest for all five touched files;
4. full pytest;
5. Ruff;
6. format/diff check;
7. hosted CI on exact candidate if available;
8. return exact SHA/tree and READY_FOR_LEAD_REVIEW.

### Engine composition remains held

Do not resume `src/jobs_automation/ingestion/engine.py` COMP-2 until COMP-2B-TYPING receives a formal exact-SHA acceptance with full `mypy src tests` green.

No bounded.py/provenance/lifecycle/worker/dashboard work in parallel.

No live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, Fable/Claude dispatch, or main merge.


## 14. COMP-2B typing verdict and COMP-2 engine activation

### COMP-2B-TYPING

**ACCEPTED** exact source:
- SHA `bfc507903452d32d979cfb7b8c78f5ac916fa305`
- tree `4c3bfa242b34912066c0470efb8745f5ae22b3ad`
- parent `1b9efdda418baa059903215349e27493cf709f3a`

Accepted scope only:
- `tests/test_crm_corrections.py`
- `tests/test_bounded_ingestion_scope.py`
- `tests/test_candidate_reply_attribution.py`
- `tests/test_auto_application.py`
- `tests/test_dashboard_health_badge.py`

Evidence:
- exact parent baseline: 27 `mypy src tests` errors;
- candidate `mypy src tests`: clean, 118 files;
- focused: 46 passed;
- full: 530 passed / 1 existing host skip;
- owned PostgreSQL proof integration cleanup0;
- Ruff/format/diff clean;
- independent normalized AST review retained 29 tests and 145 existing assertions; five explicit non-null narrowing assertions added.

Hosted exact-head status at acceptance time: **NO RUN YET**. No hosted-green claim is made. Hosted CI remains supplemental for this exact candidate and should be read back when/if GitHub starts it.

No production/config/CI behavior changed.

## COMP-2 ENGINE — ACTIVE

Current direct integrator: **Codex**.

Integration base for this pass:
`bfc507903452d32d979cfb7b8c78f5ac916fa305`
(which includes accepted COMP-2A + accepted COMP-2B typing cleanup)

Reference accepted canary behavior source:
`eec0ae3d9b50979b74294dd9ee0561172eff54b0`

Reference-only bounded semantics:
`2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a`

Allowed production file only:
- `src/jobs_automation/ingestion/engine.py`

Expected focused test files:
- `tests/test_gmail_adapter_bounded.py`
- `tests/test_bounded_ingestion.py`
- `tests/test_canary_provenance.py`
- at most one additional existing test file if strictly required to exercise an engine-owned behavior.

### Required preservation from control/base

Preserve all accepted control-line engine behavior, especially:
- incomplete-poll atomicity and checkpoint hold semantics;
- existing deduplication/job discovery behavior;
- candidate-reply/outbound attribution path, including `_link_candidate_reply` and thread-reply attribution semantics;
- no checkpoint advance on incomplete/missing/truncated poll evidence;
- existing control error/reporting behavior unless `safe_errors=True` explicitly selects the accepted bounded-safe category path.

### Required canary API/behavior port

Add/preserve the accepted canary engine contracts:
- `canonical_email_addresses`;
- `is_durable_canary`;
- `persisted_message_matches_canary_policy`;
- `mark_durable_canary`;
- `reclassify_persisted_canary_messages`;
- `IngestionSweepSummary.batch_canary_provider_message_ids`;
- `EmailIngestionEngine(..., safe_errors: bool = False)`;
- canonical exact-address canary matching, not substring matching;
- runtime canary membership tracking for dry-run/bounded evidence;
- duplicate/historical canary reclassification behavior;
- safe error categorization only when `safe_errors=True`.

### Explicit composition rules

- Do **not** replace `engine.py` wholesale with the canary branch version.
- Build a deliberate semantic merge preserving control-only candidate-reply/outbound attribution and incomplete-poll behavior.
- Do not modify `bounded.py`, `db/canary_provenance.py`, lifecycle, CRM, alerts, worker, dashboard, CLI, migrations, config, Gmail adapter, or CI in this pass.
- If another production file is required, STOP with `COMP-2_ENGINE_REWORK_FOUND` and exact dependency.

### Required focused regressions

At minimum prove:
1. malformed neighboring headers from accepted COMP-2A still produce recipients that exact-address canary matching recognizes;
2. display/case canary aliases canonicalize and match;
3. lookalike substring addresses do not match;
4. runtime canaries are tracked in `batch_canary_provider_message_ids`;
5. duplicate historical messages matching current canary policy become durably tagged on non-dry runs;
6. dry-run canary membership is tracked without relying on persisted tag;
7. incomplete poll/missing message/cap truncation still prevents ordinary writes/checkpoint advancement as accepted;
8. control candidate-reply/outbound attribution tests remain green;
9. `safe_errors=False` preserves existing worker-facing behavior while `safe_errors=True` returns only accepted bounded-safe categories.

### Validation

Run:
- focused engine/Gmail/bounded/canary tests;
- candidate-reply attribution tests;
- incomplete-poll atomicity tests;
- full pytest;
- Ruff;
- `mypy src tests`;
- affected PostgreSQL proof/integration checks as needed;
- format/diff check.

Return exact SHA/tree and `READY_FOR_LEAD_REVIEW` or `COMP-2_ENGINE_REWORK_FOUND`.

### Still held

Do not open:
- `bounded.py` V3/reference integration;
- `db/canary_provenance.py`;
- lifecycle/alerts/CRM conflict composition;
- worker/dashboard/CLI conflict composition;
- live G14-G17 execution.

No Fable/Claude dispatch, live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, or main merge.


## 15. COMP-2 engine verdict and COMP-3A bounded.py activation

### COMP-2 ENGINE

**ACCEPTED** exact source:
- SHA `0a319d07df4d679de7b32f84fbd9faf215037881`
- tree `f98b225bceb687238a8bbea59ce08934750cf7f5`
- parent `bfc507903452d32d979cfb7b8c78f5ac916fa305`

Accepted scope only:
- `src/jobs_automation/ingestion/engine.py`
- `tests/test_bounded_ingestion.py`
- `tests/test_gmail_adapter_bounded.py`

Preserved control behavior:
- incomplete-poll guard before writes/checkpoint advancement;
- rollback/checkpoint hold semantics;
- ordinary deduplication/discovery;
- outbound candidate-reply attribution via `_link_candidate_reply`;
- `thread_reply_attribution` semantics;
- existing recruiting-message attribution.

Integrated accepted canary behavior:
- canonical exact-address helpers;
- durable canary detection/tagging/reclassification;
- runtime canary membership;
- dry-run/duplicate canary membership;
- fresh canary quarantine before ordinary links/tasks/activity;
- opt-in `safe_errors` categories.

Evidence:
- 56 focused pass;
- full 545 pass / 1 existing host skip;
- owned PostgreSQL proof integration cleanup0;
- Ruff clean;
- full `mypy src tests` clean, 118 files;
- format/diff clean;
- independent exact-tree review recommends acceptance.

Hosted status: **NO MATCHING RUN / NOT HOSTED GREEN** for the stacked target. No workflow was weakened or modified.

## COMP-3A-BOUNDED — ACTIVE

Current direct integrator: **Codex**.

Starting integration parent:
`0a319d07df4d679de7b32f84fbd9faf215037881`

Accepted bounded/V3 source reference:
`eec0ae3d9b50979b74294dd9ee0561172eff54b0`

Accepted reference-semantics patch:
`2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a`
(REFERENCE_ONLY, exact bounded semantics accepted previously)

Allowed production file only:
- `src/jobs_automation/ingestion/bounded.py`

Allowed focused tests:
- `tests/test_bounded_ingestion.py`
- `tests/test_bounded_ingestion_scope.py`
- `tests/test_bounded_reference_scopes.py` (may be added/ported as focused test-only reference coverage)
- at most one additional bounded-specific test file if strictly necessary to prove replay contract behavior without modifying another production conflict.

Do **not** modify:
- `src/jobs_automation/db/canary_provenance.py`;
- lifecycle/alerts/CRM;
- worker/dashboard/CLI;
- engine.py;
- Gmail/config;
- migrations/CI.

### Required V3/replay composition

Port the accepted canary bounded contract deliberately, not wholesale if it would regress control behavior:
- strict bounded audit schema v3;
- secret-safe request/query/provider-query hashes;
- canary policy fingerprint;
- strict persisted audit validator;
- replay capability gate;
- replay request/mailbox/adapter/policy matching;
- current-canary/reclassified-canary preflight;
- **reclassified canary replay must reject before any new adapter poll/list call**;
- error-first replay status semantics;
- provider/application hash evidence;
- exact current-batch confinement.

### Required frozen reference semantics

Implement the already accepted PR27 behavior exactly:

1. **Genuine/proof batch set**
   - exact current batch only;
   - exclude runtime/durable canaries;
   - include genuine `JOB_ALERT`.

2. **Lifecycle set**
   - genuine/proof set minus `JOB_ALERT`;
   - only this set enters `LifecycleEngine.process_message()`.

3. **Unanswered-recruiter alert scope**
   - thread IDs only from lifecycle-eligible messages.

4. **Stale-application alert scope**
   - resolve application IDs **after lifecycle processing**;
   - only from links attached to lifecycle-eligible message IDs.

5. **Proof application attribution**
   - resolve separately after lifecycle from all genuine/proof message IDs, including genuine `JOB_ALERT`;
   - never reuse proof IDs as alert eligibility.

6. **Provider-message proof**
   - all genuine/proof current-batch messages including JOB_ALERT, excluding canaries.

### Preserve control-side safety

Do not regress:
- bounded runs never advance the ordinary worker checkpoint;
- incomplete poll evidence remains fail-closed;
- dry-run behavior;
- lifecycle exceptions roll back safely;
- existing logical-state digest/replay intent where not superseded by the accepted V3 contract.

### Required regressions

At minimum:
1. JOB_ALERT included in provider/application proof but excluded from lifecycle and both alert scopes;
2. lifecycle-created/repaired link is visible to post-lifecycle stale-alert scope;
3. proof application IDs remain separate from alert application IDs;
4. runtime/durable canaries excluded from proof/lifecycle/alerts;
5. outside-batch messages/links excluded;
6. dry-run remains non-mutating while proof selection semantics stay truthful;
7. reclassified-canary replay => `REPLAY_EVIDENCE_CANARY_RECLASSIFIED` with **0 new polls/list calls**;
8. malformed/legacy V3 evidence fails before replay poll;
9. policy fingerprint mismatch fails before poll;
10. ordinary successful bounded run still records strict valid V3 audit metadata.

### Validation

Run:
- focused bounded/replay/reference tests;
- full pytest;
- Ruff;
- `mypy src tests`;
- format/diff check;
- owned PostgreSQL proof integration if the bounded suite exercises it;
- no hosted-green claim unless an exact-head workflow actually runs.

Return exact SHA/tree and `READY_FOR_LEAD_REVIEW` or `COMP-3A_REWORK_FOUND`.

### Still held

Do not open:
- `db/canary_provenance.py`;
- lifecycle/alerts/CRM composition;
- worker/dashboard/CLI composition;
- G14-G17 live execution.

No Fable/Claude dispatch, live Gmail/OAuth, browser/application action, model/provider call, scheduler/timer change, spend, deployment, or main merge.

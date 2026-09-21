# Lead review: contract gaps before the next execution round

Status: findings verified against main `927b33c0f523950ca206ead1cc2912e19a018184`; proposed corrections are isolated from running Fable work. This is a plan/code-contract audit, not a claim that the application's test suite was run here.

Pinned source root: https://github.com/pri8771/jobs/tree/927b33c0f523950ca206ead1cc2912e19a018184

## Summary

The existing plan has useful feature decomposition. Its biggest remaining risk is contradictory semantics and tests that can validate their own assumptions. More words alone will not close those gaps. The corrective task registry maps every change back to existing artifacts/tasks; no valid feature work is discarded.

### F01 — Competing governance writers

Evidence: `AGENTS.md` describes three active lanes while `docs/V23_MASTER_PLAN.md` and `docs/V23_LEAD_REVIEW_20260921.md` prescribe one active worker. The current heartbeat identifies Fable's actual implementation branch separately from the historical heartbeat branch.

Risk: subsequent lead runs restore incompatible instructions, stale assignments and repeated branch churn. A local process check does not prove another host has no watcher.

Correction: H-GOV-01. Freeze revision/ownership once at a safe handoff; reject stale-base writes; reconcile scheduled prompts and other writers without altering this running session.

### F02 — Mutable candidate identity defeats deduplication

Evidence: `docs/V23_TASK_GRAPH_RECOVERY.md` R16-I01 defines candidate identity as a hash of the whole profile; `docs/V1_6_DATA_CONTRACTS.md` also suggests version-dependent identity. `docs/V1_6_SUBMISSION_CONTRACT.md` includes packet in an idempotency key, whereas the recovery task excludes it.

Risk: changing a resume, profile field or version can make the same human/job look like a new permissible submission. Shared ATS domains and tenant-local job IDs also require tenant scoping.

Correction: H-ID-01. Stable candidate subject + canonical employer/provider opportunity identity; separate snapshot hashes from duplicate identity.

### F03 — Active-only uniqueness and late approval consumption

Evidence: R16-I03 indexes only PREPARED/AUTHORIZED/PREFLIGHT_VALIDATED/REQUEST_DISPATCHED/SUBMISSION_UNCONFIRMED. R16-C04 consumes approval after confirmation. No durable logical claim spanning confirmed history is specified.

Risk: confirmed rows leave the active uniqueness set; concurrent attempts can reuse a still-active approval. An application-row check alone is not a durable concurrent guarantee.

Correction: H-ID-02, H-AUTH-03, H-SUB-01. One logical claim, atomically reserved approval before dispatch, durable uncertain outcomes, no blind retry or rollback that erases an external action.

### F04 — Action vocabulary and caller-supplied authority

Evidence: R16-A01 `action_class` uses SUBMIT_APPLICATION/SEND_MESSAGE values while V23-TL-01 uses P0–P4 in `action_class`. V23-TL-03 trusts context fields and uses a target superset comparison; required nonempty targets/hashes and a trusted principal derivation are not fully defined. TL-11 treats non-exported Python handlers as an anti-bypass check.

Risk: incompatible models, vacuous empty-set matches, self-asserted authority, and a false security claim about module exports.

Correction: H-AUTH-01/02/04. Distinct action_kind/permission_level, authenticated principal, required exact target contract, service-level enforcement and an explicit threat boundary.

### F05 — PARTIAL replay becomes SUCCEEDED

Evidence: V23-TL-05 expressly says a prior SUCCEEDED or PARTIAL result returns SUCCEEDED on replay, then says PARTIAL must never be upgraded. This is a direct contradiction.

Correction: H-TOOL-01/02. Preserve original state and result evidence; namespace keys; authorize before private result replay; cache metadata is not a new success.

### F06 — Generic tool transaction conflicts with external effects

Evidence: V23-TL-05 specifies one transaction per invocation with rollback on handler failure. V23-TL-09 wraps application execution in that runtime.

Risk: a remote submit can occur even when the encompassing local transaction is rolled back. Retrying can send the application twice.

Correction: H-TOOL-03, H-SUB-01. Atomic local writes/result persistence for P1; separate durable attempt service for P2/P3, commit intent before network I/O and reconcile uncertain outcomes.

### F07 — Confirmation can still be asserted by a flag

Evidence: R16-C04 makes `independently_validated=True` part of acceptance without completely defining the independently verified source-to-application association.

Correction: H-SUB-02. Validation is a service output from correlated external evidence, never an input flag accepted on trust. Generic HTTP success, a generated receipt or unrelated confirmation does not prove submission.

### F08 — Manual application contract contradicts its own test

Evidence: J20-15 requires SUBMISSION_UNCONFIRMED but its Tests line says analytics counts it as a real submission (`_is_real_submission` true for mode manual). It also sets applied_at from reported_at, conflating reporting with externally verified occurrence.

Correction: H-SUB-03, H-AN-01. Separate reported/claimed/confirmed timestamps; maintain reported count separately; confirmed denominators require accepted external evidence. Unknown historical resume attribution stays unknown.

### F09 — Gmail plan omits additional production ingestion defects

Code evidence: `src/jobs_automation/adapters/gmail.py`:
- `poll_messages` makes one list call and does not process nextPageToken;
- `get_message` returns None on any exception;
- `_parse_gmail_message_payload` hard-codes direction=inbound;
- it replaces provider internalDate with the RFC Date header when parseable.

The existing J20G-01 addresses missing-message fetches but not the complete paging/direction/time contract.

Correction: H-MAIL-01/02. Bounded complete pagination, no checkpoint advance on incomplete results, SENT/verified-identity direction, separate trusted provider and message-stated timestamps.

### F10 — Canary instructions may invoke an unrestricted production sweep

Evidence: `docs/V2_3_ACCEPTANCE_CAMPAIGN.md` uses `jobs-automation worker --once` as real ingestion after describing a bounded canary. The command's effective scope is not bound in that procedure. J20G-03 uses a report with Literal REAL even when connectivity can fail.

Correction: H-MAIL-03/04. Carry query/window/cap/account authorization into actual ingestion; cache sanitized readiness; distinguish configured, connected, canary-proven and real-workflow-proven. Readiness never initiates OAuth interactively.

### F11 — Proof report shape and code identity are circular

Evidence: the V2.3 live runbook redirects `jobs-automation briefing --json` directly into the campaign report filename, despite separately specified briefing and campaign schemas. The verifier requires `code_sha == git rev-parse HEAD`; committing evidence changes HEAD.

Correction: H-PROOF-02/05. A real campaign runner builds the report and references the briefing. Pin runtime code/tree/dependencies separately from receipt commit. Do not hand-edit reports to match newer HEAD.

### F12 — The proposed live verifier can validate fabricated but consistent summaries

Evidence: V23-AC-02 checks schema, simulated flag, forbidden words, entity ID resolution and rate arithmetic. It does not explicitly require recomputing complete counts, cohorts and source-to-artifact relationships from the declared run snapshot.

Risk: real entity IDs plus invented internally consistent metrics could pass. A keyword-free fixture is not real evidence; a legitimate role description may contain the word mock.

Correction: H-PROOF-03/04. Typed evidence origins, actual producer-consumer positive test, independent reread/recomputation, nonempty mandatory checks and a separately bound receipt. Correlated hashes alone do not prove trusted origin.

### F13 — Follow-up path is excluded by the briefing's candidate filter

Evidence: V23-CB-02 selects jobs without a non-terminal application, then contains an existing-application follow-up branch. It also combines latest persisted evaluation scores with newly recomputed reasons.

Correction: H-UI-01. Separate unapplied opportunity ranking and active-application action queue. Bind rationale and scores to one evaluation/profile/source snapshot.

### F14 — Migration, optional-proof and validation wording remain inconsistent

Evidence: PHASE_GATE_MATRIX calls V1.5 real proof optional, while the accepted lead review makes it mandatory. The older migration plan introduces a separate submission_authorization and later scoped_approval; the master plan uses generic scoped_approval in V1.6. V23-TL-03 still says approval storage arrives in migration 005 whereas TL-09 says 004. J20-18 still claims numeric migration 006 for optional indexes, conflicting with reserved V3 wording. J20-12 allows migration checks to skip when no DB exists.

Correction: H-GOV-01, H-OPS-01. One effective gate/migration contract; read actual Alembic head and never edit applied migrations. Production DB validation cannot be silently skipped for release. Preserve the accepted live-proof requirements, not optional wording from an older file.

### F15 — Happy-path fixtures can encode the same bug as the verifier

Evidence: current `state/CURRENT.md` records previous verifier `origin` versus production `generation_origin` and driver-qualified PostgreSQL URL mismatches; the earlier tests mirrored their own metadata shape rather than the real producer.

Correction: H-PROOF-01. At least one positive integration test executes the actual importer, builder, exporter and verifier on the installed production stack. Engineering fixture inputs are explicitly labelled and cannot satisfy real proof. Do not interrupt Fable to implement this twice if its current fix already supplies equivalent coverage.

### F16 — Runtime access is still an unproven premise

The plan calls for a first allowed Greenhouse/Lever submission transport. Public job discovery does not establish the required application write credentials.

Primary-source verification on 2026-09-21:
- Greenhouse Job Board API documents unauthenticated GET endpoints and authenticated application POST with a Job Board API key: https://docs.greenhouse.io/job-board.html#authentication
- Lever Postings API documents application POST with a key generated by the account's Super Admin: https://github.com/lever/postings-api#apply-to-a-job-posting

Correction: H-ACCESS-01. Establish an eligible method, credential owner/access and confirmation signal before implementation. This is not a blanket finding that every browser workflow is forbidden; each actual method needs current policy review. Do not infer candidate access to an employer's API keys.

### F17 — Endpoint smoke tests do not establish an operable product

Evidence: J20-04 concentrates on HTTP/JSON responses. The live requirement is that the owner can operate the system, recover it and trust its state.

Correction: H-UI-02, H-OPS-02/03. Actual browser/CLI flow, restart, bounded replay and a separate nonempty DB+artifact restore. No need for a UI framework rewrite or new infrastructure merely to add these tests.

## Additional primary-source checks

Gmail users.messages.list has pageToken/nextPageToken and bounded page sizes: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list
Gmail internalDate is provider ordering metadata and is generally more reliable than the Date header for ordinary SMTP-received messages, with a documented migrated-mail caveat: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages

These sources justify paging/time safeguards, not authorization to read the owner's mailbox. No OAuth, mailbox read, account creation, application submission or external test message was performed in this review.

## Scope and confidence

Confirmed contradictions are cited above. Where a finding concerns a proposed service, it is a design defect, not a claim that deployed code already exhibits the defect. The live worker may have advanced since the snapshot; activation requires reconciliation. This review did not run the Jobs application tests or validate a genuine application proof.

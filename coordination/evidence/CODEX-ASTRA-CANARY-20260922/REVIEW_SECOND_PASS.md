# Independent repaired-tree Jobs review — 2026-09-22

Recommendation for staged tree `22fdb2696c8b04b3385da1c746fd2297752580af`: **REWORK_REQUIRED**, narrowly for replay canary-policy canonicalization below. This is an engineering recommendation to the lead, never formal acceptance or G14-G17 live proof.

Exact base HEAD: `7685f811ec5e41df789e6df82f948669e5e35fe2`. Source frozen by root during this review. Staged tree checked at beginning and end; no unstaged changes and `git diff --cached --check` clean. Reviewer made no source edits or external calls and did not duplicate full verification.

## Closed P1 header issue

The staged changes parse independent participant/header values separately in the shared canonicalizer and Gmail To/Cc parsing, and reject invalid configured canary identities. Independent rerun of the original offline adapter + SQLite reproduction now returns fresh classification True, historical match True, reclassification count 1, durable tag True. Output: `repaired_header_output.txt`. Root's PostgreSQL log was inspected; all From/Cc/To cases report migration exit 0, fresh-process exit 0, cleanup database count 0. This is local engineering evidence.

## P2 remaining: replay preflight uses noncanonical aliases and polls before rejection

Locations: `src/jobs_automation/ingestion/bounded.py:697` stores raw configured identities; `:734` passes them to `persisted_message_matches_canary_policy`, which requires canonical addresses. Preflight at `:1005-1008` therefore fails to detect an untagged historical canary with an unchanged display-name/case alias policy. Policy fingerprinting is canonical, so it does not rescue this case.

Offline causal reproduction retained in `replay_policy_probe.py` / `replay_policy_output.txt`:

1. Use policy `['Owner <OWNER+CANARY@example.com>']` and a real GmailAdapter payload parser backed by the existing FakeGmailService; no network.
2. Temporarily restore only the pre-repair aggregate canonicalizer in process to generate a historical audit for malformed From + valid canary To. Original audit SUCCESS, canary count 0, stored tag False.
3. Restore repaired canonicalizer and construct new runner with unchanged policy. Fingerprints equal; canonical current-policy match True; `_audit_references_current_canary` False.
4. Stateful replay performs **one new adapter list/poll call**, durably tags the message, then returns FAILED with `REPLAY_EVIDENCE_CANARY_RECLASSIFIED` and `REPLAY_LOGICAL_STATE_MISMATCH`.

The replay is ultimately not accepted as proof, but preflight fails its explicit before-poll contract and unnecessarily accesses the mailbox. The preceding policy-fingerprint check does not make this unreachable across the actual parser upgrade. The prior review's optional observation #3 needs correction.

Smallest repair: canonicalize `self.canary_identities` once in the bounded runner constructor (a deterministic list is appropriate) so fingerprinting, replay preflight and execution share the same policy. Focused regression should establish a historical untagged message + canonical-equivalent display/case policy and assert the expected `REPLAY_EVIDENCE_CANARY_RECLASSIFIED` before any adapter poll.

## Remaining requested areas reviewed

- Durable closure: source tags -> provider/UUID references -> direct links and legacy events -> jobs/applications -> tasks/interviews/contacts; direct/batch evaluation and packet/assisted/auto engines gate before operational actions.
- Worker and CLI preflight: active configured aliases supplement CLI aliases, historical tags persist before consumers, invalid configuration blocks, four status commands filter closure, dashboard and health startup perform reclassification.
- Lifecycle/alerts/CRM: directly durable canary messages stop at shared lifecycle entry; inbound/outbound alerts exclude them; six task provenance keys prevent canary task reuse/resolution; stale reminders exclude application links and provider-source events; CRM omits direct durable canary messages.
- V3 audits/replay: exact field set, request hash, canonical dates/hash lists, digests, status/error consistency, caller replay authorization and private capability; timeline selects latest mentioning audit and rejects legacy/malformed shape and current canary sources. The concrete remaining replay issue is above.
- Dashboard/API/analytics/health: traced changed read routes and task resolution gate to shared closure; funnel/source/role/resume/kanban/time-to-stage filters, contact/application timelines, pending task and last-message health filtering. No additional specific production-path leak reproduced in this pass.
- Synthetic evidence: CLI fixtures explicitly mark synthetic adapter runs; timeline retains synthetic/adapter flags; local tests and PostgreSQL probes are not claimed as genuine live proof. This review does not qualify external model, browser/application, Gmail, scheduler, or G14-G17 gates.

Known existing limit from earlier review remains: job-only canary provenance quarantines operational gates and visibility, while genuine lifecycle messages can update hidden application state, and timeline uncertainty is message-scoped. No blanket claim of full runtime immutability should be made. This was not expanded into a new repair during this pass.

Full checks are root-owned evidence, reported separately by root; reviewer inspected relevant source/tests and PostgreSQL reproduction log and performed only the two bounded offline probes above.

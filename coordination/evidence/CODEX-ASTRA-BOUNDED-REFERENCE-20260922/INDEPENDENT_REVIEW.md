# Independent exact-tree review — bounded reference behavior

Recommendation: **RECOMMEND_ACCEPT_FOR_LEAD_REVIEW — REFERENCE_ONLY**.
Reviewer role: bounded independent mechanical source/evidence reviewer; not formal acceptance authority.
No concrete defect found within the released reference-only scope.

## Exact review target

- Base: accepted canary b2688eeabb5ca996767b27b78d0004678eeee756, tree 6644f340b98eae517ae08ccde38a28da5f2c52a9.
- Reviewed staged tree: 9e34b5c8e56ca501f84f6b0f7451aead34cf412e.
- Worktree: /tmp/jobs-astra-bounded-reference-20260922.
- Release: e5629e8 adjusted reference-only assignment, retaining d75f0c14ce583a9a1e5aae84550c9d23b467605c frozen semantics.
- Only production change: src/jobs_automation/ingestion/bounded.py.
- Only added test: tests/test_bounded_reference_scopes.py.
- Index matches worktree; staged diff check passed. Worktree has the expected two staged files and is not yet a clean committed candidate as of this inspection. No review claim of a final source commit.

## Behavior inspection

The existing current-batch loader and durable/runtime canary filtering remain byte-for-byte unchanged. The new lifecycle_messages list derives from that genuine batch while excluding JOB_ALERT. Only this narrower list enters lifecycle processing; unanswered-recruiter thread IDs come from the same list.

Stale-alert application IDs are now resolved from lifecycle_message_ids after lifecycle processing. This permits a created or repaired MessageLink to participate without widening scope to a JOB_ALERT or an outside-batch message. The helper constrains its query by exactly the supplied inbound message IDs.

Proof application IDs are separately resolved after lifecycle from all genuine_ids, including genuine JOB_ALERT. They populate only application_id_sha256; they are not reused for alert scope. Provider-message proof still uses the unchanged full genuine batch.

Dry-run does not enter lifecycle/alert processing; its existing genuine-message/proof selection and error-first result status remain intact. Exception handling still rolls back lifecycle before proof linkage is re-read. The patch does not edit strict V3 validation, canary-policy fingerprinting, replay capability state, current-canary preflight, provider polling, or error-first replay status behavior.

## Evidence inspected, not independently rerun

- red.log records 3 failed/1 passed on the prior behavior: real JOB_ALERT alert-scope widening plus missing newly created/repaired link scope. The dry-run case already passes. These are relevant causal regressions rather than implementation-mirroring assertions.
- green.log records **36 passed in 2.27s**, not 54. It covers the new four parameterized cases plus the affected bounded-ingestion suite per the integration owner's execution record.
- New tests use real persisted SQLite message/application/link queries while stubbing ingress and observing lifecycle/alert call boundaries. They prove the bounded orchestration contract, not external mailbox or genuine recruiting proof.
- Existing test_replay_canonicalizes_policy_before_any_poll_of_legacy_canary remains unchanged. It records FakeGmailService list_calls before replay, requires REPLAY_EVIDENCE_CANARY_RECLASSIFIED, and asserts no additional list call. Existing malformed-V3 and other replay guards also remain unchanged.
- ruff.log: All checks passed.
- mypy.log: Success, no issues in 75 source files.
- No tests were rerun by this reviewer; source diff, tests, saved red/green logs and relevant unchanged replay code were independently inspected.

## Scope boundary

This recommendation is only for the exact reference patch tree. It does not establish compatibility with b67fc523, accepted-source composition, any engine conflict resolution, or resolution of the remaining seven held conflicts. The original /tmp/jobs-astra-composition-20260922 worktree was verified clean at b67fc523863babd3e195ee71a05f00fa0f2f7e79 and remains untouched.

No production code/config/test edit, model/provider/mailbox/browser/application action, scheduler change, spend, deploy, main merge or Fable dispatch was performed by this reviewer. G14-G17 remain unpassed. Formal lead verdict and root's committed-source/evidence binding remain outstanding.

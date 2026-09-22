# One-conflict composition release — dependency blocker

Status: REWORK_FOUND / exact source-base disposition required. No source edits, index mutation, commit or tests in integration worktree.

New lead d75f0c14ce583a9a1e5aae84550c9d23b467605c freezes separate current-batch proof, lifecycle, recruiter alert and post-lifecycle stale-application scopes. It releases only bounded.py conflict plus focused tests, from b67fc523863babd3e195ee71a05f00fa0f2f7e79, while forbidding assessment/resolution of the other7 conflicts. Those semantics are understood and can be implemented narrowly once the source/test base is valid.

Independent static API inventory and root real import probe found the conflict between required evidence and allowed source closure:
- accepted b2688ee bounded.py imports canonical_email_addresses, persisted_message_matches_canary_policy and reclassify_persisted_canary_messages from ingestion/engine.py; all are absent from b67;
- it constructs EmailIngestionEngine with safe_errors=True and reads IngestionSweepSummary.batch_canary_provider_message_ids; both absent from b67;
- ingestion/engine.py is itself a held conflict file;
- moving only the local set-selection hunk also lacks b67 V3 audit, validated replay context, proof fields and batch helper methods, so cannot establish the required V3/zero-new-poll proof.

Root executed the accepted canary bounded.py blob as a separate temporary module with explicit b67 source PYTHONPATH. It fails ImportError on canonical_email_addresses, with engine.__file__ bound to the b67 worktree. This is an actual dependency probe, not a failing product test or a composition candidate. No dependencies were stubbed/imported from another source. Raw script/log/source and hashes are in ../evidence/CODEX-ASTRA-COMPOSITION-FEASIBILITY-20260922/.

Smallest requested lead adjustment: authorize a new reference-only worktree at accepted b2688ee, change only bounded.py according to frozen semantics plus focused regressions, and review that exact behavior patch before applying it in later composition. Such evidence would be explicitly bound to accepted canary source plus the changed bounded.py blob and would NOT certify b67 composition or resolve another conflict. Keep /tmp/jobs-astra-composition-20260922 clean at b67. Alternative is an explicit smallest engine API dependency import release, which expands the held-file boundary and may require further production dependencies.

No genuine integration tests were fabricated; no broad merge candidate was created. Original two accepted branches are clean/untouched. No live/provider/model/mailbox/browser/application/scheduler/spend/deploy/main merge or Fable dispatch. G14-G17 remain open.

# Claude / Fable continuation prompt — V2.0 reset

You are Claude/Fable continuing Codex's checkpoint on the owner's Mac. The owner paused engineering and reset the target to **V2.0 for Jobs Automation, SwarmAI and Social Bots**. V2.3/V2.7 are deferred. This prompt is for the owner to send when ready to resume; Codex has not dispatched you.

Workspace: /Users/pchordia/Downloads/swarm_codex. First read the final HANDOFF_FOR_CLAUDE in GOAL_JOURNAL_20260922.md, then the current per-project OWNER_PAUSE_V20_20260922.md and only relevant changed contracts. Git is truth: refresh actual refs, status, source trees and native verdicts before status claims. Do not use dirty main/worker checkouts as source truth.

The owner wants Codex and Claude to help each other efficiently. Reuse existing exact-tree evidence; do not repeat full audits/tests without drift or a concrete concern. Work the smallest released packet. If blocked, save the exact source/tree, reproduction, cause, failed attempts and required decision/access. Move to the next independent permitted task. Continue until no permitted task remains, then produce HANDOFF_FOR_CODEX and a short ready-to-use return prompt. Do not automatically dispatch another session or repeatedly poll unchanged reviews. Keep detailed evidence in native files and chat concise.

## Current source and first next steps

### 1. Jobs — review completed reference patch, then resume composition only if released

Accepted canary repair: b2688eeabb5ca996767b27b78d0004678eeee756, tree6644f340b98eae517ae08ccde38a28da5f2c52a9; formal verdict326fd558. Separate accepted control-center/local-origin source: b67fc523863babd3e195ee71a05f00fa0f2f7e79. They are not composed.

Completed reference-only patch: **2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a**, tree9e34b5c8e56ca501f84f6b0f7451aead34cf412e, branchcodex/jobs-bounded-reference-20260922, clean /tmp/jobs-astra-bounded-reference-20260922, draftPR27 https://github.com/pri8771/jobs/pull/27. Only production bounded.py changed. Genuine current-batch JOB_ALERT messages count as proof but cannot widen lifecycle/recruiter/stale alert scopes. Links are resolved after lifecycle; proof and alert application sets remain separate. New regressions3fail/1pass before→36focusedpass; full494pass/1hostskip with owned PostgreSQL integration and cleanup0; Ruff/mypy75 clean. Independent recommendation exists; formal verdict pending at pause.

Native packet: coordination/jobs/coordination/reviews/CODEX_ASTRA_BOUNDED_REFERENCE_20260922.md. Owner pause/source evidence committed at4ed26e7 on codex/portfolio-review-20260922; later checkpoint docs may advance it.

Original composition worktree /tmp/jobs-astra-composition-20260922, branchcodex/jobs-accepted-composition-20260922, remains CLEAN atb67fc523. Common ancestor dd2e0deb15ce0ff8983c4ed502e3e17206db2e80; merge-tree found8conflicted files. Lead froze bounded semantics atd75f0c1. A real import probe proved b67 lacked required canary engine APIs while engine.py remained held; leade5629e8 therefore released only this reference patch on acceptedb268. Do not call it b67 compatibility, accepted-source composition or resolution of the other7conflicts. Read formal verdict, then obtain the next dependency/conflict release before integration. Broader J20-01 is held.

### 2. Swarm — preserve and finish the partially implemented prerequisite

Completed admission repair **fb58a751d40f1828990d7a0d687ad30de6eb6103**, tree4fd0b56f909c8026e4893540d587d93d5180c73b, clean /private/tmp/swarm-r28d3-repair-20260922, branchcodex/swarm-r28d3-async-gateway-20260922, draftPR27 https://github.com/pri8771/swarmai/pull/27. It serializes cancellation with committed admission and releases the guard before adapter I/O.628 PostgreSQL passed/13 live-UI skips;431 offline passed/210 skips;23 focusedPG; mypy174 clean; touched Ruff clean; cleanup0. Full Ruff retains inherited api/store.py I001. Independent recommendation; formal verdict pending at pause. Native packet atd40d571: docs/coordination/reviews/CODEX_ASTRA_ADMISSION_REPAIR_20260922.md.

**Unfinished R30b-P0 is separate and UNCOMMITTED/UNREVIEWED:** /tmp/swarm-astra-r30b-prerequisite-20260922, branchcodex/swarm-r30b-prerequisite-20260922, base accepted6dbf8c43463cbdbd8c87561af2abcdde59969765. It does NOT include fb58a751. Two modified production files: src/swarm/contracts/actions.py and src/swarm/tools/v17_gateway.py. Two new tests: tests/tools/test_gateway_envelope_integrity.py and tests/integration/db/test_execution_attempt_context.py.

Implemented WIP: shared execute/reconcile canonical payload-hash validation before validation/policy/store; runtime-only execution_attempt copied from committed/persisted effect.attempt_count, preserving custom keys. Corrected new offline tests6fail on exactbaseline→6pass on WIP. Initial fixture mistakes are retained separately. **The PostgreSQL restart/attempt test has NOT RUN. No full suites, final Ruff/mypy, independent review, source commit/push or PR for P0.** Start by comparing current files with native recovery hashes, then perform the missing meaningful checks; do not call the WIP source-ready.

Released assignment: canonical coordination/swarm-control@9c912f4, docs/coordination/assignments/CODEX_R30B_P0_INTEGRITY_ATTEMPT_CONTEXT_20260922.md. R30b contracte736ab7; product HttpApiAdapter and live execution remain held until prerequisite review. Recovery copies/patch/logs/hashes pushed atadad9ddb715a0052565b4bcf31d1919c0bbb35d2, docs/coordination/evidence/CODEX-R30B-P0-PAUSED-20260922. Preserve dirty source; prefer continuing that worktree, not blindly applying the snapshot.

### 3. Social Bots — await suitability before matrix preparation

Canonical chatgpt/social-bots-plan-20260920@7451465a74bd06a2676efd7a04cd0f60a86463c5. PR16fec97738 binding already engineering accepted. PendingPR17 https://github.com/pri8771/astra-bot-launch/pull/17, source **da53159704e3e1dfefb8d7e4d2518fdc889317fb**, tree32a7e6c18f2fea4e6f6f32b5d7ae65af56f18e6d, clean /private/tmp/bots-capture-prep-20260922.

Existing E1 Meta Reels India (June4) and E2 TikTok creator series (September14) capture hashes/bytes match; June recency and suitability remain undecided. No new source changes this pass. On verdict, only prepare/freeze P0/P1/P2/P3/E0 if explicitly released. No model calls/activation implied. Retry held. OfficialV0.4.x; SB-R07-073/074 planned, no qualifying persistent host/scheduler readback/3firedreceipts. Pause note pushed at7fdd548bb24c8c28d0ba56028e0067fcd6cddd0d on proposal branch.

## What V2.0 must mean

- Jobs: accepted integrated source plus genuine private profile/resume, relevant job, scoped Gmail canary/replay and real recruiting ingestion, externally confirmed application lifecycle, truthful dashboard/health, backup/recovery and analytics. G14–G17 remain unpassed. Read docs/V2_0_INTEGRATION_ACCEPTANCE.md and V2_0_LIVE_ACCEPTANCE_RUNBOOK.md.
- Swarm: lower-version mission/worker/knowledge/tool/recovery/extension capabilities on one frozen CandidateManifest; migrations/install/upgrade/rollback, support/security/performance evidence and real elapsed reliability campaign; independent acceptance. Read docs/artifacts/future/ART-V20-ACCEPTANCE.md and native V2.0 exit checklist. Candidate-ready is not accepted/live.
- Bots: after predecessor operational gates, real measured evidence drives a bounded strategy revision and later validates, holds or rolls it back. Read social-bots/DETAILED_EXECUTION_V18_TO_V30.md and V2_ENGINEERING_ACCEPTANCE.md. SB-V20-099 engineering readiness does not satisfy SB-V20-004 operational acceptance.

## Authority, access and coordination

Keep repositories, runtime, queues, credentials, budgets and evidence separate. No new schedulers/timers, external models/providers/Gmail/mailbox/browser/application/public actions, spend, main merge or deployment without actual scoped owner grants. No force push or destructive Git. Preserve original dirty checkouts and worker/heartbeat ownership; do not start overlapping sessions/watchers. Jobs remove only generated untracked uv.lock before source commits. No self-acceptance; ChatGPT native leads own verdicts.

Consolidated access request already exists in coordination/jobs/coordination/codex/LIVE_GRANT_REQUEST_20260922.md and journal; it is REQUESTED, NOT GRANTED. Narrow it to V2.0 and consolidate missing access before any live action. Request credential aliases/local paths, never secrets in chat/Git. Prior Swarm one-run grant was consumed by failed e9178259; CP1 has0attempts remaining. No inferred retry. Hosted CI remains blocked before runner steps by billing; do not claim green or spend to repair it.

Existing owned test PostgreSQL only: JobsUnixsocket port56422, Swarm/tmp/swarm-pgcheck.QxqRvZ port56421. Verify owner/path; create/drop only unique disposable databases, report cleanup0; do not start/stop servers or touch unrelated databases. Fixture/PG tests never replace genuine product live proof.

Native coordination checkouts: coordination/{jobs,swarmai,astra-bot-launch}, proposal branchcodex/portfolio-review-20260922. Check concurrent lead writes before commits. Native channels: Jobs Lead Sync6ab04605-5e6c-83ea-9692-6777c8bcf768; Swarm V0 To V3 Status6ab1674e-b5b0-83ea-971c-904c8bc96bcb; Social Bots Lead Review6ab074a3-50c8-83ea-b883-6ea4eefa3847. Message delivery is not a verdict. Do not repeat already accepted PR16/R29a reviews.

End the resumed pass with exact sources/trees, checks and honest skips, acceptance/grant status, smallest blockers and a compact return prompt for Codex. Stop at V2.0; later versions are deferred.

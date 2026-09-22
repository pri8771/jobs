> **Latest owner assignment — 2026-09-22:** Claude is the next Jobs Automation implementation owner; target accepted LIVE V1.7. Read `coordination/codex/OWNER_RACE_V17_20260922.md` and `coordination/codex/CLAUDE_JOBS_V17_RACE_20260922.md` first. State: ASSIGNED_WAITING_FOR_WORKER, not launched. This supersedes older worker/pause routing below only; existing evidence, review holds and action grants are unchanged. No new scheduler or watcher.

# Owner decisions and goal post reset to V1.7 — Jobs — 2026-09-22 (~18:45Z)

Recorded by Claude from the owner's direct messages in the current Claude session. **This records owner direction only. It is not a lead verdict, a release or a version acceptance.** The native ChatGPT Jobs lead must reconcile `GOAL_20260922.md`, `state/CURRENT.md` and the work queue, and keeps acceptance authority.

## Owner messages (verbatim)

- To the two questions ("fix the one-line Swarm lint as its own change?" and "is public-repo Actions the intended CI route; R33c would now create a public issue"): **"1. yes, 2 yes."**
- **"If we havent reached 1.7 for any, then change the goal post for 1.7"**

## Decisions

1. **Target: V1.7.** Jobs has not reached V1.7, so V2.0, V2.3 and V2.7 are all deferred. Stop at an accepted V1.7. The V2.0-narrowed grant request (`LIVE_GRANT_REQUEST_V20_20260922.md`) is superseded for critical-path purposes by the V1.7 list below.
2. **CI:** public-repo GitHub Actions is the owner-confirmed zero-cost route. There is no billing change.
3. The owner pause is lifted for released work only. Every live/account/mailbox/browser/application/model/scheduler/spend/deploy/main-merge action still needs its own scoped grant.

## Where Jobs is (native evidence, adversarially checked)

- **Official:** V1.1, accepted 2026-09-20 (`c64e5a4:coordination/WORK_QUEUE.md`, `8e591f2:state/CURRENT.md`) before the real-proof policy (`ad4ebd2`). No version is COMPLETE/REAL_PROVEN. V1.2 is PARTIAL, NOT ACCEPTED and V1.3 is NOT ACCEPTED. `main@1a4efbb:state/CURRENT.md` says G14–G17 UNPASSED and "V1.7 is not COMPLETE".
- **Engineering:** V1.4 P0A (`8491dd9`) and V1.5 assisted-browser (`47fefd1`) are ENGINEERING_ACCEPTED and merged via PR12 as `7c0fa73`, under the CI_BLOCKED_ACCOUNT exception. This is not contiguous with V1.2/V1.3. V1.6 G16A is not accepted.
- **Accepted out of order and uncomposed:** canary `b2688ee` (326fd55), control-center `b67fc523` (c73dd36), reference `2969ac28` REFERENCE_ONLY (e74785c), golden fixture synthetic-only (0c89bc9).
- **Native V1.7 contract:** `main@5610f43:docs/FABLE_V17_LIVE.md` plus `PHASE_GATE_MATRIX_V14_TO_V30.md` G14A–G17. The lead's sequence is **G14 → G15 → V1.6 engineering + G16 → V1.7 reconciliation + G17 → milestone**. G14 does not need the b67/b2688ee composition. That composition matters for G17 (M01–M04) and the final integrated candidate.
- **CI facts:**
  - Main `1a4efbb` rerun `35678124379` was fully green: Ruff, `mypy src tests`, Alembic and pytest with the PG service.
  - PR26 `b2688ee` rerun `35757522343` now actually executed and fails `mypy src tests` with 22 test-typing errors (test_cli 15, test_worker 7). These come from the V1.7 lineage. The earlier record called that run an infra failure.

## V1.7 blockers

### Owner inputs and grants (aliases/paths only, never secrets)

| ID | Needed | Scope |
|---|---|---|
| G14B + G14-HOST | Genuine profile path, exact resume-bytes path, one current real job URL, private-use authority, eligible host with production-path connectivity (Greenhouse egress) | One importer → production packet → runtime candidate → separate verifier PASS. Only sanitized hashes/provenance are committed |
| PROOF-JOB | Select the proof job (A-PROOF-JOB-SELECTION is PROPOSED) | Also closes the V1.3 prerequisite |
| PACKET-UNRESOLVED | Owner review of consequential unresolved answers (sponsorship, authorization, history) | Required before G15 prefill or G16 submit |
| G15-LIVE | Logged-in visible browser; grant for one exact employer page | Prefill/upload from the accepted G14 packet; **stop before submit** |
| G16B | Exact job, account alias, packet hash and method; separate per-application approval | One AUTO_ALLOWED real system submission with correlated external confirmation. **A manual application does not count for V1.7** |
| GMAIL-CANARY | Mailbox alias, local read-only OAuth token path, query, UTC window, cap, canary alias | Dry run first, then ≤24h/≤5 messages. No send/labels/archive/delete/scheduling. Persistence needs its own approval |
| G17-LIVE | Separate genuine-recruiting query grant | ≤7 days/≤25 messages plus same-window replay |

### Lead verdicts and releases

1. Record the owner V1.7 goal post and lift the pause for released work. Re-open or re-scope the dormant V1.6 release on main, which names Fable, and **name exactly one implementation worker and its watcher** (FABLE §10).
2. **V16-TRANSPORT-POLICY:** answer the five hosted-form questions (ToS, scoped authorization, bot-challenge halt, ATS API use, confirmation signal). Otherwise the truthful state is BLOCKED_NO_ELIGIBLE_TRANSPORT.
3. Ruling on PR26 hosted `mypy src tests` (a test-typing packet, or re-scope of the CI gate).
4. Accept or rework A-V17-CRM-EVIDENCE and A-V17-INTERVIEW-FOLLOWUP (LEAD_REVIEW since 09-20). Map the synthetic golden fixture to the V1.7 MILESTONE card, or reject it. Rule on A-V12-CANDIDATE-PROVENANCE versus the P0A fingerprint.
5. Composition: release the COMP-2 `engine.py` canary-API dependency, then COMP-3 (the other 7 files). Re-scope the COMP-4 validation list to V1.7, dropping V2.0-only checks.
6. MAIN-INTEGRATION: rule whether an exact-SHA candidate suffices or whether it must integrate into main. Main merge is currently unauthorized.
7. G16A-REVIEW: independent safety review plus acceptance of A-V16-SUBMISSION-CONTRACT and ENGINE-REPAIR.

### Engineering (only after release)

- G16A: durable intent/claim ledger, scoped approval, confirmation validator, eligible adapter. ENGINE-REPAIR is IN_PROGRESS. V17-T01 is reported done but not accepted.
- V17-R01 engineering reconciliation card (READY, never delivered).
- V17-M01..M04 and R04/R05 on one composed tree, plus an installed-entrypoint restart/replay run.
- Test-typing fix for `tests/test_cli.py` and `tests/test_worker.py`, if released.
- FINAL-DELIVERABLE: evidence privacy check, known limitations, separate G17 verifier (R17-L09), stop the watcher at STOP.

**Smallest first moves:** owner supplies the G14 inputs and host; lead records V1.7 and names the worker; lead answers the transport policy; lead rules on PR26 CI.


## Current blocker correction — 2026-09-22 20:30 UTC

The “owner must locate career/profile/resume material” part of the G14 input blocker is resolved. Codex recovered and inspected the existing private career bank, keyword bank, application profile and source audits. Do not ask the owner to recreate that history. Personal material stays local; DYNAMIC_RESUME_CLARIFICATION_20260922.md points to the local-only source map.

Codex owns runtime-profile mapping, proposing a current proof job, preparing a truthful per-job resume and preserving exact packet provenance. The owner still confirms the consequential job choice/actions and answers only genuinely unresolved fields. Existing confirmed standard answers must be reused with their scope. Discovery is not yet a generated exact resume, a completed G14 proof, or a grant for browser/application/mailbox actions. This correction does not alter the other live gate requirements or the current bounded engineering release.

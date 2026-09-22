# HANDOFF_FOR_CODEX — Jobs V1.7 race (Claude) — 2026-09-22 (~21:05Z–22:10Z)

Claude executed `CLAUDE_JOBS_V17_RACE_20260922.md` as the owner-assigned Jobs implementation owner. No competing Jobs source writer was found at startup. The dirty main checkout `repositories/jobs` was never touched, and no history was rewritten. No Gmail/OAuth, employer page, browser, application, model/provider, scheduler, spend, deployment or main merge occurred. **V1.7 is not live-accepted.** G14 now has a genuine verifier PASS that is awaiting a lead verdict. G15, G16 and G17 are unpassed.

## 1. COMP-3A — READY_FOR_LEAD_REVIEW

- Candidate: `claude/jobs-comp3a-bounded-20260922@212b76280677ac61d878abaec580d798199b84fc`, tree `233fd37dce56b5c13d68ffbf9a547063eb1efa52`, draft PR31, parent accepted engine 0a319d0.
- Packet: `coordination/codex/COMP3A_BOUNDED_RETURN_20260922.md`.
- Scope: bounded.py and 3 bounded test files. bounded.py equals the accepted reference 2969ac28 plus two disclosed narrow additions: the fail-closed legacy replay, and a mailbox check before canary reclassification is committed.
- Checks (owned PG 56422, cleanup 0):
  - full 571 passed / 1 host skip / 3 strict xfails (each a named held dependency);
  - `mypy src tests` clean (119 files); Ruff, format and diff clean.
- Red-before evidence is kept.
- Independent review:
  - Round 1, three lenses: spec ACCEPT, control ACCEPT, tests REWORK.
  - Rework de29999, then a delta re-review: ACCEPT with three minors.
  - Minors fixed in 212b762, then a final confirm: ACCEPT.
  - Two optional non-blocking follow-ups are recorded: a committed non-BoundedIngestionError rollback test, and anchoring the mismatch regex.
- Hosted CI: stacked target, NO RUN. This is not a green claim.

**Prepared, NOT a candidate until released:** COMP-3A-CLI, a port of the accepted eec0ae3 `ingest_mailbox` function only.
- Branch `claude/jobs-comp3a-cli-proposal-v3-20260922@9b591fa50bab8e1d1391600aeef4c5af6588fd65`, tree `613755ae`.
- Full 572 / 1 / 2 xfail; cleanup 0.
- Earlier proposals cd9b987 and bb1a3ed are superseded.

**Exact held dependencies (strict xfails):**
- CLI replay port (the proposal above).
- The timeline/`db/canary_provenance.py` application-bound replay exclusion, which is absent on 0a319d0 (2 xfails).

## 2. G14 — genuine proof run, verifier PASS

Record: `coordination/codex/CLAUDE_G14_GENUINE_PROOF_20260922.md`. It contains hashes only; private data stays in `/Users/pchordia/Downloads/swarm_codex/jobs_private`, mode 700/600.

- Code: clean detached worktree `/Users/pchordia/Downloads/swarm_codex/review/jobs-g14-run-1a4efbb` at origin/main 1a4efbb, the accepted proof path under §7.
- DB: new local PG `jobs_v17_live`, migrated to head 003. A post-run `pg_dump` snapshot is kept privately (sha256 `462a025f…`). **Do not re-import 7967740 into this DB**; an in-place update would break re-verification.
- Job: Greenhouse OpenSesame 7967740, the only job the importer supports. Job row `acd4792b-…`.
- Inputs, frozen read-only:
  - profile v2, sha256 `2f659011…c095`;
  - truthful résumé v2, sha256 `8b67aaaa…7d82d`. It uses 81 verified atoms. The v1 fact-check had one line fail; that line was fixed, and v2 passed an independent re-check.
- Run: packet `96890d59-4d46-4f87-8f88-5a6ce5a4e953`, hash `40b2f596…de20c`, 2 answers resolved and 5 unresolved (truthful), `is_live_ready=False`.
- Separate verifier: `REAL_PROOF_PASS`. Redacted bundle `c0bc9ae9…971f`, receipt `bd05f691…8635`. **Not committed**: the plan requires a lead-approved step first.
- Independent review, 3 lenses: all **RECOMMEND_G14_PASS**. The verifier was independently re-run with identical results, the privacy allowlist is clean, and the provenance hashes match. Major findings for the lead, awaiting verification:
  - the owner's explicit G14 authority is recorded only from chat, and an explicit owner confirmation has been requested;
  - the deterministic cover letter has unsupported claims and an internal `UNRESOLVED` marker, so it **must be repaired before G15/G16**;
  - `is_live_ready` ignores cover-letter review.
- Minors for the lead: `run_timestamp_utc` carries a local offset; `code_commit_sha` is derived from the cwd; a hard-coded `resume_version`; understated unresolved categories.

## 3. G15, G16 and G17 — exact blockers

| Gate | Who clears it | Smallest next step |
|---|---|---|
| G15 prefill | Lead: G14 REAL_PROVEN and cover-letter repair ruling. Owner: proof/application job decision (OpenSesame pays $150–170K, below the stated floor; fit is about 40%) or an importer-generalization release; Q12–Q16 answers (proposed privately, 4/5 fact-check PASS and Q14 fixed; Q16 needs an owner example or acceptance of the honest gap answer); Playwright package install permission; exact prefill grant (this job, packet 96890d59/40b2f596, visible browser, stop before submit) | Owner answers, then the lead verdict, then a scoped G15 run |
| G16 submit | Lead: **release G16A** (V1.6 submission engine: durable intent/claim ledger, scoped approval, confirmation validator, Greenhouse hosted-form adapter under §3). It has never been released or built. Then the owner's per-application approval | Lead release of the G16A implementation packet |
| G17 recruiting ingestion | Lead: name the minimum composed G17 source (COMP-3A + CLI, plus the lifecycle/timeline/provenance and worker composition). Owner: a new **Desktop-app** OAuth client with `gmail.readonly` only. The owner offered the `unsubscriber.me` Workspace (project `unsubscriber-web-app-dev`, gcloud authenticated), but its existing web client redirects only to app.unsubscriber.me and cannot serve the loopback flow. Then one consent as the recruiting mailbox; mailbox, canary alias, query, window and cap | Lead composition release, and owner OAuth client plus consent |

## 4. Next bounded tasks (in order, once released)

1. After the COMP-3A verdict: land COMP-3A-CLI if released, then the timeline/`canary_provenance` composition that clears the two strict xfails.
2. Repair the deterministic cover letter so it uses claim-level verified atoms only and no internal markers, and gate `is_live_ready` on cover-letter review, if the lead releases it.
3. The G16A submission engine, if released.
4. With the owner's answers and grants: G15 on the accepted G14 packet (or a regenerated one after the cover-letter repair), then G16, then G17.

## Return prompt for Codex

> Resume Jobs V1.7 from `coordination/codex/HANDOFF_FOR_CODEX_JOBS_V17_20260922.md`. Refresh refs and verdicts. Do not repeat Claude's COMP-3A suites or reviews, or the G14 run or verification, absent drift; exact evidence and hashes are recorded.
>
> Obtain the lead's verdicts on:
> - COMP-3A 212b762 (PR31);
> - the COMP-3A-CLI release (9b591fa);
> - G14 REAL_PROVEN for proof d0f38e88, including approval to commit its redacted bundle and receipt.
>
> Then implement only released packets: CLI, then timeline/provenance composition, the cover-letter repair, and G16A.
>
> Keep every live boundary: G15/G16/G17 need the owner's exact grants recorded above. Never re-import 7967740 into `jobs_v17_live`. When blocked, record the cause and continue other released Jobs work. End with a compact HANDOFF_FOR_CLAUDE.

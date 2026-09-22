# HANDOFF_FOR_CODEX — Jobs V1.7 race (Claude) — 2026-09-22 (~21:05Z–23:10Z)

Claude executed `CLAUDE_JOBS_V17_RACE_20260922.md` as the owner-assigned Jobs implementation owner. No competing Jobs source writer was found at startup. The dirty main checkout `repositories/jobs` was never touched, and no history was rewritten. No Gmail/OAuth, employer page, browser, application, model/provider, scheduler, spend, deployment or main merge occurred. **V1.7 is not live-accepted.** Two genuine G14 proofs (OpenSesame, Flexport) have verifier PASS and independent review, and await a lead verdict. G15 and G16 are **BLOCKED_NO_ELIGIBLE_TRANSPORT** pending a lead ruling on the Greenhouse route, and G16A engineering is unbuilt. G17 is unpassed.

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
- Independent review, 3 lenses: all **RECOMMEND_G14_PASS**. The verifier was independently re-run with identical results, the privacy allowlist is clean, and the provenance hashes match. Three majors were **adversarially refuted as G14 defects**:
  - the owner's pre-run instruction is in the session record;
  - the deterministic cover letter's unsupported boilerplate and internal marker are real but are **G15/G16 blockers, not G14 defects**;
  - `is_live_ready` ignoring cover-letter review is a latent gate gap.
- Minors for the lead: `run_timestamp_utc` carries a local offset; `code_commit_sha` is derived from the cwd; a hard-coded `resume_version`; understated unresolved categories.

## 2b. Better-fit job: second G14 (Flexport) and importer generalization

- The owner chose a better-fit job. Importer generalization `claude/jobs-g14-importer-generalize-20260922@2ce1194142679629cb32c966ee2141c13f5b0239` (tree `a6e081fe`, on 1a4efbb) was independently reviewed: **RECOMMEND_ACCEPT**. Full PG 399/1; mypy and Ruff clean.
- **Flexport 8110413 G14: `REAL_PROOF_PASS`.**
  - DB `jobs_v17_live_flexport`, code `2ce11941`.
  - Packet `08075334-f712-4c2b-9f07-eb120ee3a0bb`, hash `89f69a06…896e`, **8 answers resolved, 0 unresolved, `is_live_ready=True`**.
  - Bundle `13a5bea7…9e75`, receipt `b5d1ffe6…0141`.
  - Truthful résumé `2595e00b…` passed its fact-check.
  - Profile v4 `0f991637…` includes two **owner-delegated test answers** (prior Flexport employment = No; 50% travel = Yes). They must be re-confirmed before any real submit.
  - Details and the independent review are in `CLAUDE_G14_GENUINE_PROOF_20260922.md` (addendum). **Do not re-import 8110413 into that DB.**
- Playwright 1.63.0 is installed in the shared engine venv, with owner permission; its Chromium v1243 was already cached. The real-browser assisted engineering test now runs and passes.

## 3. G15, G16 and G17 — exact blockers

| Gate | Blocker, and who clears it | Smallest next step |
|---|---|---|
| **G15 prefill** | **Lead (transport policy):** the destination-policy review (`GREENHOUSE_DESTINATION_POLICY_REVIEW_20260922.md`) finds Greenhouse automated/assisted eligibility **UNCLEAR**. Greenhouse publishes no candidate terms, Flexport's clause is ambiguous, and Greenhouse documents reCAPTCHA scoring plus bot detection. So §3 gives **BLOCKED_NO_ELIGIBLE_TRANSPORT**, and the registry has no Greenhouse entry (default `blocked`). Also needed: lead G14 REAL_PROVEN; owner's exact prefill yes | Lead rules: (a) visible assisted prefill with a human submit is acceptable here; (b) employer consent; or (c) a V1.7 G15 redefinition. Then the owner's exact yes and a G15 run on packet 08075334 |
| **G16 submit** | The same transport blocker. **G16A engineering has never been released or built** (intent/claim ledger, scoped approval, confirmation validator, adapter). Per-application owner approval, with the two delegated answers re-confirmed. The confirmation signal needs a correlated email, which in turn needs G17 access | Lead policy ruling plus a G16A release |
| **G17 ingestion** | Lead names the minimum composed source. OAuth: the owner prefers reusing the unsubscriber.me **web** client. That works if `http://localhost:8765/` is added to its authorized redirects, the consent screen allows the recruiting Gmail, and a one-time helper mints a `gmail.readonly`-only token. Needs the owner's yes for that client change and the consent itself. Then mailbox, canary, query, window and cap | Owner yes on the redirect change, lead composition release |

## 4. Next bounded tasks (once released)

1. COMP-3A verdict, then COMP-3A-CLI, then the timeline/`canary_provenance` composition (clears the strict xfails).
2. A lead policy decision on the Greenhouse route (G15/G16 reachability).
3. The G16A submission engine, if released. Optional importer hardening (reviewer note).
4. The cover-letter fallback repair: unmapped boilerplate, a tense bug now that the current role is listed first, and an internal marker. Needed before any employer-visible cover letter. Flexport's form has no cover-letter field.
5. With the owner's grants: G15 on packet 08075334, then G16, then G17.

## Return prompt for Codex

> Resume Jobs V1.7 from `coordination/codex/HANDOFF_FOR_CODEX_JOBS_V17_20260922.md`. Refresh refs and verdicts. Do not repeat Claude's COMP-3A suites or reviews, or the G14 run or verification, absent drift; exact evidence and hashes are recorded.
>
> Obtain the lead's verdicts on:
> - COMP-3A 212b762 (PR31);
> - the COMP-3A-CLI release (9b591fa);
> - G14 REAL_PROVEN for proofs d0f38e88 (OpenSesame) and 94cfa17d (Flexport; importer 2ce1194), including approval to commit their redacted bundles and receipts;
> - a Greenhouse transport-policy ruling per `GREENHOUSE_DESTINATION_POLICY_REVIEW_20260922.md`.
>
> Then implement only released packets: CLI, then timeline/provenance composition, the cover-letter repair, and G16A.
>
> Keep every live boundary: G15/G16/G17 need the owner's exact grants recorded above. Never re-import 7967740 into `jobs_v17_live` or 8110413 into `jobs_v17_live_flexport`. When blocked, record the cause and continue other released Jobs work. End with a compact HANDOFF_FOR_CLAUDE.

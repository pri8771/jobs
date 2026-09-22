# HANDOFF_FOR_CODEX — Claude resume pass — 2026-09-22 (~17:55–18:50Z)

**Target is now V1.7 for all three projects.** Owner, verbatim: "If we havent reached 1.7 for any, then change the goal post for 1.7". None has reached it. V2.0, V2.3 and V2.7 are deferred.

Owner also answered **"1. yes, 2 yes."**: the Swarm lint packet is released, and public-repo Actions is the CI route. R33c's public target is OK'd in principle.

Git is truth; refresh refs and verdicts first. No live, mailbox, browser, application, model, scheduler, spend, merge or deploy action was taken, and nothing was dispatched.

## Official vs engineering (adversarially checked)

| Project | Official | Engineering frontier | Full V1.7 blocker record (branch `codex/portfolio-review-20260922`) |
|---|---|---|---|
| Jobs | **V1.1**; G14–G17 unpassed | V1.4/V1.5 accepted (main 7c0fa73); G16A not accepted; b2688ee/b67fc523/2969ac28 accepted but uncomposed | jobs `coordination/codex/OWNER_TARGET_V17_20260922.md` |
| SwarmAI | **none ≥1.0**; V1.1 highest verified | partway V1.7; latest accepted fb58a751 | swarmai `docs/coordination/OWNER_TARGET_V17_20260922.md` |
| Bots | **V0.4.x**; V0.3 accepted | non-sequential slices to V1.3/V1.4; PR6–PR16 accepted | astra-bot-launch `social-bots/lead-reviews/OWNER_TARGET_V17_20260922.md` |

## Done this pass (do not repeat without drift)

- **Swarm R30b-P0: READY_FOR_LEAD_REVIEW.** `11bd4b5276458b2b7adc11528f117e919524f035` / tree `33990992`, PR28, packet e72de3a.
  - Full owned PG 623/13 and offline 427/209. The new tests are 7 red on the base, then green.
  - A 3-lens review found no P0 defect.
  - Disclosed R28b1 test compatibility change.
  - Follow-up for the lead: `make_approval` does not run the integrity check.
- **Swarm lint packet (owner-released).** `349c732c335d83eaa431d30ea7f2b52b8d4431a3`, PR29.
  - **First fully green Swarm hosted CI** (35767004625). Hosted CI skips PG integration.
  - Local PG 616/13.
- **Hosted CI now executes on the public repos.**
  - Jobs main `1a4efbb` is fully green.
  - Jobs PR26 `b2688ee` fails `mypy src tests`: 22 test-typing errors from the V1.7 lineage.
  - Bots lineages have no workflow.
  - Mistake: I reran Jobs' read-only heartbeat monitor and cancelled it.
- **Checkpoints:** Jobs ca5d0bc and Bots 63ce2a5.
- **V2.0 grant request** at ca5d0bc. It is superseded by the V1.7 grant tables in the OWNER_TARGET docs.

## Critical path (lead's native sequence)

- **Jobs:** G14 first, on main; composition is not needed for G14. Then G15 → G16A engineering + G16B → V1.7 reconciliation + G17.
  - Lead must record V1.7 and name one worker (the dormant V1.6 Fable release must be re-opened or re-scoped).
  - Lead must rule on transport policy and on PR26 CI.
  - Owner must supply the G14 inputs and host.
- **Swarm:** PR28/PR29 verdicts, then one tip: fb58a751 + P0 + lint + **R02c 1c9ff44** (worker.py overlap, untested), then PG composition.
  - **R31a is releasable now.**
  - Queue reconciliation: R02a/R17a are listed "ready" though accepted.
  - Reviews needed: R27a/R27b, MISSION-CANCEL-01 and the CP3 rerun.
  - Owner: G12 providers and the CP1 attempt disposition.
- **Bots:** LEAD-066 (PR17) → V04-B prepare-only matrix → G-MODEL-V04.
  - Lead must also: set the target to V1.7, reassign card owners, and release the READY cards (SB-V07-001, SB-R07-042/044/071, SB-V07-WIN-001, SB-R07-051).

## Return prompt for Codex

> Resume the three-project work toward **V1.7** across Jobs, SwarmAI and Social Bots. V1.7 is the owner's new goal post; V2.0 and later are deferred.
>
> **Read first:**
> - `/Users/pchordia/Downloads/swarm_codex/HANDOFF_FOR_CODEX_20260922.md`.
> - Each project's `OWNER_TARGET_V17_20260922.md` on `codex/portfolio-review-20260922`.
> - Refresh Git refs and native lead verdicts before acting.
>
> **Reuse, don't repeat:** reuse Claude's exact-tree evidence (swarmai PR28 `11bd4b52` with `evidence/CLAUDE-R30B-P0-20260922`; PR29 `349c732c`). Do not rerun suites or reviews unless drift or a concrete concern appears.
>
> **Implement only what the native leads release after the V1.7 reset.** Expected first releases:
> - Swarm: PR28/PR29 verdicts, then one composed tip (fb58a751 + P0 + lint + R02c 1c9ff44) with an owned-PG run, then R31a.
> - Jobs: lead records V1.7 and names the worker, then G14 preparation, the transport-policy follow-ups and a PR26 test-typing fix if released.
> - Bots: LEAD-066, then the V04-B prepare-only matrix and any released READY cards.
>
> **Boundaries:** keep all live-action and approval boundaries. Owner grants remain REQUESTED unless a scoped grant is recorded. Use public-repo GitHub Actions for exact-SHA CI with no billing change; hosted Swarm CI skips PostgreSQL, so owned-PG evidence stays required.
>
> **When blocked:** record the exact cause and move to independent permitted work. Continue until none remains, then write HANDOFF_FOR_CLAUDE and a compact return prompt. Do not automatically dispatch another session.

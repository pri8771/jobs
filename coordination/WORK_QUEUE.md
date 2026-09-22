# Active queue — V1.7 live only

Owner scope: **get V1.7 live and stop**. Exactly one Fable implementation session and one owned five-minute worker heartbeat. ChatGPT is lead and sole milestone acceptance authority. V2.0/V2.3/V3 are inactive future inventory.

Canonical execution: `docs/FABLE_V17_LIVE.md`.
Lead handoff: `coordination/V17_LEAD_HANDOFF.md`.
Active implementation branch: `claude/serene-brown-g6uij0`.
Draft review PR: #12.

## Current reviewed position

Latest reviewed worker code: `a6b5ba34eface2cb205e3d9e3809c339d38b06b7`.

Phase 0 is complete as an operational discovery step, not as milestone acceptance:
- consolidated readiness report exists and is accepted as current operational inventory;
- V17-T01 transport research is useful support evidence but does **not** make a live transport eligible;
- worker-host PostgreSQL and Playwright engineering capability is reported available;
- exact-head code validation/READY handoff for the new hygiene changes is still pending;
- no G14/G15/G16/G17 live proof has passed.

## P0 — A-V14-P0A-INTEGRITY

State: **IN_PROGRESS / REWORK; not accepted**.

Fable must complete F145-01..06 as one coherent current-branch batch. Preserve all consolidated PR #11 review findings, including:
- closed runtime candidate schema and candidate/receipt separation;
- credential-safe DB identity and mandatory persisted packet/resume/artifact/source linkage;
- persisted answers/provenance/unresolved/profile/selected-resume binding;
- canonical Greenhouse source binding and generation-origin truth;
- real PostgreSQL compatibility and positive production-constructor coverage;
- fail-closed behavior for missing/tampered evidence.

Required handoff: actual diff + targeted proof tests + full pytest + Ruff + mypy + real PostgreSQL production-path validation available on the worker host. Hosted Actions currently fail before runner steps, so exact-code local/worker validation may be reviewed as engineering evidence but must never be described as hosted CI-green.

No private profile/resume proof before ChatGPT accepts P0A.

## Safe parallel work inside the same worker session

While P0A is waiting on lead review, the same Fable session may continue F145-07..11 V1.5 engineering only:
- semantic form fingerprint/destination identity;
- upload selection/result/readback evidence;
- no false submission truth from URL keywords/arbitrary evidence;
- prefill-only flow must stop before submit;
- local controlled Playwright engineering validation is permitted.

This does not open G15 on a real employer page.

## Live gates

### G14 — genuine V1.4 packet proof
BLOCKED until P0A acceptance plus an eligible host with the genuine private profile, exact selected `resume_ai_software_engineer` bytes, and a current real job/source. Then run the production packet path and independently validate the runtime candidate/receipt. Private inputs remain local.

### G15 — genuine visible-browser prefill
BLOCKED until accepted real packet + V1.5 engineering acceptance + a scoped owner grant naming the real application page. Perform actual safe prefill/uploads, capture post-fill evidence, and **STOP BEFORE SUBMIT**.

### G16 — one real system submission
BLOCKED until V1.6 authorization/idempotency/preflight/confirmation/hygiene/transport engineering is accepted and the owner explicitly approves the exact desired job, packet and method. Employer-credentialed ATS APIs are not candidate-eligible. Hosted-browser submission is only a candidate transport if policy and exact owner authorization permit it. CAPTCHA/MFA/verification is a terminal manual barrier. Require correlated external confirmation; local success flags/manual reports are not substitutes.

### G17 — genuine recruiting lifecycle proof
BLOCKED until the owner authorizes bounded read-only Gmail access and supplies/selects a bounded genuine recruiting evidence set. Reuse merged PR #3 lifecycle/CRM code; close only demonstrated ingestion/link/replay gaps. Prove production ingestion, meaningful timeline/interview/follow-up/outcome evidence, and idempotent replay/restart.

## Engineering sequence after P0A/V1.5

1. V1.6: V17-A01/A02/I01/I02/P01/P02/D01/C01/C02/H01/T02/X01, strictly bounded by `docs/FABLE_V17_LIVE.md`.
2. G16 when the exact live gate opens.
3. V1.7: V17-R01/M01..M04/R02..R05 only as needed to reconcile merged code to the acceptance criteria.
4. G17 when the bounded mailbox/evidence gate opens.
5. `A-V17-MILESTONE-GATE`: accept only after engineering + genuine G14/G15/G16/G17 all pass.
6. **STOP.** Do not assign V2/V3.

## Operations

- One implementation session only; no historical lane restart.
- One worker watcher only: `FIVE_MIN_2026_09_21` / `ACTIVE_5M` every ~5 minutes while working.
- Active heartbeat publication branch is `worker/v14-real-proof`; it is the watcher stream for the current Fable session, not a second implementation lane.
- Latest lead-verified heartbeat at this sync: #27 at `2026-09-22T00:50:27Z`.
- Heartbeat issue-comment workflow and hosted CI remain runner-start blocked (`steps: []`, `runner_id: 0`). Direct lead comments to issue #7 remain required.
- `worker-pc` gets no task unless a concrete independent need exists and checkout/fetch/test permission is verified first. Do not repeat the failed clean-sync under unchanged permissions.

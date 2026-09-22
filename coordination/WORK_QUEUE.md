# Active queue — V1.7 live only

Owner scope: **get V1.7 live and stop**. Exactly one Fable/Claude implementation worker/session and one owned five-minute worker heartbeat. ChatGPT is lead and milestone acceptor. V2/V3 remain inactive future inventory.

Canonical execution: `docs/FABLE_V17_LIVE.md`.
Lead handoff: `coordination/V17_LEAD_HANDOFF.md`.
Latest lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

## Current accepted engineering position

PR #12 has been lead-reviewed and merged. Exact engineering sources:
- V1.4 P0A: `8491dd98154ff750f49cbb64d2a79eca5cb06069` — **ENGINEERING ACCEPTED**.
- V1.5 assisted-browser: `47fefd1b0ca354360353577685f6619a94f00f42` — **ENGINEERING ACCEPTED**.
- integration on `main`: `7c0fa73bf350392a88b47442455359a43cf926b0`.

Worker-host validation reports 395 tests including real PostgreSQL producer-to-consumer proof-path coverage and real headless Playwright engineering-form coverage, plus Ruff and mypy green. Hosted Actions are `CI_BLOCKED_ACCOUNT` before steps and are not green. A read-only `worker-pc` exact-head check confirmed the SHA but could not run Python due harness approval, so it adds zero test credit.

## P0 LIVE — G14 / A-V14-REAL-PROOF

State: **BLOCKED ON GENUINE APPROVED INPUTS / ELIGIBLE HOST; UNPASSED**.

P0A is no longer the blocker. To open G14, the execution host must actually have:
- the approved genuine private candidate profile;
- the exact selected real resume bytes/mapping;
- a current real job/source suitable for the packet proof;
- working production-path connectivity/configuration.

Then run the production importer -> packet runner -> independent verifier and preserve only sanitized hashes/provenance in committed evidence. Private inputs remain local. No example/synthetic profile, temp resume, fake job, mock model, silent fallback or hand-authored proof evidence is allowed.

The last reviewed Fable host reported it does **not** have the required private inputs and public Greenhouse egress. Do not self-open this gate or fabricate substitutes.

## Safe independent engineering while G14 is blocked

The same single Fable session should synchronize latest `main` and continue bounded **V1.6 engineering** from `docs/FABLE_V17_LIVE.md`, prioritizing:
- authorization semantics for exact job + packet + method;
- durable idempotency/concurrency safety;
- immediate pre-submit packet/artifact/policy preflight;
- external-confirmation truth and reconciliation;
- task/telemetry/error hygiene;
- eligible candidate-side transport only;
- removal of unsafe fallbacks/retries and any code path that can infer submission truth from local state, URL text or untrusted evidence.

Return one coherent reviewable batch with targeted/full validation. Do not perform a live submit.

## G15 — genuine visible-browser prefill

State: **BLOCKED / UNPASSED** until accepted genuine G14 packet + accepted V1.5 engineering + a scoped owner grant naming the real application page/session. Perform safe visible prefill/uploads, capture post-fill evidence, and **STOP BEFORE SUBMIT**. LinkedIn/Indeed submission remains MANUAL_ONLY.

## G16 — one real system submission

State: **BLOCKED / UNPASSED** until V1.6 authorization/idempotency/preflight/confirmation/hygiene/eligible-transport engineering is accepted and the owner explicitly approves the exact desired job, packet and method. A real system action plus correlated external confirmation is required. A manual report, mock, test employer, or public API GET is not a substitute. CAPTCHA/MFA/verification is a manual terminal barrier.

## G17 — genuine recruiting lifecycle proof

State: **BLOCKED / UNPASSED** until bounded genuine recruiting evidence and the required read-only access are explicitly authorized. Reuse merged PR #3 lifecycle/CRM code; do not broadly rewrite it. Required proof: production ingestion/linking, meaningful timeline/interview/follow-up/outcome evidence, and idempotent replay/restart.

## Completion sequence

1. G14 genuine packet proof.
2. G15 genuine visible-browser prefill proof, stopping before submit.
3. Finish/accept V1.6 engineering and G16 one exact approved real system submission with correlated external confirmation.
4. Reconcile only the V1.7 gaps needed around merged PR #3 and prove G17 with genuine bounded evidence.
5. Accept `A-V17-MILESTONE-GATE` only when engineering + G14 + G15 + G16 + G17 all pass.
6. **STOP.** Await new owner scope. Do not assign V2/V3.

## Operations

- One implementation session only; do not restart historical lanes.
- One worker watcher only: `FIVE_MIN_2026_09_21` / `ACTIVE_5M` every ~5 minutes while working.
- Watcher publication branch remains `worker/v14-real-proof` for this same Fable session; it is not a second implementation lane.
- Latest lead-verified heartbeat: **#40 at `2026-09-22T01:56:01Z`**.
- Hosted heartbeat comments/CI may remain runner-start blocked; direct lead issue #7 updates continue.
- Do not repeat `worker-pc` Python validation under unchanged harness permissions.
- No Gmail/mailbox, real employer-page prefill, submission, messaging, calendar, spending, CAPTCHA/MFA handling, or fabricated candidate facts without the exact scoped grant.
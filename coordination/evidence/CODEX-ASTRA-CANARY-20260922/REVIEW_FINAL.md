# Final independent Jobs exact-tree review — 2026-09-22

**Recommendation: RECOMMEND_ACCEPT for engineering review of staged tree `6644f340b98eae517ae08ccde38a28da5f2c52a9`, subject to the integration owner's settled full-check results and the actual lead's formal verdict.** This recommendation is not formal acceptance, merge authorization, deployment, or G14-G17 live proof.

## Exact identity

- Worktree: `/tmp/jobs-v17-cli-gate-20260922`
- Base HEAD: `7685f811ec5e41df789e6df82f948669e5e35fe2`
- Reviewed staged successor tree: `6644f340b98eae517ae08ccde38a28da5f2c52a9`
- Tree identity confirmed before and after bounded probes. No unstaged source changes; staged diff whitespace check clean.
- Reviewer made no repository source/test edits, no external calls, and no full-suite repeat. Evidence scripts and reports remain in `/tmp/jobs-astra-canary-header-20260922/`.

## Concrete findings closed independently

1. **P1 malformed independent header suppresses recipient canary classification:** per-field canonical parsing and independent Gmail To/Cc parsing preserve the valid alias; invalid configured identities fail validation. Independent replay of the original real-adapter-parser + SQLite reproduction now returns canonical alias present, fresh classification True, historical match True, reclassified count 1 and durable canary tag True. See `final_header_output.txt`. Root's prior migrated PostgreSQL From/Cc/To log was inspected and reports fresh-process readback pass and zero remaining scratch databases for each case.
2. **P2 noncanonical alias misses historical-canary replay preflight:** constructor now uses `sorted(canonical_email_addresses(canary_identities or []))`, aligning replay matching and policy fingerprints. Independent rerun of retained historical-parser probe now reports unchanged fingerprint, current-policy match True, preflight-canary detection True, rejection `REPLAY_EVIDENCE_CANARY_RECLASSIFIED`, and **zero new poll/list calls**. See `repaired_replay_output.txt`.

Reviewed the exact successor delta from prior staged tree `22fdb2696c8b04b3385da1c746fd2297752580af`: one production constructor canonicalization, its concrete historical-audit regression, and the historical review supersession notice. The regression first obtains a writer-shaped old-parser audit and verifies rejection before any new poll; it addresses the reproduced production-path cause.

## Review coverage and limits

The preceding independent pass covered the requested durable source/provenance closure; worker/polling/lifecycle/alerts/CRM preflight and quarantine; strict V3 metadata, replay authorization and timeline selection; evaluation, packet, assisted and auto-apply gates; dashboard/API/analytics/health/CLI visibility; and explicit synthetic evidence markers. Details and causal evidence are retained in `REVIEW.md` and `REVIEW_SECOND_PASS.md`. No unresolved blocking finding remains in this reviewed source scope after the two fixes.

Root owns settled full pytest, Ruff, mypy and production-dialect verification. This reviewer was told the 67 affected tests passed and inspected the PostgreSQL header-reclassification log, but did not independently repeat the full suite or certify hosted CI. Attach the settled exact-tree check results separately before seeking formal lead disposition.

Retain the documented non-blocking limit: job-only durable canary provenance quarantines operational gates and visibility, while genuine lifecycle messages can still update hidden historical application state; timeline uncertainty is message-scoped. Do not describe quarantine as full runtime immutability or describe this engineering review as broad live readiness. Historical review comments marked unreachable were corrected for the two reproduced cases.

No real mailbox, external model, live application/browser, public action, scheduler, spend, deployment, merge, or G14-G17 genuine evidence was exercised or approved by this review.

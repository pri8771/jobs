# Jobs canary exact-tree repair — ready for formal review

Recommendation: **RECOMMEND_ACCEPT**, bounded engineering only. Source **b2688eeabb5ca996767b27b78d0004678eeee756**, tree **6644f340b98eae517ae08ccde38a28da5f2c52a9**, candidate branch codex/jobs-v17-cli-gate-20260922. Commit tree exactly matches the independently reviewed staged tree. Draft PR: https://github.com/pri8771/jobs/pull/26. Source clean and pushed; uv.lock removed before committing. No self-acceptance.

## Fresh-state reconciliation and actual repairs

Initial status/diff/check empty at7685f811; d337424e had already been committed/pushed, superseding uncommitted handoff. Initial local full480pass2skip, Ruff/mypy75clean. The earlier recommend-accept review contained two incorrect unreachable assessments, now explicitly superseded in source documentation.

Independent mechanical review then root independently reproduced:
1. Malformed raw From erases valid recipient alias in aggregate strict getaddresses; malformed Cc can also erase To in Gmail parsing. Invalid configured alias can silently empty policy. Repair parses independent values separately in shared canonicalization and Gmail recipient parsing; invalid configured identities fail closed. Regression red7fail1pass, repaired modules35pass.
2. Historical writer-shaped audit with unchanged display/case alias policy can reach a poll before rejection. Repair canonicalizes runner identities at construction; concrete new regression red then green. Independent final probe rejects before any new poll.

Final review examined durable provenance closure; worker, polling, lifecycle, alerts, CRM, dashboard, health, CLI; V3 audit/replay validation; operational gates; visibility and genuine-vs-synthetic boundaries. **No unresolved blocking finding in reviewed scope**. Final exact-tree review is retained with earlier rework reports; formal acceptance is reserved for ChatGPT lead.

## Settled evidence

- 67 affected tests pass.
- Exact settled full **490 passed,1 host-specific skip in62.16s**; actual owned PostgreSQL proof integration enabled. No hosted CI claim.
- `uv run ruff check .` clean; `uv run mypy src/jobs_automation` clean75files; staged/working diff check clean.
- Supplemental malformed From/Cc/To (run before final bounded-constructor edit; header/config/ingestion source unchanged afterward): each actual migrated disposable PostgreSQL → fresh-process durable-canary readback passes; each remaining database count0. Initial supplemental harness SQL used plural table name, failed after successful product assertions; raw failure/cleanup0 retained. Corrected singular model table rerun passes, no product workaround.
- Independent final header probe: fresh/historical matches true and durable tag1. Independent historical replay probe: preflight reclassified error and0newpolls.
- Logs, scripts, source identity, red-before failures, intermediate/final independent reports and SHA256SUMS: ../evidence/CODEX-ASTRA-CANARY-20260922/.

Non-blocking limit remains: job-only canary provenance quarantines gates/visibility but genuine messages may update hidden historical lifecycle state; timeline uncertainty remains message-scoped. No runtime-immutability claim. CLI traceback friendliness is separate optional hardening.

## Requested lead disposition

Accept/rework exact source/tree for bounded canary/CLI/V3 engineering. G14-G17 remain UNPASSED; no real mailbox, private candidate/application/browser/model/public action, spend, scheduler, main merge or deployment. Current owner says V2.3 floor/V2.7 target; Jobs V2.3 contract exists, V2.7 lacks canonical definition and needs owner/lead disposition.

Fresh native c73dd361 already accepts separate local-origin source b67fc523/PR25. That source is **not an ancestor** of this candidate (common source ancestor dd2e0de). Broader J20-01 stop remains; request a bounded exact-source composition/next-task release only after verdict rather than claiming this branch contains all independently accepted V2.0 work. Do not merge main or import coordination application snapshots.

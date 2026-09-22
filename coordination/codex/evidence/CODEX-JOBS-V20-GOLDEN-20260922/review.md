# Jobs V2.0 synthetic golden fixture — independent review recommendation

**READY_FOR_LEAD_REVIEW / RECOMMEND_ACCEPT** for the engineering synthetic golden fixture only. Codex prepared the harness and packet; the root coordinator independently reran it. ChatGPT engineering lead remains the formal exact-source acceptance authority.

- **Project/repository:** Jobs Automation / `pri8771/jobs`.
- **Artifact and submission:** exact clean source `832d85f5177ca82564c9d0b6c168790f26ea1dc3`, tree `047eb8501e562cbbca450e946e260a1b8454f74b`, previously accepted candidate-reply engineering source.
- **Reviewer actual identity/role:** Codex review-preparation agent; root coordinator performed the independent rerun. Neither role is the formal acceptance authority.
- **Evidence run:** `/tmp/jobs-golden-root-run.py` created a unique PostgreSQL database, migrated it to Alembic head, invoked the complete synthetic workflow, extracted the machine report, dropped the database, and verified `remaining_database_count=0`.
- **Release:** ChatGPT lead `4d5b82f5d69201d5810aa39e7708de5a89f2e06d` accepts the reply repair and resumes this exact-source golden diagnostic.
- **Contract:** `docs/V2_0_INTEGRATION_FIXTURE.md`, A-V20-INTEGRATION-FIXTURE, all 17 steps through existing application services.
- **Reviewed paths:** the two packeted harnesses, independent wrapper, unmodified raw migration/workflow logs, structured workflow report and wrapper result.

## Checks actually executed

From `/Users/pchordia/Downloads/swarm_codex/review/jobs-fixture-source`:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-golden-root-run.py
```

The wrapper itself asserted clean HEAD/tree, created a uniquely named database on the owned Jobs PostgreSQL test server, ran:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/alembic upgrade head
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-v20-golden-steps9-17.py
```

Observed results: migration exit `0`, workflow exit `0`, `PASS_STEPS_1_17`, and cleanup database count `0`. Exact output is in `root-result/{migration.log,workflow.log,report.json,run.json}`.

The final exact-source candidate-reply packet at native coordination commit `80448a7eca6c603fad58439f6982822ce09801ee` records **463 passed, 1 existing host-loopback skip in 68.08s**, Ruff over all `src`/`tests`, and mypy over **74 source files**. Those results are reused context and were **not freshly rerun** for this fixture packet.

## Positive product-path coverage

The deterministic fixture exercised alert ingestion, normalization, deduplication, evaluation, shortlist, explicit resume selection, immutable resume/cover-letter hashes, packet provenance, unresolved EEO and unsupported questions, a non-live manual application, confirmation, recruiter outreach, scheduled interview, candidate reply attribution, rejection, dashboards, CRM, redacted timeline, analytics, health, and same-database replay.

The durable result contains one job and application, six persisted messages and links, five lifecycle events, one follow-up and one interview. Application CRM contains confirmation, outreach, interview, reply and rejection. The proven recruiter contact CRM contains outreach, interview, reply and rejection. The redacted reply retains method `thread_reply_attribution` and link confidence `0.85`. Two pending reviews preserve both packet ambiguity and the unscheduled-interview reason.

A new `WorkerDaemon` object replayed all six original messages into the same database. It polled six, ingested zero, produced zero transitions and zero errors. Message/link/event/follow-up/interview counts, funnel analytics, resume analytics, application CRM, contact CRM, redacted timeline and pending reviews remained unchanged.

## Evidence boundaries

This is controlled synthetic engineering evidence. Email uses `MockEmailAdapter`; packet generation uses a deterministic provider; the application remains non-live/manual. Dashboard coverage invokes production route handlers through `DummyRequestHandler`, not an HTTP server or browser. Replay uses fresh daemon/session objects in the same Python process, not a fresh operating-system process. Health truthfully reports Gmail `NOT_CONFIGURED` and ATS adapters as simulation-only, so overall health is `DEGRADED`.

The fixture made no Gmail/provider network request, sent no message, submitted no application, used no private mailbox or candidate content, and made no public or deployment action. It is not live proof. Genuine G14–G17, account/host, provider, elapsed-time and independent live checkpoints remain open.

## Adverse and diagnostic coverage

The fixture verifies same-database full replay rather than substituting two independent database runs. It preserves stable counts and analytics, duplicate interview idempotency, packet hash validation, explicit resume identity and hashes, contact-scoped reply attribution, and visible unresolved review reasons. Earlier harness-assumption failures are recorded in `harness-assumption-diagnostics.md`; none is cited as a product defect or passing evidence.

## Recommendation

**RECOMMEND_ACCEPT** exact source `832d85f5177ca82564c9d0b6c168790f26ea1dc3` / tree `047eb8501e562cbbca450e946e260a1b8454f74b` for A-V20-INTEGRATION-FIXTURE synthetic engineering coverage only. Request a formal exact-source verdict from ChatGPT engineering lead. This recommendation does not establish live readiness or close G14–G17.

The next bounded independent task must come from the lead's native verdict/release and must preserve the remaining genuine-input and live gates.

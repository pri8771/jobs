# V1.7 CLI-gate independent review — 2026-09-22

Independent engineering review by the Fable/Claude worker of the canary-provenance repair produced in the Codex session on `codex/jobs-v17-cli-gate-20260922`. This is a review recommendation for the lead, not acceptance: ChatGPT remains the acceptance authority, and no canary, fixture or test evidence here substitutes for the genuine G14–G17 live gates.

## Disposition: RECOMMEND_ACCEPT

| Item | Value |
| --- | --- |
| Base reviewed against | `bc93a8a0bd381f9f675440b62c91aaf3b8406795` (`fix: exclude canary batches from proof association`) |
| Reviewed tree | committed unchanged as `d337424e8fde6f2a54e99ac7a1d02aed1878cc60` (28 files, 3760+/263-) |
| Branch | `codex/jobs-v17-cli-gate-20260922` (linear on top of `origin/main`) |
| `uv run pytest -q` | 480 passed, 2 skipped, exit 0 (run twice) |
| `uv run ruff check .` | clean, exit 0 |
| `uv run mypy src/jobs_automation` | clean, 75 files, exit 0 |
| `git diff --check` | clean, exit 0 |

Review question: does the exact tree contain any canary-contamination path or evidence-contract failure across fresh/historical alias reclassification, worker / polling CLI / update-lifecycle / bounded replay / alerts, the evaluation / packet / assisted / auto gates, CRM / dashboard / analytics / health / CLI status visibility, and bounded V3 audit validation plus timeline proof eligibility. Answer: no.

## What the repair does

Policy and primitives
- `config/platforms.example.yaml`, `src/jobs_automation/core/platforms.py:22` — `email.canary_identities`, the durable owner-controlled alias policy.
- `src/jobs_automation/ingestion/engine.py:33-100` — exact-address canonicalisation (display names, case, ordering and duplicates normalised; lookalike prefixes/suffixes no longer match), durable tag predicate, one-way `mark_durable_canary`, `reclassify_persisted_canary_messages`. The sweep classifies provider duplicates under the active policy, tags them on non-dry runs, tracks them in memory on dry runs, and `continue`s before any job, link, review-task or activity write for fresh canaries.
- `src/jobs_automation/db/canary_provenance.py` (new) — read-only closure from durable canary messages through links and legacy events to jobs, applications, tasks, interviews and contacts, plus the fail-closed `require_job_without_durable_canary_provenance` gate. It never repairs or deletes historical rows.

Entrypoints and lifecycle
- `src/jobs_automation/worker.py` — loads the policy from `platforms.yaml` (missing file tolerated, invalid file fails the sweep before any poll), reclassifies before ingestion even when Gmail is unavailable, passes identities to the engine, reports `canary_messages_reclassified`.
- `src/jobs_automation/cli/main.py` — `poll-emails`, `update-lifecycle`, `worker`, `ingest-mailbox` merge configured plus `--canary-identity` aliases and reclassify first; `evaluate-jobs`, `prepare-packets`, `assisted-apply`, `auto-apply`, `dashboard`, `health-check`, `lifecycle-timeline` reclassify under the configured policy; `mailbox-status`, `review-queue`, `lifecycle-status`, `contacts` refuse to render when the policy cannot be loaded and hide reconciliation-only rows with explicit excluded counts.
- `src/jobs_automation/lifecycle/engine.py:110` — a durable canary is a hard stop before any state, CRM, interview or task mutation.
- `src/jobs_automation/lifecycle/alerts.py` — canary inbound and outbound are ignored in scoped and unscoped modes; tasks carrying any of six canary provenance keys are neither reused nor resolved; stale reminders skip applications with canary links or canary-sourced events.
- `src/jobs_automation/lifecycle/crm.py` — touchpoints, timelines and contact→application lookups skip durable canaries.

Operational gates
- `evaluation/engine.py`, `preparation/packet_builder.py`, `browser/assisted_engine.py`, `automation/auto_engine.py` — `CanaryProvenanceReconciliationRequiredError` before evaluation, packet build, plan build or auto execution; batch evaluation and CLI selection exclude quarantined jobs in the query.

Visibility
- `dashboard/analytics.py`, `dashboard/server.py`, `health.py` — every funnel, source, role, resume, time-to-stage, kanban, jobs, reviews, interviews, contacts, audit, follow-ups, timeline and offers route filters through the closure; resolving a quarantined review task returns 409 without mutation; health excludes quarantined pending tasks and canary messages with explicit counts.

Evidence contract
- `ingestion/bounded.py:53,367` — audit schema v3 with a strict exact-shape validator shared by replay preflight and timeline; digests include the canary flag; `canary_policy_sha256` is bound into every audit; replay requires the same policy, rejects originals whose provider hashes are now canary, and the private `_run` cannot mint a replay without the public `replay` capability.
- `lifecycle/timeline.py:40,196` — timeline schema v2; proof only from valid v3 SUCCESS audits that do not reference a current canary; the latest *mentioning* audit is validated strictly so malformed evidence cannot fall back to an older row; canary-sourced events, tasks and links are excluded and counted.

Tests: `tests/test_canary_provenance.py` (new) plus additions in nine existing modules.

## Verification by focus area

- Fresh and historical reclassification: fresh canaries create no jobs, links, review tasks or activity updates; duplicate canaries are durably tagged on non-dry runs and excluded in memory on dry runs, so a rolled-back dry run cannot present them as genuine; historical reclassification is one-way and committed before any consumer runs.
- Worker, polling CLI, update-lifecycle, bounded replay, alerts: an invalid `platforms.yaml` blocks the poll; v2 audits, policy-fingerprint mismatch and reclassified evidence all fail before any mailbox poll; `run()` and `_run()` both refuse replay requests without the capability; the unscoped worker alert pass ignores canary inbound and canary replies.
- Gates: all four engines raise before operational work; batch and CLI selection filter quarantined jobs.
- Visibility: every `do_GET` route in `dashboard/server.py` was traced; `assess_gmail_readiness` reads only audit rows, so readiness cannot count canary mail.
- Evidence contract: the audit writer (`audit_metadata`, `_safe_poll_metadata`, `_safe_error_codes`, `mailbox_fingerprint`, `_utc_iso`) was cross-checked field by field against `is_valid_bounded_audit_metadata`: exact key set, canonical UTC ISO, sorted unique hash and error lists, status/dry_run/complete/error consistency, poll shape. They agree. The timeline replay block is null for legacy v2 rows, other-application rows, malformed latest rows, policy drift between replay and original, and any audit whose provider hashes intersect current canaries.

## Non-blocking observations (not required for acceptance)

1. Strict header parsing is all-or-nothing per call. `canonical_email_addresses` (`ingestion/engine.py:42`) passes the whole participant list to `email.utils.getaddresses`, which in Python 3.13 strict mode returns `[('', '')]` for the entire list when one value has an unexpected address count. Reproduced: `canonical_email_addresses(["owner+canary@example.com", "a@b.com;c@d.com"])` → `set()`. Not reachable with adapter data: the Gmail adapter stores bare parsed recipients and a parsed `sender_address`, and the From header of canary traffic is owner-controlled. Optional hardening: parse each value in its own `getaddresses([value])` call, and add a `platforms.py` validator requiring each configured identity to canonicalise to exactly one address so a malformed policy entry fails closed instead of silently emptying the policy.
2. Job-level provenance is a visibility quarantine only. Reproduced with an in-memory probe: an application whose job carries only a job-level canary link but receives genuine recruiter mail is hidden by every status surface and blocked by all four gates, yet `LifecycleEngine.process_message` still advances it on the genuine message, `check_stale_applications` still creates a reminder (which the closure then hides), and `build_timeline_export` reports `canary_lifecycle_state_requires_reconciliation: false` (`lifecycle/timeline.py:430`) because its exclusions are message-scoped. No canary-derived data enters evidence through this path. Optional follow-up: a `job_has_durable_canary_provenance` flag in the export's `uncertainty` block, also consulted in `_applications_with_canary_lifecycle_provenance` (`lifecycle/alerts.py:82`).
3. `BoundedIngestionRunner._audit_references_current_canary` (`ingestion/bounded.py:734`) passes raw configured identities to `persisted_message_matches_canary_policy`, which expects canonical addresses. Unreachable behind the preceding policy-fingerprint check; canonicalising `self.canary_identities` once in `__init__` (`bounded.py:697`) would remove the inconsistency.
4. Operator-facing behaviour changes for release notes: the four status commands now commit one-way durable tags before rendering; more commands require a loadable `platforms.yaml` (the example file is the fallback); `assisted-apply --job-id` / `auto-apply --job-id` on a quarantined job exit via an uncaught `CanaryProvenanceReconciliationRequiredError` traceback (fail-closed, not a friendly message).

## Method

- All four checks run on the exact tree; pytest run twice to capture an exact exit code.
- Full read of every source diff plus the surrounding current code for the bounded runner, timeline, alerts, lifecycle engine, worker, CLI, dashboard, health, readiness and the Gmail adapter.
- Two probes against in-memory SQLite from outside the repo: thirteen header shapes through `getaddresses` strict mode, and the job-level provenance scenario above.
- No repo file was modified during the review. The only side effect, an untracked `uv.lock` generated by `uv run`, was removed before committing.

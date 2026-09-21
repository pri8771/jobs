# Artifact-First Recovery Execution — V1.4 to V1.7

Date: 2026-09-21

Goal:
Reach V1.7 with genuine live evidence at each checkpoint using the smallest safe engineering batches possible.

Operating mode:
- one Antigravity implementation session,
- one active artifact at a time,
- one heartbeat watcher,
- fixed 5-minute cadence,
- fresh branch per coherent artifact batch when useful,
- no giant version-sized work item,
- no self-acceptance.

## Recovery design

The old branches are evidence/source branches.
Do not keep repairing giant diverged PRs indefinitely.

For integration artifacts:
- branch from current `origin/main`,
- port/cherry-pick only required code commits,
- do not port heartbeat/history churn,
- run focused tests,
- produce one small reviewable PR/batch.

## Artifact chain

### A-V14-P0A-INTEGRITY
Purpose:
Finish proof-tool integrity only.

Current source:
- latest repair `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Small tasks:
- R14-P01 / SP1 — independently bind persisted JobSource attestation to local source_attestation:
  provider, source kind, public job ID, API URL, fetched_at, description SHA, question SHA, canonical URL.
- R14-P02 / SP1 — adversarial DB-source attestation mismatch tests.
- R14-P03 / SP1 — run targeted proof tests + full pytest/Ruff/format/mypy.
- R14-P04 / SP1 — if GitHub hosted CI cannot run due account billing lock, record CI_BLOCKED_ACCOUNT and request independent exact-head execution; do not mislabel as code failure.

Acceptance:
ChatGPT lead proof-integrity review passes.

### A-V14-CLEAN-INTEGRATION
Purpose:
Get proof tooling onto a clean branch based on current main.

Tasks:
- R14-I01 / SP1 — create fresh branch from latest main.
- R14-I02 / SP1 — port only the V1.4 proof code changes from the relevant code commits; no heartbeat/history files.
- R14-I03 / SP1 — resolve only real code conflicts.
- R14-I04 / SP1 — full regression checks.
- R14-I05 / SP1 — small PR/review.

Candidate source commits to inspect/port:
- `8f8c21f...`
- `3ce19cf...`
- `5e505846...`
- final R14-P01 repair commit

Do not blindly cherry-pick if current main already contains equivalent code.

### A-V14-REAL-PROOF
Purpose:
Genuine V1.4 live packet proof.

Tasks:
- R14-L01 / SP1 — verify private candidate profile is genuine/non-example.
- R14-L02 / SP1 — run production resume selector and identify exact selected variant.
- R14-L03 / SP1 — verify exact genuine resume bytes exist for that variant; if not, BLOCKED_PRIVATE_INPUT, never synthesize.
- R14-L04 / SP1 — re-fetch/import a currently-live public proof job and questions.
- R14-L05 / LIVE — run production packet builder.
- R14-L06 / LIVE — run independent verifier.
- R14-L07 / SP1 — commit redacted candidate + receipt and request lead acceptance.

V1.4 completion requires LIVE_PROOF_PASS.

---

### A-V15-CLEAN-INTEGRATION
Purpose:
Port the already-developed V1.5 assisted-safety code onto current main without dragging old PR history.

Source commits to inspect:
- `44f5fd9...`
- `3ef4002...`
- `09f1852...`

Tasks:
- R15-I01 / SP1 — fresh branch from accepted V1.4 main.
- R15-I02 / SP1 — port initial assisted runtime code only if not already present.
- R15-I03 / SP1 — port accepted A-R15-01..05 repairs.
- R15-I04 / SP1 — port A-R15-06..09 residual safety.
- R15-I05 / SP1 — run targeted assisted-safety tests.
- R15-I06 / SP1 — full pytest/Ruff/format/mypy.
- R15-I07 / SP1 — small PR/review.

Acceptance:
A-V15-BROWSER-SAFETY-CONTRACT + A-V15-ASSISTED-APPLICATION ENGINEERING_ACCEPTED.

### A-V15-LIVE-ASSISTED-PROOF
Purpose:
Genuine V1.5 visible-browser proof.

Tasks:
- R15-L01 / SP1 — choose a real job/application page using the accepted V1.4 packet or a newly accepted real packet.
- R15-L02 / USER_GATE — explicit owner authorization for real visible browser prefill.
- R15-L03 / LIVE — inspect page before writing.
- R15-L04 / LIVE — classify fields and prefill safe fields only.
- R15-L05 / LIVE — verify resume/cover-letter mapping/hashes.
- R15-L06 / LIVE — stop at pre-submit review boundary.
- R15-L07 / SP1 — commit redacted field/provenance/review evidence.

Do not submit unless separately authorized.

V1.5 completion requires LIVE_PROOF_PASS.

---

## V1.6 engineering — split into small artifacts

### A-V16-AUTHORIZATION
- R16-A01 / SP1 — migration/model for scoped job+packet+method authorization.
- R16-A02 / SP1 — validator for active/expired/consumed/revoked authorization.
- R16-A03 / SP1 — changed job/packet/method invalidates approval.
- R16-A04 / SP1 — tests.

### A-V16-IDEMPOTENCY
- R16-I01 / SP1 — stable logical idempotency key.
- R16-I02 / SP1 — durable attempt row/state.
- R16-I03 / SP1 — unique/concurrency guard.
- R16-I04 / SP1 — existing SUBMITTED/CONFIRMED/UNCONFIRMED duplicate blocks.
- R16-I05 / SP1 — tests.

### A-V16-PREFLIGHT
- R16-P01 / SP1 — explicit packet required for real mode.
- R16-P02 / SP1 — packet.job_id guard.
- R16-P03 / SP1 — resume/cover-letter artifact read-back SHA.
- R16-P04 / SP1 — answer/provenance + unresolved-fact gate.
- R16-P05 / SP1 — policy/authorization/kill-switch/rate gate.
- R16-P06 / SP1 — immutable pre-submit manifest.
- R16-P07 / SP1 — tests.

### A-V16-CONFIRMATION
- R16-C01 / SP1 — external confirmation evidence model.
- R16-C02 / SP1 — adapter/transport success alone -> SUBMISSION_UNCONFIRMED.
- R16-C03 / SP1 — ambiguous post-dispatch failure -> SUBMISSION_UNCONFIRMED, no blind retry.
- R16-C04 / SP1 — validated external evidence -> CONFIRMED/SUBMITTED.
- R16-C05 / SP1 — tests.

### A-V16-HYGIENE
- R16-H01 / SP1 — close only submission-satisfied tasks.
- R16-H02 / SP1 — separate attempt pacing from successful submission analytics.
- R16-H03 / SP1 — sanitize error/audit evidence.
- R16-H04 / SP1 — tests.

### A-V16-TRANSPORT
Purpose:
Identify and implement one genuinely permitted system-submit transport.

Tasks:
- R16-T01 / SP1 — current public policy/technical feasibility review of candidate destinations.
- R16-T02 / SP1 — select one transport only if AUTO_ALLOWED can be justified.
- R16-T03 / SP2 — implement narrow transport against existing ATSAdapter contract.
- R16-T04 / SP1 — test NOT_IMPLEMENTED/manual barriers truthfully.
- R16-T05 / SP1 — adversarial transport tests.

If no eligible compliant transport exists:
emit LIVE_PROOF_BLOCKED_NO_ELIGIBLE_TRANSPORT.
Do not fake V1.6 completion.

### A-V16-FIRST-REAL-SUBMISSION
Tasks:
- R16-L01 / SP1 — choose a job the owner actually wants.
- R16-L02 / USER_GATE — explicit exact-job+packet+method authorization.
- R16-L03 / LIVE — preflight/idempotency.
- R16-L04 / LIVE — one real system submit through approved transport.
- R16-L05 / LIVE — capture independent external confirmation.
- R16-L06 / SP1 — commit redacted evidence + lead review.

V1.6 completion requires LIVE_PROOF_PASS.

---

## V1.7 — exploit existing code; do not rebuild

### A-V17-ENGINEERING-RECONCILIATION
Current code is substantial and already merged.

Tasks:
- R17-E01 / SP1 — audit A-V17-CRM-EVIDENCE criteria against current main.
- R17-E02 / SP1 — audit A-V17-INTERVIEW-FOLLOWUP criteria against current main.
- R17-E03 / SP1 — add only missing regression tests, if any.
- R17-E04 / SP1 — full targeted + repository checks.
- R17-E05 / SP1 — reconcile artifact cards to ACCEPTED if evidence supports it.

No broad lifecycle rewrite.

### A-V17-LIVE-LIFECYCLE-PROOF
Fastest route:
use existing historical real recruiting/application email instead of waiting for new recruiter activity.

Tasks:
- R17-L01 / USER_GATE — explicit read-only Gmail authorization if not already authorized.
- R17-L02 / SP1 — harmless Gmail runtime/readiness canary.
- R17-L03 / SP1 — identify a bounded historical real recruiting/application thread set.
- R17-L04 / LIVE — ingest via production Gmail/ingestion path.
- R17-L05 / LIVE — link contact/company/job/application evidence.
- R17-L06 / LIVE — run lifecycle/interview/follow-up processing.
- R17-L07 / LIVE — replay same bounded evidence and verify idempotency.
- R17-L08 / SP1 — emit redacted reconstructable timeline proof.
- R17-L09 / SP1 — independent review.

Preferred evidence set:
one real application thread plus recruiter/interview/rejection/offer evidence if present.
Multiple real historical threads may be combined if one thread does not contain every lifecycle type.

### A-V17-MILESTONE-GATE
Accept only when:
- V1.4 LIVE_PROOF_PASS,
- V1.5 LIVE_PROOF_PASS,
- V1.6 LIVE_PROOF_PASS,
- V1.7 engineering artifacts accepted,
- V1.7 LIVE_PROOF_PASS.

## Review cadence

After every artifact:
1. worker pushes small coherent batch,
2. heartbeat says READY_FOR_LEAD_REVIEW,
3. ChatGPT reviews actual code/evidence,
4. accept or issue one bounded rework,
5. worker advances only after gate opens.

Do not accumulate five artifacts before review.

## CI infrastructure fallback

If GitHub hosted Actions cannot start because of account billing/spending lock:
- record `CI_BLOCKED_ACCOUNT`,
- do not call it a code failure,
- run full local checks on exact head,
- request independent exact-head execution/audit where available,
- resume GitHub CI once infrastructure is restored.

Do not pretend blocked CI is green.

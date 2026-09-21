# Active Work Queue

ChatGPT owns prioritization and acceptance.

Fresh lead re-audit baseline: 2026-09-20 21:20 ET

## Formal milestones

V1.7 -> V2.0 -> V2.3 -> V3.0

## Current accepted foundation

### A-V14-PACKET-SAFETY — ACCEPTED

Lane A residual repair was merged to main as:
- merge commit `8a0cdb4`

Main CI:
- PASS

Accepted protections:
- immutable/content-addressed artifacts
- exact resume family attribution
- generation origin/live-readiness gate
- quantitative claims require exact evidence
- prior V1.4 packet-safety requirements remain satisfied

## Lane A — V1.5 Assisted Application

Branch:
- `worker/v15-assisted-application`

Artifact:
- A-V15-BROWSER-SAFETY-CONTRACT
- A-V15-ASSISTED-APPLICATION

Ready tasks:
- J15-00 SP2 require explicit accepted packet ID; no latest-packet fallback
- J15-01 SP2 inspect form before any write + field classification/provenance
- J15-02 SP2 manual barrier classifier
- J15-03 SP3 machine-readable pre-submit review manifest
- J15-04 SP2 artifact read-back/hash verification immediately before upload
- J15-07 SP3 one persistent visible Playwright context for inspect/prefill/upload/review
- J15-08 SP2 block unresolved/UNKNOWN_REQUIRED before prefill
- J15-09 SP2 external-evidence-only submitted state
- J15-10 SP1 mock browser can never create real submitted state

Engineering only. No live application/session without user approval.

## Lane B — V1.7 + V2.0 Rework

Branch:
- `worker/recruiting-ops`

Existing worker commits:
- 21f2be9 V1.7
- bd98cf5 V2.0 platform/analytics batch

Do not throw these away.

Lead re-audit:
- docs/LANE_B_REAUDIT.md

Rework tasks:
- B-R17-01 SP2 add conservative classifier paths for RECRUITER_FOLLOW_UP/BACKGROUND_CHECK/ONBOARDING/WITHDRAWAL and end-to-end tests
- B-R17-02 SP2 contradictory rejection after OFFER_ACCEPTED/ONBOARDING -> review, not silent regression
- B-R20-01 SP3 historical funnel/resume/source/role outcome metrics use ApplicationEvent history, not current status only
- B-R20-02 SP2 fix "applications submitted" denominator; simulation/non-submitted rows do not count as real submitted
- B-R20-03 SP1 remove "statistically robust" overclaim; descriptive sample-size language only
- B-R20-04 SP2 remove false Gmail readiness inference; wait for Lane C typed readiness for final integration
- B-R20-06 SP2 protect dashboard state-changing POST when not strictly local/authorized

Worker-run history claim J20-14 is NOT accepted yet.
Do not expand it in this batch unless ChatGPT explicitly reassigns B-R20-05.

After rework:
- full tests
- Ruff
- mypy
- push
- READY FOR LEAD RE-REVIEW

## Lane C — Live Data & Candidate Provenance

Branch:
- `worker/live-data-foundations`

Artifacts:
- A-V12-CANDIDATE-PROVENANCE
- A-V20-GMAIL-RUNTIME-READINESS

Ready:
- J12-01 SP2 private-safe candidate fact provenance records
- J12-02 SP2 allowed_for_application enforcement
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 Gmail partial-fetch must fail closed/no checkpoint advance
- J20G-02 SP2 persistent ignored OAuth runtime wiring
- J20G-03 SP2 typed secret-free REAL-Gmail diagnostic

Do not perform actual OAuth or access real mailbox.
Final health integration waits until the readiness interface is reviewed.

## Lane D — V2.3 Foundations

Branch:
- `worker/v23-foundations`

Lane D does NOT redo Lane B's V2.0 code.

Artifacts:
- A-V23-OPPORTUNITY-GRAPH
- A-V23-TARGET-COMPANY-WATCH
- A-V23-AGENT-TOOLS

Ready tasks:

### Opportunity graph
- J23O-01 SP2 implement read-only opportunity graph projection over existing relational models; no graph DB and no new schema
- J23O-02 SP2 typed evidence-preserving queries for company/job/contact/application/resume relationships
- J23O-03 SP2 edge/projection dedupe + provenance tests

### Target company watch
- J23T-01 SP2 local target-company watch configuration/model in new V2.3 module without external polling
- J23T-02 SP2 derive known jobs/applications/contacts/signals from existing DB truth
- J23T-03 SP1 tests for pause/dedupe/already-known roles

### Agent tool layer
- J23A-01 SP2 typed ToolResult/request envelope + permission metadata
- J23A-02 SP3 read-only wrappers for jobs/applications/contacts/timelines/resume analytics/policy/health
- J23A-03 SP2 local-write/draft interface contracts without external side effects

No external actions.
No MCP requirement yet.
No shared DB migration unless ChatGPT explicitly authorizes one.

## Scout — QA / Prep / Adversarial Review

Branch:
- `scout/qa-prep`

Scout owns no production code by default.

First priorities:
1. independently re-audit Lane B repair branch
2. audit Lane A V1.5 branch once code lands
3. audit Lane C Gmail/provenance branch
4. audit Lane D V2.3 interfaces
5. maintain V2 integration risk log

Scout outputs only under coordination/scout/.

## Remaining V2.0 acceptance work

Even when B rework is accepted, V2.0 still requires:
- Lane C Gmail runtime readiness
- actual user OAuth/live Gmail canary
- candidate provenance
- A-V20 integration fixture after core branches merge
- accepted safe application execution path
- real-data integration evidence

Do not call V2.0 live ACCEPTED from simulated/test evidence.

## Safety

- no fabricated candidate facts
- no mock == real
- LinkedIn/Indeed remain MANUAL_ONLY
- no CAPTCHA/MFA bypass
- external confirmation required for real submitted state
- consequential external actions require scoped user approval

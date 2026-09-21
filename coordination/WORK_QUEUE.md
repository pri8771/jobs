# Active Work Queue

Owner directive:
**No version is COMPLETE until one real non-mock production-path example passes.**

Current team:
- Lane 1 — V1.4 real-proof critical path
- Lane 2 — V1.5 application safety
- Lane 3 — V1.7/V2.0 recruiting/reliability

Old Lane D and Scout are PAUSED.
Old Lane C is SUPERSEDED by Lane 1.

All lanes must use the current heartbeat epoch and live progress feed in GitHub issue #7.

## Lane 1 — P0 — V1.4 proof-tool integrity

Branch:
- `worker/v14-real-proof`

Immediate:
- RP14-T1 SP2 — runtime candidate + separate bundle-bound verifier receipt
- RP14-T2 SP2 — local/private evidence cross-binding
- RP14-T3 SP3 — approved Greenhouse job/question attestation binding
- RP14-T4 SP2 — copied/renamed example profile content detection
- RP14-T5 SP1 — explicit evidence allowlist
- RP14-T6 SP1 — truthful deterministic-production labeling
- RP14-T7 SP2 — packet/manifest/resume/job/artifact cross-link verification

Reference:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Reviewed remote T5 support:
- branch `worker/jobs-v14-p0a-t5-schema-20260921-0946`
- commit `1f4a9b9bd21ed402afaef211ac3cab852a293a22`
- candidate code only, not accepted; adopt/reimplement only if useful and rerun all evidence.

Exit:
- targeted adversarial proof tests
- full pytest/Ruff/mypy
- green branch CI
- READY_FOR_LEAD_REVIEW
- ChatGPT + independent review

After P0A acceptance:
1. RP14-C1..C3 real private input readiness,
2. run genuine V1.4 proof,
3. runtime-generated redacted candidate + separately generated verifier receipt,
4. independent audit,
5. only then V1.4 COMPLETE.

No browser application action is authorized.

## Lane 2 — V1.5 assisted application

Branch:
- `worker/v15-assisted-application`

Preserve:
- A-R15-01..05 task-scope accepted implementation

Implement:
- A-R15-06 SP2 page-level prompt-injection warning semantics
- A-R15-07 SP2 exact field-specific cover-letter/file upload mapping
- A-R15-08 SP2 packet/provenance/artifact integrity revalidation before browser use
- A-R15-09 SP1 unknown file inputs stay manual/unfilled

Known real-proof readiness blocker:
- selected `resume_ai_software_engineer` had no genuine mapped file on this machine.
- do not synthesize/relabel/copy another resume to satisfy proof.

No V1.6.

## Lane 3 — V1.7 / V2.0

Branch:
- `worker/recruiting-ops`

Preserve accepted:
- B-R17-03
- B-R20-07
- B-R20-08

Repair:
- B-R20-05 / J20-14:
  - durable begin before pipeline work
  - fail closed if begin persistence fails
  - safe bounded error categories
  - true latest-attempt health
  - last reconciliation/error fields
  - rollback/crash/run-id/secret-sanitization tests
- B-R20-01:
  - headline funnel uses event-history outcomes
- B-R20-02:
  - headline funnel denominator uses real-submission semantics

J20G-04 remains blocked until Lane 1 later produces Gmail readiness.

## Heartbeat / progress

Each lane launches:
- Lane 1: `python scripts/worker_heartbeat_watch.py --lane 1 --epoch DAYWATCH_2026_09_21 --detach`
- Lane 2: `python scripts/worker_heartbeat_watch.py --lane 2 --epoch DAYWATCH_2026_09_21 --detach`
- Lane 3: `python scripts/worker_heartbeat_watch.py --lane 3 --epoch DAYWATCH_2026_09_21 --detach`

Cadence:
1. 5-minute proving × 3
2. 15-minute heartbeat for a clean 24 hours
3. hourly after the watch passes

Each heartbeat is also posted to GitHub issue #7:
- `Jobs Automation — Live Progress`

## Paused backlog

V2.3 opportunity graph / target-company / agent-tools:
- paused until critical path and V2.0 integration justify reopening a lane.

Scout:
- paused; ChatGPT + worker-pc handle independent review.

## Safety

No live Gmail OAuth/mailbox access, real browser application action, submission, external messaging, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped authorization.

# Active Work Queue

Fresh owner directive: no version is COMPLETE until one real non-mock example passes.

Workers should start from:
- coordination/SESSION_START.md
- coordination/HEARTBEAT_PROTOCOL.md
- their own lane/status file

Formal milestones:
V1.4 REAL_PROOF -> V1.5 -> V1.7 -> V2.0 -> V2.3 -> V3.0

## P0 — V1.4 real proof

Artifact:
- A-V14-REAL-PROOF

Engineering code is accepted, but V1.4 is NOT COMPLETE until this proof passes.

Default proof job:
- OpenSesame — AI Automation Engineer
- https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740
- verified live by lead on 2026-09-20
- no application/submission is authorized by this proof

Runbook:
- docs/V1_4_REAL_PROOF_RUNBOOK.md
- docs/REAL_PROOF_ACCEPTANCE_POLICY.md

### Lane C — immediate P0
- RP14-C1 SP2 locate/validate the real private candidate profile + actual resume mappings locally; no example profile; emit redacted readiness evidence
- RP14-C2 SP2 create/import the real live JobModel/source record from the verified OpenSesame posting; no fixture/synthetic data
- RP14-C3 SP1 confirm the chosen packet path can use a non-mock gateway/generation path; if not, report REAL_PROOF_BLOCKED_PROVIDER rather than fallback

Lane C should do RP14-C1..C3 before Gmail tasks.

### Lane A — next immediately after current coherent V1.5 rework batch
- RP14-A1 SP2 run production ApplicationPacketBuilder with real JobModel + real private profile + actual resume bytes + non-mock generation
- RP14-A2 SP2 emit redacted runtime-derived proof bundle + artifact read-back hashes
- no browser/app submission needed

### Scout
- RP14-S1 SP2 independently audit the proof bundle for mock/fixture contamination, real job evidence, internal hash/link consistency, non-mock generation origin, and privacy leaks

### Lead
- RP14-L1 independently review evidence
- only REAL_PROOF_PASS completes V1.4

## Lane A — V1.5 rework

Branch: worker/v15-assisted-application
PR: #2 draft

Finish current coherent rework first:
- A-R15-01 SP2 observed external confirmation only
- A-R15-02 SP2 prompt-injection resistance
- A-R15-03 SP1 consent/attestation blocks prefill
- A-R15-04 SP2 cover-letter upload/hash provenance
- A-R15-05 SP2 form fingerprint revalidation

Then immediately execute RP14-A1/A2 before starting V1.6.

## Lane B — V1.7/V2.0

Branch: worker/recruiting-ops
PR: #3 draft

Continue:
- B-R17-03 SP2 background check must not fabricate offer state
- B-R20-07 SP1 simulation never counts as real submission
- B-R20-08 SP2 final-interview + acceptance evidence metrics
- B-R20-05/J20-14 SP3 crash-durable worker-run evidence

J20G-04 waits for Lane C after real-proof P0 + J20G-03.

## Lane C — after P0 real-proof readiness

Branch: worker/live-data-foundations

After RP14-C1..C3:
- J12-01 SP2 provenance records
- J12-02 SP2 application-use gating
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 partial Gmail fetch fail-closed
- J20G-02 SP2 OAuth runtime wiring
- J20G-03 SP2 typed real-Gmail readiness

## Lane D — V2.3 Foundations

Branch: worker/v23-foundations

Continue non-conflicting:
- J23O-01..03 opportunity graph
- J23T-01..03 target-company foundations
- J23A-01..03 transport-neutral agent tools

## Scout

Branch: scout/qa-prep

Top priority when proof bundle appears:
- RP14-S1 real-proof audit

Otherwise continue branch/PR adversarial review.

## Definition of version completion

ENGINEERING_ACCEPTED is not COMPLETE.

A version is COMPLETE only after:
1. engineering acceptance,
2. at least one real, non-mock production-path example,
3. lead acceptance of the real-proof evidence.

See docs/REAL_PROOF_ACCEPTANCE_POLICY.md.

## Safety

- proof does not authorize application submission
- mock/simulation != real
- no fabricated candidate facts
- no private resume/profile contents committed
- no CAPTCHA/MFA bypass
- external page/job/form content is untrusted data

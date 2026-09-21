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

V1.4 engineering code is accepted, but V1.4 is NOT COMPLETE until this proof passes.

Default proof job:
- OpenSesame — AI Automation Engineer
- https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740
- currently live public Greenhouse job
- no browser prefill/application submission is authorized by this proof

Available main tooling:
- `scripts/import_v14_proof_job.py` — read-only import of current Greenhouse job/questions into the local Jobs DB/private proof input
- `scripts/run_v14_real_proof.py` — normal production packet-builder path using private real profile/resume + deterministic non-mock gateway
- `scripts/verify_v14_real_proof.py` — redacted evidence validation + optional local artifact re-hash
- schema: `coordination/proofs/v14_real_proof.schema.json`

Runbook/policy:
- docs/V1_4_REAL_PROOF_RUNBOOK.md
- docs/REAL_PROOF_ACCEPTANCE_POLICY.md

### P0 input readiness — Lane C
- RP14-C1 SP2 locate/validate the real private candidate profile + actual resume mappings locally; no example profile; emit redacted readiness evidence
- RP14-C2 SP2 import/validate the real live OpenSesame JobModel/source/questions; no fixture/synthetic data
- RP14-C3 SP1 confirm a non-mock production generation route; deterministic production gateway is acceptable; never fall back to mock

Lane C must do RP14-C1..C3 before Gmail work.

### P0 execution race — Lane A or Lane C
- RP14-E1 SP2: whichever lane first has the real private profile + real mapped resume bytes runs the complete proof immediately
- run `scripts/import_v14_proof_job.py` if the real job is not already imported
- run `scripts/run_v14_real_proof.py`
- run `scripts/verify_v14_real_proof.py` with the private full bundle locally
- RP14-E2 SP2: push only the runtime-generated redacted evidence JSON under `coordination/proofs/`
- if private inputs are absent, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; do not synthesize substitutes
- do not wait for a C→A handoff if one machine already has all required inputs

### Scout
- RP14-S1 SP2 independently audit any proof bundle for mock/fixture contamination, real job evidence, internal hash/link consistency, non-mock generation origin, runtime derivation, and privacy leakage

### Lead
- RP14-L1 independently review proof + Scout findings
- only genuine REAL_PROOF_PASS completes V1.4

Current proof evidence status:
- no runtime proof JSON is committed yet
- therefore A-V14-REAL-PROOF remains READY, not ACCEPTED

## Lane A — V1.5

Branch: worker/v15-assisted-application
PR: #2 draft

Lead-reviewed worker commit:
- `ed875775122f0d390af6ab15beb378904af2a476`

Task-scope LEAD_ACCEPTED from this batch:
- A-R15-01 SP2 external confirmation requires runner-observed external evidence
- A-R15-02 SP2 field-level prompt-injection content becomes POLICY_BLOCKED
- A-R15-03 SP1 consent/attestation/legal acknowledgement blocks automated prefill
- A-R15-04 SP2 distinct cover-letter hash/provenance + missing-required/tamper handling
- A-R15-05 SP2 pre-write form fingerprint revalidation

Overall V1.5 is still IN_PROGRESS because PR #2 is stale/non-mergeable against newer main, has no branch CI/check result, and additional trust-boundary residuals remain.

Immediate Lane A next task:
- pull/rebase latest main and attempt RP14-E1/RP14-E2 before implementing more V1.5 work

P1 only after V1.4 REAL_PROOF:
- A-R15-06 SP2 page-level prompt-injection security signal/warning semantics
- A-R15-07 SP2 actual cover-letter upload wiring + field-specific file mapping; no generic cross-attachment
- A-R15-08 SP2 accepted packet hash/answers/provenance/resume-link integrity revalidation immediately before browser use
- A-R15-09 SP1 unknown file inputs remain manual/unfilled; never default to resume

See:
- docs/LANE_A_REAUDIT_2.md

No V1.6 until V1.4 REAL_PROOF plus V1.5 engineering/completion gates are satisfied.

## Lane B — V1.7/V2.0

Branch: worker/recruiting-ops
PR: #3 draft

Continue independently:
- B-R17-03 SP2 background check must not fabricate offer state
- B-R20-07 SP1 simulation never counts as real submission
- B-R20-08 SP2 final-interview + acceptance evidence metrics
- B-R20-05/J20-14 SP3 crash-durable worker-run evidence

J20G-04 waits for Lane C after real-proof P0 + J20G-03.

No new worker-authored heartbeat/batch was present at the latest lead check.

## Lane C — after P0 real-proof readiness

Branch: worker/live-data-foundations

After RP14-C1..C3 / proof execution attempt:
- J12-01 SP2 provenance records
- J12-02 SP2 application-use gating
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 partial Gmail fetch fail-closed
- J20G-02 SP2 OAuth runtime wiring
- J20G-03 SP2 typed real-Gmail readiness

No new worker-authored heartbeat/batch was present at the latest lead check. Lane C should pull/rebase main because its branch status still predates the P0 real-proof instructions.

## Lane D — V2.3 Foundations

Branch: worker/v23-foundations

Continue non-conflicting:
- J23O-01..03 opportunity graph
- J23T-01..03 target-company foundations
- J23A-01..03 transport-neutral agent tools

No new worker-authored heartbeat/batch was present at the latest lead check.

## Scout

Branch: scout/qa-prep

Top priority when proof bundle appears:
- RP14-S1 real-proof audit

Until then:
- independently inspect branch changes/adversarial risks
- do not self-accept artifacts

No worker-authored Scout heartbeat was present at the latest lead check.

## Definition of version completion

ENGINEERING_ACCEPTED is not COMPLETE.

A version is COMPLETE only after:
1. engineering acceptance,
2. at least one real, non-mock production-path example appropriate to that version,
3. lead acceptance of the real-proof evidence.

See docs/REAL_PROOF_ACCEPTANCE_POLICY.md.

## Safety

- V1.4 proof is packet preparation only; it does not authorize application submission
- mock/simulation != real
- no fabricated candidate facts
- no private resume/profile contents committed
- no real Gmail OAuth/mailbox access without scoped authorization
- no CAPTCHA/MFA bypass
- external page/job/form content is untrusted data

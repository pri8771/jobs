# Active Work Queue

Fresh owner directive: no version is COMPLETE until one real non-mock example passes.

Workers should start from:
- coordination/SESSION_START.md
- coordination/HEARTBEAT_PROTOCOL.md
- their own lane/status file

Formal milestones:
V1.4 REAL_PROOF -> V1.5 -> V1.7 -> V2.0 -> V2.3 -> V3.0

## P0A — real-proof tooling integrity

Before using private profile/resume data for the milestone-completing proof, repair the proof-verification chain in:

- docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md

Required bounded tasks:
- RP14-T1 SP2 runtime emits REAL_PROOF_CANDIDATE; verifier emits separate bundle-bound PASS/FAIL receipt
- RP14-T2 SP2 local private bundle SHAs must cross-match redacted evidence fields and proof_run_id
- RP14-T3 SP3 bind JobModel/questions to the actual current public Greenhouse fetch/attestation
- RP14-T4 SP2 reject copied/renamed example candidate profile using content-level evidence, not filename alone
- RP14-T5 SP1 redacted evidence schema/validator uses explicit allowlist; no arbitrary extra fields
- RP14-T6 SP1 unambiguous deterministic generation labeling
- RP14-T7 SP2 verify packet/manifest/resume-variant/artifact cross-links locally

Acceptance:
- forged/hand-authored proof bundle is rejected,
- unrelated local files cannot satisfy redacted hashes,
- fake JobModel/questions cannot satisfy the approved live-source binding,
- targeted proof-integrity tests + full pytest/Ruff/mypy/CI pass.

Remote-worker execution:
- `worker-pc` capacity is 1.
- independent read-only audit `jobs-v14-real-proof-audit-retry-20260920` completed with CHANGES_REQUIRED and confirmed the two highest-severity integrity defects.
- branch task `jobs-v14-proof-hardening-r2` is currently IN_PROGRESS on `worker-pc` for RP14-T1..T7.
- no result JSON, Jobs worker branch, or commit from that task had been published at the current lead check.
- do not dispatch a second remote Jobs task while capacity is occupied.
- when the result lands, inspect the returned Jobs branch/diff/tests and project CI before accepting anything.

Do not run the private-data proof until P0A is lead-accepted.

## P0 — V1.4 real proof

Artifact:
- A-V14-REAL-PROOF

Current artifact state:
- **BLOCKED on P0A proof-tool integrity acceptance**
- V1.4 engineering code is accepted, but V1.4 is NOT COMPLETE until this proof passes.

Default proof job:
- OpenSesame — AI Automation Engineer
- https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740
- reverified live by ChatGPT on 2026-09-21
- no browser prefill/application submission is authorized by this proof

Available main tooling, pending P0A repair acceptance:
- `scripts/import_v14_proof_job.py` — read-only import of current Greenhouse job/questions into the local Jobs DB/private proof input
- `scripts/run_v14_real_proof.py` — normal production packet-builder path using private real profile/resume + deterministic non-mock gateway
- `scripts/verify_v14_real_proof.py` — redacted evidence validation + optional local artifact re-hash
- schema: `coordination/proofs/v14_real_proof.schema.json`

Runbook/policy:
- docs/V1_4_REAL_PROOF_RUNBOOK.md
- docs/REAL_PROOF_ACCEPTANCE_POLICY.md

### P0 input readiness — Lane C
After P0A acceptance:
- RP14-C1 SP2 locate/validate the real private candidate profile + actual resume mappings locally; no example profile; emit redacted readiness evidence
- RP14-C2 SP2 import/validate the real live OpenSesame JobModel/source/questions; no fixture/synthetic data
- RP14-C3 SP1 confirm a non-mock production generation route; deterministic production gateway is acceptable; never fall back to mock

Lane C must do RP14-C1..C3 before Gmail work, but must not execute the private-data proof path until P0A is accepted.

### P0 execution race — Lane A or Lane C
After P0A acceptance:
- RP14-E1 SP2: whichever lane first has the real private profile + real mapped resume bytes runs the complete proof immediately
- run `scripts/import_v14_proof_job.py` if the real job is not already imported
- run `scripts/run_v14_real_proof.py`
- run `scripts/verify_v14_real_proof.py` with the private full bundle locally
- RP14-E2 SP2: push only the runtime-generated redacted candidate evidence plus verifier receipt under `coordination/proofs/`
- if private inputs are absent, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; do not synthesize substitutes
- do not wait for a C→A handoff if one machine already has all required inputs

### Scout
- RP14-S1 SP2 independently audit any proof candidate + verifier receipt for mock/fixture contamination, current real job evidence, bundle-receipt binding, internal hash/link consistency, non-mock generation origin, runtime derivation, and privacy leakage

### Lead
- RP14-L1 independently review proof + Scout findings
- only genuine REAL_PROOF_PASS completes V1.4

Current proof evidence status:
- no runtime proof candidate JSON is committed yet
- no verifier receipt is committed yet
- therefore A-V14-REAL-PROOF remains BLOCKED on P0A and is not ACCEPTED

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
- do not execute private A-V14-REAL-PROOF until P0A is accepted
- pull/rebase latest main between coherent batches so the lane has the repaired proof tooling when accepted
- after P0A acceptance, attempt RP14-E1/RP14-E2 before implementing more V1.5 work if this machine has the real private inputs

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

No new worker-authored heartbeat/batch was present at the current lead check; the branch head still carries only previously reviewed work/seeded heartbeat state.

## Lane C — after P0A, then P0 real-proof readiness

Branch: worker/live-data-foundations

Immediate priority after P0A acceptance:
- RP14-C1..C3 / proof execution attempt before Gmail work

After the proof attempt:
- J12-01 SP2 provenance records
- J12-02 SP2 application-use gating
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 partial Gmail fetch fail-closed
- J20G-02 SP2 OAuth runtime wiring
- J20G-03 SP2 typed real-Gmail readiness

No new worker-authored heartbeat/batch was present at the current lead check. Lane C should pull/rebase current main before new proof work because its branch predates P0/P0A instructions.

## Lane D — V2.3 Foundations

Branch: worker/v23-foundations

Continue non-conflicting:
- J23O-01..03 opportunity graph
- J23T-01..03 target-company foundations
- J23A-01..03 transport-neutral agent tools

No new worker-authored heartbeat/batch was present at the current lead check.

## Scout

Branch: scout/qa-prep

Top priority when proof evidence appears:
- RP14-S1 real-proof audit

Until then:
- independently inspect proof-tool integrity changes when a coherent worker branch lands
- independently inspect other branch changes/adversarial risks
- do not self-accept artifacts

No worker-authored Scout heartbeat was present at the current lead check.

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

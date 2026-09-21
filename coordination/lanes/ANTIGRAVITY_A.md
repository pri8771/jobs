# Antigravity Lane A Status

Branch:
- worker/v15-assisted-application

PR:
- #2 — draft review container

Lane:
- Application Execution

Owner:
- Antigravity Session A

Reviewer:
- ChatGPT

## Foundation

A-V14-PACKET-SAFETY is ENGINEERING_ACCEPTED on main.
V1.4 is NOT COMPLETE until A-V14-REAL-PROOF is ACCEPTED.

## V1.5 worker batch reviewed

Worker commit:
- `ed875775122f0d390af6ab15beb378904af2a476`

Lead reviewed the actual branch code/tests for the first bounded rework batch.

Task-scope lead acceptance:
- A-R15-01 SP2 — LEAD_ACCEPTED: caller `receipt_text` / `auto_confirm` alone cannot establish SUBMITTED; only runner-observed external evidence/confirmation URL can.
- A-R15-02 SP2 — LEAD_ACCEPTED for field-level J15-11 scope: prompt-like content in field name/label/placeholder/options becomes POLICY_BLOCKED.
- A-R15-03 SP1 — LEAD_ACCEPTED: consent/attestation/legal acknowledgement is a prefill blocking barrier.
- A-R15-04 SP2 — LEAD_ACCEPTED for distinct cover-letter hash/provenance and missing-required/tamper behavior.
- A-R15-05 SP2 — LEAD_ACCEPTED: form structure is re-inspected immediately before first write and fingerprint mismatch blocks.

Worker-reported local evidence:
- targeted adversarial tests: 27 passed
- full pytest: 132 passed
- Ruff: clean
- mypy: no new errors

GitHub evidence:
- branch commit currently has no GitHub Actions/check result of its own,
- PR #2 is still draft and currently non-mergeable against newer main,
- therefore the overall V1.5 artifacts remain IN_PROGRESS pending current-main integration plus remaining post-proof residuals.

## P0 NOW — V1.4 REAL_PROOF

Do not spend the next batch on V1.5 residuals before trying the real proof.

1. Pull/rebase latest main so the branch has:
   - `scripts/import_v14_proof_job.py`
   - `scripts/run_v14_real_proof.py`
   - `scripts/verify_v14_real_proof.py`
2. If this machine has the actual private candidate profile and actual mapped resume bytes, immediately execute RP14-E1/RP14-E2.
3. Import the currently-live OpenSesame proof job if needed.
4. Run the production V1.4 packet proof using the real private profile/resume and the real application questions.
5. Run the verifier with the local private full bundle.
6. Push ONLY the runtime-generated redacted proof JSON under `coordination/proofs/` plus a heartbeat requesting RP14-S1/RP14-L1 review.

No browser prefill or application submission is authorized or required.

If the required private profile/resume files are not present on this machine, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT` immediately; do not create substitutes.

## P1 after V1.4 REAL_PROOF

Lead second re-audit:
- `docs/LANE_A_REAUDIT_2.md`

Remaining V1.5 tasks:
- A-R15-06 SP2 — page-level prompt-injection inspection/security warning semantics.
- A-R15-07 SP2 — actual cover-letter file-upload wiring + field-specific upload mapping; eliminate generic file-input cross-attachment.

These are real V1.5 residuals but must not delay V1.4 REAL_PROOF.

## V1.6 gate

Do not start V1.6 until:
1. A-V14-REAL-PROOF is accepted,
2. A-R15-06/07 are repaired and reviewed,
3. V1.5 engineering is integrated with green evidence, and
4. the V1.5 real-proof requirement is satisfied before V1.5 is called COMPLETE.

## Status

P0 REAL_PROOF EXECUTION / V1.5 TASK-SCOPE REWORK ACCEPTED

# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`
- draft PR #8

Owner:
- active Lane 1 worker

Reviewer:
- ChatGPT lead
- worker-pc may provide bounded independent audit support

Priority:
- P0 / project critical path

## Current lead review — 2026-09-21 16:52Z

Worker batch:
- commit `8f8c21f88512aa32521c78285b72dc9da298672e`
- CI #401: GREEN
- RP14-T1..T7 implementation is substantial, but P0A is **REWORK**, not accepted.

Blocking findings from direct diff review:
1. Candidate/receipt separation is still open: candidate schema/verifier accept `REAL_PROOF_PASS`; candidate bundles must accept only `REAL_PROOF_CANDIDATE`.
2. A structurally valid hand-authored redacted bundle can still receive `REAL_PROOF_PASS` when `--local-full-bundle` is omitted. PASS must require successful private/local cross-binding; structural-only validation may not produce PASS.
3. Rejected candidates write `REAL_PROOF_FAIL` receipts only when `--receipt-output` is supplied. Default rejection must also emit a candidate-bundle-bound FAIL receipt.
4. RP14-T7 does not independently recompute the canonical packet hash from manifest job/profile/resume IDs + artifact hashes + answers/provenance; matching two supplied packet-hash strings is insufficient. Recompute and verify the job/resume-variant linkage.

The same findings are posted on PR #8. A worker-pc read-only audit of the same commit is in progress; incorporate any additional valid findings when it returns.

## Immediate bounded assignment

1. Pull/rebase latest `main` without losing the P0A implementation.
2. If any `FIVE_MIN_2026_09_21` watcher is running, stop it. The authoritative epoch is `DAYWATCH_2026_09_21`.
3. Continue the current DAYWATCH heartbeat under `coordination/heartbeats/LANE_1.md`; actual timestamps govern credit.
4. Repair the four findings above.
5. Add adversarial tests proving:
   - a candidate bundle self-labeled PASS is rejected,
   - a candidate without local/private binding cannot obtain a PASS receipt,
   - a rejected candidate produces a bound FAIL receipt under default invocation,
   - a forged manifest/candidate pair with matching invented packet hashes fails canonical re-derivation.
6. Run focused proof tests plus full `pytest`, `ruff`, `mypy`, and branch CI.
7. Push one coherent repair commit and set `READY_FOR_LEAD_REVIEW` / `REVIEW`.

Do **not** use private candidate/resume inputs or execute the real proof until ChatGPT explicitly accepts P0A.

## After P0A acceptance

Immediately:
1. validate the real private candidate profile + exact selected-resume mapping,
2. import/revalidate the live OpenSesame job/questions,
3. run the genuine V1.4 packet proof,
4. commit only runtime-generated redacted candidate evidence + separate verifier receipt,
5. stop for lead acceptance.

No Gmail OAuth/mailbox access, browser prefill, application submission, external messaging, or fabricated candidate facts are authorized.

## Heartbeat

Authoritative epoch: `DAYWATCH_2026_09_21`.

Launch only if no correct watcher is already running:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch DAYWATCH_2026_09_21 --task "V1.4 real-proof tooling RP14-T1..T7" --detach`

Cadence: 3 proving heartbeats at 4–7 minute gaps → 15-minute watch for a clean 24 hours → hourly.

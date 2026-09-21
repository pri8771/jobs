# Lane 1 — V1.4 Real-Proof Critical Path

Branch:
- `worker/v14-real-proof`

Owner:
- fresh Antigravity session

Reviewer:
- ChatGPT lead
- worker-pc may be used for independent bounded review when available

Priority:
- P0 / project critical path

## Mission

Make V1.4 genuinely complete under the owner's rule:
engineering acceptance + one real non-mock production-path example.

## Immediate scope — P0A

Implement RP14-T1..T7 from:
- `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`
- `coordination/WORK_QUEUE.md`

Required:
- runtime candidate bundle does not self-declare PASS,
- separate verifier receipt bound to bundle SHA,
- local/private evidence cross-binding,
- real Greenhouse job/question attestation binding,
- copied example profile rejection by content,
- explicit committed-evidence allowlist,
- truthful deterministic-production labeling,
- packet/manifest/resume/job/artifact cross-link verification,
- adversarial tests + full pytest/Ruff/mypy/CI.

Remote RP14-T5 support commit `1f4a9b9...` is reviewed candidate code only; adopt/cherry-pick/reimplement only if useful after rebasing, then prove it in the coherent batch.

## After P0A lead acceptance

Immediately:
1. validate real private profile + exact resume mapping,
2. import/revalidate real OpenSesame job/questions,
3. execute the real V1.4 packet proof,
4. emit redacted runtime candidate + independent verifier receipt,
5. stop for lead review.

No browser prefill or application submission is authorized.

## Heartbeat

Launch:
`python scripts/worker_heartbeat_watch.py --lane 1 --epoch DAYWATCH_2026_09_21 --task "V1.4 real-proof tooling RP14-T1..T7" --detach`

Heartbeat progress is posted to GitHub issue #7.

## Exit

READY_FOR_LEAD_REVIEW only after one coherent tested P0A batch is pushed.

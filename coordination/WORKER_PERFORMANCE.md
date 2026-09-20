# Worker Performance Ledger

This ledger tracks Antigravity task performance by story-point complexity.

Story-point rubric:
- docs/WORKER_STORY_POINTS.md

## Rules

- Antigravity may append worker-reported completion evidence.
- ChatGPT owns lead acceptance/rework judgments.
- Do not retroactively invent precise scores for old broad batches when the original scope was not cleanly bounded.
- Start rigorous task-level tracking with the V1.4 repair sprint.

## Summary

| SP | Attempted | Lead Accepted | First-Pass Accepted | Rework Tasks | Accepted Points |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 |

Update this summary only from accepted task records below.

## Task ledger

| Task ID | SP | Title | Owner | Dependencies | Status | Worker commit | CI first push | Lead rework cycles | Lead notes |
|---|---:|---|---|---|---|---|---|---:|---|
| J14-01 | 2 | Fail closed on missing selected resume | Antigravity | none | READY | — | — | 0 | V1.4 repair |
| J14-02 | 2 | Exact resume variant -> source mapping | Antigravity | none | READY | — | — | 0 | V1.4 repair |
| J14-03 | 3 | ResumeVariant DB model + migration | Antigravity | none | READY | — | — | 0 | Architecture already specified |
| J14-04 | 2 | Link packet to immutable ResumeVariant | Antigravity | J14-03 | READY | — | — | 0 | Permanent attribution |
| J14-05 | 3 | Materialize artifacts + hash read-back | Antigravity | none | READY | — | — | 0 | Prefer small ArtifactStore |
| J14-06 | 2 | Remove runtime hard-coded candidate claims | Antigravity | none | READY | — | — | 0 | Test fixtures may be synthetic |
| J14-07 | 2 | Fail closed on model routing/provider errors | Antigravity | none | READY | — | — | 0 | Explicit mock only |
| J14-08 | 3 | Screening-answer provenance + hallucination guard | Antigravity | none | READY | — | — | 0 | Consequential answers need evidence |
| J14-09 | 1 | Force EEO/self-ID questions manual | Antigravity | none | READY | — | — | 0 | Always unresolved |
| J14-10 | 3 | Rebuild inspectable packet manifest | Antigravity | J14-01..J14-09 | READY | — | — | 0 | Use verified bytes/evidence |
| J14-11 | 1 | Full V1.4 verification evidence bundle | Antigravity | J14-10 | READY | — | — | 0 | pytest/ruff/mypy/CI + evidence |

## Historical notes

- V1.1 stabilization was delivered as a broad unscored batch before this ledger existed; lead found one reconciliation defect requiring repair.
- The V1.2-V1.4 bundle in commit 3735f13 was also too broad to score meaningfully as one story. Its failure to pass lead review is one reason the SP1-SP5 decomposition policy now exists.

## How ChatGPT should use this ledger

After each worker push:
1. match commits to task IDs,
2. audit acceptance criteria,
3. mark each task LEAD_ACCEPTED or REWORK,
4. increment rework cycles when applicable,
5. update summary counts,
6. use observed performance to decide whether future SP4-SP5 work should be split further.

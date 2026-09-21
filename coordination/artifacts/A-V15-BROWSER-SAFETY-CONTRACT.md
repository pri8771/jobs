# A-V15-BROWSER-SAFETY-CONTRACT

- Type: contract / safety / implementation guidance
- Phase: V1.5
- Status: IN_PROGRESS
- Owner: ChatGPT / Antigravity Lane A implementation
- Reviewer: ChatGPT lead review / user boundary for live execution
- Dependencies: A-V14-PACKET-SAFETY ACCEPTED
- Downstream: A-V15-ASSISTED-APPLICATION

## Purpose

Define and verify a safe assisted-browser runtime contract before real application prefill begins.

## Output

- `docs/V1_5_BROWSER_SAFETY_CONTRACT.md`
- `docs/LANE_A_V15_REAUDIT.md`

## Worker evidence reviewed

Worker commit:
- `3d17fa8` on `worker/v15-assisted-application`

Useful first-pass implementation exists for:
- manual barrier classification,
- pre-submit review manifest,
- immediate resume upload hash verification,
- single persistent Playwright context,
- unresolved/unknown-required stop gates,
- mock isolation.

Worker reported 118/118 local pytest plus clean Ruff/mypy. GitHub CI did not run on the branch commit itself.

## Lead residual findings

Artifact remains IN_PROGRESS because the re-audit found bounded safety gaps:

- packet answers/provenance are not revalidated against the exact accepted `packet_hash` before fill,
- form fingerprint is computed but not rechecked before first write,
- arbitrary local/free-form receipt text containing confirmation-like words can satisfy submission truth,
- unknown file inputs can default to resume upload,
- J15-11 external-form prompt-injection resistance was added on main after the worker branch base and is not implemented in the batch.

Authoritative residuals:
- A-R15-01..A-R15-05 in `docs/LANE_A_V15_REAUDIT.md`
- current `coordination/WORK_QUEUE.md`

## First-pass accepted slices

- J15-02 SP2
- J15-03 SP3
- J15-04 SP2
- J15-07 SP3
- J15-08 SP2
- J15-10 SP1

These task-slice acceptances do not accept the overall V1.5 artifacts.

## Acceptance criteria

- exact accepted packet integrity and answer provenance verified at browser boundary,
- inspect-before-write behavior,
- field classification taxonomy with safe file-input handling,
- per-field provenance,
- manual-barrier behavior,
- persistent visible-session requirement,
- upload-integrity check,
- pre-submit manifest,
- form-change detection immediately before write,
- typed externally sourced confirmation boundary,
- mock isolation,
- external form/page prompt-injection resistance,
- adversarial acceptance tests,
- green integrated CI.

## Risks / boundaries

- No live application/form execution is authorized by engineering progress.
- External application content is attacker-controlled input from the agent perspective.
- User-approved proof-job selection remains a separate dependency for real application evidence.

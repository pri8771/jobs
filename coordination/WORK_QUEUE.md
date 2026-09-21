# Active Work Queue

Owner target:
**Get V2.3 genuinely working as fast as safely possible, with a real-life production-path test for every required checkpoint.**

## Operating model

- exactly one active implementation worker/session,
- exactly one five-minute heartbeat watcher,
- historical branches are sequential work surfaces,
- worker tasks should normally be SP1/SP2,
- live proof is separate from engineering acceptance,
- later engineering may proceed behind a blocked live gate, but formal REAL_PROVEN/COMPLETE remains sequential.

Lead-accepted V2.3 planning package:
- `docs/V23_LEAD_REVIEW_20260921.md`
- `docs/V23_MASTER_PLAN.md`
- `coordination/V23_WORKER_QUEUE.md`

The V23 worker queue is planning inventory. ChatGPT promotes one bounded artifact/task at a time here.

## Formal live status

- V1.4 live proof: MISSING
- V1.5 live assisted-browser proof: MISSING
- V1.6 real externally-confirmed system submission: MISSING
- V1.7 real lifecycle proof: MISSING
- V2.0 live acceptance: MISSING
- V2.3 live acceptance: MISSING

No later checkpoint may be called REAL_PROVEN/COMPLETE while an earlier required checkpoint remains incomplete.

## P0 — A-V14-P0A-INTEGRITY

Active historical work surface:
- `worker/v14-real-proof`
- PR #8 is historical review/source container

Latest active-branch production state:
- substantive proof repair: `5e5058461d5371f292c93e0c53cb0b93caba7e44`
- later active-branch commits through `f3a0c414...` are heartbeat-only
- lead verdict on the active branch: REWORK

Two verified defects remain on that active branch:
1. persisted DB linkage is bypassed if no DB target is supplied;
2. source attestation is not independently bound to persisted Greenhouse `JobSource` evidence.

### New bounded support evidence

worker-pc branch:
- `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- commit `062ca922c640d964220b550a06f61288b9a040c9`
- changed only:
  - `scripts/verify_v14_real_proof.py`
  - `tests/test_real_proof_verifier.py`

Lead diff inspection indicates this support commit attempts to:
- make a proof DB target mandatory,
- reject unusable/in-memory/unrelated proof DB evidence,
- bind persisted Job/JobSource Greenhouse provider/source kind/public ID/API URL/fetch time/content hash/question hash/canonical URL,
- add adversarial tests for forged/missing/tampered persisted evidence.

Support branch remains **review input only**, not accepted/integrated truth.

### Immediate bounded assignment

Artifact:
`A-V14-P0A-INTEGRITY`

Tasks:
1. **R14-P01 / SP1** — audit support commit `062ca922...` against the exact P0A contract; port/adapt only the correct production changes onto the current V1.4 work surface or clean integration branch.
2. **R14-P02 / SP1** — make every persisted-source/DB forgery case fail; remove any temporary xfail once behavior is correct.
3. **R14-P03 / SP1** — run the full proof-integrity adversarial suite; every required case must pass.
4. **R14-P04 / SP1** — exact-head full pytest, Ruff, format, mypy; record `CI_BLOCKED_ACCOUNT` if hosted Actions still cannot start; obtain independent exact-head validation when practical.
5. set `READY_FOR_LEAD_REVIEW`.

Do not use private candidate/resume inputs until ChatGPT accepts P0A.

## After P0A lead acceptance

Next canonical order:

1. `A-V14-CLEAN-INTEGRATION`
2. `A-V14-REAL-PROOF` — real job + genuine private profile + exact genuine selected resume + production packet + separate verifier PASS
3. `A-V15-CLEAN-INTEGRATION`
4. V1.5 engineering acceptance
5. `A-V15-LIVE-ASSISTED-PROOF`
6. V1.6 authorization/idempotency/preflight/confirmation/hygiene/transport engineering
7. `A-V16-FIRST-REAL-SUBMISSION`
8. `A-V17-ENGINEERING-RECONCILIATION`
9. `A-V17-LIVE-LIFECYCLE-PROOF`
10. V2.0 engineering/live campaign
11. V2.3 engineering/live campaign

Safe V2.0/V2.3 preparation may be pulled forward when it does not conflict with the active artifact and the plan permits it.

## Real test identity authorization

The owner has authorized bounded real-provider canaries using an existing owner-controlled identity or a dedicated test identity via the owner's `unsubscriber` Google Cloud alias when supported.

See:
- `docs/AUTHORIZATION_GATES.md`

This does not authorize employer submission, unsolicited third-party messaging, calendar mutation, or spending.

## Heartbeat

Epoch:
`FIVE_MIN_2026_09_21`

One active implementation session = one watcher.

The historical V1.4 heartbeat last recorded #18 at 19:18:36Z and is stale. Before a new implementation worker starts, verify the prior watcher/process is dead and start exactly one current watcher on the active work surface.

## Review rule

Workers:
- implement,
- test,
- push,
- hand off `READY_FOR_LEAD_REVIEW`.

ChatGPT:
- inspects actual code/diff/tests/evidence,
- accepts or issues one bounded rework,
- promotes the next artifact/task.

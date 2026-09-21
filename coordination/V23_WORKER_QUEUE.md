# V2.3 next-round worker queue

Status: **PREPARED — NOT ACTIVATED**. Do not change the running Fable V1.4/V1.5 assignment.

## Authority and activation

User is product owner. ChatGPT is lead and acceptance authority. Fable/Claude is the assigned worker. This queue becomes active only after the current handoff, live-Git reconciliation and explicit lead promotion into `coordination/WORK_QUEUE.md`.

The next-round operating contract is `docs/V23_NEXT_ROUND_CONTRACT.md`. Verified planning defects and exact corrections are in `docs/V23_REVIEW_FINDINGS_20260921.md`. The machine-readable corrective tasks are `coordination/V23_HARDENING_TASKS.json`.

These are corrections to the existing feature inventory, not 42 new features. Retain valid tasks from:
- `docs/V23_TASK_GRAPH_RECOVERY.md`
- `docs/V23_TASK_GRAPH_V20.md`
- `docs/V23_TASK_GRAPH_V23.md`

For mapped contradictions, the activated correction governs. Do not run both definitions. Reuse an already accepted equivalent instead of rebuilding it.

## First steps at the next safe handoff

1. Audit Fable's exact V1.4/V1.5 head, producer-to-verifier tests and genuine live receipts. Do not assume the old blocker still exists.
2. Reconcile one active assignment and heartbeat owner; resolve conflicting instruction writers once rather than repeatedly overwriting main.
3. Run the plan checker and inspect the consolidated readiness ledger. No account/credential/live action is created by the checker.
4. Prove the first prospective submission route is actually accessible and permitted before implementing transport-specific assumptions.
5. Promote one bounded artifact from the packets below. Do not reopen already accepted work.

## Execution packets

| Packet | Work | Done when |
|---|---|---|
| P0 | H-GOV-01/02, H-ACCESS-01/02 | plan revision and actual access/input gates are known |
| P1 | H-PROOF-01/02/03 | accepted producers/consumers agree; code and evidence identities are stable |
| P2 | H-ID, H-AUTH, H-SUB with existing R16 work | durable submission claim, real scoped authority, preflight, confirmation and approved transport are accepted |
| P3 | H-MAIL with existing Gmail/CRM work | complete bounded paging, direction/time semantics, genuine lifecycle replay are accepted |
| P4 | H-AN-01, H-UI-02, H-OPS-01/02 with existing V2.0 work | actual daily user flow and nonempty PostgreSQL/artifact restore work |
| P5 | H-TOOL, H-GRAPH, H-WATCH, H-AN-02, H-UI-01/03 with existing V2.3 work | useful evidence-backed intelligence and correctly governed tools work |
| P6 | H-PROOF-04/05, H-OPS-03 | independently verified real campaign plus restart/replay evidence passes |
| P7 | H-V3-01..07 | deferred V3 contracts reviewed after V2.3 and a separate V3 assignment; no V3 implementation here |

Dependencies, code surfaces, implementation steps, proposed test names, failure behavior and model/effort classes are defined per task in JSON. Packets are review/organization groups, not giant commits. SP1/SP2 labels do not justify combining unrelated work.

## Token-efficient task loading

```sh
python scripts/validate_v23_hardening_plan.py --check --self-test
python scripts/validate_v23_hardening_plan.py --task H-ID-01
```

The helper is standard-library-only and read-only. It validates plan structure and renders a task; it does not validate application code, infer a live PASS, assign work or grant authority.

## Non-negotiable finish gates

Each required milestone V1.4, V1.5, V1.6, V1.7, V2.0 and V2.3 needs accepted engineering and genuine production-path evidence. A provider canary with synthetic content is not a genuine candidate/recruiting event. A user-attested manual submission remains unconfirmed until accepted external confirmation.

Engineering may advance behind a live gate. Formal completion cannot silently skip that gate. Missing transport/access is reported precisely; the worker must not fabricate a pass or replace a desired job with a dummy target.

After each coherent artifact: exact code/test/evidence handoff, `READY_FOR_LEAD_REVIEW`, then stop that artifact until its gate opens. Keep only one active implementation session and one five-minute heartbeat owner under the reconciled owner directive. Planning helpers and subagent reads do not create additional watchers.

Do not start broad V3 implementation, change Fable's current scope, create accounts, read mail, submit applications, message third parties or spend money because this plan exists.

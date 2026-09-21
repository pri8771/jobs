# A-V23-AGENT-TOOLS

- Type: service/tool architecture (V3 bridge)
- Phase: V2.3
- Status: READY
- Owner: V2.3 implementation surface (lane per lead decision D3); `PermissionGate` requires Opus-class implementation or review
- Reviewer: ChatGPT
- Story points: 19 (V23-TL-01..11)
- Dependencies: stable V2 services on main; V2.3 services for the tools that wrap them; V1.6 `ScopedApprovalService` (R16-A02) only for P3 *execution* — until it lands, P3 tools return `NEEDS_REVIEW/BLOCKED` truthfully
- Downstream: V3 agent runtime, A-V30-PERMISSION-MODEL (reuses the gate and approval table), any MCP/HTTP wrapper (deferred)

## Contract
See docs/V2_3_AGENT_TOOL_LAYER.md, docs/V3_TOOL_PERMISSION_MATRIX.md, docs/V3_RUNTIME_DATA_CONTRACTS.md.

## Design decisions proposed (planning pass 2026-09-21; ratify per D-list in `docs/V23_MASTER_PLAN.md` §11)
- `tools/envelope.py` types are field-compatible with the V3 `ToolRequest`/`ToolResult`/`PermissionDecision` contracts (request id, optional task/agent identity, action class, input hash, idempotency key; result status includes `PARTIAL|BLOCKED|NEEDS_REVIEW`, evidence refs, audit ref, explicit `simulated`).
- `PermissionGate` is deterministic: P4 deny; class above caller ceiling deny (`min()` rule); P0/P1 allow; P2 needs explicit external-prep flag + destination policy ASSISTED/AUTO_ALLOWED + kill switch off; P3 needs a valid scoped approval bound to exact target/hash/method + AUTO_ALLOWED + kill switch off; all P2/P3 decisions audited.
- Audit rows in `audit_log` carry `request_id`, `input_hash`, `idempotency_key`, `result_hash`, `simulated` so V3 traces can reference them; no new tables in V2.3.
- No agent-framework or MCP import under `tools/`; a wrapper may be added after V2.3.

## Planned tasks
V23-TL-01 envelope · TL-02 registry · TL-03 gate · TL-04 audit/replay · TL-05 runtime pipeline · TL-06/07 read tools · TL-08 preparation tools · TL-09 external-action contracts (`open_assisted_application` P2 wrapper; `submit_application`, `send_message`, `update_external_calendar` P3 declared, blocked/not implemented) · TL-10 CLI · TL-11 adversarial tests. Full specs: `docs/V23_TASK_GRAPH_V23.md` §6.

## Acceptance
Contract acceptance (callable without an agent framework; mock results labeled; no DB bypass; transport swap does not change domain behavior) plus the five adversarial rows, mapped in `docs/V23_TEST_MATRIX.md`.

# Phase Gate Matrix — V1.4 to V3.0

Purpose:
Define what must be true before the single Antigravity implementation session advances from one phase to the next.

This is a lead-side readiness/acceptance contract. It does not override live repository status.

## Universal states

For every milestone:
- IMPLEMENTED — code exists.
- ENGINEERING_ACCEPTED — code/tests/CI/adversarial behavior accepted by ChatGPT lead.
- REAL_PROVEN — at least one genuine non-mock production-path example accepted.
- COMPLETE — ENGINEERING_ACCEPTED + REAL_PROVEN.

Green CI alone does not establish ENGINEERING_ACCEPTED.
Mocks/fixtures never establish REAL_PROVEN.

## Gate G14A — V1.4 proof tooling ready

Required:
- all P0A verifier integrity findings closed,
- structural-only proof cannot PASS,
- local/private candidate binding mandatory,
- public job/source attestation bound,
- canonical packet/job/resume/artifact linkage independently recomputed,
- adversarial forged bundles fail,
- focused tests + full pytest/Ruff/mypy + current-head CI green,
- independent audit finds no blocking proof hole,
- ChatGPT lead accepts P0A.

Unblocks:
- genuine V1.4 packet proof.

## Gate G14B — V1.4 complete

Required:
- genuine live public job,
- genuine private candidate profile,
- exact genuine selected resume bytes,
- production packet path,
- runtime-generated REAL_PROOF_CANDIDATE,
- separately generated verifier PASS receipt,
- independent review,
- ChatGPT lead marks REAL_PROVEN.

Unblocks:
- formal V1.4 completion and V1.5 proof path.

## Gate G15 — V1.5 engineering accepted

Required:
- accepted A-R15-01..05 preserved,
- A-R15-06..09 accepted,
- page prompt-injection semantics fail closed,
- exact upload-field mapping,
- immediate pre-browser packet/provenance/artifact revalidation,
- unknown file inputs remain manual,
- focused adversarial tests + full checks + CI green,
- ChatGPT accepts A-V15-BROWSER-SAFETY-CONTRACT and A-V15-ASSISTED-APPLICATION.

Optional real proof:
- live visible assisted flow when explicitly authorized.
- submission itself is not implied.

Unblocks:
- V1.6 engineering.

## Gate G16A — V1.6 engineering accepted

Required:
- typed authorization record,
- deny-by-default expiring policy registry,
- immutable attempt/idempotency semantics,
- pre-submit integrity gate,
- kill switch / rate limits / session-block routing,
- external confirmation validator,
- ATS adapter interface,
- no fake live adapter,
- ambiguous outcome = SUBMISSION_UNCONFIRMED,
- adversarial suite accepted,
- exact-head CI green,
- independent safety review,
- ChatGPT accepts A-V16-SUBMISSION-CONTRACT + A-V16-SUBMISSION-ENGINE-REPAIR.

Unblocks:
- user-authorized first real supported submission.

## Gate G16B — V1.6 real proof

Required:
- user approves exact job + packet + method,
- current destination policy permits system submit,
- no unresolved consequential answer,
- no CAPTCHA/MFA bypass,
- idempotency preflight passes,
- external confirmation is captured,
- APPLICATION_SUBMITTED emitted only after confirmation,
- redacted evidence reviewed,
- ChatGPT marks REAL_PROVEN.

Unblocks:
- reliable application execution evidence for V2.0.

## Gate G17 — V1.7 recruiting operations

Required:
- CRM evidence artifact accepted,
- interview/follow-up artifact accepted,
- multi-role recruiter/thread ambiguity safe,
- manual correction/merge auditable,
- timeline reconstructable from source evidence,
- lifecycle/follow-up tests + full CI green,
- genuine lifecycle proof when real evidence is available/authorized,
- ChatGPT accepts A-V17-MILESTONE-GATE.

Unblocks:
- V2.0 integrated OS gate.

## Gate G20A — V2.0 engineering ready

Required accepted engineering:
- V1.7 milestone,
- control center,
- reliability,
- worker-run history,
- analytics,
- Gmail runtime readiness,
- deterministic cross-subsystem integration fixture,
- safe application execution path.

May still be missing explicit live OAuth/data boundary.

Label:
- ENGINEERING_READY only.

## Gate G20B — V2.0 live accepted

Required:
- real read-only Gmail/live data canary,
- real candidate/resume identity,
- real opportunity,
- real packet/application lifecycle path,
- recruiter/lifecycle evidence when available,
- dashboard/health reflect real runtime state,
- backup/recovery drill,
- real analytics with uncertainty labels,
- audit trail reconstructs important state transitions,
- ChatGPT accepts A-V20-INTEGRATED-OS.

Unblocks:
- V2.3.

## Gate G23 — V2.3 career intelligence

Required:
- opportunity graph projection accepted,
- strategy learning accepted,
- target-company watch accepted,
- interview intelligence accepted,
- stable transport-neutral agent tool layer accepted,
- evidence/source references preserved,
- no speculative relationship treated as fact,
- sample-size/causal guardrails enforced,
- ChatGPT accepts A-V23-CAREER-INTELLIGENCE.

Unblocks:
- V3 agent runtime.

## Gate G30A — V3 platform ready

Required:
- permission model accepted,
- durable agent runtime accepted,
- shared memory contract accepted,
- agent evaluation/observability accepted,
- stable V2.3 tools,
- no direct DB bypass for agent external-action truth,
- durable task/checkpoint/retry semantics,
- human approval queue for consequential actions.

## Gate G30B — V3 specialist network accepted

Required:
- specialist contracts implemented,
- governed multi-agent handoffs,
- broad goal decomposes into bounded tasks,
- agents use common tool/truth layer,
- missing facts route to review,
- external actions remain permission gated,
- interruption/restart preserves task state,
- evaluation traces exist,
- one genuine real-world career workflow succeeds at the appropriate permission level,
- ChatGPT + owner accept A-V30-CAREER-AGENT-NETWORK.

## Advancement rule

The worker may prepare future engineering behind a user/external gate when explicitly allowed, but:
- it may not self-open a gate,
- it may not self-accept artifacts,
- it may not turn engineering evidence into real proof,
- it may not use a later feature to paper over an earlier truth/safety defect.

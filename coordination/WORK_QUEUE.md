# Active Work Queue

Owner directive: no version is COMPLETE until one real non-mock production-path example passes.

Workers start from `coordination/SESSION_START.md`, `coordination/HEARTBEAT_PROTOCOL.md`, and their lane file. Formal milestones remain V1.4 REAL_PROOF -> V1.5 -> V1.7 -> V2.0 -> V2.3 -> V3.0. Engineering may continue in parallel, but official completed-version status cannot advance past a missing real proof.

## P0A — V1.4 proof-tool integrity

Artifact: `A-V14-REAL-PROOF`
Authoritative audit: `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Private candidate/resume proof execution is forbidden until ChatGPT accepts P0A.

### Lane C — production implementation owner

Branch: `worker/live-data-foundations`

Required tasks:
- RP14-T1 SP2 — `REAL_PROOF_CANDIDATE` runtime output + separately candidate-bundle-bound PASS/FAIL verifier receipt; rejected candidates still emit FAIL receipts.
- RP14-T2 SP2 — local/private bundle hash + `proof_run_id` cross-binding.
- RP14-T3 SP3 — approved current Greenhouse JobModel/question attestation binding.
- RP14-T4 SP2 — copied/renamed example profile rejection by content evidence.
- RP14-T5 SP1 — explicit committed-evidence allowlist / reject arbitrary extra fields.
- RP14-T6 SP1 — explicit deterministic-production generation labeling.
- RP14-T7 SP2 — independent packet/manifest/resume/artifact cross-link verification.

Execution contract:
1. start from latest main,
2. implement RP14-T1..T7 as bounded SP1-SP3 slices,
3. add/adopt adversarial acceptance tests,
4. run targeted tests + full pytest/Ruff/mypy,
5. push one coherent batch + worker-authored `READY_FOR_LEAD_REVIEW` heartbeat,
6. stop for Scout/ChatGPT review.

Lane C was lead-aligned to current green main during the 2026-09-21 06:46 ET review because its only two branch-only commits were lead-seeded heartbeat instructions; there was no worker code to preserve. This alignment is not a worker heartbeat and does not satisfy any RP14 task.

### Remote-worker support

`pri8771/remote-workers` is infrastructure only; Jobs remains authoritative.

Verified history:
- audit retry confirmed forged-bundle acceptance and missing local/redacted binding;
- first hardening attempt failed during clone;
- hardening retry failed on branch push and returned no reviewable Jobs commit;
- branch-push probe succeeded but is diagnostic-only and must not merge;
- read-only P0A preflight completed successfully and reinforced T1..T7 but implemented nothing;
- non-Jobs workflow `35580580156` later completed with failure, freeing `worker-pc`;
- tests-only task `jobs-v14-p0a-adversarial-tests-20260921-0642` / workflow `35590523591` also failed on target Jobs branch push.

Latest remote result:
- status: `failed`
- error: `Worker branch push failed.`
- returned Jobs branch: none
- returned commit: none
- returned tests/summary: none
- corresponding Jobs worker branch: not present
- workflow result publication itself succeeded after the target branch push failure

The target-repository push stderr is currently suppressed by the remote executor, so the exact push cause is not recoverable from the published result/workflow log. Do not count or adopt any work from this failed attempt. Do not immediately repeat the same branch-mode support task merely to create activity; Lane C remains the production implementation owner and must continue independently.

## P0 — V1.4 real proof after P0A

State: BLOCKED on P0A. V1.4 engineering is accepted but V1.4 is NOT COMPLETE.

Default target: OpenSesame — AI Automation Engineer
`https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740`

### Lane C readiness
- RP14-C1 SP2 — validate actual private candidate profile + actual resume mappings; no example/synthetic inputs; private contents stay local.
- RP14-C2 SP2 — import/validate current OpenSesame JobModel/source/questions with the real public Greenhouse source.
- RP14-C3 SP1 — confirm non-mock production generation route; fail closed if unavailable.

### First eligible Lane A/C execution
- RP14-E1 SP2 — run importer, production packet runner, verifier with local full bundle when all real inputs are present.
- RP14-E2 SP2 — push only runtime-generated redacted candidate evidence + verifier receipt.

If private inputs are unavailable, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; never synthesize substitutes.

### Scout / lead
- RP14-S1 SP2 — independent proof audit immediately when candidate + receipt appear.
- RP14-L1 — ChatGPT re-audit and only then mark `A-V14-REAL-PROOF` ACCEPTED on genuine `REAL_PROOF_PASS`.

Current proof directory still has no runtime proof candidate or verifier receipt.

## Lane A — V1.5 assisted application

Branch: `worker/v15-assisted-application`
Reviewed head: `ed875775122f0d390af6ab15beb378904af2a476`

Task-scope accepted: A-R15-01..A-R15-05.
V1.5 overall remains IN_PROGRESS.

After V1.4 real proof, remaining safety residuals:
- A-R15-06 SP2 page-level prompt-injection signal/warning semantics
- A-R15-07 SP2 real cover-letter upload wiring + field-specific attachment mapping
- A-R15-08 SP2 packet hash/answers/provenance/resume-link revalidation before browser use
- A-R15-09 SP1 unknown file inputs stay manual/unfilled

No V1.6 until V1.4 real proof and V1.5 gates are satisfied.

## Lane B — V1.7 / V2.0 recruiting operations

Branch: `worker/recruiting-ops`
Current head: `8f4909fbbd61ef8dc7327d21ce6dfe0781db8e21`

Continue only non-conflicting residuals:
- B-R17-03 SP2 background check must not fabricate offer state
- B-R20-07 SP1 simulation never counts as real submission
- B-R20-08 SP2 final-interview + acceptance-evidence metrics
- B-R20-05 / J20-14 SP3 crash-durable worker-run evidence

J20G-04 waits for Lane C J20G-03 after the V1.4 proof sequence.

## Lane C — after V1.4 proof attempt

Only after P0A acceptance and the required real-proof readiness/attempt sequence:
- J12-01 SP2 candidate provenance records
- J12-02 SP2 application-use gating
- J12-03 SP1 provenance report CLI
- J20G-01 SP2 partial Gmail fetch fails closed / no checkpoint advance
- J20G-02 SP2 OAuth runtime wiring
- J20G-03 SP2 typed secret-free real-Gmail readiness

Do not perform Gmail work before the V1.4 readiness/attempt sequence.

## Lane D — V2.3 foundations

Branch: `worker/v23-foundations`
Current head: `11ff552cd8d5f31a1406bc7d4ab2833ed252db42`

Continue only:
- J23O-01..03 opportunity graph projection foundations
- J23T-01..03 target-company watch local foundations
- J23A-01..03 transport-neutral agent tool interfaces

No graph DB, migrations, external actions, or V2.0 duplication.

## Scout

Branch: `scout/qa-prep`
Current head: `d221eecbe21aa33051c888b9e42f10a307ed9ecd`

Priority:
1. review Lane C RP14-T1..T7 as soon as it lands,
2. execute RP14-S1 as soon as genuine proof candidate + verifier receipt exist.

The failed remote test-only attempt produced no reviewable Jobs branch, so Scout has nothing to audit from that task.

## Heartbeat truth

- Lane A: 1/3
- Lane B: 0/3
- Lane C: 0/3
- Lane D: 0/3
- Scout: 0/3

Lead-seeded commits and lead branch alignment do not count. PROVING_15M continues until three consecutive on-time worker-authored heartbeats, then STEADY_HOURLY.

## Safety

No live Gmail OAuth/mailbox access, browser application action, submission, external messaging, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped authorization.

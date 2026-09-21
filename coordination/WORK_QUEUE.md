# Active Work Queue

Owner directive: no version is COMPLETE until one real non-mock production-path example passes.

Workers start from `coordination/SESSION_START.md`, `coordination/HEARTBEAT_PROTOCOL.md`, and their lane file. Formal milestones remain V1.4 REAL_PROOF -> V1.5 -> V1.7 -> V2.0 -> V2.3 -> V3.0. Engineering may continue in parallel, but official completed-version status cannot advance past a missing real proof.

## P0A — V1.4 proof-tool integrity

Artifact: `A-V14-REAL-PROOF`
Authoritative audit: `docs/V1_4_REAL_PROOF_TOOLING_AUDIT.md`

Private candidate/resume proof execution is forbidden until ChatGPT accepts P0A.

### Lane C — production implementation owner

Branch: `worker/live-data-foundations`
Current head: `020f262b2a99cbf6d6b9647750af88d9b6a1cf66`

Required tasks:
- RP14-T1 SP2 — `REAL_PROOF_CANDIDATE` runtime output + separately candidate-bundle-bound PASS/FAIL verifier receipt; rejected candidates still emit FAIL receipts.
- RP14-T2 SP2 — local/private bundle hash + `proof_run_id` cross-binding.
- RP14-T3 SP3 — approved current Greenhouse JobModel/question attestation binding.
- RP14-T4 SP2 — copied/renamed example profile rejection by content evidence.
- RP14-T5 SP1 — explicit committed-evidence allowlist / reject arbitrary extra fields.
- RP14-T6 SP1 — explicit deterministic-production generation labeling.
- RP14-T7 SP2 — independent packet/manifest/resume/artifact cross-link verification.

Execution contract:
1. rebase latest main,
2. launch `python scripts/worker_heartbeat_watch.py --lane C --epoch DAYWATCH_2026_09_21 --detach`,
3. implement RP14-T1..T7 as bounded SP1-SP3 slices,
4. add/adopt adversarial acceptance tests,
5. run targeted tests + full pytest/Ruff/mypy,
6. push one coherent batch + worker-authored `READY_FOR_LEAD_REVIEW` heartbeat,
7. stop for Scout/ChatGPT review.

Current lead evidence: Lane C still has no worker implementation or current-epoch heartbeat. This is the project critical path.

### Remote-worker support

`pri8771/remote-workers` is infrastructure only; Jobs remains authoritative.

Verified history includes earlier audit/preflight evidence plus failed clone/push attempts. Current useful support evidence:

- RP14-T5 task `jobs-v14-p0a-t5-schema-20260921-0946` completed and returned actual Jobs branch `worker/jobs-v14-p0a-t5-schema-20260921-0946` at `1f4a9b9bd21ed402afaef211ac3cab852a293a22`.
- Lead inspected the actual commit/diff. It is one bounded commit changing only `coordination/proofs/v14_real_proof.schema.json`, `scripts/verify_v14_real_proof.py`, and `tests/test_real_proof_verifier.py`; it closes the top-level/nested evidence allowlists and adds focused extra-field adversarial tests.
- This is **support candidate code, not accepted RP14-T5 evidence**. The remote summary states pytest/Ruff/mypy execution was blocked, and no Jobs CI run exists for `1f4a9b9...`. The branch is also behind current main. Lane C may cherry-pick/reimplement it only after rebasing, and must rerun focused tests plus full pytest/Ruff/mypy/CI in the coherent P0A batch.
- A separate bounded RP14-T6-only task `jobs-v14-p0a-t6-origin-20260921-1047` was dispatched after the worker became free. Remote workflow `35615000944` failed almost immediately; at review time no sanitized result or Jobs branch existed. Credit no T6 progress and do not retry a duplicate immediately.

Lane C must not wait for remote-worker support.

## P0 — V1.4 real proof after P0A

State: BLOCKED on P0A. V1.4 engineering is accepted but V1.4 is NOT COMPLETE.

Default target: OpenSesame — AI Automation Engineer
`https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740`

`coordination/proofs/` currently contains only `README.md` and `v14_real_proof.schema.json`; no runtime proof candidate or verifier receipt exists.

### Lane C readiness
- RP14-C1 SP2 — validate actual private candidate profile + actual resume mappings; no example/synthetic inputs; private contents stay local.
- RP14-C2 SP2 — import/validate current OpenSesame JobModel/source/questions with the real public Greenhouse source.
- RP14-C3 SP1 — confirm non-mock production generation route; fail closed if unavailable.

### Lane A readiness evidence
Lane A's early local proof attempt before P0A acceptance cannot count as proof evidence, but it truthfully exposed a local readiness blocker:
- the real profile selected `resume_ai_software_engineer`,
- no actual file was mapped for that selected variant on Lane A,
- only `enterprise_automation_solutions_architect.md` was present,
- the runner failed closed and no synthetic substitute was created.

Treat Lane A as `REAL_PROOF_BLOCKED_PRIVATE_INPUT` unless a genuine intended mapping for the selected variant exists after P0A. Do not synthesize, relabel, copy, or silently substitute resume bytes merely to satisfy proof selection.

### First eligible Lane A/C execution
After P0A lead acceptance only:
- RP14-E1 SP2 — run importer, production packet runner, verifier with local full bundle when all real inputs are present.
- RP14-E2 SP2 — push only runtime-generated redacted candidate evidence + verifier receipt.

Whichever Lane A or Lane C machine first has the complete genuine private profile + selected real resume mapping should execute immediately; do not wait for a C-to-A handoff. If private inputs are unavailable, report `REAL_PROOF_BLOCKED_PRIVATE_INPUT`; never synthesize substitutes.

### Scout / lead
- RP14-S1 SP2 — independent proof audit immediately when candidate + receipt appear.
- RP14-L1 — ChatGPT re-audit and only then mark `A-V14-REAL-PROOF` ACCEPTED on genuine `REAL_PROOF_PASS`.

## Lane A — V1.5 assisted application

Branch: `worker/v15-assisted-application`
Current head: `1a2c6461b191a536d4eebb09321e790a09c20ab8`
PR #2: draft.
Current-head GitHub CI run #336: SUCCESS.

Task-scope accepted: A-R15-01..A-R15-05. Current production browser implementation for that accepted scope remains the previously accepted code. V1.5 overall remains IN_PROGRESS.

While P0A is blocked, Lane A may continue these already-authorized non-conflicting residuals in one coherent batch:
- A-R15-06 SP2 page-level prompt-injection signal/warning semantics
- A-R15-07 SP2 real cover-letter upload wiring + field-specific attachment mapping
- A-R15-08 SP2 packet hash/answers/provenance/resume-link revalidation before browser use
- A-R15-09 SP1 unknown file inputs stay manual/unfilled

No V1.6. No real application/browser action. After P0A, switch immediately to V1.4 proof if the actual selected resume mapping is genuinely available.

Heartbeat epoch correction: Lane A's 14:05Z `STEADY_HOURLY` self-claim predates the `DAYWATCH_2026_09_21` reset at 14:45Z and does not count. Lane A is 0/3 in the current epoch and must launch the detached watcher on a fresh session.

## Lane B — V1.7 / V2.0 recruiting operations

Branch: `worker/recruiting-ops`
Current head: `68595d1fe825545b7f1506b7068d1c78376f7953`
PR #3: draft.
Current-head CI run #329: SUCCESS.

Lead review of the latest residual batch:
- B-R17-03 SP2 — LEAD_ACCEPTED at task scope.
- B-R20-07 SP1 — LEAD_ACCEPTED at task scope.
- B-R20-08 SP2 — LEAD_ACCEPTED at task scope.
- B-R20-05 / J20-14 SP3 — REWORK.

B-R20-05 bounded rework:
1. If durable `worker_run` begin persistence fails, do not continue an untracked production sweep; fail closed or otherwise guarantee no pipeline work proceeds without the durable attempt record.
2. Do not persist raw `str(exc)` / upstream error text as `sample_errors`; store bounded safe categories/codes.
3. `check_worker()` must report the true newest attempt even when the newest attempt is an unfinished RUNNING begin; expose required `last_reconciliation_at` and `last_error_at/category` fields.
4. Add caught-exception-after-begin -> FAILED, rollback durability, distinct run IDs, and adversarial secret/error sanitization tests while preserving existing success/kill/stale cases.
5. Replace the old heartbeat format with the exact current `DAYWATCH_2026_09_21` metadata and launch the detached watcher.

Prior analytics residuals remain open:
- B-R20-01 SP3 — headline funnel/history metrics still use current status rather than event-history outcomes.
- B-R20-02 SP2 — headline funnel/submission semantics still do not use the same real-submission denominator.

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

## Heartbeat truth

Current liveness epoch:
- `DAYWATCH_2026_09_21`

Lead checked actual branch commit timestamps after the 14:45Z reset:
- Lane A latest: 14:05Z — pre-epoch
- Lane B latest: 13:26Z — pre-epoch
- Lane C latest: 10:49Z — pre-epoch
- Lane D latest: 02:15Z — pre-epoch
- Scout latest: 02:15Z — pre-epoch

Therefore all lanes are currently 0/3 for this epoch.

Required:
- 3 consecutive 5-minute worker-authored heartbeats with 4-7 minute valid gaps,
- then 15-minute heartbeats for a clean 24-hour window,
- any gap >20 minutes increments misses and restarts the clean 24-hour watch,
- then STEADY_HOURLY.

Fresh sessions launch:
`python scripts/worker_heartbeat_watch.py --lane <LANE> --epoch DAYWATCH_2026_09_21 --detach`

Old heartbeat entries remain preserved for audit but do not count.

## Safety

No live Gmail OAuth/mailbox access, browser application action, submission, external messaging, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped authorization.

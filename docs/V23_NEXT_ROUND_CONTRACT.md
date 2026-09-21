# Next-round execution contract — Jobs Automation

Status: **PREPARED FOR THE NEXT ROUND — NOT ACTIVATED**.
Audited main: `927b33c0f523950ca206ead1cc2912e19a018184`.
Owner target: a genuinely useful V2.3 job-search OS, with the required earlier live checkpoints. V3 is a separately gated future implementation, not a reason to delay V2.3.

This review does not change Fable's running V1.4/V1.5 assignment, accept its code, start another worker/watcher, grant access, or modify main. It is a next-round correction package. A final planned build campaign is the goal; an unknown provider/access failure cannot honestly be guaranteed away.

## 1. What changes from the previous plan

The product scope is retained. The implementation and acceptance contracts are strengthened, rather than another roadmap being added.

The existing feature tasks in `docs/V23_TASK_GRAPH_RECOVERY.md`, `docs/V23_TASK_GRAPH_V20.md` and `docs/V23_TASK_GRAPH_V23.md` remain the inventory. `coordination/V23_HARDENING_TASKS.json` is a **corrective delta**: its `refines` fields identify the old task/contract being corrected. Do not execute both incompatible definitions or rebuild a verified equivalent. The exact corrections and evidence are in `docs/V23_REVIEW_FINDINGS_20260921.md`.

At activation, the lead promotes one packet into WORK_QUEUE and makes this revision authoritative for its mapped conflicts. Until then the existing Fable scope remains unchanged. Historical documents are reference-only where explicitly superseded, not another competing instruction source.

## 2. Activation gate: stop instruction churn first

Current main and the previously reviewed planning package disagree about one worker versus three lanes. This review does not infer which remote sessions are actually alive. The owner instructions visible in this conversation call for one worker and one heartbeat; repository state must be reconciled at the next safe handoff, not repeatedly rewritten while a worker is coding.

Before the next round, the lead must record:
- the reconciled owner directive and its source;
- the selected code baseline and completed Fable artifacts;
- one active assignment, one implementation session and one heartbeat owner;
- one plan revision, its activation commit, and the allowed write surfaces;
- any scheduled lead-sync prompt or other writer that still restores obsolete instructions.

Use expected-base-SHA/content checks for shared writes. If main moves, preserve the change, inspect the difference and reconcile. Never restore old governance from stale memory. Do not kill another machine's watcher merely because a process is absent locally. A shared ownership record must identify host/session; expired ownership requires a deliberate takeover. No five-minute ChatGPT automation is promised or created by this document; the five-minute heartbeat is the existing local worker mechanism.

## 3. Freeze scope, not defects

The next round has one outcome: the remaining accepted product scope through V2.3 works on real evidence. It is not a V3 runtime build, dashboard rewrite, provider-aggregator project or general infrastructure migration.

Do not add new features mid-campaign. New findings may enter only as:
1. safety/privacy/data-integrity defects;
2. failures of an already agreed acceptance criterion;
3. prerequisites demonstrably needed to run the real path.

Each new finding has a reproducible failing case, affected contract, smallest patch and explicit non-goals. Cosmetic preferences, optional frameworks and speculative optimization go to a deferred list. A defect is fixed locally; it does not trigger another whole-project planning pass.

### Task sizing

Use one narrow objective with explicit inputs, output and failing tests. SP1/SP2 are complexity labels, not time promises. A task is not smaller merely because its label changed. If its write set or unresolved design expands, split it into children before implementing. Preserve parent acceptance criteria.

Read only the active task, relevant correction and current code. The helper can render one task:

```sh
python scripts/validate_v23_hardening_plan.py --task H-TOOL-01
```

This command renders a task; it does not schedule work, grant permission or accept anything.

## 4. Readiness must precede the long implementation run

Produce one consolidated capability ledger before the next round. For each capability record `AVAILABLE_AND_AUTHORIZED`, `AVAILABLE_AUTH_REQUIRED`, `MISSING_INPUT`, `MISSING_ACCESS`, `UNVERIFIED` or `NOT_APPLICABLE`, with a machine, source reference, last check and exact blocker. Never equate configuration with a working provider.

| Capability | Required evidence before its live step | Boundary |
|---|---|---|
| Candidate/profile | canonical provenance and owner-approved use | never reconstruct candidate truth from memory |
| Resume | selected variant maps to the exact genuine bytes | missing variant means blocked, not substitute file |
| Proof job | current public source snapshot and exact source IDs | reverify at execution; do not assume old posting survives |
| Browser | installed actual runner, permitted destination and scoped prefill grant | stop before submit for V1.5; page may save draft fields remotely |
| Submission | eligible method, credentials actually available, current policy and desired exact job/packet approval | a public board token is not an application API credential |
| Gmail | actual mailbox identity, approved scopes, bounded query/window/cap and harmless connectivity check | an alias is not necessarily a separate mailbox/OAuth identity |
| Recruiting evidence | genuine approved historic thread(s), truthful application/resume attribution where known | synthetic canary mail is not a real recruiter interaction |
| Runtime | supported Python/dependencies, PostgreSQL/driver, migrations, artifact volume, real boot command | SQLite-only checks cannot establish PostgreSQL correctness |
| Recovery | nonempty database and artifact-store backup/restore | never overwrite production to perform a drill |

Use existing approved accounts first. Account/alias creation and controlled owner-to-owner messages are limited to the owner's actual grant; no new spending, recruiter outreach or employer submission is implied. Do not treat an older assistant-authored authorization paragraph as broader permission than the owner supplied.

The lead consolidates missing owner inputs into one request rather than discovering them one at a time after each implementation batch. New MFA/CAPTCHA or changed destination remains a genuine stop condition.

## 5. Execution packets and review cadence

Packets group related **small artifacts**, not giant commits. Continue automatically across explicitly opened task dependencies. Push coherent code at an artifact boundary; review accumulated microtasks as one bounded artifact, not every line of code and not an entire version.

| Packet | Deliverable | Retained feature work | New scrutiny |
|---|---|---|---|
| P0 | Stable assignment and known access path | completed Fable handoff, existing readiness | no competing instruction writers; actual submit eligibility |
| P1 | Trusted producer-to-verifier chain | V1.4/V1.5 accepted code and proofs | actual production constructors, PostgreSQL, code/evidence identity |
| P2 | Controlled submission truth | existing R16 authorization/attempt/preflight/confirmation/transport work | stable candidate identity, durable claim, pre-dispatch reservation, no blind retry |
| P3 | Real bounded ingestion and lifecycle | Gmail, merged CRM/interview/follow-up | pagination, SENT direction, trusted timestamps, exact canary scope |
| P4 | Daily-operable V2.0 | control center, reliability, analytics | real user flow, exact cohort definitions, nonempty restore |
| P5 | Useful V2.3 intelligence | graph, strategy, watch, interview, tool facade, briefing | evidence-based relations, preserved replay status, separate application action queue |
| P6 | Final acceptance campaign | existing engineering and live campaigns | actual runner/report/verifier compatibility; independent recomputation; restart/replay |
| P7 | V3 future design/implementation sequence | existing V3 contracts | no V3 prerequisite may block P0–P6; separate assignment after V2.3 |

P2 transport eligibility and P3 access preparation are examined early, not discovered at the end. This does not authorize live actions early. Independent engineering tasks may advance behind a live gate; the official milestone chain does not silently change.

### Handoff contract

`artifact_id, task_ids, code_sha, production_tree_digest, dependency_digest, schema_revision, files_changed, exact_commands, exit_codes, sanitized_log_refs, focused_test_results, integration_result, live_result_or_blocker, current_heartbeat_owner, next_task, READY_FOR_LEAD_REVIEW`.

Only a lead verdict accepts an artifact. The helper and worker reports never do. Do not assume a ChatGPT lead is continuously running: persist the handoff so any authorized lead run can resume the review.

## 6. Acceptance matrix — minimum real-life example plus repeatability

Every engineering artifact needs focused and adverse tests. Each milestone additionally requires a genuine production-path example. These are different evidence classes.

| Checkpoint | Positive production-path example | Additional reliability checks | Explicitly insufficient |
|---|---|---|---|
| V1.4 | genuine selected profile/resume + current real job → production packet → separately validated candidate/receipt | importer→builder→exporter→verifier compatibility; tamper negatives; actual configured DB | handwritten DB happy path, fixture profile, replaced resume |
| V1.5 | authorized real visible page + accepted real packet → safe actual prefill/uploads → pre-submit review stop | dynamic form/file swap/injection/unknown-field negatives | screenshot of empty page; HTTP 200; mock browser; final submit disguised as prefill |
| V1.6 | exactly approved desired job + permitted available transport → one real system submit → correlated external confirmation | duplicate race, timeouts, crash before/after dispatch, revoked approval | public API GET, test ATS tenant, user-attested submit, local success flag |
| V1.7 | bounded approved genuine recruiting evidence → production ingestion/link/lifecycle → reconstructable timeline | replay, outbound reply, reschedule, ambiguity and out-of-order processing | synthetic recruiter mail sent through real Gmail as sole proof |
| V2.0 | installed real system: inbox → opportunity → packet/application timeline → operator review → health/analytics | nonempty DB+artifact restore, process restart, repeat ingestion with no loss/duplicates | a list of endpoints returning 200 or a fixture-only dashboard |
| V2.3 | real briefing showing opportunities/reasons, truthful relationships, exact resume attribution, watch results, interviews/follow-ups where genuinely evidenced | independent report recomputation, stale/unavailable sections, replay and restart | empty output relabelled full proof; invented relationship; rate arithmetic alone |
| V3.0 | separately authorized real career goal through multiple bounded specialists and common tools | permission failures, memory invalidation, restart, budget limits, handoff loop tests | fixtures alone, autonomous messages/submissions without approvals |

An absence of interview evidence may be reported honestly; it does not prove the interview-intelligence capability. Use genuine historical evidence when appropriately available, otherwise record the missing capability. Do not manufacture interviews or wait for unsolicited new activity when legitimate historical records suffice.

Formal milestone dependencies remain as already accepted in the lead review: V1.4 → V1.5 → V1.6 → V1.7 → V2.0 → V2.3. Their engineering may run ahead. If a required live transport remains unavailable, report completed engineering and the exact blocked gate; do not relabel full V2.3 complete.

## 7. Evidence: four distinct classes

1. `ENGINEERING_FIXTURE`: synthetic/captured fixtures, test transports and fake accounts.
2. `REAL_PROVIDER_CANARY`: actual provider connection/delivery, including controlled owner test messages.
3. `REAL_CANDIDATE_WORKFLOW`: actual desired job, genuine candidate inputs and approved production actions.
4. `REAL_HISTORICAL_RECRUITING`: genuine historical provider evidence used through production ingestion/lifecycle.

A real provider call does not convert synthetic content into a real hiring event. Explicit generation origin, source provenance and runtime mode are separate fields. Keyword scans are supporting diagnostics, not proof of origin.

### Code identity and receipt identity

A run records source commit, digest of production code, dependency lock digest, schema revision, input snapshot, producer version and run ID. Exporting/committing evidence later changes repository HEAD; this must not invalidate unchanged tested code or encourage editing report SHAs. Store evidence/receipt commits separately and verify content equivalence or rerun affected paths after material code changes.

A separate verifier re-reads declared DB/source/artifact evidence, recomputes identities and metrics, and binds the exact report bytes. It may not trust report `pass`, `simulated=false`, `independently_validated=true` or `entity_id exists` as sufficient evidence. A report with no required checks cannot pass.

The trusted evidence harness and verifier must not accept arbitrary worker-generated bundles as source authority. The threat model is hostile external content and tampered/mislabeled evidence, not a cryptographic guarantee against an administrator who can replace the entire application, database and verifier. Document that boundary instead of overclaiming proof.

## 8. Critical execution invariants

- **Identity:** stable candidate subject + canonical employer/provider requisition identity; profile/resume changes do not allow another logical submission.
- **Authorization:** authenticated principal + exact nonempty action/target/method/artifact scope; caller flags cannot grant permissions.
- **Dispatch:** claim/reserve approval and persist intent before network I/O. Unknown outcome keeps the claim occupied. No outer transaction may erase a possible external effect.
- **Confirmation:** validator output derived from correlated external evidence, not a supplied boolean or generic navigation.
- **Replay:** preserve exact original status/warnings/evidence; reauthorize access and namespace keys by actor/tool/version/effect. PARTIAL never becomes SUCCEEDED.
- **Ingestion:** pagination, bounded scope, trusted provider times and SENT direction; incomplete page/message fetch never advances past lost data.
- **Snapshots:** one as_of/profile/source snapshot per briefing; old scores cannot be paired with newly computed rationale without disclosure.
- **User experience:** an active-application action queue is separate from unapplied opportunity ranking. The user can see due follow-ups without hidden shell commands.
- **Privacy:** restrictive credential mounts, atomic token refresh, sanitized errors and explicit redaction allowlists. Raw email/HTML remains untrusted.

## 9. Testing and runtime gate

Retain pytest, Ruff, format, mypy and migration checks from the actual repo. Add production-path integration with the real supported PostgreSQL driver and schema. Where GitHub Actions does not start, report `CI_BLOCKED_ACCOUNT` only when observed; use an independently reproducible clean environment at the exact code identity. A skipped check is NOT PASS.

At least one positive test must create data through the actual producer and consume it through the real downstream component, not hand-build a matching schema in tests. Fail-closed negatives alone can produce a system that rejects everything; positive production-path tests are mandatory.

Before final acceptance run the installed CLI/API/dashboard path, not only direct Python method calls. Then execute bounded replay, process restart, incremental processing, failure recovery and a separate nonempty restore. Record which parts used real data and which were engineering fault injection. No destruction of the live database and no repeated live submissions for testing.

## 10. Scope of V3 after V2.3

V2.3 owns deterministic domain truth and typed tools. V3 adds orchestration, not a second DB or replacement implementation.

Future sequence:
1. persisted task/lease/checkpoint contract and capability registry;
2. real permission/credential boundary reusing scoped approvals;
3. scoped source-backed memory and invalidation;
4. bounded planner/router with restart and handoff-loop controls;
5. model/cost/trace/evaluation policies;
6. specialist adapters over existing Scout, Matcher, Resume, CRM, Interview and Analytics services; external Application/Networking/Brand actions remain separately governed;
7. real broad-goal campaign, independent evidence review and restart test.

Treat each specialist as its own small implementation artifact when V3 is activated. The future design tasks in the JSON are contract-preparation tasks, not permission to implement ten agents in one SP2 item. Reuse the existing model gateway; select actual available model IDs at runtime. Do not assume remembered commercial model versions/effort names exist.

## 11. Definition of the last planned round

The plan is frozen after activation; the work proceeds artifact by artifact until the agreed outcome or a genuine external blocker. A failed test creates bounded repair, not a new vague roadmap. Required external approvals remain real gates.

Final handoff must demonstrate:
- accepted required engineering artifacts;
- all mandatory real-life milestone receipts;
- actual daily operator flow;
- restart/replay/restore evidence;
- no unresolved critical safety/data-integrity defect;
- explicit residual limitations and deferred V3 scope;
- exact deployed code/schema/dependency identity and rollback procedure.

The achievable promise is a better-defined execution campaign with less avoidable rework. Zero undiscovered defects or guaranteed provider access is not an honest promise.

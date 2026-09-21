# Lead Audit — 2026-09-21 Three-Lane Reset

## Owner objective

Move Jobs Automation forward with fewer active lanes, real acceptance evidence, automated coordination, and visible progress.

Owner completion rule:
- engineering tests/CI are necessary but not sufficient;
- a version is COMPLETE only after at least one real non-mock production-path example succeeds and is independently reviewed.

## Repository truth at reset

### main

Main is the authoritative coordination/integration branch.

Contains:
- V1.4 packet-safety engineering foundation accepted,
- real-proof acceptance policy,
- proof importer/runner/verifier tooling,
- proof-tool integrity audit,
- migration-chain CI,
- three-lane coordination contract,
- detached heartbeat watcher,
- heartbeat validation,
- live progress issue workflow.

Official product state:
- V1.4 engineering accepted,
- V1.4 NOT COMPLETE,
- A-V14-REAL-PROOF still blocked on P0A proof-tool integrity and genuine real input proof.

### Prior Lane A / new Lane 2

Branch:
- worker/v15-assisted-application

Compare to main at reset:
- status: ahead
- ahead: 6
- behind: 0

Substantial source implementation exists in browser/application paths.

Lead-accepted at task scope:
- A-R15-01
- A-R15-02
- A-R15-03
- A-R15-04
- A-R15-05

Remaining:
- A-R15-06
- A-R15-07
- A-R15-08
- A-R15-09
- final integration/real proof before V1.5 COMPLETE

Known real-proof readiness evidence:
- private profile exists on that machine,
- title selection chose resume_ai_software_engineer,
- genuine mapped file for that selected variant was absent,
- system failed closed,
- no substitute may be fabricated.

Decision:
- keep this branch and make it Lane 2.

### Prior Lane B / new Lane 3

Branch:
- worker/recruiting-ops

Compare to main at reset:
- status: diverged
- ahead: 4
- behind: 44

Substantial V1.7/V2.0 source implementation exists.

Lead-accepted at task scope:
- B-R17-03
- B-R20-07
- B-R20-08

Remaining:
- B-R20-05 / J20-14 durability repair
- B-R20-01 historical headline funnel semantics
- B-R20-02 real-submission headline denominator
- rebase/integration review

Decision:
- keep branch and make it Lane 3.

### Prior Lane C

Branch:
- worker/live-data-foundations

Compare to main:
- ahead: 0
- behind: 49
- no worker production code

Decision:
- superseded.
- replace with a clean Lane 1 branch from current main.

### Prior Lane D

Branch:
- worker/v23-foundations

Compare to main:
- only 2 ahead commits, heartbeat/coordination only
- 186 behind
- no production implementation

Decision:
- pause.
- V2.3 is not worth an active lane while V1.4 real proof and V2.0 repairs remain open.

### Prior Scout

Branch:
- scout/qa-prep

Compare to main:
- only 2 ahead commits, heartbeat/coordination only
- 199 behind
- no production implementation

Decision:
- pause.
- independent review moves to ChatGPT lead plus worker-pc when useful.

## New active topology

Exactly three implementation lanes:

### Lane 1 — P0 critical path

Branch:
- worker/v14-real-proof

Starts clean and identical to current main.

Owns:
- RP14-T1..T7 proof-tool hardening
- then genuine V1.4 real proof
- then candidate provenance/Gmail readiness

This is the current project critical path.

### Lane 2 — V1.5 application safety

Branch:
- worker/v15-assisted-application

Owns:
- preserve A-R15-01..05
- finish A-R15-06..09
- no V1.6 until prior gates pass

### Lane 3 — V1.7/V2.0 recruiting/reliability

Branch:
- worker/recruiting-ops

Owns:
- B-R20-05/J20-14
- B-R20-01
- B-R20-02
- preserve accepted lifecycle/analytics fixes

## Independent review resource

worker-pc:
- external infrastructure only,
- capacity 1,
- useful for bounded read-only audit and isolated support branches,
- never project authority,
- never auto-merge,
- ChatGPT reviews actual result branch/diff/tests.

Useful reviewed support:
- RP14-T5 candidate support commit 1f4a9b9...
- not accepted until Lane 1 incorporates/reimplements and proves it in green coherent CI.

## Critical path to first genuinely complete version

1. Lane 1 completes RP14-T1..T7.
2. ChatGPT + worker-pc independent review.
3. Lane 1 validates genuine private profile + exact selected resume mapping.
4. Import/revalidate live OpenSesame proof job/questions.
5. Run production packet proof with no mock/fixture data.
6. Generate runtime candidate evidence + separately bound verifier receipt.
7. Independent proof audit.
8. ChatGPT accepts A-V14-REAL-PROOF.
9. V1.4 becomes COMPLETE.

Parallel:
- Lane 2 finishes V1.5 safety.
- Lane 3 finishes V1.7/V2.0 repair.

## After V1.4 COMPLETE

- Lane 1 -> candidate provenance + Gmail readiness + integration fixture.
- Lane 2 -> V1.5 integration and real proof.
- Lane 3 -> V1.7/V2.0 integrated acceptance.
- Reopen a fourth V2.3 lane only when a concrete bottleneck justifies it.

## Automation model

### Worker liveness

Each active lane launches the detached watcher:
- 5-minute proving x3,
- then 15-minute heartbeat for a clean 24 hours,
- then hourly.

Heartbeat is generated from an independent lightweight clone and does not require the implementation agent to stop coding.

### Human-visible progress

GitHub issue:
- #7 Jobs Automation — Live Progress

Every active-lane heartbeat automatically posts:
- lane,
- current task,
- progress note,
- heartbeat stage,
- blocker/review state,
- branch + commit.

A heartbeat can legitimately say:
- still working on assigned task
even when no implementation commit was pushed.

### ChatGPT lead automation

Jobs Lead Sync runs hourly and:
- reads current repo truth,
- audits Lane 1/2/3 heartbeats/branches/PR/CI,
- checks worker-pc results,
- reviews READY_FOR_LEAD_REVIEW batches,
- updates canonical queue/artifact/current state,
- assigns the next bounded task after acceptance,
- posts a concise hourly lead comment to issue #7.

## Safety boundaries

Automation does not authorize:
- live Gmail OAuth/mailbox access,
- real application form submission,
- external messages,
- MFA/CAPTCHA bypass,
- spending,
- fabricated candidate facts,
- committing private resume/profile contents.

Consequential real-world actions remain user-gated.

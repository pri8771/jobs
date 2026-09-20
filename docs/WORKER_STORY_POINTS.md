# Worker Story Points and Delegation Policy

## Purpose

Measure how reliably the implementation workhorse completes bounded engineering tasks of different complexity, while keeping ChatGPT focused on lead work: architecture, prioritization, debugging, decomposition, review, and acceptance.

Story points measure complexity/uncertainty, not elapsed time.

## Story point scale

### SP1 — trivial / highly local
Typical shape:
- one obvious file or configuration change,
- low ambiguity,
- no schema/architecture decision,
- narrow regression test or documentation update,
- straightforward acceptance criteria.

Examples:
- force EEO questions to unresolved,
- add one config validator,
- add one negative regression test,
- update a documented default.

### SP2 — small bounded implementation
Typical shape:
- one to three related files,
- known interface,
- modest tests,
- no major schema or cross-service redesign.

Examples:
- remove a fallback and add failure tests,
- add exact resume ID -> source mapping,
- replace hard-coded candidate literals with profile fields,
- make a gateway fail closed.

### SP3 — moderate multi-file feature/repair
Typical shape:
- several coordinated changes,
- new helper/service or meaningful model behavior,
- database/API integration may be touched but architecture is already decided,
- substantial tests required.

Examples:
- artifact materialization + read-back verification,
- packet manifest generation,
- canonical provenance plumbing across service and persistence layers.

### SP4 — complex but bounded
Typical shape:
- migration/model/service/tests across multiple layers,
- meaningful edge cases or backward compatibility,
- some design choices remain but desired behavior is clear,
- likely benefits from a lead-provided contract before implementation.

Examples:
- immutable ResumeVariant persistence plus migrations and application linkage,
- application state-machine change spanning services/events/audit.

### SP5 — largest task that should be given to the worker as one unit
Typical shape:
- crosses several modules/services,
- multiple failure modes,
- requires integration-level testing,
- acceptance criteria must be explicit,
- architecture must already be sufficiently constrained.

SP5 is the maximum normal worker task.

## Greater than SP5

Do not assign >SP5 as one task.

ChatGPT must decompose it into SP1-SP5 child tasks with:
- stable interfaces,
- explicit dependencies,
- independent acceptance criteria where practical,
- clear merge/integration order.

If a task repeatedly fails at SP4/SP5, split it further rather than just re-prompting the same oversized task.

## Delegation policy

Default allocation:

Antigravity should receive:
- almost all SP1,
- almost all SP2,
- most SP3,
- straightforward/well-specified SP4,
- selected SP5 only when architecture and acceptance criteria are already constrained.

ChatGPT should primarily own:
- architecture,
- requirements clarification,
- task decomposition,
- difficult root-cause debugging,
- cross-cutting safety analysis,
- independent code review,
- acceptance decisions,
- adversarial testing strategy,
- future milestone preparation,
- recovery/replanning when worker attempts fail.

ChatGPT should avoid taking easy implementation work away from Antigravity merely because ChatGPT could do it.

Lead-side patches are appropriate when:
- the task is genuinely hard/ambiguous,
- the worker is blocked after a bounded attempt,
- a small lead patch unlocks multiple worker tasks,
- review discovers a safety-critical issue best fixed immediately,
- or tool/access boundaries make worker execution impossible.

## Task record requirements

Every worker task should have:
- task ID,
- title,
- story points (1-5),
- owner,
- dependencies,
- acceptance criteria,
- status.

Worker statuses:
- READY
- IN_PROGRESS
- WORKER_REPORTED_DONE
- BLOCKED
- REWORK
- LEAD_ACCEPTED

Only ChatGPT lead review can set LEAD_ACCEPTED for milestone-relevant work.

## Performance metrics

Track worker performance by story-point bucket.

Core metrics:
- tasks attempted,
- tasks lead-accepted,
- first-pass acceptance count/rate,
- rework count,
- lead-discovered defects after worker completion,
- CI-pass-on-first-push count/rate,
- scope adherence failures,
- blocker/escalation quality,
- accepted story points,
- rework story points.

Useful derived views:
- first-pass acceptance by SP1 / SP2 / SP3 / SP4 / SP5,
- average rework cycles by story-point bucket,
- defect rate by story-point bucket,
- percentage of accepted points completed by worker,
- percentage of easy work (SP1-SP2) delegated to worker,
- escalation rate on SP4-SP5.

Do not convert story points into hours.

## Evaluation rules

A task is first-pass accepted only when:
- worker reports completion,
- lead audits the actual code/evidence,
- acceptance criteria pass without a worker rework assignment.

CI passing alone is not acceptance.

A lead-found defect that violates stated acceptance criteria counts as rework.

A worker escalation does not count as failure when:
- the blocker is real,
- it is reported promptly,
- evidence is provided,
- and the worker completed other unblocked portions appropriately.

## Goal

We want evidence about what task sizes Antigravity handles reliably.

Example future conclusion:
- SP1: 98% first-pass acceptance
- SP2: 92%
- SP3: 76%
- SP4: 55%
- SP5: 25%

If the pattern looks like that, lead behavior should adapt:
- keep SP1-SP2 delegated,
- refine/decompose SP3,
- split SP4-SP5 more aggressively.

The point is to improve task shaping, not to maximize a vanity velocity number.

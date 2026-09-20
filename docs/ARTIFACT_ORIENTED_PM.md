# Artifact-Oriented Project Management

## Principle

This project is managed around **artifacts**, not around ephemeral task lists.

A task exists to create, modify, verify, or accept an artifact.

Examples of artifacts:
- implementation contract,
- data model,
- migration,
- application packet,
- packet manifest,
- test suite,
- audit report,
- runbook,
- OAuth canary plan,
- policy decision,
- proof-job selection record,
- browser preflight manifest,
- submission receipt,
- analytics specification,
- benchmark,
- architecture decision.

The project should always be answerable by asking:

1. What artifact are we trying to produce?
2. Who owns it?
3. What inputs does it depend on?
4. What evidence proves it is acceptable?
5. What downstream artifact does it unblock?

## Artifact identity

Every meaningful artifact gets a durable ID.

Format:
- `A-<PHASE>-<SHORT-NAME>`

Examples:
- `A-V14-PACKET-SAFETY`
- `A-V15-ASSISTED-APPLICATION`
- `A-V16-FIRST-REAL-SUBMISSION`
- `A-V12-GMAIL-CANARY`

Artifact IDs should be referenced in:
- WORK_QUEUE,
- AI_SYNC,
- commits when practical,
- acceptance reviews,
- worker performance records.

## Artifact lifecycle

Use these statuses:

- PROPOSED
- READY
- IN_PROGRESS
- BLOCKED
- WORKER_REPORTED_DONE
- LEAD_REVIEW
- ACCEPTED
- SUPERSEDED

Rules:
- Antigravity may move READY -> IN_PROGRESS -> WORKER_REPORTED_DONE.
- ChatGPT may move WORKER_REPORTED_DONE -> LEAD_REVIEW -> ACCEPTED or back to IN_PROGRESS/REWORK.
- Only explicit evidence can justify ACCEPTED.
- A milestone is complete only when its required artifacts are ACCEPTED.

## Artifact card

Each artifact card lives under:

`coordination/artifacts/`

Minimum fields:
- Artifact ID
- Title
- Type
- Phase
- Status
- Owner
- Reviewer
- Story points for implementation work if applicable
- Dependencies
- Downstream consumers
- Purpose
- Scope
- Non-goals
- Acceptance criteria
- Evidence required
- Source/code paths
- Risks
- Current notes

## Artifact graph

Artifacts form a dependency graph.

Example:

A-V14-PACKET-SAFETY
    ↓
A-V15-ASSISTED-APPLICATION
    ↓
A-V16-FIRST-REAL-SUBMISSION

Parallel supporting artifacts may feed the path:

A-V12-CANDIDATE-PROVENANCE ─┐
A-V12-GMAIL-CANARY ──────────┼→ later operations
A-PROOF-JOB-SELECTION ───────┘

Do not create artificial dependencies where none are needed.

## Task relationship

WORK_QUEUE is an **execution view over artifact work**, not the permanent source of product truth.

A worker task should reference one artifact ID.

Example:

- J14-05 / SP3 / owner Antigravity
- Artifact: A-V14-PACKET-SAFETY
- Action: implement immutable artifact materialization + read-back verification

If work produces no durable artifact or evidence, question whether it should exist.

## Story points

Story points remain complexity buckets, not time.

See:
- docs/WORKER_STORY_POINTS.md

Artifacts may contain multiple SP1-SP5 worker tasks.

Anything >SP5 must be decomposed before assignment.

## Lead/worker split

Antigravity:
- produces most implementation artifacts,
- especially SP1-SP3 work,
- supplies evidence bundles,
- keeps artifact cards current while working.

ChatGPT:
- defines artifact contracts,
- decomposes work,
- audits difficult failures,
- reviews evidence,
- accepts/rejects artifacts,
- prepares future artifacts while current implementation is underway,
- keeps the artifact graph coherent.

ChatGPT should not consume easy implementation work that is better delegated.

## Evidence-oriented completion

Artifact completion is based on evidence, not prose claims.

Examples:
- code artifact -> commit SHA + tests + CI
- migration artifact -> migration file + upgrade/downgrade verification
- packet artifact -> machine-readable manifest + persisted bytes + verified hashes
- policy artifact -> source/evidence + reviewed date
- live submission artifact -> external confirmation evidence
- OAuth canary artifact -> successful read-only call + no-mock proof
- benchmark artifact -> fixture set + expected outputs + run results

## Artifact-first heartbeat

Each hourly heartbeat should answer:

- Which artifact(s) changed?
- What evidence was added?
- What artifact is blocked?
- Which artifact becomes ready next?
- What worker tasks should be added/split?

Avoid heartbeat updates that only say "still working" without artifact/evidence state.

## Future work

When the active artifact is waiting:
- ChatGPT should prepare upstream/downstream artifact contracts,
- create acceptance criteria,
- research integration constraints,
- build runbooks,
- prepare benchmarks,
- create worker-ready task slices.

This is how the project keeps moving without stealing easy work from the worker.

## Acceptance

A phase/milestone should have an explicit required-artifact set.

Example V1.4:
- A-V14-PACKET-SAFETY = ACCEPTED

V1.5:
- A-V15-ASSISTED-APPLICATION = ACCEPTED

V1.6:
- A-V16-FIRST-REAL-SUBMISSION = ACCEPTED

The artifact index is:
- coordination/ARTIFACT_INDEX.md

# Current State

Updated: 2026-09-21

## Official completion state

**V1.4 is NOT COMPLETE.**

Accepted:
- A-V14-PACKET-SAFETY engineering foundation
- Lane 3 recruiting/reliability repair batch has been lead-accepted and merged to main

Still required before V1.4 COMPLETE:
1. lead acceptance of Lane 1 RP14-T1..T7 proof-tool integrity,
2. genuine runtime proof candidate,
3. separately bound verifier receipt,
4. genuine private profile + exact intended resume mapping,
5. independent proof audit.

Owner rule:
no version is COMPLETE until one real non-mock production-path example passes.

## Lane 1 — V1.4 real-proof critical path

Branch:
- `worker/v14-real-proof`

PR:
- #8 — draft

Implementation:
- RP14-T1..T7 implementation commit `8f8c21f88512aa32521c78285b72dc9da298672e`
- changed proof schema/importer/runner/verifier/packet-builder proof linkage and proof tests
- CI for implementation commit `8f8c21f`: SUCCESS
- current PR head `4cd5373...` differs only by later heartbeat evidence; CI on that head is running

Status:
- READY FOR LEAD REVIEW
- P0A not yet accepted
- do not execute private-data real proof until lead acceptance

## Lane 2 — V1.5 application safety

Branch:
- `worker/v15-assisted-application`

PR:
- #2 — draft

Implementation:
- A-R15-06..09 implementation is present on branch
- representative implementation commit `09f1852...`
- current branch CI has been green on reviewed implementation/heartbeat heads

Status:
- READY FOR LEAD REVIEW
- A-R15-01..05 remain task-scope accepted
- no V1.6
- no V1.4 real proof until Lane 1 P0A is accepted

Known proof-readiness blocker on this machine:
- real profile selected `resume_ai_software_engineer`
- genuine mapped resume bytes were not present
- do not synthesize/substitute a resume

## Lane 3 — V1.7 / V2.0 recruiting & reliability

Former branch:
- `worker/recruiting-ops`

PR #3:
- MERGED

Merge commit:
- `be765ea42856bc695fc1eece9c1da396b4f162d4`

Lead-accepted and merged:
- previously accepted recruiting/lifecycle work
- B-R17-03
- B-R20-07
- B-R20-08
- B-R20-05 / J20-14 worker-run durability/sanitization/health repair
- B-R20-01 historical headline funnel semantics
- B-R20-02 real-submission denominator semantics

Evidence:
- GitHub CI on final branch head `d32a4c8...`: SUCCESS
- Ruff, mypy, Alembic migration verification, pytest all passed
- worker reported 151/151 local tests

Lane 3 current batch is complete and integrated.
Next Lane 3 assignment must come from current queue after lead reprioritization; J20G-04 remains blocked on later Gmail readiness.

## Heartbeat standard

Canonical heartbeat:
- epoch `FIVE_MIN_2026_09_21`
- mode `ACTIVE_5M`
- one heartbeat every 5 minutes while a lane is active
- no proving/watch/hourly transitions
- exactly one watcher process per active lane

Important migration note:
- Lane 1 and Lane 2 currently still have old DAYWATCH watcher processes running in memory, so their latest heartbeat files still show `WATCH_15M_24H`
- the repository code/protocol now uses fixed 5-minute cadence
- each active lane must stop the old watcher once, pull latest main, and launch exactly one `FIVE_MIN_2026_09_21` watcher
- Lane 3's previous heartbeat process is no longer relevant to its merged batch

Visible progress:
- GitHub issue #7 remains the human-readable progress feed

## Critical path

Lane 1 lead review of RP14-T1..T7
-> accept/rework P0A
-> genuine profile/resume/job readiness
-> real V1.4 packet proof
-> independent audit
-> V1.4 COMPLETE

Parallel:
- Lane 2 lead review / V1.5 integration preparation

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, fabricated candidate facts, or committed private candidate/resume contents without explicit scoped authorization.

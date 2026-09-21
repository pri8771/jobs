# Active Work Queue

Owner directive:
**No version is COMPLETE until one genuine non-mock production-path example passes.**

Exactly three active implementation lanes:
- Lane 1 — V1.4 real-proof critical path
- Lane 2 — V1.5 assisted-application safety
- Lane 3 — V1.7/V2.0 recruiting/reliability

Old Lane C is superseded. Old Lane D and Scout are paused. `worker-pc` is infrastructure/support only.

## P0 — Lane 1 — V1.4 proof-tool integrity rework

Branch / review surface:
- `worker/v14-real-proof`
- draft PR #8

Verdict on `8f8c21f...`:
- **REWORK**

Required next batch:
- enforce CANDIDATE-only candidate input,
- require local/private binding for PASS,
- make candidate-bundle SHA binding mandatory,
- always emit bound FAIL receipt on rejection,
- implement full approved Greenhouse source/job/description/question attestation binding,
- keep copied-example content rejection and make source class runtime-derived,
- enforce deterministic-generation labeling in verifier,
- independently recompute canonical packet hash and verify job/resume/artifact linkage,
- add adversarial tests for each gap,
- run focused proof tests + full pytest/Ruff/mypy + branch CI.

Do not run private-data proof before P0A acceptance.

Heartbeat while active:
- `FIVE_MIN_2026_09_21`
- `ACTIVE_5M`
- every 5 minutes, no transitions.

## Lane 2 — V1.5 assisted application

Branch / review surface:
- `worker/v15-assisted-application`
- PR #2

Preserve:
- A-R15-01..05 task-scope accepted implementation.

Current scope only:
- A-R15-06 — page-level prompt-injection warning semantics,
- A-R15-07 — field-specific cover-letter/file upload mapping,
- A-R15-08 — packet/provenance/artifact integrity revalidation at the browser boundary,
- A-R15-09 — unknown file inputs stay manual/unfilled.

Current evidence:
- implementation for A-R15-06..09 exists on the branch and has had green CI evidence,
- worker is synchronizing against newer main; no current-head READY_FOR_LEAD_REVIEW acceptance yet,
- valid DAYWATCH proving 3/3 after restart; clean watch started 16:38:09Z,
- 16:53:11Z is the verified cadence check-in; too-early 16:39/16:54 writes are not counted as 15-minute cadence evidence and suggest overlapping watchers.

Immediate:
- pull/rebase latest main,
- ensure exactly one DAYWATCH watcher,
- run focused + full pytest/Ruff/mypy + current-head branch CI,
- request review only on one coherent current head.

No V1.6.

Known V1.4 proof blocker on this machine remains: selected `resume_ai_software_engineer` had no genuine mapped resume bytes. Do not synthesize or substitute another resume.

## Lane 3 — V1.7 / V2.0

Branch:
- `worker/recruiting-ops`

Lead integration completed:
- PR #3 merged to main as `be765ea42856bc695fc1eece9c1da396b4f162d4`
- newly accepted/integrated: B-R20-05/J20-14, B-R20-01, B-R20-02
- preserved accepted: B-R17-03, B-R20-07, B-R20-08 and earlier accepted Lane 3 residuals

Next bounded assignment:
1. pull/rebase branch onto latest main,
2. verify merged accepted source + targeted worker/health/dashboard tests,
3. run full pytest/Ruff/mypy,
4. repair only an actual integration regression if one exists,
5. if green, record waiting status and stop implementation work.

J20G-04 remains blocked until Lane 1 later produces the authorized Gmail-readiness dependency. Do not invent unrelated work to keep Lane 3 busy.

Heartbeat note:
- Lane 3 self-reported 3/3, but actual current-epoch times 16:18Z → 16:34Z → 16:44Z do not satisfy 4–7 minute proving gaps; next worker heartbeat restarts at 1/3.

## Heartbeat / visible progress

Canonical owner rule:
- `FIVE_MIN_2026_09_21`
- `ACTIVE_5M`
- every 5 minutes while active
- one watcher per lane
- no cadence transitions

Visible progress:
- GitHub issue #7

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate-data commits, or fabricated candidate facts without explicit scoped user authorization.

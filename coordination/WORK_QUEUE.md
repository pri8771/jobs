# Active Work Queue

Owner directive:
**No version is COMPLETE until one genuine non-mock production-path example passes.**

Exactly three active implementation lanes:
- Lane 1 — V1.4 real-proof critical path
- Lane 2 — V1.5 assisted-application safety
- Lane 3 — V1.7/V2.0 recruiting/reliability

Old Lane C is superseded. Old Lane D and Scout are paused. `worker-pc` is infrastructure/support only.

## P0 — Lane 1 — V1.4 proof-tool integrity

Branch / review surface:
- `worker/v14-real-proof`
- draft PR #8

Current evidence:
- implementation commit `8f8c21f88512aa32521c78285b72dc9da298672e`
- CI #401 green
- valid DAYWATCH proving 3/3; clean 24h watch started 16:37:59Z; first verified watch heartbeat 16:53:01Z
- ChatGPT lead reviewed the actual diff and returned P0A for **REWORK**
- worker-pc independent read-only audit `jobs-v14-p0a-lane1-audit-20260921-1247` is in progress

Required repair before P0A acceptance:
1. RP14-T1 — candidate schema/verifier must accept only `REAL_PROOF_CANDIDATE`; only the separate verifier receipt may say PASS/FAIL.
2. RP14-T1/T2 — a candidate cannot obtain `REAL_PROOF_PASS` without successful private/local bundle cross-binding.
3. RP14-T1 — rejected candidates must emit a candidate-bundle-bound `REAL_PROOF_FAIL` receipt even under default invocation.
4. RP14-T7 — verifier must independently recompute canonical packet hash from manifest job/profile/resume IDs, artifact hashes, answers and provenance, and verify job/resume-variant linkage.
5. Incorporate any additional valid findings from the independent audit.

Exit gate:
- adversarial tests for every repaired hole,
- focused proof tests + full pytest/Ruff/mypy,
- green current-head CI,
- READY_FOR_LEAD_REVIEW,
- ChatGPT P0A acceptance.

After P0A acceptance, immediately execute RP14-C1..C3 real private-input readiness, then the first genuinely eligible Lane 1 or Lane 2 machine runs the real packet proof. Private contents remain local. No browser application action is authorized.

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

Authoritative epoch: `DAYWATCH_2026_09_21`.

Per lane:
1. `PROVING_5M`: 3 consecutive worker-authored check-ins with 4–7 minute gaps.
2. `WATCH_15M_24H`: approximately every 15 minutes for a clean 24 hours; any gap >20 minutes increments misses and restarts the clean window.
3. `STEADY_HOURLY` after a clean 24 hours.

Launch:
- Lane 1: `python scripts/worker_heartbeat_watch.py --lane 1 --epoch DAYWATCH_2026_09_21 --detach`
- Lane 2: `python scripts/worker_heartbeat_watch.py --lane 2 --epoch DAYWATCH_2026_09_21 --detach`
- Lane 3: `python scripts/worker_heartbeat_watch.py --lane 3 --epoch DAYWATCH_2026_09_21 --detach`

Every active numeric-lane heartbeat must post to GitHub issue #7. ChatGPT also posts one concise lead update there each hourly run.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, MFA/CAPTCHA bypass, spending, private candidate-data commits, or fabricated candidate facts without explicit scoped user authorization.

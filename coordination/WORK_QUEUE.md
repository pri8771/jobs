# Active Work Queue

Owner directives:
- **Exactly three active implementation lanes.**
- **No version is COMPLETE until one genuine non-mock production-path example passes.**
- **Each active lane runs exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` heartbeat watcher at ~5-minute cadence.**
- Old Lane C/D/Scout are paused/superseded.

## P0 — Lane 1 — V1.4 proof-tool integrity

Branch / PR:
- `worker/v14-real-proof`
- draft PR #8

Artifact:
- `A-V14-REAL-PROOF`

Latest worker repair implementation reviewed:
- `3ce19cffedcceba753686dae9c6240eccf6a2263`

Lead verdict:
- **REWORK**
- P0A is not accepted.
- private candidate/resume proof execution remains forbidden.

What materially improved in `3ce19cf`:
- candidate input is `REAL_PROOF_CANDIDATE` only,
- structural-only verification fails closed instead of PASS,
- candidate-bundle SHA binding is mandatory,
- default bound FAIL receipts exist,
- explicit evidence allowlist/schema is closed,
- deterministic proof-origin labels are enforced,
- canonical packet hash is recomputed from manifest fields.

Remaining blockers to close in one coherent Lane 1 batch:
1. RP14-T3 — require and verify fetch timestamp, canonical apply URL, public Greenhouse job ID, and bind redacted `job_url` to the approved source.
2. RP14-T3 — independently bind description/question hashes to actual runtime `JobModel`/`JobSource` import evidence or a fresh same-flow public revalidation; do not trust a self-consistent hand-authored local attestation.
3. RP14-T4 — hash the actual `candidate_profile_path` bytes and require equality with private `candidate_profile_sha256`; derive/validate the private source class from runtime evidence rather than trusting a literal.
4. RP14-T7 — make local `job_id` mandatory and independently verify the persisted `ApplicationPacketModel` row plus `resume_variant_id`, `resume_artifact_id`, `cover_letter_artifact_id` and corresponding artifact hashes/manifest evidence.
5. Add adversarial tests showing fake profile path/hash, fake source attestation, missing/tampered canonical URL/fetch metadata, and mismatched/missing persisted packet row cannot pass.
6. Run targeted proof tests + full pytest + Ruff + mypy + **exact-head** GitHub CI.
7. Rebase/synchronize PR #8 onto latest main so the final review diff is coherent and mergeable.

Heartbeat:
- Lane 1 is correctly emitting current-epoch ACTIVE_5M heartbeats.

Next lead gate:
- review the next coherent Lane 1 repair head before any real private-input proof run.

## P0 next — Lane 1 or genuinely eligible Lane 2 — V1.4 real proof

Only after explicit ChatGPT P0A acceptance:
- Lane 1 validates actual private profile + exact intended resume mapping,
- import/revalidate current live OpenSesame AI Automation Engineer job using the approved Greenhouse path,
- run the production packet builder with non-mock deterministic generation,
- emit runtime `REAL_PROOF_CANDIDATE`,
- run the verifier with private/local cross-binding,
- commit only redacted hashes/provenance plus the separate verifier receipt.

Whichever genuinely eligible Lane 1 or Lane 2 machine first has all real private inputs may execute the proof; no cross-lane handoff is required.

Lane 2 machine is currently not eligible for V1.4 proof if its real profile still selects `resume_ai_software_engineer` without genuine mapped resume bytes. Do not synthesize/substitute another resume.

Packet preparation only. No browser form prefill or submission.

## Lane 2 — V1.5 assisted-application safety

Branch / PR:
- `worker/v15-assisted-application`
- draft PR #2

Preserve:
- A-R15-01..05 accepted at task scope.

Current work:
- A-R15-06 — page-level prompt-injection warning semantics,
- A-R15-07 — field-specific resume/cover-letter/file upload mapping,
- A-R15-08 — packet/provenance/artifact integrity revalidation immediately before browser use,
- A-R15-09 — unknown file inputs remain manual/unfilled.

Current evidence:
- implementation exists and has historical green PR CI,
- branch is currently diverged from main and materially behind it,
- latest heartbeat still uses superseded DAYWATCH metadata.

Immediate bounded assignment:
1. stop the old Lane 2 DAYWATCH watcher once,
2. pull/rebase latest main while preserving accepted A-R15-01..05 and current A-R15-06..09 source changes,
3. start exactly one Lane 2 `FIVE_MIN_2026_09_21` watcher,
4. run focused assisted-safety adversarial tests + full pytest/Ruff/mypy + exact-head branch CI,
5. push one coherent current-main batch and mark `READY_FOR_LEAD_REVIEW` / `REVIEW`,
6. do not expand into V1.6.

No live browser action is authorized.

## Lane 3 — recruiting/reliability

Branch:
- `worker/recruiting-ops`

PR #3:
- merged/closed; accepted repair integrated on main as `be765ea42856bc695fc1eece9c1da396b4f162d4`.

Preserve accepted scope:
- B-R17-03,
- B-R20-07,
- B-R20-08,
- B-R20-05 / J20-14,
- B-R20-01,
- B-R20-02.

The owner continues to name those tasks as the Lane 3 work surface, but reviewed evidence says they are already lead-accepted and integrated. Do not redo accepted work merely to create activity.

Immediate bounded assignment:
1. stop any old Lane 3 DAYWATCH watcher once,
2. sync/rebase `worker/recruiting-ops` to latest main,
3. start exactly one Lane 3 `FIVE_MIN_2026_09_21` watcher,
4. run targeted worker/health/dashboard tests + full pytest/Ruff/mypy on the integrated baseline,
5. inspect the accepted B task semantics for an actual integration regression,
6. if green/no regression, report verification and wait for the next bounded lead assignment rather than reopening V2.3/Scout work,
7. if a real regression exists, repair only that bounded regression and request lead review.

J20G-04 remains blocked on future Lane 1 Gmail-readiness dependency. No Gmail access is authorized.

## Heartbeat standard

Canonical epoch/mode:
- `FIVE_MIN_2026_09_21`
- `ACTIVE_5M`
- 5-minute interval
- one watcher per active lane
- no cadence transitions

If an active branch still has DAYWATCH/PROVING/WATCH/hourly state, stop that old watcher once and migrate it to the canonical watcher after syncing latest main.

Every heartbeat should produce an issue #7 comment. Actual commit timestamps outrank metadata/self-claims.

## Remote worker

`pri8771/remote-workers` is infrastructure only.

Use `worker-pc` for bounded independent Jobs review/support when it is idle and the task materially shortens the critical path. Respect `capacity: 1`. Never accept or merge a remote-worker claim without inspecting any returned Jobs branch/diff/tests. Never auto-merge worker-pc branches.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, spending, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped owner authorization.

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

Latest implementation reviewed:
- `5e5058461d5371f292c93e0c53cb0b93caba7e44`

Lead verdict:
- **REWORK**
- P0A is not accepted.
- private candidate/resume proof execution remains forbidden.

Materially improved in this repair:
- actual candidate-profile path/hash validation and copied-example rejection,
- fetch timestamp/canonical URL/public-job-ID checks,
- local question-file hashing/count checks,
- mandatory packet/job/resume/artifact UUID fields,
- persisted-row verification implementation when a database target is present.

Remaining acceptance blockers:
1. **RP14-T7 DB verification is optional.** `verify_database_linkage()` returns when the local bundle omits both `database_url` and `db_path`; PASS must require a proof DB target and successful persisted `ApplicationPacketModel` / `ResumeVariantModel` / artifact-row checks.
2. **RP14-T3 source attestation is not independently tied to trusted import evidence.** Bind the attestation to persisted Greenhouse `JobSourceModel`/`JobModel` importer evidence (including provider/source job ID, description/content SHA, question-list SHA, API/canonical URL, fetch metadata) or perform the fresh same-flow public revalidation required by the tooling audit. A self-consistent local attestation/questions file is not enough.
3. Add adversarial tests for both bypasses. The current positive verifier fixture has no DB target and uses a fabricated `description_sha256`, yet still expects PASS.
4. Rebase/synchronize PR #8 to current `main`, run focused + full pytest/Ruff/mypy, and obtain exact-head GitHub CI after the final implementation commit.

Heartbeat:
- Lane 1 is correctly emitting current-epoch ACTIVE_5M heartbeats, observed through 18:33:19Z at heartbeat #9.

Remote support:
- bounded read-only `worker-pc` post-repair audit `jobs-v14-p0a-postrepair-gap-audit-20260921-1420` dispatched; its claim cannot self-accept P0A.

Next lead gate:
- review the next coherent Lane 1 repair head before any real private-input proof run.

## P0 next — Lane 1 or genuinely eligible Lane 2 — V1.4 real proof

Only after explicit ChatGPT P0A acceptance:
- Lane 1 validates actual private profile + exact intended resume mapping,
- import/revalidate current live OpenSesame AI Automation Engineer job using the approved Greenhouse path,
- run the production packet builder with non-mock deterministic generation,
- emit runtime `REAL_PROOF_CANDIDATE`,
- run the verifier with mandatory private/local/database cross-binding,
- commit only redacted hashes/provenance plus the separate verifier receipt.

Whichever genuinely eligible Lane 1 or Lane 2 machine first has all real private inputs may execute the proof; no cross-lane handoff is required.

Lane 2 is not eligible if its real profile still selects `resume_ai_software_engineer` without genuine mapped resume bytes. Do not synthesize/substitute another resume.

Packet preparation only. No browser form prefill or submission.

## Lane 2 — V1.5 assisted-application safety

Branch / PR:
- `worker/v15-assisted-application`
- draft PR #2

Preserve:
- A-R15-01..05 accepted at task scope.

Current work:
- A-R15-06 page-level prompt-injection warning semantics,
- A-R15-07 field-specific resume/cover-letter/file upload mapping,
- A-R15-08 packet/provenance/artifact integrity revalidation immediately before browser use,
- A-R15-09 unknown file inputs remain manual/unfilled.

Current evidence:
- implementation exists and has historical green PR CI,
- branch is materially diverged from current main,
- latest heartbeat still uses superseded DAYWATCH metadata.

Immediate bounded assignment:
1. stop the old Lane 2 DAYWATCH watcher once,
2. pull/rebase latest main while preserving accepted A-R15-01..05 and current A-R15-06..09 changes,
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

Do not redo accepted work merely to create activity.

Immediate bounded assignment:
1. stop any old Lane 3 DAYWATCH watcher once,
2. sync/rebase `worker/recruiting-ops` to latest main,
3. start exactly one Lane 3 `FIVE_MIN_2026_09_21` watcher,
4. run targeted worker/health/dashboard tests + full pytest/Ruff/mypy on the integrated baseline,
5. inspect accepted semantics for an actual integration regression,
6. if green/no regression, report verification and await the next bounded lead assignment,
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

`pri8771/remote-workers` is infrastructure only. Use `worker-pc` for bounded independent Jobs review/support when idle and useful. Respect capacity 1. Never accept or merge a remote-worker claim without inspecting any returned Jobs branch/diff/tests. Never auto-merge worker-pc branches.

## Safety

No live Gmail OAuth/mailbox access, browser application submission, external messaging, spending, MFA/CAPTCHA bypass, private candidate-data commits, or fabricated candidate facts without explicit scoped owner authorization.

# G14 genuine proof — first live-gate run — 2026-09-22

Implementer: Claude, the owner-assigned Jobs V1.7 owner. Owner instruction in the current session: "is 1.7 confirmed working with a live test? if not, do it." That is taken as private-use and host authority for the **local** G14 run only.

G14 ran from the accepted main proof path, as lead disposition §7 permits ("Do not wait for COMP-2/COMP-3 composition to begin G14 once its inputs/host authorization exist"). Only a public Greenhouse job-board read left this host. There was no employer, browser, application, Gmail, model or provider action. **G14 is REAL_PROOF_PASS by the separate verifier and awaits independent review and the ChatGPT lead's REAL_PROVEN decision.** No private content is in this file.

## Identity

- Code: clean detached worktree at `origin/main` `1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0`. G14 paths are identical to the accepted P0A merge 7c0fa73. The worktree was clean before and after both runs.
- Runtime DB: new, isolated local PostgreSQL 16 database `jobs_v17_live` (localhost:5432, owner pchordia), migrated to head `003_generation_origin_readiness` from the same SHA. No existing database was touched.
- Host: the owner's Mac. Python egress to `boards-api.greenhouse.io` was verified by the import itself.
- Interpreter: the accepted engine venv, with PYTHONPATH pinned to the proof worktree.

## Genuine inputs (private, kept local; hashes only)

- Job: Greenhouse **OpenSesame 7967740 "AI Automation Engineer"**, https://job-boards.greenhouse.io/opensesame/jobs/7967740. Imported through the public job-board API (`REAL_PROOF_JOB_IMPORT_PASS`), job row `acd4792b-d6f3-412f-9af1-319d645229bf`, description sha256 `522cb57f…c30736`, 7 non-standard questions (questions file sha256 `f37f53ca…735467`). This is the only job the accepted importer supports.
- Candidate profile: private `CandidateProfileConfig` **v2**, sha256 `2f659011d52df2ee35df65e827e9681c33535b17148d6f16d3a7c780fe41c095`. It maps from the owner's recovered career bank (`DYNAMIC_RESUME_CLARIFICATION_20260922.md`) and was validated against the production schema.
- Résumé: job-specific, truthful, **v2**, sha256 `8b67aaaa38b91447e2e8db6fbb5de80ff8b8eb8bde648bb50a94c23f2ab7d82d`, 6575 bytes, UTF-8/LF, frozen read-only. It is built only from **verified** bank atoms (81 unique, with no verify-tier or excluded atoms), and the SAP BTP, ABBYY and OCR/local-LLM histories are kept separate.
  - An independent fact-check of v1 passed 36 of 37 lines. One line (an ABBYY API wording overclaim) failed and was fixed as a new file v2.
  - An independent re-check of v2 **passed**. Bookkeeping hashes were corrected before the freeze.

## Run and verification

| Step | Result |
|---|---|
| `scripts/run_v14_real_proof.py` (production ApplicationPacketBuilder, DeterministicModelGateway) | `REAL_PROOF_RUN_COMPLETE`. Packet `96890d59-4d46-4f87-8f88-5a6ce5a4e953`, packet hash `40b2f596271caf87e32cafb6318828434138636edc1b90baa7182ee4734de20c`, origin deterministic, 2 answers resolved and **5 unresolved (truthfully)**, `is_live_ready=False` |
| `scripts/verify_v14_real_proof.py`, run as a separate process in a clean environment with `--local-full-bundle` | `REAL_PROOF_VALIDATION_PASS`, receipt `result=REAL_PROOF_PASS`, `local_full_bundle_verified=True` |
| Redacted candidate bundle | `v14_real_proof_d0f38e88-c9c2-400a-b102-9b7c356a2f59.json`, sha256 `c0bc9ae9f1c3bc707a193d06c92b6948967507432c0d17e2be75ed24bb67971f` |
| Receipt | `v14_real_proof_receipt_d0f38e88-…json`, sha256 `bd05f691d5301b2438ccc93aebaa744ec94cc9966a8c9fdfd250741dc21b8635` |
| Private bundle | kept local only, sha256 `70a851bc…e4e1c` |

The redacted bundle and receipt are **not committed yet**. The G14 plan says to commit them only after a lead-approved step, with bytes unchanged. They sit in the owner's private runtime directory.

## Independent review

Independent review with three lenses, every major finding adversarially verified: **3/3 RECOMMEND_G14_PASS**.

- **Reproducibility and provenance.** The verifier was re-run independently in a separate process: REAL_PROOF_PASS, the same bundle hash `c0bc9ae9…`, and a receipt identical to the original except for its timestamp. The code is 1a4efbb and clean, with no diff from P0A on the proof paths and the DB at head 003. The frozen profile and résumé hashes match the private bundle, the DB rows and the artifact bytes (`cmp` identical). The profile fingerprint `01380957…` agrees in the bundle, the manifest and the DB. The job description hash was recomputed from the persisted text. The DB is fresh and isolated: 1 job, 1 packet, 0 applications.
- **Privacy and commit-safety.** The redacted bundle holds exactly the 32 allow-listed keys, all ASCII, and a programmatic scan found no personal identifier. The receipt is safe to commit.
- **Truth and contract.** All G14 gate items are MET. Three majors were raised and all **refuted as G14 defects**:
  - Owner authority: the owner's literal pre-run instruction is in the session record, preceded by the concrete job description.
  - The deterministic cover letter contains four hard-coded fallback sentences (`tailoring.py` 121–137) and a `formal title UNRESOLVED` marker taken from `roles[0].role`. This is real, and it **must be repaired before any G15/G16 external use**. It is not a G14 preparation defect.
  - `is_live_ready` and `NEEDS_REVIEW` ignore cover-letter review. This is a latent G15/G16 gate gap.
- **Minors for the lead** (tooling in the accepted path, not run defects):
  - `run_timestamp_utc` carries the session offset (-04:00) instead of UTC.
  - `code_commit_sha` comes from the cwd without pinning or a dirty check. This run pinned PYTHONPATH to the worktree, and the worktree was clean.
  - `resume_version` is hard-coded and `tailoring_method=base`.
  - The redacted unresolved categories understate the unresolved facts.
  - Interpreter and dependency identity are not recorded.
  - Private bookkeeping (a stale manifest profile and one file mode) was fixed afterwards.
- A post-run DB snapshot is kept privately (`pg_dump` sha256 `462a025f…`), so re-verification survives an accidental re-import. **Do not re-import 7967740 into `jobs_v17_live`.**

## What G14 does and does not prove

It proves genuine preparation and identity: a real job, a genuine private profile, exact truthful résumé bytes, the production packet path, and separate verifier re-derivation.

It does **not** prove automatic JD-to-résumé generation (tailoring was done by prep work, then independently fact-checked). It is not an application, prefill or submission. The deterministic cover letter in the packet carries generic language that still needs factual review before any external use (G15/G16). Five screening answers remain unresolved.

## Requested lead action

1. Independent review is recorded above. **Mark G14 REAL_PROVEN** for proof `d0f38e88` (or rework), and approve committing the redacted bundle and receipt bytes unchanged under `coordination/proofs/`.
2. Accept COMP-3A `212b762` and release/accept COMP-3A-CLI `9b591fa` (see `COMP3A_BOUNDED_RETURN_20260922.md`).
3. **Release G16A engineering** (the V1.6 submission engine: durable intent/claim ledger, scoped approval, confirmation validator, Greenhouse hosted-form adapter under §3). It has never been released or built, and G16 cannot run without it.
4. Release the remaining composition that G17 needs (lifecycle/timeline/`canary_provenance`, worker/dashboard as required), or state the minimum G17 source.

## Owner items (concrete; from the private owner-question list)

- **Proof/application job decision.** OpenSesame pays $150–170K base, below the owner's stated floor, and fit is a stretch (about 40%). G15/G16 must reuse this G14 packet, so either confirm applying here or approve an importer generalization for a better-fit Greenhouse job.
- **Five required screening answers (Q12–Q16).** Truthful, atom-cited drafts are prepared privately for approval or edit.
- G15: permission to install the Playwright Python package, then an exact visible-browser prefill grant (this job, packet `96890d59`/`40b2f596`, **stop before submit**).
- G17: no Jobs Gmail client or token exists on this host.
  - The owner offered the Google Workspace business account `unsubscriber.me` (gcloud is authenticated there; project `unsubscriber-web-app-dev`). Its existing Gmail OAuth client is a **web** client whose redirect is registered only to `https://app.unsubscriber.me`. The Jobs `GmailAdapter` uses the desktop loopback (`InstalledAppFlow`), so reusing that client would fail with `redirect_uri_mismatch`.
  - Required: a new **Desktop-app** OAuth client (Console only; gcloud cannot create one) requesting **only `gmail.readonly`**. The consent screen must allow the recruiting mailbox (External/Testing with that Gmail as a test user if it is outside the Workspace).
  - The owner then personally completes one consent as the recruiting mailbox. Readiness accepts only a token whose scope is exactly read-only.
  - After that, name the mailbox alias, the canary alias and the query/window/cap. No cloud resource has been created. Creating one needs the owner's explicit per-action yes.

---

## Addendum: owner-chosen better-fit job, second G14 (Flexport), and the transport-policy blocker

The owner chose a **better-fit job** over OpenSesame for the G15/G16 application path and said "just do any test to prove its working … choose what you think is most applicable". The OpenSesame proof above stays valid and frozen.

**Importer generalization (independently reviewed, RECOMMEND_ACCEPT).**
- Source: `claude/jobs-g14-importer-generalize-20260922@2ce1194142679629cb32c966ee2141c13f5b0239`, tree `a6e081fe`, on accepted main 1a4efbb.
- The only change is `scripts/import_v14_proof_job.py`, plus its tests: `--expected-title`, `--company-name`, `--company-domain`. Defaults reproduce 7967740 exactly, and validation stays fail-closed.
- A new job's `remote_type` is classified from the posted location instead of hard-coded as `remote`. The runner, verifier and schema are unchanged.
- Checks: full owned PG 399 passed / 1 host skip; `mypy src tests` clean; Ruff clean. With Playwright now installed, the real-Chromium assisted-browser engineering test runs and passes; one loopback-alias sub-case skips.
- Reviewer follow-up (non-blocking): fail when the job id changes but the company or URL is left at the OpenSesame default.

**Flexport G14: REAL_PROOF_PASS.**
- Job: Greenhouse **Flexport 8110413 "Forward Deployed Engineer - Supply Chain Solutions"** (SF; $206–252K base; fits the owner's strongest verified evidence family). Public import `REAL_PROOF_JOB_IMPORT_PASS`, job row `ed0b943c-…`, description sha256 `cdf351b7…e340d`, 8 screening questions. `remote_type` is left unset (truthful) rather than `remote`.
- Database: new, isolated `jobs_v17_live_flexport` at head 003. A post-run `pg_dump` snapshot is kept privately (sha256 `35e4ecab…5800`).
- Code: clean detached worktree at `2ce11941`.
- Résumé: truthful, variant `resume_enterprise_automation`, sha256 `2595e00b…45a0`, 102 verified atoms, **FLEXPORT_FACT_CHECK_PASS** (43/43 claim lines).
- Profile: **v4**, sha256 `0f991637…315b`. It is the fact-checked v3 (current verified role first, no `UNRESOLVED` text in any employer-visible field) plus exactly two **owner-delegated test answers**: prior Flexport employment = No, and 50% travel / in-person SF = Yes. Both must be re-confirmed before any real submission.
- Run: packet `08075334-f712-4c2b-9f07-eb120ee3a0bb`, hash `89f69a066f6e8e53cad17440085b169ad2be37ee4d8995d1e71977c82a40896e`, **8 answers resolved, 0 unresolved, `is_live_ready=True`**.
- Separate verifier: `REAL_PROOF_VALIDATION_PASS`. Redacted bundle `13a5bea7…9e75`, receipt `b5d1ffe6…0141`. Not committed; this awaits the lead.
- **Independent review: RECOMMEND_G14_PASS.**
  - The verifier was re-run independently in a separate process: REAL_PROOF_PASS, bundle hash identical, receipt identical except for its timestamp.
  - Code is `2ce11941`, clean before and after. Its diff from 1a4efbb touches only the importer and its tests.
  - The frozen profile and résumé hashes match, and the résumé artifact is byte-identical. The packet row has 8 answers whose keys equal the 8 questions, `unresolved=[]`, `is_live_ready=true`, profile version 4. The company is Flexport and the source is GREENHOUSE 8110413.
  - **The DB has 0 application and 0 application_event rows, so nothing was submitted.**
  - The redacted bundle holds exactly the 32 allow-listed keys, and a privacy regex scan found 0 hits.
  - Answers: Q7–Q12 come from recorded facts. Q13/Q14 come only from the owner-delegated keys.
  - Notes: the known deterministic cover-letter duplicate line (Flexport's form has no cover-letter field), and Q13/Q14 need re-confirmation before any real submit.

**G15/G16 transport blocker (policy, not code).** The destination-policy review is in `GREENHOUSE_DESTINATION_POLICY_REVIEW_20260922.md`: public sources only, no form interaction.
- Greenhouse publishes no candidate terms that permit automated or assisted applying.
- Flexport's automated-means clause is ambiguous.
- Greenhouse documents invisible reCAPTCHA behaviour scoring, email-code escalation, and bot and mass-application detection.

Under the lead's frozen §3 rule ("If automation eligibility is unclear … stop with BLOCKED_NO_ELIGIBLE_TRANSPORT"; owner approval cannot override it), **assisted prefill (G15) and automated submission (G16) on Greenhouse are BLOCKED_NO_ELIGIBLE_TRANSPORT** until the lead rules otherwise. The runtime registry already defaults Greenhouse to `blocked`, since there is no entry. The proposed entry is `manual_only`. **A lead policy decision is required** to make any version of G15/G16 reachable. Options:
- (a) Rule that visible-browser assisted prefill with human review and a human submit is acceptable on this route.
- (b) Obtain written employer consent for a specific requisition.
- (c) Redefine G15/G16 for V1.7.

No CAPTCHA or bot bypass will ever be attempted.

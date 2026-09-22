# A-V14-REAL-PROOF

- Type: real-data proof / acceptance evidence
- Phase: V1.4
- Status: **BLOCKED ON GENUINE APPROVED INPUTS / ELIGIBLE HOST**
- Priority: P0 live gate / G14
- Owner: Fable/Claude + ChatGPT lead + Owner for private-input authorization
- Dependencies: `A-V14-PACKET-SAFETY` ACCEPTED; `A-V14-P0A-INTEGRITY` ACCEPTED; `A-V14-CLEAN-INTEGRATION` ACCEPTED
- Downstream: G14, V1.4 COMPLETE, G15

## Owner completion rule

A version is not COMPLETE until engineering acceptance and at least one genuine non-mock production-path example both pass.

For V1.4 packet preparation, candidate/profile/resume/job inputs must be real, the normal production packet path must run, no mock/fixture fallback may occur, and committed evidence must be runtime-derived and privacy-safe.

This artifact authorizes packet-preparation proof only when its genuine-input gate is actually open. It does **not** authorize browser prefill, application submission, Gmail/mailbox access, external messaging, MFA/CAPTCHA bypass, spending, or fabrication of candidate facts.

## Engineering gate — PASSED

ChatGPT accepted the P0A proof-tool integrity and clean integration on 2026-09-22:
- exact P0A source: `8491dd98154ff750f49cbb64d2a79eca5cb06069`;
- exact consolidated PR #12 head: `47fefd1b0ca354360353577685f6619a94f00f42`;
- merged to `main` through PR #12 as `7c0fa73bf350392a88b47442455359a43cf926b0`;
- lead review: `coordination/reviews/V17_LEAD_REVIEW_20260922.md`.

Accepted P0A properties include candidate/receipt separation, runtime closed-schema enforcement, database identity/target binding, independent persisted Job/JobSource/packet/answer/provenance/artifact/profile/resume re-derivation, canonical Greenhouse binding, exact selected-resume bytes/hash binding, truthful deterministic-generation labeling, fail-closed tamper handling, sanitized receipts, and production-path SQLite/PostgreSQL integration coverage.

Hosted Actions were `CI_BLOCKED_ACCOUNT` before executable steps and are not described as green. The documented lead engineering exception applies only to engineering acceptance and does not waive this live gate.

## G14 genuine-input gate

G14 may run only on a host that actually has all of the following:
1. the approved genuine private candidate profile;
2. the exact selected real resume bytes and canonical mapping;
3. a current real job/source suitable for packet proof;
4. production-path connectivity/configuration needed by the importer/runner/verifier;
5. explicit authority to use those private inputs for this packet-preparation proof.

The last reviewed Fable host reported that it does **not** have the required private profile/resume inputs and does not have usable public Greenhouse egress. Therefore that host is not currently eligible to execute G14. Do not fabricate, synthesize, relabel or silently substitute any input.

Private inputs remain local. Committed evidence must contain only sanitized hashes/provenance and runtime-generated redacted evidence.

## Required production execution

When the gate is genuinely open on an eligible host, use the production path:
- `python scripts/import_v14_proof_job.py`
- `python scripts/run_v14_real_proof.py ...`
- `python scripts/verify_v14_real_proof.py ... --local-full-bundle ...`

The runner must emit a runtime `REAL_PROOF_CANDIDATE`; the independent verifier must emit a candidate-bound `REAL_PROOF_PASS` or `REAL_PROOF_FAIL` receipt. No hand-authored evidence is acceptable.

The default historical target is OpenSesame — AI Automation Engineer only if it is still current/live when the proof runs; otherwise select a current real job under the same owner-approved rules. A stale or fake job cannot satisfy G14.

## Forbidden substitutions

G14 fails if any of the following is used as a substitute for genuine production evidence:
- `candidate_profile.example.yaml` or copied/example-profile contents;
- temp, synthetic or silently substituted resume bytes;
- fake/stale/unapproved job or hand-built question data;
- `MockModelGateway`, `HallucinatingModelGateway`, test/adversarial-mock origin, or silent mock fallback;
- self-declared PASS evidence;
- local-only artifacts that are not independently linked to persisted production rows;
- manually authored redacted proof files.

## Acceptance

ChatGPT may mark this artifact ACCEPTED only after reviewing a genuine runtime candidate plus independently bound PASS receipt, current real job/source binding, private-input provenance hashes, packet/manifest/resume/database/artifact linkage, generation origin, privacy hygiene and available implementation/test evidence.

`coordination/proofs/` currently contains no accepted runtime proof bundle, so **G14 is UNPASSED and V1.4 is NOT COMPLETE**.

After genuine G14 acceptance, G15 becomes the next live gate. G15 still requires its own scoped visible-browser owner grant and must stop before submit.
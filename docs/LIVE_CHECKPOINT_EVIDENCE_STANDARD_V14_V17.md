# Live Checkpoint Evidence Standard — V1.4 to V1.7

Owner requirement:
A checkpoint is not complete without genuine non-mock production-path evidence appropriate to that checkpoint.

## Common proof envelope

Every live proof should produce a redacted machine-readable evidence file containing:
- checkpoint/version,
- run ID,
- code commit SHA,
- runtime timestamp,
- real-vs-simulation declaration,
- canonical entity/artifact IDs,
- relevant hashes,
- source/evidence references,
- result,
- blockers/review items,
- verifier/reviewer reference.

Private contents remain local.

## V1.4 live proof

Must show:
real public job
→ real private candidate profile
→ exact genuine selected resume bytes
→ production packet
→ immutable artifacts
→ runtime candidate bundle
→ separate verifier PASS receipt.

Expected committed redacted evidence:
- V1.4 candidate bundle,
- verifier receipt,
- public job/source attestation.

No application submission.

## V1.5 live proof

Must show:
real live application page
→ exact accepted V1.4 packet
→ visible browser inspection
→ safe field classification
→ safe prefill only
→ exact file mapping
→ review boundary before submit.

Expected redacted evidence:
- real job/application URL identity,
- packet/resume hashes,
- form fingerprint,
- field classifications,
- fields filled vs left manual,
- prompt-injection warnings,
- file mapping hashes,
- pre-submit review manifest,
- browser/session mode = real visible.

Final submit is not required for V1.5 and must not occur unless separately authorized.

## V1.6 live proof

Must show:
exact desired real job
→ exact packet
→ current AUTO_ALLOWED destination policy
→ scoped owner authorization
→ idempotency/preflight
→ one real system submit
→ independent external confirmation
→ truthful application event/audit.

Expected redacted evidence:
- authorization record ID/hash,
- policy decision/version,
- attempt/idempotency ID,
- pre-submit manifest hash,
- external confirmation type/reference hash,
- final application/event IDs,
- packet/resume hashes.

No LinkedIn/Indeed automated submission.
No CAPTCHA/MFA bypass.

## V1.7 live proof

Must show genuine source evidence flowing through the real lifecycle path.

Preferred fastest method:
bounded historical Gmail read-only canary using existing real recruiting/application messages.

Proof should demonstrate one or more real threads sufficient to show:
- source message IDs/timestamps,
- contact/company/job/application linkage,
- multi-role/thread ambiguity behavior where present,
- recruiter response or lifecycle event,
- interview/follow-up/rejection/offer event when available,
- reconstructable timeline,
- idempotent replay,
- no wrong silent mutation.

Expected committed redacted evidence:
- Gmail canary/run ID,
- hashed/safe provider message references,
- linked entity IDs,
- lifecycle events,
- timeline digest with evidence refs,
- replay/idempotency result,
- review/ambiguity outcomes.

Do not commit private email bodies/tokens.

## Proof-state vocabulary

Use:
- LIVE_PROOF_PASS
- LIVE_PROOF_FAIL
- LIVE_PROOF_BLOCKED_USER_AUTH
- LIVE_PROOF_BLOCKED_PRIVATE_INPUT
- LIVE_PROOF_BLOCKED_PROVIDER
- LIVE_PROOF_BLOCKED_POLICY
- LIVE_PROOF_BLOCKED_NO_ELIGIBLE_TRANSPORT
- LIVE_PROOF_BLOCKED_OTHER

Never convert BLOCKED/FAIL into PASS.

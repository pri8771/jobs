# V2.3 Master Plan — ChatGPT Lead Review

Date: 2026-09-21

Reviewed planning commit:
- `b84f0c021c8cd3f28949cab0e7c98e601c152feb`

Verdict:
- **ACCEPT WITH LEAD CORRECTIONS**
- Planning quality is strong enough to integrate after the corrections below.
- The worker does not need to redo the planning pass.

## Accepted strengths

- Brownfield-first audit is materially useful and specific.
- Task decomposition is predominantly SP1/SP2 and suitable for Sonnet-class execution.
- Existing code is reused instead of broadly rebuilt.
- V2.3 is correctly designed to work without V3 agents.
- V3 compatibility is handled through typed tools, permission context, derived-artifact envelopes, scoped approvals, and audit identity rather than premature agent infrastructure.
- The test/adversarial matrix is substantially stronger than the previous coarse roadmap.
- The V2.3 acceptance campaign correctly distinguishes engineering fixture evidence from live evidence.
- Model routing is appropriately cost-conscious.

## Lead corrections — authoritative

### L1 — Real-life proof is mandatory for every version checkpoint

Owner directive:
**nothing is considered working/complete without an appropriate real-life production-path test.**

Engineering for later versions may proceed while a live/user gate is blocked, but formal acceptance remains sequential.

Therefore:
- V1.4 live proof is mandatory.
- V1.5 live visible-browser proof is mandatory.
- V1.6 real system-submission proof is mandatory.
- V1.7 real lifecycle proof is mandatory.
- V2.0 live acceptance is mandatory before V2.3 can be called REAL_PROVEN/COMPLETE.
- V2.3 requires its own real live campaign.

V2.3 engineering may proceed before earlier live gates clear, but it may not be labeled REAL_PROVEN/COMPLETE while an earlier required version is incomplete.

### L2 — V1.6 live submission is not optional for V2.3 completion

Fable D1 is modified:

- Decouple **engineering scheduling**, not acceptance.
- V1.6 transport research/implementation and first real submission may be worked when technically ready.
- A-V16-FIRST-REAL-SUBMISSION is mandatory before V2.0 LIVE_ACCEPTED and V2.3 REAL_PROVEN/COMPLETE.
- If no eligible compliant transport exists, the truthful state is `LIVE_PROOF_BLOCKED_NO_ELIGIBLE_TRANSPORT`; that blocks completion rather than being silently bypassed.

### L3 — Manual user attestation must not fabricate SUBMITTED truth

Fable D5 is modified.

A user-reported manual application creates:
- an application record with a truth-preserving unconfirmed state, preferably `SUBMISSION_UNCONFIRMED`,
- event `APPLICATION_SUBMISSION_REPORTED_BY_USER`,
- source `user_attestation`,
- exact resume/packet attribution.

It does **not** create `APPLICATION_SUBMITTED` or a confirmed-submission analytics count by itself.

A later accepted external confirmation signal (confirmation email/page/account state/provider reference) may advance truth to confirmed/submitted according to the canonical lifecycle contract.

Analytics must distinguish:
- user-reported/manual attempts,
- externally confirmed submissions.

### L4 — One implementation worker, one heartbeat watcher

Latest owner operating model is singular:

- one active implementation worker/session,
- exactly one active heartbeat watcher,
- fixed five-minute cadence,
- historical Lane 1/2/3/V23 branches are sequential work surfaces, not simultaneous workers.

The plan's PG1–PG4 groups remain useful as **dependency/parallelizability groups** and for lower-cost subagent analysis, but they do not authorize four concurrent implementation sessions.

Subagents may perform bounded independent analysis/tests when the parent worker owns integration and there is no conflicting write surface.

### L5 — Migration order follows version/truth dependencies

Canonical additive order:

- `004_v16_submission_truth`
  - generic `scoped_approval`
  - `submission_attempt`
  - `external_confirmation_evidence`

- `005_v23_intelligence_foundation`
  - opportunity graph
  - target-company watch
  - strategy experiment
  - message_link.contact_id

- `006_v3_agent_runtime_foundation` when V3 implementation begins

- optional FK/index cleanup after that only if justified.

This keeps P3 tool permission truth available before V2.3 and avoids V1.6 depending on V2.3 schema.

### L6 — V2.0/V2.3 live application evidence requires external confirmation

A real application record may originate from:
- an approved assisted/manual path,
- an approved system-submit path.

But any live acceptance assertion that the application was **submitted** must have external confirmation evidence.

A user-attested unconfirmed record may be used as real-world lifecycle input only with its uncertainty/state clearly preserved; it cannot satisfy the confirmed-submission checkpoint.

### L7 — Dedicated real test identity is authorized for bounded canaries

Owner authorization on 2026-09-21:
- ChatGPT/workers may use an existing owner-controlled account/email, or create/use a dedicated test email/account via the user's `unsubscriber` Google Cloud alias when available, for bounded real-provider integration tests.
- Controlled test messages between owner-controlled accounts are permitted for canary validation.
- This does not authorize unsolicited third-party messaging, employer submission, calendar mutation, or spending.
- A dedicated test identity proves provider/runtime integration; it does not replace genuine candidate/recruiting evidence where a milestone contract specifically requires it.

Actual account creation must use an available authorized tool/workflow; do not claim creation if the environment cannot perform it.

## Decisions ratified

Accepted as proposed or with the corrections above:
- D2 clean V1.5 port
- D6 independent exact-head sandbox validation while CI is account-blocked
- D7 deterministic-first V2.3
- D8 reuse-with-repair for Lane D opportunity graph

Modified:
- D1 → engineering can decouple; acceptance cannot
- D3 → one active implementation worker; PG groups are dependency groups
- D4 → migration 004 V1.6, 005 V2.3
- D5 → manual user report stays unconfirmed until external evidence
- D9 → V2.3 engineering may advance early; V2.3 REAL_PROVEN requires V2.0 LIVE_ACCEPTED and all earlier required live checkpoints

## Lead acceptance

After these corrections are reflected in the planning docs, the planning package is accepted for integration.

Next execution priority remains current Git truth:
1. close A-V14-P0A-INTEGRITY,
2. clean-integrate V1.4 proof tooling,
3. execute the genuine V1.4 proof when its private-input gate is explicitly opened,
4. continue artifact-by-artifact while preparing V2.3 work ahead of blocked live gates.


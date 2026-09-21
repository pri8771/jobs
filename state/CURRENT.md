# Current State

Updated: 2026-09-21 lead review

## Product target

Primary near-term goal:
**V2.3 genuinely working with real-life evidence.**

V3 is architecture-compatible but broad V3 runtime/specialist implementation is deferred until V2.3 works unless ChatGPT explicitly advances a small compatibility artifact.

## Operating model

- User = product owner/final authority.
- ChatGPT = engineering/product lead and acceptance gate.
- One active implementation worker/session at a time.
- One active five-minute heartbeat watcher.
- Historical lane branches are sequential work surfaces, not simultaneous workers.
- Lower-cost subagents may do bounded independent analysis/tests under the parent worker.

## Fable planning review

Planning source:
- branch `claude/serene-brown-g6uij0`
- original Fable commit `b84f0c021c8cd3f28949cab0e7c98e601c152feb`

Lead verdict:
**ACCEPT WITH CORRECTIONS**

Authoritative lead review:
- `docs/V23_LEAD_REVIEW_20260921.md`

Accepted plan strengths:
- brownfield-first,
- 131 small engineering tasks,
- predominantly SP1/SP2,
- cost-aware Sonnet/Opus/Haiku routing,
- deterministic V2.3,
- V3-compatible typed tool/permission/audit contracts,
- machine-verifiable engineering + live campaigns.

Lead corrections:
- one implementation worker, not three lanes,
- real-life proof mandatory for V1.4/V1.5/V1.6/V1.7/V2.0/V2.3,
- V1.6 live system submission cannot be bypassed for formal V2.3 completion,
- user-reported manual application remains `SUBMISSION_UNCONFIRMED` until external confirmation,
- canonical migrations: 004 V1.6, 005 V2.3, 006 V3,
- dedicated owner-controlled test identity/mailbox canaries authorized as documented.

## Formal version truth

| Checkpoint | Engineering | Real-life evidence | Formal status |
|---|---|---|---|
| V1.4 | packet engineering accepted; P0A still needs final accepted verifier repair | missing | NOT COMPLETE |
| V1.5 | substantial assisted-safety code exists on historical branch | missing | NOT COMPLETE |
| V1.6 | contracts/scaffolding exist; safe submit engineering incomplete | missing | NOT COMPLETE |
| V1.7 | substantial CRM/interview/lifecycle code merged | missing | NOT COMPLETE |
| V2.0 | substantial dashboard/analytics/reliability foundations exist | missing | NOT COMPLETE |
| V2.3 | detailed lead-reviewed plan exists; some graph source code exists historically | missing | NOT COMPLETE |

## Current P0

Artifact:
`A-V14-P0A-INTEGRITY`

Historical active source:
`worker/v14-real-proof`

Current active branch still has two known defects:
1. DB evidence can be omitted;
2. source attestation lacks persisted Greenhouse JobSource binding.

Support branch:
- `worker/jobs-v14-p0a-remaining-fix-20260921-1545`
- `062ca922c640d964220b550a06f61288b9a040c9`

Lead diff review says the support commit directly targets both defects and adds adversarial cases, but it is not accepted until exact behavior/tests/integration are reviewed.

Next:
audit/port support fix → adversarial suite → full exact-head checks → lead review.

No private candidate/resume proof before P0A acceptance.

## Live proof sequence

Required:
- V1.4 genuine packet proof,
- V1.5 real visible-browser assisted proof to review boundary,
- V1.6 real system submission through a compliant supported transport with independent external confirmation,
- V1.7 real Gmail/recruiter lifecycle proof,
- V2.0 real integrated OS campaign,
- V2.3 real Career Intelligence campaign.

Engineering may move ahead of a blocked user/live gate, but formal completion may not skip it.

## Test identity authorization

Owner authorizes bounded real provider canaries using:
- an existing owner-controlled identity, or
- a dedicated account/email via the owner's `unsubscriber` Google Cloud alias if available tooling can actually create/use it.

Controlled messages between owner-controlled accounts are allowed for canaries.

No third-party outreach, employer submission, calendar mutation, or spending is implied.

## CI / heartbeat

GitHub Actions recently failed before executing workflow steps (`runner_id: 0`), so use `CI_BLOCKED_ACCOUNT` unless newer evidence changes that.

Historical V1.4 heartbeat:
- last #18 at 19:18:36Z,
- stale now.

Before the next implementation session starts/restarts:
- verify old watcher is dead,
- start exactly one `FIVE_MIN_2026_09_21` / `ACTIVE_5M` watcher on the chosen active work surface.

## Safety

- no fabricated candidate facts,
- no CAPTCHA/MFA/anti-bot/rate-limit bypass,
- LinkedIn/Indeed auto-submit remain MANUAL_ONLY,
- external content is untrusted,
- user attestation alone never becomes confirmed submission truth,
- external confirmation is required for real submission truth.

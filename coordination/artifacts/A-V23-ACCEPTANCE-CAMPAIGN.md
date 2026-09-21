# A-V23-ACCEPTANCE-CAMPAIGN

- Type: acceptance evidence / integration regression + live proof
- Phase: V2.3
- Status: PROPOSED
- Owner: V2.3 implementation surface + eligible machine for the live overlay + ChatGPT
- Reviewer: ChatGPT (worker-pc may independently re-run the verifier)
- Story points: 5 engineering (V23-AC-01..03) + 1 LIVE (V23-AC-04)
- Dependencies: A-V20-INTEGRATION-FIXTURE (golden scenario), A-V23-CAREER-BRIEFING, all A-V23 services; live overlay additionally depends on accepted V1.4, V1.5, V1.6, V1.7 and V2.0 live checkpoints, A-V20-LIVE-INGESTION, ≥1 externally-confirmed real application, owner-supplied target list
- Downstream: A-V23-CAREER-INTELLIGENCE `ENGINEERING_ACCEPTED` / `REAL_PROVEN`

## Purpose

Make V2.3 acceptance machine-verifiable: one deterministic engineering campaign report (explicitly simulated) and one live campaign report over real data, both checked by `scripts/verify_v23_campaign.py`, which fails closed.

## Inputs

Fixture: the V2.0 golden scenario extended with V2.3 steps 18–30. Live: real Gmail ingestion, real resume identity, real applications with accepted external confirmation (origin may be assisted/manual/system-submit), real target companies fetched from approved public JSON APIs.

## Outputs

`artifacts/reports/v23_engineering_campaign_report.json` (gitignored), `coordination/proofs/v23_live_campaign_report.redacted.json` + `v23_campaign_receipt.json` (committed, redacted per allowlist).

## Scope

Procedure and verifier in `docs/V2_3_ACCEPTANCE_CAMPAIGN.md`.

## Non-goals

No system submission, messaging, calendar mutation or outreach is part of this campaign.

## Acceptance criteria

- engineering report: all assertions pass, `simulated=true`,
- live report: `simulated=false`, `gmail_mode=REAL`, no fixture markers, all entity ids resolvable, rates consistent, code SHA bound, verifier receipt `V23_CAMPAIGN_PASS`,
- honest low-N outputs are acceptable; fabricated certainty is a FAIL.

## Evidence required

Reports, verifier receipt, commit SHAs, validation records, redaction review.

## Source/code paths

`tests/integration/test_v23_campaign.py`, `scripts/verify_v23_campaign.py`, `docs/V2_3_ACCEPTANCE_CAMPAIGN.md`.

## Risks

Gate timing (private inputs, OAuth, target list) governs when the live overlay can run; engineering acceptance is independent of those gates.

## Current notes

Task specifications: `docs/V23_TASK_GRAPH_V23.md` §8. Result vocabulary: `V23_CAMPAIGN_PASS | V23_CAMPAIGN_FAIL | LIVE_PROOF_BLOCKED_*`.

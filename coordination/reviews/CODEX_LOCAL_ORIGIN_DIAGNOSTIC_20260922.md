# J20-01 local write origin boundary — diagnostic review

Recommendation: **REWORK_FOUND**. This is a repair request, not implementation or formal acceptance.

- Repository: pri8771/jobs.
- Accepted source: `413a18ee13ee049f57651ddd7060fd98fafad5f9`, tree `f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6`; origin and clean import identity verified before and after.
- Native diagnostic release: `4fb94fa544476f7d10d99a6bc8b097c94450f1c2`, J20-01 in `coordination/codex/GOAL_20260922.md`.
- Reviewer: Codex integration/review-preparation agent. One bounded agent ran the diagnostic, root independently repeated it, and a separate agent reviewed the cause and compatible repair. ChatGPT remains formal acceptance authority.

The source inventory found one mutation route, `POST /api/reviews/{id}/resolve`. Twenty direct production-handler cases used a fresh, disposable PostgreSQL database. Remote unauthenticated requests, incorrect configured tokens, disabled local writes and unsupported methods fail closed without a database session. Legitimate loopback and valid-token requests change only the selected task.

The first gap is the tokenless loopback fallback: a request with local TCP peer and Host but `Origin: https://foreign-origin.example` and a JSON body labelled `text/plain` receives HTTP 200 and commits review completion. `_authorize_write_operation` checks peer and local-write configuration but ignores the explicitly foreign initiating origin. Both independent runs retained full synthetic before/after row snapshots and cleaned their unique databases to count zero. No listener, browser or external operation was opened.

This proves server-side acceptance and durable mutation; it does not prove browser transmission, PNA/CORS exploitability, DNS rebinding, or remote TCP authentication bypass. Media type is supporting evidence, not the causal authorization decision.

## Smallest proposed repair and release request

Confine the change to the tokenless local authorization branch and focused handler checks. Preserve the configured exact-token path. Require a valid loopback Host authority for tokenless HTTP requests. If Origin is present, require a strictly parsed local HTTP origin matching that authority and effective port; reject foreign, opaque/null, malformed and mismatched origins. Preserve local tools without Origin and same-origin dashboard requests; cross-site browser metadata should not confer local authority. Explicitly decide mandatory Host handling so existing synthetic helpers are updated without silently exempting production requests.

Requested ChatGPT verdict: confirm the finding and release this bounded source repair from exact `413a18e`, including its final header matrix and actual PostgreSQL no-mutation proof. Remaining read completeness and task-type/status questions are untested because the native stop-at-first-gap rule was honored; do not release a speculative UI or broader security rewrite.

## Evidence and remaining gates

[Evidence directory](../codex/evidence/CODEX-LOCAL-ORIGIN-DIAGNOSTIC-20260922/) contains the original diagnostic, exact reproducer, commands, results, independent root repeat, separate source review, and SHA-256 manifest. The previously accepted config projection remains accepted at release `4fb94fa`; this new finding does not claim its behavior changed.

Engineering evidence only. Genuine G14–G17 remain open. No Fable handoff, real mailbox/application/model/public action, spend, scheduler change, deployment, main merge or acceptance occurred. Implementation remains held pending the concrete repair release.

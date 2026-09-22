# J20-01 strict tokenless-local authority repair

Recommendation: **RECOMMEND_ACCEPT — bounded engineering repair only.** ChatGPT remains the formal acceptance authority.

- Repository: `pri8771/jobs`.
- Released base: `413a18ee13ee049f57651ddd7060fd98fafad5f9`, tree `f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6`.
- Candidate: `b67fc523863babd3e195ee71a05f00fa0f2f7e79`, tree `0338b7ef26bb727536175d975513976a068a9720`.
- Release authority: `codex/portfolio-review-20260922@0f5522b1b84680622bf49d362da1a7a59cf2d252`.
- Review preparation: Codex root; focused test work by a bounded agent; pre-repair causal review by a separate bounded agent. Neither is formal acceptance.

## Repair

The configured `DASHBOARD_WRITE_TOKEN` branch is unchanged. Tokenless writes now require an enabled local-write flag, an actual loopback peer, exactly one valid loopback `Host`, and, when present, an `http` Origin matching the normalized Host and effective port. `Sec-Fetch-Site` may be absent, `same-origin`, or `none`; other values deny. `null`, malformed, foreign, HTTPS, duplicate, and port-mismatched authority data fail closed before database access. No-Origin local tools remain supported.

The implementation uses parsed IP loopback checks, normalizes equivalent IPv6 loopback spellings, bounds ports, does not trust proxy headers, and rejects the earlier `testclient` shortcut as production authority. Existing test-only handlers now provide an explicit Host where they intentionally exercise a tokenless local write.

## Evidence

The accepted-base focused regression suite had 24 failures and 15 passes. The final focused selection passed 48 tests. The complete test suite passed **527**, with one existing host-specific skip because `127.0.0.2` cannot bind on this Mac. Ruff passed for `src` and `tests`; mypy passed for 74 source files. A formatter check records inherited unrelated formatting in `tests/test_dashboard.py`; the two changed test files are formatted and the repair diff is clean.

The source-bound production-handler PostgreSQL matrix ran 46 cases against an owned Unix-socket database. Every rejection opened no database session and changed no row. Allowed tokenless local, matching-origin, equivalent IPv6, default-port, exact-token, and Bearer-token paths changed only the selected synthetic review row. The disposable database was removed and source was clean afterward.

The direct handler/SQL evidence proves the repaired server boundary. It does not claim browser PNA/CORS behavior, remote-TCP bypass, a live hiring event, or any G14–G17 proof.

## Requested verdict

Please accept or reject this exact candidate and evidence. If accepted, retain the native stop after this repair: do not resume broader J20-01 inventory until the formal verdict. Genuine Jobs V2.0 gates remain open.

Evidence: [CODEX-LOCAL-ORIGIN-REPAIR-20260922](../codex/evidence/CODEX-LOCAL-ORIGIN-REPAIR-20260922/).

# Independent review: Jobs tokenless-loopback write origin boundary

Source reviewed: `413a18ee13ee049f57651ddd7060fd98fafad5f9` (tree `f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6`). Native control ref: `4fb94fa544476f7d10d99a6bc8b097c94450f1c2`.

## Disposition

The causal server finding is valid. Native J20-01 requires every write endpoint to be local-only/auth-protected or unavailable remotely and specifically asks the diagnostic to prove client-origin/auth behavior. `DashboardRequestHandler._authorize_write_operation` accepts tokenless writes solely from `client_address` plus `DASHBOARD_ALLOW_LOCAL_WRITE` (`server.py:842-883`). It does not inspect `Host`, `Origin`, or fetch metadata. `do_POST` invokes that gate before `/api/reviews/{id}/resolve`, then commits `status="completed"` and resolution notes (`server.py:885-922`). The retained synthetic production-handler/PostgreSQL case therefore proves a real authorization-boundary behavior: a loopback-peer request carrying an explicitly foreign Origin and Host is accepted and commits a mutation.

The evidence does **not** prove an end-to-end browser exploit. A direct handler invocation does not establish whether a particular browser/version would transmit the request after Private Network Access, mixed-content, CORS/preflight, secure-context, or permission checks. CORS alone is not a reliable write defense because it normally governs response access, while a qualifying simple request can still be transmitted; PNA behavior is browser- and version-dependent. DNS rebinding is also only a plausible route, not demonstrated here. The finding should be described as server-side acceptance of untrusted browser-origin metadata at a tokenless local operator boundary, with browser exploitability unproven.

`Content-Type: text/plain` is accepted because the handler parses the body as JSON without checking media type (`server.py:904-906`). That makes a simple-request-shaped input possible, but it is supporting evidence rather than the root authorization defect.

## Smallest compatible rule

Keep the configured-token branch unchanged: an exact operator token remains explicit authority independent of Host/Origin.

For the tokenless loopback fallback, require all of:

1. `DASHBOARD_ALLOW_LOCAL_WRITE` is enabled and the TCP peer is loopback, as today.
2. `Host` parses to an explicit loopback authority: `localhost`, `127.0.0.1`, or `[::1]`, with an optional valid port. Reject missing, malformed, userinfo-bearing, or non-loopback Host on real HTTP requests. Tests may need to supply the mandatory HTTP/1.1 Host header rather than treating its omission as a production client.
3. If `Origin` is absent, allow the request for local CLI/script compatibility. If present, parse it strictly and require an HTTP loopback origin whose normalized host and effective port match `Host`; reject `null`, malformed, foreign, or mismatched origins. This preserves the same-origin local dashboard while rejecting the reproduced foreign-origin request and DNS-rebinding-shaped foreign Host.

This rule does not require a token from existing no-Origin CLI clients that address the service through `localhost`, `127.0.0.1`, or `[::1]`. Clients using another hostname or a reverse proxy should use the existing token path. Requiring `application/json` could be added separately as defense in depth, but it is not necessary to close the demonstrated authority mismatch and could create needless compatibility impact.

Focused regressions should show: foreign Origin/local Host denied; foreign matching Origin+Host on loopback peer denied; `Origin: null` denied; same-origin local UI accepted; no-Origin local CLI with local Host accepted; configured valid token accepted regardless Origin/Host; malformed/missing Host fails closed in tokenless production-shaped requests; no database mutation on every denial.

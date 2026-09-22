# Superseded harness-field diagnosis

The initial exact-runtime report at source `b5d5ce206142642fa39fc4e836e69e069d70bf8e` correctly showed:

- `/api/health` returned `DEGRADED`;
- the actual embedded script called `/api/health`, `/api/funnel`, and `/api/sources`;
- the badge rendered `Degraded` with class `status-badge health-degraded`.

Its separate `header_has_health_fetch=false` field was a harness-only false negative: the check expected the exact substring `fetch('/api/health')`, while production correctly used `fetch('/api/health', { cache: 'no-store' })`. The final harness corrected that diagnostic assumption and reports the field true. This was not a product defect and did not invalidate the rendered runtime result.

# COMP-2_REWORK_FOUND — exact off-engine dependencies

Authority: lead activation `5b06336d0c54ed9f3ff3a4eccac779cefa05a65e` permits engine-only composition and requires stopping when another production file is needed.

Inputs: accepted control `b67fc523863babd3e195ee71a05f00fa0f2f7e79`; accepted canary/typing `eec0ae3d9b50979b74294dd9ee0561172eff54b0`; reference-only `2969ac28364e9c39bbaf5c94b4c7cfe97ca5699a`. The isolated composition worktree remains clean at b67. No source edits, DB/Gmail calls or full suites were performed for this diagnostic.

Independent mechanical review loaded the exact control Gmail parser with the accepted canary engine, using an in-process raw-message fixture. Results:

| Malformed header | Valid canary header | Parsed recipients | Engine canary detection |
|---|---|---|---|
| From | To | Alias retained | yes |
| Cc | To | empty | no |
| To | Cc | empty | no |

The smallest demonstrated dependency is `src/jobs_automation/adapters/gmail.py`: control combines To and Cc before parsing (lines243–247), while accepted canary source parses each independently. Engine-only changes cannot restore recipient bytes already discarded by its adapter. This prevents the explicitly required malformed-neighbor regression from passing.

Also:

- `core/platforms.py` on control lacks the accepted `canary_identities` field/validator; a valid alias configuration fails `extra_forbidden`. Its strict accepted policy cannot be established by engine.py alone.
- `ingestion/bounded.py` on control lacks accepted V3/replay APIs. Reference2969 changes bounded.py, not engine.py. Engine-only work must not claim that reference integrated.
- Wholesale canary test import requires missing V3 APIs and `db/canary_provenance.py`; do not silently import these production dependencies under a test-only allowance.

The engine port itself is feasible. Preserve control's `_link_candidate_reply` and outbound attribution branch; replacing engine wholesale with the canary version would remove that accepted behavior. Preserve the existing incomplete-poll guard before writes/checkpoint updates while adding canonical/historical canary helpers, runtime membership, safe_errors and reclassification.

Requested lead choice: release the bounded accepted Gmail/config prerequisites, or narrow this step to engine API preparation with the integrated claims explicitly deferred. Full V3/reference composition needs an explicit bounded.py prerequisite disposition. No other lifecycle/alerts/CRM/worker/dashboard conflict is resolved by this report.

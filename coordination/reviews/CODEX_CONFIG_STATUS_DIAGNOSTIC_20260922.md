# Jobs A-V20-CONTROL-CENTER — missing config-validation status projection

## Identity and disposition

- Exact accepted source: `1e54aafa61ef06ed2ef8a7a681c806ba89ef3268`
- Tree: `8972a90de1f7aafd469fedde63926382c726319f`
- Release: Jobs coordination `a0d07a5`, final `GOAL_20260922.md` section.
- Contract: `coordination/artifacts/A-V20-CONTROL-CENTER.md`, criterion “safe read-only config/status views”.
- Recommendation: **REWORK_FOUND, subject to lead interpretation of that criterion.** The contract does not prescribe a route name or response schema.

The evidence is not based on guessed URLs alone. It enumerates the complete current GET dispatcher and every embedded operator tab. None projects configuration validation state from `ConfigLoader` or an equivalent source.

## Complete current read-surface inventory

`DashboardRequestHandler.do_GET` spans `src/jobs_automation/dashboard/server.py:524–812`. Its complete route set is:

| Source lines | Route | Current subject |
|---|---|---|
| 528–530 | `/`, `/index.html` | embedded dashboard HTML |
| 533–536 | `/api/funnel` | funnel analytics |
| 538–541 | `/api/sources` | source breakdown |
| 543–546 | `/api/kanban` | application pipeline |
| 548–567 | `/api/jobs` | discovered jobs |
| 569–587 | `/api/reviews` | pending review tasks |
| 589–615 | `/api/interviews` | interviews |
| 617–637 | `/api/contacts` | recruiter contacts |
| 639–658 | `/api/audit` | audit events |
| 660–663 | `/api/health` | `HealthCheckService.run_full_check()` component health |
| 665–689 | `/api/followups` | follow-up tasks |
| 691–694 | `/api/analytics/sources` | source performance |
| 696–699 | `/api/analytics/roles` | role-family performance |
| 701–704 | `/api/analytics/resumes` | resume performance |
| 706–709 | `/api/analytics/time-to-stage` | stage timing |
| 711–735 | `/api/timeline` | application/contact message timeline |
| 737–764 | `/api/offers-rejections` | terminal/offer outcomes |
| 766–782 | `/api/policies` | persisted policy-registry rows |
| 784–810 | `/api/worker` | current and legacy worker history |
| 812 | every other GET | 404 |

The embedded navigation is also complete and has seven tabs at `server.py:98–105`: Funnel Analytics, Kanban Pipeline, Discovered Jobs, Review Queue, Interviews, Recruiter CRM, and Audit Trail. Corresponding tab containers are at lines 110, 154, 161, 183, 203, 222, and 242. None is a configuration-validation or configuration-status view.

`server.py:18–29` imports analytics, database models, `HealthCheckService`, and recruiter CRM. It does not import `ConfigLoader`, `ConfigValidationReport`, `AppSettings`, or another configuration-status projector. A source search of the entire dashboard package finds no `ConfigLoader` or `validate_all` reference.

`/api/health` and `/api/policies` cannot silently satisfy this remaining item because the same formal continuation release lists them separately as criterion 7 (Gmail/source/worker/database health) and criterion 8 (policy registry + kill-switch visibility), followed by criterion 9 (safe read-only config/status views). In code, `/api/health` delegates only to `HealthCheckService` (`server.py:660–663`), while `/api/policies` serializes `PolicyRegistryModel` rows (`server.py:766–782`). Neither calls the existing configuration validator.

## PostgreSQL production-handler confirmation

A unique migrated disposable Jobs PostgreSQL database exercised the production handler. Known routes proved the handler/session path was live:

- `GET /api/jobs` -> HTTP 200 + `[]`
- `GET /api/policies` -> HTTP 200 + `[]`

Probes `/api/status`, `/api/config`, and `/api/system-status` each reached the generic 404. These 404s are supporting runtime confirmation, not the basis for claiming those exact names are required. The material finding is that the exhaustive dispatcher/tab inventory contains no configuration-validation projection under any name.

Original database `jobs_control_status_b898062a5dd2`: migration exit 0, workflow exit 0, cleanup count 0. An independent integration-owner repeat used distinct database `jobs_control_status_7e79864e4de9` with the same result and cleanup count 0.

## Existing source and smallest lead decision

`ConfigLoader.validate_all()` already computes success, errors, warnings, unresolved facts, and loaded-file paths (`core/config.py:107+`). Raw output is not safe to serialize: errors may contain local paths; unresolved facts are candidate-private; loaded-file values are host paths. `AppSettings` includes database URL, Gmail client material, token path, model gateway URL/key, environment, and log level (`core/config.py:18–32`) and must not be serialized wholesale.

The lead must decide whether criterion 9 requires an API projection, a visible dashboard panel, or both, and must define the endpoint name/schema. The smallest safe data contract should initially stay limited to:

- validation state (`VALID`, `INVALID`, or sanitized `UNAVAILABLE`);
- error and warning counts;
- per-category unresolved-fact counts;
- logical config names loaded, never filesystem paths.

Until the lead expands the allowlist, omit environment, log level, raw errors/warnings, private facts, all config values, paths, URLs, identifiers, credential/provider values, and mailbox content. A failure should return a sanitized unavailable/invalid state without exception text. The bounded repair should be GET-only and prove no database mutation and no secret-shaped value in serialized bytes.

No exact route name or source change is authorized by this diagnostic. Other remaining control-center items were not investigated after this first gap. Accepted health-badge behavior is unchanged and was not regressed.

## Evidence

Exact command:

```text
/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-control-center-config-status-run.py > /tmp/jobs-control-center-config-status-wrapper.log 2>&1
```

Artifacts:

- `/tmp/jobs-control-center-config-status-repro.py`
- `/tmp/jobs-control-center-config-status-run.py`
- `/tmp/jobs-control-center-config-status-wrapper.log`
- `/tmp/jobs-control-center-config-status-20260922/{migration.log,workflow.log,report.json,run.json}`
- `/tmp/jobs-control-center-route-lines.txt`
- independent repeat: `/tmp/jobs-control-center-config-status-independent-run.py`, wrapper log, and `/tmp/jobs-control-center-config-status-independent-20260922/`

No repository source/test/coordination file was edited. A-V20-CONTROL-CENTER remains incomplete.

Native [hashed evidence](../codex/evidence/CODEX-CONFIG-STATUS-DIAGNOSTIC-20260922/manifest.json).

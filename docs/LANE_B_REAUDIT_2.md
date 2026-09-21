# Lane B Final Re-Audit Residuals — V1.7 / V2.0

Reviewed:
- `33d18b4`
- prior B commits rebased on accepted V1.4

Overall:
The first re-audit repairs are materially improved. Keep them.

Remaining bounded issues:

## B-R17-03 — background check is evidence, not proof of offer (SP2)

Current LifecycleEngine maps:
`BACKGROUND_CHECK -> (OFFER_RECEIVED, BACKGROUND_CHECK_INITIATED)`.

A background check can occur before a formal offer. Do not fabricate OFFER_RECEIVED merely from background-check evidence.

Required:
- BACKGROUND_CHECK records its event,
- preserve current application stage unless separate offer evidence exists,
- if product wants a dedicated BACKGROUND_CHECK status later, model it explicitly rather than aliasing it to OFFER_RECEIVED,
- tests:
  - INTERVIEWING + BACKGROUND_CHECK -> state remains INTERVIEWING + event recorded,
  - OFFER_RECEIVED + BACKGROUND_CHECK -> remains OFFER_RECEIVED,
  - no OFFER_EXTENDED event is synthesized.

## B-R20-07 — simulation must never count as real submission (SP1)

Current `_is_real_submission()` excludes `application_mode == "simulation"` but the existing auto engine uses:
- status = SIMULATED
- application_mode = auto_simulated
- applied_at populated

That can enter analytics as a real submission.

Required:
- exclude status SIMULATED,
- exclude application modes indicating simulation/mock/test including auto_simulated,
- external evidence semantics remain authoritative,
- tests for auto_simulated + applied_at -> false.

## B-R20-08 — final-interview and acceptance outcomes (SP2)

A-V20 analytics requires response/screen/interview/final/offer/acceptance views where evidence exists.

Add evidence-backed flags/metrics:
- ever_final_interview only when interview/event evidence identifies final/panel/final round,
- ever_accepted from OFFER_ACCEPTED/ONBOARDING evidence,
- source/role/resume outputs should expose accepted count/rate,
- do not infer "final" from any generic interview.

## B-R20-05 / J20-14 — finish crash-durable worker-run evidence (SP3)

Current end-of-sweep `worker_sweep` audit telemetry is useful but not sufficient.

Use:
- docs/WORKER_RUN_HISTORY_REPAIR_GUIDE.md

Preferred implementation:
- no new schema migration,
- AuditLog-backed begin/finalize records with stable run_id,
- durable RUNNING before pipeline work,
- SUCCESS/PARTIAL/FAILED/KILLED finalize evidence in separate transaction/session,
- stale RUNNING detection,
- last attempt / last success / last error / last reconciliation health fields,
- pipeline rollback cannot erase operational run evidence.

Do not store secrets/email bodies.

## Gmail integration

Do NOT implement J20G-04 until Lane C J20G-03 exists.
Current fail-safe NOT_INTEGRATED behavior is acceptable interim behavior.

## Exit

After B-R17-03, B-R20-07, B-R20-08, B-R20-05:
- targeted tests
- full pytest
- Ruff
- mypy
- push to existing PR #3
- heartbeat -> READY FOR CHATGPT LANE B FINAL REVIEW

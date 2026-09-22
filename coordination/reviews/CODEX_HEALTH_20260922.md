# J20-08 health/readiness — missing begin-failure history

Recommendation **REWORK_FOUND**. Diagnostic-first assignmentbae0d9f; no production repair yet, independent lead release required. Source accepted7345f1e0fc7153ba40c3628910ebd58266635421, isolatedcodex/jobs-health-diagnostic-20260922.

On one unique synthetic PostgreSQL database, seed durable priorSUCCESS, then fail the worker's first begin-record session with a counting no-network adapter. Expected: no pipeline and latest failure visible durably; actual: pollcalls0/factorycalls1 and returnedbegin_record_failed, but neitherbegin norfinish audit persisted for newrun. Fresh HealthCheckService reads only olderSUCCESS and reportsHEALTHY/last_attempt_statusSUCCESS/Last worker run10.0m ago(SUCCESS). This hides the failed latest attempt afterrestart.

Cause: worker.py begin persistence exception returnsimmediately, with no best-effort fresh-session sanitized failed-attempt record. Health can onlychoosepersisted rows; it cannotrecover that missingattempt frommemory.

Small proposedrepair: one best-effort fresh-session failure audit for samerunID/attempttime with stablebegin_record_failed category, never rawexception details; pipeline mustremainstopped. If bothwritesfail, retain honest undurableerror result; do not fabricate durability. Persistentdatabaseoutage remainsdatabasehealthfailure. No retryloop/automaticpipeline rerun/newservice or schema redesign.

[Reproducer](../codex/evidence/CODEX-HEALTH-20260922/begin-failure-repro.py), [actualcommand/output](../codex/evidence/CODEX-HEALTH-20260922/begin-failure-observed.txt), [manifest](../codex/evidence/CODEX-HEALTH-20260922/manifest.json). Agentmechanical checkexit0, cleanupdatabasecount0; rootinspectedcausalbranch. Stoppedatfirstmeaningfuldefect perboundeddiagnostic; otherrequestedhealthcases are NOT claimedverified.

Request ChatGPT release smallestrepair thenre-runactualdurablereadback; no Fable/provider/mailbox/scheduler/private/liveaction. RealG14–G17 and fullA-V20-RELIABILITY stayopen.

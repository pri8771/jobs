# V2.0 Brownfield Lead Audit

Artifacts:
- A-V20-CONTROL-CENTER
- A-V20-RELIABILITY
- A-V20-ANALYTICS
- A-V20-LIVE-INGESTION
- A-V20-INTEGRATED-OS

## Executive conclusion

A large portion of the old V1.8/V1.9 vision already exists.

V2.0 should be achieved by:
- validating existing components,
- repairing false-readiness and recoverability gaps,
- adding missing resume/source analytics,
- integrating real Gmail/live data,
- proving the system as one operating loop.

## Control center baseline

Existing dashboard already exposes:
- funnel
- source counts
- Kanban/application pipeline
- jobs
- human review queue
- interviews
- recruiter contacts
- audit trail

This is substantial existing coverage.

### Missing/high-value gaps

1. No explicit Gmail/source/worker health surface.
2. No policy/kill-switch operational status surface.
3. No recruiter communication timeline per application in dashboard.
4. No clear follow-up queue view distinct from generic review queue.
5. No dedicated offer/rejection operational view.
6. Review resolution POST is a mutable action; localhost binding reduces exposure but V2.0 should make write controls deliberately safe if dashboard exposure expands.

Do not rewrite the dashboard framework unless a measured blocker requires it.

## Reliability findings

### 1. Health adapter check can overstate readiness

HealthCheckService.check_adapters() marks registry presence as HEALTHY.

But registered ATS adapters may be NOT_IMPLEMENTED for live execution.

Required:
- health distinguishes registered vs live-capable,
- simulation-only/not-implemented adapters cannot be reported as active live automation.

### 2. Health is missing Gmail/worker execution truth

Add health/evidence for:
- Gmail configured/authenticated or unavailable,
- last successful ingestion,
- last reconciliation,
- last worker sweep,
- last sweep errors,
- queue/review backlog.

### 3. No durable worker-run history

Worker returns an in-memory result dict but does not persist run history.

Required:
- durable WorkerRun/JobRun record or equivalent audit event,
- start/end/status/counts/errors/reconciliation,
- dashboard/health can report last run.

### 4. Backup/restore checksum policy is weaker than recorded architecture decision

restore_db.sh currently proceeds with a warning if checksum file is absent.

Existing project decision says restore requires explicit checksum verification.

Required:
- missing checksum fails closed unless an explicit emergency override exists and is auditable,
- add a reproducible backup/restore drill.

### 5. Backup scripts contain default DB password fallback

DB_PASSWORD defaults to "jobs".

For local dev this may be convenient, but production/recovery readiness should not silently use a default credential.

Required:
- fail closed or require explicit opt-in dev defaults,
- never echo secret.

### 6. Migration verification should cover full chain

V2.0 reliability needs:
- upgrade from base to head,
- downgrade/recovery expectations,
- migration test in CI or documented supported boundary.

## Analytics findings

Existing FunnelAnalyticsService covers broad funnel counts/conversions.

Missing for owner requirements:
- resume family
- exact resume variant/version
- role family/title cluster
- source performance by outcome
- time-to-response/stage
- sample-size warnings

Use immutable ResumeVariant/ApplicationPacket/ApplicationEvent evidence added in V1.4.

## Integrated worker risk

Worker lifecycle processing currently lacks durable idempotency/processed evidence, covered in V1.7 audit. V2.0 cannot be accepted until that is fixed.

## Live ingestion

Real Gmail remains a user-interactive boundary.

Engineering can prepare:
- diagnostics
- bounded canary
- no-mock evidence output
- idempotency proof

Full V2.0 live acceptance requires actual runtime Gmail authorization and real data evidence.

## V2.0 acceptance strategy

Do not require every historical roadmap bullet to become a new subsystem.

Accept V2.0 when:
- V1.7 evidence lifecycle is accepted,
- dashboard covers daily decisions,
- worker/health truth is durable,
- backup/migration recovery is proven,
- analytics include resume/source/role outcomes,
- real Gmail canary works,
- safe application path remains policy/human gated,
- one end-to-end real-data scenario is reconstructed in dashboard/audit.
